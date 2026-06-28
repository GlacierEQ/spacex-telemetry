"""Information-theoretic anomaly detection — novel failure discovery.

Standard telemetry monitoring looks for known patterns (thresholds, rates).
This detects NOVEL failures — things that have never happened before.

Innovation: Uses information theory to detect anomalies without knowing
what to look for. If the compression ratio of telemetry data suddenly
changes, something new is happening that the model hasn't seen before.

The wheel: telemetry decoding
The vehicle: detecting the unknown

Key insight: Normal telemetry compresses well because it's predictable.
Anomalies are surprising — they don't compress. The compression ratio
IS the anomaly detector.

Pure math, zero external dependencies.
"""

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TelemetryBlock:
    sensor_id: int
    values: list[float]
    timestamp: float


@dataclass
class InformationMetrics:
    entropy_bits: float
    compression_ratio: float
    surprise_index: float
    novelty_score: float
    is_anomaly: bool


class SimpleCompressor:
    """LZ77-inspired compressor for floating point telemetry.

    Not a full LZ77 — just the core idea: find repeated patterns
    and replace them with references. The compression ratio tells us
    how predictable the data is.
    """

    def __init__(self, window_size: int = 128, min_match: int = 3):
        self.window_size = window_size
        self.min_match = min_match

    def compress_ratio(self, data: list[float]) -> float:
        if len(data) < self.min_match:
            return 1.0

        quantized = [round(v, 2) for v in data]
        original_size = len(quantized) * 8

        compressed_size = 0
        i = 0
        window = []

        while i < len(quantized):
            best_len = 0
            best_offset = 0

            search_start = max(0, len(window) - self.window_size)
            for j in range(search_start, len(window)):
                match_len = 0
                while (i + match_len < len(quantized) and
                       j + match_len < len(window) and
                       window[j + match_len] == quantized[i + match_len]):
                    match_len += 1
                    if match_len >= 200:
                        break

                if match_len > best_len:
                    best_len = match_len
                    best_offset = len(window) - j

            if best_len >= self.min_match:
                compressed_size += 4
                window.extend(quantized[i:i + best_len])
                i += best_len
            else:
                compressed_size += 8
                window.append(quantized[i])
                i += 1

            if len(window) > self.window_size * 2:
                window = window[-self.window_size:]

        return compressed_size / original_size if original_size > 0 else 1.0


class EntropyAnalyzer:
    """Shannon entropy computation for telemetry value distributions.

    Normal telemetry has consistent entropy — the values fluctuate
    within predictable ranges. Anomalies change the entropy.
    """

    def __init__(self, num_bins: int = 32):
        self.num_bins = num_bins

    def compute_entropy(self, data: list[float]) -> float:
        if len(data) < 2:
            return 0.0

        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val < 1e-10:
            return 0.0

        bins = [0] * self.num_bins
        for v in data:
            bin_idx = min(int((v - min_val) / range_val * self.num_bins), self.num_bins - 1)
            bins[bin_idx] += 1

        n = len(data)
        entropy = 0.0
        for count in bins:
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)

        return entropy

    def max_entropy(self) -> float:
        return math.log2(self.num_bins)

    def normalized_entropy(self, data: list[float]) -> float:
        return self.compute_entropy(data) / self.max_entropy()


class SurpriseIndex:
    """Quantifies how "surprising" new data is given historical context.

    Innovation: Uses Kullback-Leibler divergence between the historical
    distribution and the recent distribution. High divergence = the data
    is behaving differently than before = something new is happening.
    """

    def __init__(self, history_size: int = 500, num_bins: int = 32):
        self.history_size = history_size
        self.num_bins = num_bins
        self._history: list[float] = []

    def update(self, value: float):
        self._history.append(value)
        if len(self._history) > self.history_size:
            self._history = self._history[-self.history_size:]

    def compute_surprise(self, recent: list[float]) -> float:
        if len(self._history) < 50 or len(recent) < 10:
            return 0.0

        hist_bins = self._histogram(self._history)
        recent_bins = self._histogram(recent)

        kl_div = 0.0
        for i in range(self.num_bins):
            p = hist_bins[i]
            q = recent_bins[i]
            if p > 0 and q > 0:
                kl_div += p * math.log(p / q)
            elif p > 0 and q == 0:
                kl_div += p * 10

        return kl_div

    def _histogram(self, data: list[float]) -> list[float]:
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val < 1e-10:
            return [1.0 / self.num_bins] * self.num_bins

        bins = [0.0] * self.num_bins
        for v in data:
            bin_idx = min(int((v - min_val) / range_val * self.num_bins), self.num_bins - 1)
            bins[bin_idx] += 1

        n = len(data)
        return [b / n for b in bins]


class NoveltyDetector:
    """Detects novel failures — things that have never happened before.

    Innovation: Traditional monitoring can only detect KNOWN failure modes.
    This detects UNKNOWN failure modes by monitoring information content.

    If the telemetry stream suddenly becomes:
    - Less compressible → new pattern emerging
    - Higher entropy → more randomness than usual
    - Higher surprise → behaving differently than history

    Then something NEW is happening, even if no threshold is crossed.
    """

    def __init__(self):
        self.compressor = SimpleCompressor()
        self.entropy_analyzer = EntropyAnalyzer()
        self.surprise_index = SurpriseIndex()
        self._baseline_compression: Optional[float] = None
        self._baseline_entropy: Optional[float] = None
        self._compression_history: list[float] = []
        self._entropy_history: list[float] = []
        self._anomaly_count: int = 0

    def set_baseline(self, telemetry_blocks: list[TelemetryBlock]):
        compressions = []
        entropies = []

        for block in telemetry_blocks:
            if len(block.values) >= 10:
                c = self.compressor.compress_ratio(block.values)
                e = self.entropy_analyzer.normalized_entropy(block.values)
                compressions.append(c)
                entropies.append(e)
                for v in block.values:
                    self.surprise_index.update(v)

        if compressions:
            self._baseline_compression = sum(compressions) / len(compressions)
            self._baseline_entropy = sum(entropies) / len(entropies)

    def analyze_block(self, block: TelemetryBlock) -> InformationMetrics:
        if len(block.values) < 10:
            return InformationMetrics(
                entropy_bits=0, compression_ratio=1.0,
                surprise_index=0, novelty_score=0, is_anomaly=False,
            )

        compression = self.compressor.compress_ratio(block.values)
        entropy = self.entropy_analyzer.normalized_entropy(block.values)
        surprise = self.surprise_index.compute_surprise(block.values)

        for v in block.values:
            self.surprise_index.update(v)

        self._compression_history.append(compression)
        self._entropy_history.append(entropy)

        if len(self._compression_history) > 100:
            self._compression_history = self._compression_history[-100:]
            self._entropy_history = self._entropy_history[-100:]

        compression_deviation = 0.0
        entropy_deviation = 0.0

        if self._baseline_compression is not None and len(self._compression_history) >= 5:
            recent_c = self._compression_history[-5:]
            mean_c = sum(recent_c) / len(recent_c)
            std_c = math.sqrt(sum((x - mean_c) ** 2 for x in recent_c) / len(recent_c)) if len(recent_c) > 1 else 0.01
            compression_deviation = abs(compression - self._baseline_compression) / max(std_c, 0.01)

        if self._baseline_entropy is not None and len(self._entropy_history) >= 5:
            recent_e = self._entropy_history[-5:]
            mean_e = sum(recent_e) / len(recent_e)
            std_e = math.sqrt(sum((x - mean_e) ** 2 for x in recent_e) / len(recent_e)) if len(recent_e) > 1 else 0.01
            entropy_deviation = abs(entropy - self._baseline_entropy) / max(std_e, 0.01)

        novelty_score = (compression_deviation + entropy_deviation + surprise) / 3.0
        is_anomaly = novelty_score > 2.5 or surprise > 3.0

        if is_anomaly:
            self._anomaly_count += 1

        return InformationMetrics(
            entropy_bits=entropy,
            compression_ratio=compression,
            surprise_index=surprise,
            novelty_score=novelty_score,
            is_anomaly=is_anomaly,
        )

    def get_anomaly_report(self) -> dict:
        return {
            "total_anomalies": self._anomaly_count,
            "baseline_compression": self._baseline_compression,
            "baseline_entropy": self._baseline_entropy,
            "recent_compression": self._compression_history[-5:] if self._compression_history else [],
            "recent_entropy": self._entropy_history[-5:] if self._entropy_history else [],
        }
