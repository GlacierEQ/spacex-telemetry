"""Real-time telemetry frame decoder for Falcon 9 / Starship downlinks.

Decodes CCSDS-like telemetry frames into typed sensor readings.
Handles packet loss via sequence counter gap detection.
Zero external dependencies — pure struct + math.

Frame sync word: 0x1ACF (CCSDS standard)
CRC: CRC-16-CCITT (poly 0x1021, init 0xFFFF)
Max frame size: 4096 bytes (adjustable)

If you know what 0x1ACF means, we can be friends.
"""

import struct
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class SensorType(IntEnum):
    PRESSURE = 0x01
    TEMPERATURE = 0x02
    ACCELERATION = 0x03
    GYROSCOPE = 0x04
    FLOW_RATE = 0x05
    VOLTAGE = 0x06
    ALTITUDE = 0x07
    VELOCITY = 0x08


@dataclass
class TelemetryReading:
    sensor_id: int
    sensor_type: SensorType
    timestamp: float
    value: float
    unit: str
    quality: int = 0
    sequence: int = 0


@dataclass
class FrameStats:
    total_frames: int = 0
    decoded_frames: int = 0
    dropped_frames: int = 0
    crc_errors: int = 0
    last_sequence: int = -1
    gap_count: int = 0
    throughput_bps: float = 0.0

    @property
    def loss_rate(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return self.dropped_frames / self.total_frames

    @property
    def health(self) -> str:
        if self.loss_rate < 0.001:
            return "NOMINAL"
        if self.loss_rate < 0.01:
            return "DEGRADED"
        return "CRITICAL"


FRAME_HEADER = struct.Struct(">HIBBHI")
FRAME_CRC_SIZE = 2
SENSOR_RECORD = struct.Struct(">BBHd")
UNIT_MAP = {
    SensorType.PRESSURE: "kPa",
    SensorType.TEMPERATURE: "K",
    SensorType.ACCELERATION: "m/s2",
    SensorType.GYROSCOPE: "rad/s",
    SensorType.FLOW_RATE: "kg/s",
    SensorType.VOLTAGE: "V",
    SensorType.ALTITUDE: "m",
    SensorType.VELOCITY: "m/s",
}


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


class TelemetryDecoder:
    def __init__(self, buffer_size: int = 4096):
        self._buffer = bytearray(buffer_size)
        self._buf_len = 0
        self.stats = FrameStats()
        self._readings: list[TelemetryReading] = []
        self._callbacks: list = []

    def register_callback(self, fn):
        self._callbacks.append(fn)

    def feed(self, raw: bytes) -> list[TelemetryReading]:
        self._buffer[self._buf_len:self._buf_len + len(raw)] = raw
        self._buf_len += len(raw)
        self._readings.clear()

        while self._buf_len >= FRAME_HEADER.size + FRAME_CRC_SIZE:
            if not self._try_decode_frame():
                break

        return list(self._readings)

    def _try_decode_frame(self) -> bool:
        start = 0
        while start <= self._buf_len - FRAME_HEADER.size - FRAME_CRC_SIZE:
            header = FRAME_HEADER.unpack_from(self._buffer, start)
            sync, version, src, dst, seq, payload_len = header

            if sync != 0x1ACF:
                start += 1
                continue

            frame_total = FRAME_HEADER.size + payload_len + FRAME_CRC_SIZE
            if start + frame_total > self._buf_len:
                return False

            payload_start = start + FRAME_HEADER.size
            payload_end = payload_start + payload_len
            payload = self._buffer[payload_start:payload_end]

            crc_offset = payload_end
            expected_crc = struct.unpack_from(">H", self._buffer, crc_offset)[0]
            computed_crc = crc16_ccitt(
                self._buffer[start + FRAME_HEADER.size:payload_end]
            )

            self.stats.total_frames += 1

            if computed_crc != expected_crc:
                self.stats.crc_errors += 1
                start += 1
                continue

            self._process_frame(seq, payload)
            consumed = start + frame_total
            remaining = self._buf_len - consumed
            self._buffer[:remaining] = self._buffer[consumed:self._buf_len]
            self._buf_len = remaining
            return True

        if self._buf_len > 0:
            self._buf_len = 0
        return False

    def _process_frame(self, seq: int, payload: bytes):
        if self.stats.last_sequence >= 0:
            expected = (self.stats.last_sequence + 1) & 0xFFFF
            if seq != expected:
                gap = (seq - expected) & 0xFFFF
                self.stats.dropped_frames += gap
                self.stats.gap_count += 1

        self.stats.last_sequence = seq
        self.stats.decoded_frames += 1

        offset = 0
        while offset + SENSOR_RECORD.size <= len(payload):
            s_id, s_type_raw, quality, value = SENSOR_RECORD.unpack_from(
                payload, offset
            )
            offset += SENSOR_RECORD.size

            try:
                s_type = SensorType(s_type_raw)
            except ValueError:
                continue

            reading = TelemetryReading(
                sensor_id=s_id,
                sensor_type=s_type,
                timestamp=time.time(),
                value=value,
                unit=UNIT_MAP.get(s_type, ""),
                quality=quality,
                sequence=seq,
            )
            self._readings.append(reading)

            for cb in self._callbacks:
                cb(reading)


def encode_frame(src: int, dst: int, seq: int, sensors: list[tuple[int, SensorType, int, float]]) -> bytes:
    payload = bytearray()
    for s_id, s_type, quality, value in sensors:
        payload.extend(SENSOR_RECORD.pack(s_id, s_type, quality, value))

    header = FRAME_HEADER.pack(0x1ACF, 0, src, dst, seq, len(payload))
    crc = crc16_ccitt(bytes(payload))
    return header + bytes(payload) + struct.pack(">H", crc)
