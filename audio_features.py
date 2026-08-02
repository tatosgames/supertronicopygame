"""Audio feature extraction for the reactive visualizer."""

from __future__ import annotations

import math
from dataclasses import dataclass

try:
    import numpy as np
except ImportError:  # The visualizer can run without audio dependencies.
    np = None


AUDIO_FEATURES_AVAILABLE = np is not None


@dataclass(frozen=True)
class AudioFeatures:
    level: float = 0.0
    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    onset_pulse: float = 0.0
    available: bool = False


class AudioFeatureProcessor:
    """Convert a mono sample block into normalized visual features."""

    def __init__(
        self,
        samplerate: int = 44100,
        blocksize: int = 1024,
        noise_gate_dbfs: float = -45.0,
        onset_delta_db: float = 8.0,
        onset_cooldown: float = 0.18,
    ) -> None:
        if np is None:
            raise RuntimeError("numpy is not installed")

        self.samplerate = samplerate
        self.blocksize = blocksize
        self.noise_gate_dbfs = noise_gate_dbfs
        self.onset_delta_db = onset_delta_db
        self.onset_cooldown = onset_cooldown
        self._previous_dbfs = noise_gate_dbfs
        self._cooldown = 0.0
        self._window = np.hanning(blocksize).astype(np.float32)
        frequencies = np.fft.rfftfreq(blocksize, 1.0 / samplerate)
        self._band_masks = (
            (frequencies >= 60.0) & (frequencies < 250.0),
            (frequencies >= 250.0) & (frequencies < 2000.0),
            (frequencies >= 2000.0) & (frequencies < 8000.0),
        )

    @staticmethod
    def _dbfs(samples) -> float:
        rms = float(np.sqrt(np.mean(np.square(samples), dtype=np.float64)))
        return 20.0 * math.log10(max(rms, 1e-7))

    @staticmethod
    def _normalize_dbfs(dbfs: float) -> float:
        return min(1.0, max(0.0, (dbfs + 60.0) / 60.0))

    def _band_level(self, spectrum, mask) -> float:
        band = spectrum[mask]
        if band.size == 0:
            return 0.0
        band_rms = float(np.sqrt(np.mean(np.square(band), dtype=np.float64)))
        return self._normalize_dbfs(20.0 * math.log10(max(band_rms, 1e-7)))

    def process(self, samples) -> AudioFeatures:
        samples = np.asarray(samples, dtype=np.float32)
        if samples.size == 0:
            return AudioFeatures(available=True)

        dbfs = self._dbfs(samples)
        elapsed = samples.size / self.samplerate
        self._cooldown = max(0.0, self._cooldown - elapsed)
        onset = (
            dbfs >= self.noise_gate_dbfs
            and dbfs - self._previous_dbfs >= self.onset_delta_db
            and self._cooldown <= 0.0
        )
        self._previous_dbfs = self._previous_dbfs * 0.85 + dbfs * 0.15
        if onset:
            self._cooldown = self.onset_cooldown

        if dbfs < self.noise_gate_dbfs:
            return AudioFeatures(available=True)

        padded = samples
        window = self._window
        masks = self._band_masks
        if samples.size != self.blocksize:
            window = np.hanning(samples.size).astype(np.float32)
            frequencies = np.fft.rfftfreq(samples.size, 1.0 / self.samplerate)
            masks = (
                (frequencies >= 60.0) & (frequencies < 250.0),
                (frequencies >= 250.0) & (frequencies < 2000.0),
                (frequencies >= 2000.0) & (frequencies < 8000.0),
            )
        spectrum = np.abs(np.fft.rfft(padded * window))
        spectrum /= max(1.0, float(np.sum(window) * 0.5))
        bands = tuple(self._band_level(spectrum, mask) for mask in masks)

        return AudioFeatures(
            level=self._normalize_dbfs(dbfs),
            low=bands[0],
            mid=bands[1],
            high=bands[2],
            onset_pulse=1.0 if onset else 0.0,
            available=True,
        )
