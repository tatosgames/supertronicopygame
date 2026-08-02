import math

import pygame

from config import Config, Palette


Point = tuple[int, int]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def clamp_int(value: float) -> int:
    return max(0, min(255, int(value)))


def mix_color(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return (
        clamp_int(color[0] + amount),
        clamp_int(color[1] + amount),
        clamp_int(color[2] + amount),
    )


def blend_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        clamp_int(a[0] + (b[0] - a[0]) * t),
        clamp_int(a[1] + (b[1] - a[1]) * t),
        clamp_int(a[2] + (b[2] - a[2]) * t),
    )


def smoothstep(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def blend_palette(a: Palette, b: Palette, t: float) -> Palette:
    return Palette(
        name=b.name if t >= 0.5 else a.name,
        background=blend_color(a.background, b.background, t),
        green=blend_color(a.green, b.green, t),
        glow=blend_color(a.glow, b.glow, t),
        dim=blend_color(a.dim, b.dim, t),
        red=blend_color(a.red, b.red, t),
        yellow=blend_color(a.yellow, b.yellow, t),
        cyan=blend_color(a.cyan, b.cyan, t),
        magenta=blend_color(a.magenta, b.magenta, t),
        text=blend_color(a.text, b.text, t),
    )


class Projection:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.center_x = 0.0
        self.horizon_y = 0
        self.focal_length = 0.0
        self.refresh()

    def refresh(self) -> None:
        self.center_x = self.config.width * 0.5
        self.horizon_y = self.config.horizon_y
        self.focal_length = self.config.focal_length

    def project(self, x: float, y: float, z: float) -> Point | None:
        if z <= 0.05:
            return None
        sx = self.center_x + (x / z) * self.focal_length
        sy = self.horizon_y + (y / z) * self.focal_length
        if sy < -160:
            return None
        return int(sx), int(sy)


class LineBatch:
    def __init__(self) -> None:
        self.lines: list[tuple[Point, Point, tuple[int, int, int], bool]] = []
        self.polylines: list[tuple[list[Point], tuple[int, int, int], bool]] = []

    def clear(self) -> None:
        self.lines.clear()
        self.polylines.clear()

    def add(self, a: Point | None, b: Point | None, color: tuple[int, int, int], glow: bool = True) -> None:
        if a is not None and b is not None:
            self.lines.append((a, b, color, glow))

    def add_polyline(self, points: list[Point], color: tuple[int, int, int], glow: bool = True) -> None:
        if len(points) >= 2:
            self.polylines.append((points, color, glow))

    def draw(
        self,
        surface: pygame.Surface,
        glow: bool,
        glow_color: tuple[int, int, int],
        audio_pulse: float = 0.0,
    ) -> None:
        if glow:
            glow_width = 3 + int(audio_pulse * 2.0)
            for a, b, _, line_glow in self.lines:
                if line_glow:
                    pygame.draw.line(surface, glow_color, a, b, glow_width)
            for points, _, line_glow in self.polylines:
                if line_glow:
                    pygame.draw.lines(surface, glow_color, False, points, glow_width)
        for a, b, color, _ in self.lines:
            pygame.draw.line(surface, color, a, b, 1)
        for points, color, _ in self.polylines:
            pygame.draw.lines(surface, color, False, points, 1)


class VectorDistortion:
    """Apply a bounded, audio-triggered CRT-style warp in fixed-size bands."""

    def __init__(self, config: Config, band_height: int = 20) -> None:
        self.config = config
        self.band_height = band_height

    def offsets(self, t: float, audio_pulse: float) -> list[int]:
        """Return deterministic horizontal offsets, bounded by the configured limit."""
        amplitude = int(round(self.config.vector_distortion_max_pixels * clamp(audio_pulse, 0.0, 1.0)))
        band_count = math.ceil(self.config.height / self.band_height)
        if amplitude == 0:
            return [0] * band_count

        return [
            int(round(amplitude * (
                math.sin(t * 31.0 + band * 1.71)
                + 0.42 * math.sin(t * 57.0 + band * 0.63)
            ) / 1.42))
            for band in range(band_count)
        ]

    def draw(
        self,
        source: pygame.Surface,
        target: pygame.Surface,
        background: tuple[int, int, int],
        t: float,
        audio_pulse: float,
    ) -> None:
        target.fill(background)
        for band, offset in enumerate(self.offsets(t, audio_pulse)):
            y = band * self.band_height
            height = min(self.band_height, self.config.height - y)
            target.blit(source, (offset, y), pygame.Rect(0, y, self.config.width, height))
