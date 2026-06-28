"""Telemetry pipeline controller — routes decoded readings to storage, alerts, and dashboards.

Manages sensor health via rolling windows. Triggers alerts on threshold breaches.
Feeds a ring buffer for time-series queries without external DB.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from alpha.telemetry_decoder import (
    SensorType,
    TelemetryDecoder,
    TelemetryReading,
)


@dataclass
class Threshold:
    sensor_type: SensorType
    min_val: float
    max_val: float
    window_size: int = 10
    consecutive_breaches: int = 3


@dataclass
class Alert:
    sensor_id: int
    sensor_type: SensorType
    value: float
    threshold: Threshold
    timestamp: float
    severity: str = "WARNING"


class SensorHealth:
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._values: deque[float] = deque(maxlen=window_size)
        self._timestamps: deque[float] = deque(maxlen=window_size)
        self.breach_count: int = 0

    def push(self, value: float, timestamp: float):
        self._values.append(value)
        self._timestamps.append(timestamp)

    @property
    def mean(self) -> float:
        return sum(self._values) / len(self._values) if self._values else 0.0

    @property
    def variance(self) -> float:
        if len(self._values) < 2:
            return 0.0
        m = self.mean
        return sum((v - m) ** 2 for v in self._values) / (len(self._values) - 1)

    @property
    def std_dev(self) -> float:
        return self.variance ** 0.5

    @property
    def rate_of_change(self) -> float:
        if len(self._values) < 2:
            return 0.0
        dt = self._timestamps[-1] - self._timestamps[0]
        if dt <= 0:
            return 0.0
        return (self._values[-1] - self._values[0]) / dt


class TelemetryController:
    def __init__(self, decoder: Optional[TelemetryDecoder] = None):
        self.decoder = decoder or TelemetryDecoder()
        self.decoder.register_callback(self._on_reading)
        self.thresholds: list[Threshold] = []
        self._health: dict[int, SensorHealth] = {}
        self._ring_buffer: deque[TelemetryReading] = deque(maxlen=10000)
        self._alerts: deque[Alert] = deque(maxlen=1000)
        self._alert_callbacks: list = []
        self._storage_callbacks: list = []
        self._start_time = time.time()

    def add_threshold(self, threshold: Threshold):
        self.thresholds.append(threshold)

    def register_alert_callback(self, fn):
        self._alert_callbacks.append(fn)

    def register_storage_callback(self, fn):
        self._storage_callbacks.append(fn)

    def feed(self, raw: bytes) -> int:
        readings = self.decoder.feed(raw)
        return len(readings)

    def _on_reading(self, reading: TelemetryReading):
        self._ring_buffer.append(reading)

        if reading.sensor_id not in self._health:
            self._health[reading.sensor_id] = SensorHealth()
        self._health[reading.sensor_id].push(reading.value, reading.timestamp)

        self._check_thresholds(reading)

        for cb in self._storage_callbacks:
            cb(reading)

    def _check_thresholds(self, reading: TelemetryReading):
        for t in self.thresholds:
            if t.sensor_type != reading.sensor_type:
                continue
            health = self._health.get(reading.sensor_id)
            if not health:
                continue

            if reading.value < t.min_val or reading.value > t.max_val:
                health.breach_count += 1
                if health.breach_count >= t.consecutive_breaches:
                    severity = "CRITICAL" if health.breach_count >= t.consecutive_breaches * 2 else "WARNING"
                    alert = Alert(
                        sensor_id=reading.sensor_id,
                        sensor_type=reading.sensor_type,
                        value=reading.value,
                        threshold=t,
                        timestamp=reading.timestamp,
                        severity=severity,
                    )
                    self._alerts.append(alert)
                    for cb in self._alert_callbacks:
                        cb(alert)
            else:
                health.breach_count = 0

    def query_history(
        self,
        sensor_id: Optional[int] = None,
        sensor_type: Optional[SensorType] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> list[TelemetryReading]:
        results = []
        for r in reversed(self._ring_buffer):
            if sensor_id is not None and r.sensor_id != sensor_id:
                continue
            if sensor_type is not None and r.sensor_type != sensor_type:
                continue
            if since is not None and r.timestamp < since:
                continue
            results.append(r)
            if len(results) >= limit:
                break
        return results

    def get_sensor_health(self, sensor_id: int) -> Optional[SensorHealth]:
        return self._health.get(sensor_id)

    @property
    def active_alerts(self) -> list[Alert]:
        return list(self._alerts)

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time

    @property
    def pipeline_stats(self) -> dict:
        return {
            "uptime_s": round(self.uptime, 1),
            "total_readings": len(self._ring_buffer),
            "unique_sensors": len(self._health),
            "active_alerts": len(self._alerts),
            "decoder_stats": {
                "total_frames": self.decoder.stats.total_frames,
                "loss_rate": round(self.decoder.stats.loss_rate, 6),
                "health": self.decoder.stats.health,
            },
        }
