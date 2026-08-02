"""USB microphone level capture isolated from the Pygame render loop."""

from __future__ import annotations

import math
import threading

try:
    import sounddevice as sd
except ImportError:  # The visualizer can still run without microphone support.
    sd = None

from audio_features import AUDIO_FEATURES_AVAILABLE, AudioFeatureProcessor, AudioFeatures


class Microphone:
    """Capture a smoothed mono RMS level from the first suitable USB input."""

    def __init__(self, samplerate: int = 44100, blocksize: int = 1024, enabled: bool = True) -> None:
        self.features = AudioFeatures()
        self.available = False
        self.device_name = ""
        self.error: str | None = None
        self._target_level = 0.0
        self._pending_features = AudioFeatures()
        self._lock = threading.Lock()
        self._stream = None
        self._blocksize = blocksize
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._stream_finished = False
        self._stopping = False
        self._processor: AudioFeatureProcessor | None = None

        if not enabled:
            return

        if not AUDIO_FEATURES_AVAILABLE or sd is None:
            self.error = "numpy or sounddevice is not installed"
            return

        try:
            device = self._find_usb_input()
            if device is None:
                self.error = "no USB audio input device found"
                return

            self.device_name = str(sd.query_devices(device)["name"])
            self._processor = AudioFeatureProcessor(samplerate, blocksize)
            self._stream = sd.InputStream(
                device=device,
                channels=1,
                samplerate=samplerate,
                blocksize=blocksize,
                dtype="float32",
            )
        except Exception as exc:  # Audio must never prevent the visualizer from starting.
            self.error = str(exc)
            self._stream = None

    @staticmethod
    def _find_usb_input() -> int | None:
        assert sd is not None

        devices = sd.query_devices()
        candidates: list[tuple[int, int, str]] = []
        preferred_terms = ("usb pnp sound device", "usb audio", "usb")

        for index, device in enumerate(devices):
            if int(device.get("max_input_channels", 0)) < 1:
                continue
            name = str(device.get("name", ""))
            lowered = name.lower()
            rank = next(
                (term_index for term_index, term in enumerate(preferred_terms) if term in lowered),
                len(preferred_terms),
            )
            if rank < len(preferred_terms):
                candidates.append((rank, index, name))

        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][1]

    def _capture_loop(self) -> None:
        if self._processor is None or self._stream is None:
            return

        try:
            while not self._stop_event.is_set():
                indata, overflowed = self._stream.read(self._blocksize)
                if overflowed:
                    with self._lock:
                        self.error = self.error or "audio input overflow"

                features = self._processor.process(indata[:, 0])
                with self._lock:
                    self._pending_features = features
        except Exception as exc:
            if not self._stopping:
                with self._lock:
                    self.error = str(exc)
                    self._stream_finished = True

    def start(self) -> None:
        if self._stream is None:
            return
        self._stream_finished = False
        self._stop_event.clear()
        self._pending_features = AudioFeatures(available=True)
        try:
            self._stream.start()
            self._stopping = False
            self.available = True
            self._worker = threading.Thread(
                target=self._capture_loop,
                name="microphone-capture",
                daemon=True,
            )
            self._worker.start()
        except Exception as exc:
            self.error = str(exc)
            self.available = False

    def update(self, dt: float) -> None:
        with self._lock:
            target = self._pending_features
            stream_finished = self._stream_finished

        if stream_finished and not self._stopping:
            self.available = False
            if self.error is None:
                self.error = "audio input stream stopped"
            target = AudioFeatures()

        # Use frame-rate independent exponential lerp. Audio attacks stay
        # responsive, while the slower release keeps visual effects readable.
        response_up = 1.0 - math.exp(-max(0.0, dt) * 12.0)
        response_down = 1.0 - math.exp(-max(0.0, dt) * 2.2)

        def smooth(current: float, incoming: float) -> float:
            response = response_up if incoming > current else response_down
            return current + (incoming - current) * response

        onset = max(self.features.onset_pulse - max(0.0, dt) / 0.4, target.onset_pulse)
        self.features = AudioFeatures(
            level=smooth(self.features.level, target.level),
            low=smooth(self.features.low, target.low),
            mid=smooth(self.features.mid, target.mid),
            high=smooth(self.features.high, target.high),
            onset_pulse=onset,
            available=self.available,
        )

    def stop(self) -> None:
        if self._stream is None:
            return
        self._stopping = True
        self._stop_event.set()
        worker = self._worker
        try:
            self._stream.stop()
            if worker is not None:
                worker.join(timeout=1.0)
            self._stream.close()
        except Exception:
            pass
        finally:
            self._stream = None
            self._worker = None
            self.available = False
