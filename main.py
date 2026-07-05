import argparse
import math
import random
import sys
from dataclasses import dataclass

import pygame

from config import Config, Palette


Point = tuple[int, int]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def mix_color(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return (
        clamp_int(color[0] + amount),
        clamp_int(color[1] + amount),
        clamp_int(color[2] + amount),
    )


def clamp_int(value: float) -> int:
    return max(0, min(255, int(value)))


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

    def clear(self) -> None:
        self.lines.clear()

    def add(self, a: Point | None, b: Point | None, color: tuple[int, int, int], glow: bool = True) -> None:
        if a is not None and b is not None:
            self.lines.append((a, b, color, glow))

    def draw(self, surface: pygame.Surface, glow: bool, glow_color: tuple[int, int, int]) -> None:
        if glow:
            for a, b, _, line_glow in self.lines:
                if line_glow:
                    pygame.draw.line(surface, glow_color, a, b, 3)
        for a, b, color, _ in self.lines:
            pygame.draw.line(surface, color, a, b, 1)


@dataclass
class Star:
    x: float
    y: float
    speed: float
    phase: float
    color_mode: int


@dataclass
class DataColumn:
    x: int
    y: float
    speed: float
    height: int
    gap: int


class BackgroundRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.stars: list[Star] = []
        self.columns: list[DataColumn] = []
        self.seed = -1
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        self.seed = seed
        rng = random.Random(seed + 404)
        sky_h = max(24, self.config.horizon_y - 4)
        self.stars = [
            Star(
                x=rng.uniform(0, self.config.width),
                y=rng.uniform(0, sky_h),
                speed=rng.uniform(1.0, 8.0),
                phase=rng.uniform(0.0, math.tau),
                color_mode=rng.randint(0, 3),
            )
            for _ in range(self.config.star_count)
        ]
        self.columns = [
            DataColumn(
                x=rng.randrange(0, self.config.width, 8),
                y=rng.uniform(-sky_h, sky_h),
                speed=rng.uniform(8.0, 24.0),
                height=rng.randint(8, 24),
                gap=rng.randint(9, 18),
            )
            for _ in range(self.config.data_column_count)
        ]

    def draw(self, surface: pygame.Surface, t: float) -> None:
        palette = self.config.palette
        sky_h = max(24, self.config.horizon_y - 4)
        colors = (palette.dim, palette.green, palette.cyan, palette.magenta)
        for star in self.stars:
            x = int((star.x - t * star.speed * self.config.speed * 0.22) % self.config.width)
            pulse = math.sin(t * 3.0 + star.phase)
            color = colors[star.color_mode]
            if pulse > 0.55:
                pygame.draw.line(surface, color, (x - 1, int(star.y)), (x + 1, int(star.y)), 1)
            else:
                surface.set_at((x, int(star.y)), color)

        for col in self.columns:
            y = (col.y + t * col.speed * self.config.speed) % (sky_h + col.height * 2) - col.height * 2
            color = palette.dim if int((col.x + t) // 16) % 2 else palette.green
            for i in range(0, col.height, col.gap):
                yy = int(y + i)
                if 0 <= yy < sky_h:
                    pygame.draw.line(surface, color, (col.x, yy), (col.x, min(sky_h, yy + 3)), 1)


class GridRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config

    def draw(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch) -> None:
        palette = self.config.palette
        scroll = (t * self.config.grid_scroll_rate * self.config.speed) % self.config.grid_spacing_z
        floor_y = 1.25
        z = self.config.grid_z_near + ((self.config.grid_spacing_z - scroll) % self.config.grid_spacing_z)
        if z <= self.config.grid_z_near + 0.01:
            z += self.config.grid_spacing_z
        while z <= self.config.grid_z_far:
            fade = 1.0 - (z / self.config.grid_z_far) * 0.75
            color = mix_color(palette.green, int(-70 * (1.0 - fade)))
            a = projection.project(-self.config.grid_extent_x, floor_y, z)
            b = projection.project(self.config.grid_extent_x, floor_y, z)
            batch.add(a, b, color)
            z += self.config.grid_spacing_z

        x = -self.config.grid_extent_x
        while x <= self.config.grid_extent_x + 0.01:
            a = projection.project(x, floor_y, self.config.grid_z_near)
            b = projection.project(x, floor_y, self.config.grid_z_far)
            batch.add(a, b, palette.dim, glow=False)
            x += self.config.grid_spacing_x

        for rail_x in (-4.0, 4.0):
            batch.add(
                projection.project(rail_x, floor_y, self.config.grid_z_near),
                projection.project(rail_x * 0.35, floor_y, self.config.grid_z_far),
                palette.green,
            )
        for stripe_x in (-0.35, 0.35):
            batch.add(
                projection.project(stripe_x, floor_y, self.config.grid_z_near),
                projection.project(stripe_x * 0.25, floor_y, self.config.grid_z_far),
                palette.cyan,
            )


class TerrainRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.points: list[tuple[float, float]] = []
        self.far_points: list[tuple[float, float]] = []
        self.seed = -1
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        self.seed = seed
        self.points = self._make_profile(seed + 101, 0.25, 0)
        self.far_points = self._make_profile(seed + 111, 0.14, -8)

    def _make_profile(self, seed: int, height_ratio: float, baseline_offset: int) -> list[tuple[float, float]]:
        rng = random.Random(seed)
        points: list[tuple[float, float]] = []
        step = self.config.width / (self.config.mountain_count - 1)
        baseline = self.config.horizon_y + baseline_offset
        y = baseline + rng.uniform(-2, 5)
        for i in range(self.config.mountain_count):
            target = baseline - rng.uniform(2, self.config.height * height_ratio)
            y = y * 0.58 + target * 0.42
            points.append((i * step, y))
        return points

    def draw(self, surface: pygame.Surface, t: float) -> None:
        palette = self.config.palette
        horizon = self.config.horizon_y
        self._draw_layer(surface, self.far_points, t * 0.45, palette.dim, palette.glow, horizon - 7)
        self._draw_layer(surface, self.points, t, palette.green, palette.glow, horizon)

    def _draw_layer(
        self,
        surface: pygame.Surface,
        points: list[tuple[float, float]],
        t: float,
        color: tuple[int, int, int],
        glow_color: tuple[int, int, int],
        horizon: int,
    ) -> None:
        offset = (t * 8.0 * self.config.speed) % self.config.width
        pygame.draw.line(surface, glow_color, (0, horizon), (self.config.width, horizon), 2)
        pygame.draw.line(surface, color, (0, horizon), (self.config.width, horizon), 1)
        wave_t = t * 0.7
        step = points[1][0] - points[0][0]
        split = max(0, min(len(points) - 1, int(offset / step)))
        self._draw_profile_range(surface, points, split, len(points), -offset, wave_t, color, glow_color, horizon)
        self._draw_profile_range(surface, points, 0, split + 2, self.config.width - offset, wave_t, color, glow_color, horizon)

    def _draw_profile_range(
        self,
        surface: pygame.Surface,
        points: list[tuple[float, float]],
        start: int,
        end: int,
        shift: float,
        wave_t: float,
        color: tuple[int, int, int],
        glow_color: tuple[int, int, int],
        horizon: int,
    ) -> None:
        last: Point | None = None
        for i in range(start, min(end, len(points))):
            x, y = points[i]
            sx = x + shift
            if sx < -12 or sx > self.config.width + 12:
                last = None
                continue
            point = (int(sx), int(y + math.sin(wave_t + sx * 0.03) * 1.3))
            if last is not None:
                c = ((last[0] + point[0]) // 2, horizon + 5)
                pygame.draw.line(surface, glow_color, last, point, 2)
                pygame.draw.line(surface, color, last, point, 1)
                pygame.draw.line(surface, color, last, c, 1)
                if i % 2 == 0:
                    pygame.draw.line(surface, color, point, c, 1)
            last = point


@dataclass
class Building:
    x: float
    w: float
    h: float
    roof: int
    bands: int
    columns: int
    ornament: int
    color_mode: int


class CityRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.buildings: list[Building] = []
        self.seed = -1
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        self.seed = seed
        rng = random.Random(seed + 202)
        buildings: list[Building] = []
        x = -17.5
        while x < 17.5 and len(buildings) < self.config.city_count:
            w = rng.uniform(0.95, 2.35)
            h = rng.uniform(1.4, 7.4)
            roof = rng.choice([0, 0, 0, 1, 2])
            bands = rng.choice([0, 0, 1, 1, 2])
            columns = rng.choice([0, 0, 1, 1, 2])
            ornament = rng.choice([0, 0, 0, 0, 1, 2])
            color_mode = rng.choice([0, 0, 0, 1, 2])
            buildings.append(
                Building(
                    x=x,
                    w=w,
                    h=h,
                    roof=roof,
                    bands=bands,
                    columns=columns,
                    ornament=ornament,
                    color_mode=color_mode,
                )
            )
            x += w + rng.uniform(0.75, 1.65)
        self.buildings = buildings

    def draw(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch) -> None:
        palette = self.config.palette
        parallax = math.sin(t * 0.10 * self.config.speed) * 0.45
        z = 21.5
        ground_y = -0.18
        for building in self.buildings:
            x0 = building.x + parallax
            x1 = x0 + building.w
            top_y = ground_y - building.h
            p0 = projection.project(x0, ground_y, z)
            p1 = projection.project(x1, ground_y, z)
            p2 = projection.project(x1, top_y, z)
            p3 = projection.project(x0, top_y, z)
            self._fill_mask(surface, palette.background, (p0, p1, p2, p3))
            accent_colors = (palette.green, palette.cyan, palette.magenta)
            color = accent_colors[building.color_mode] if building.h > 5.8 else palette.green
            if building.h <= 2.8:
                color = palette.dim
            batch.add(p0, p1, color)
            batch.add(p1, p2, color)
            batch.add(p2, p3, color)
            batch.add(p3, p0, color)

            for band in range(1, building.bands + 1):
                y = ground_y - building.h * band / (building.bands + 1)
                batch.add(projection.project(x0, y, z), projection.project(x1, y, z), palette.dim, glow=False)
            for col in range(1, building.columns + 1):
                x = x0 + building.w * col / (building.columns + 1)
                batch.add(projection.project(x, ground_y, z), projection.project(x, top_y, z), palette.dim, glow=False)

            if building.roof == 1:
                apex = projection.project((x0 + x1) * 0.5, top_y - building.w * 1.2, z)
                self._fill_mask(surface, palette.background, (p3, p2, apex))
                batch.add(p3, apex, color)
                batch.add(apex, p2, color)
            elif building.roof == 2:
                spire = projection.project((x0 + x1) * 0.5, top_y - building.h * 0.45, z)
                base = projection.project((x0 + x1) * 0.5, top_y, z)
                batch.add(base, spire, palette.yellow if building.h > 6.5 else color)

            mid_x = (x0 + x1) * 0.5
            if building.ornament == 1 and building.h > 5.0:
                tip = projection.project(mid_x, top_y - 1.2, z)
                left = projection.project(mid_x - building.w * 0.25, top_y, z)
                right = projection.project(mid_x + building.w * 0.25, top_y, z)
                batch.add(left, tip, palette.cyan)
                batch.add(tip, right, palette.cyan)
            elif building.ornament == 2 and building.h > 6.2:
                mast = projection.project(mid_x, top_y - 1.6, z)
                base = projection.project(mid_x, top_y, z)
                batch.add(base, mast, palette.dim, glow=False)
                beacon = projection.project(mid_x, top_y - 1.8 + math.sin(t * 4.0) * 0.12, z)
                if beacon is not None:
                    pygame.draw.circle(surface, palette.red, beacon, 1)

    def _fill_mask(
        self,
        surface: pygame.Surface,
        color: tuple[int, int, int],
        points: tuple[Point | None, ...],
    ) -> None:
        if all(point is not None for point in points):
            pygame.draw.polygon(surface, color, points)


class SunRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.style = 0
        self.x_ratio = 0.34
        self.y_ratio = 0.23
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        rng = random.Random(seed + 505)
        self.style = rng.randint(0, 2)
        self.x_ratio = rng.choice([0.28, 0.34, 0.42, 0.64, 0.72])
        self.y_ratio = rng.uniform(0.18, 0.28)

    def draw(self, surface: pygame.Surface, t: float) -> None:
        palette = self.config.palette
        radius = int(self.config.height * (0.135 + math.sin(t * 1.3) * 0.006))
        cx = int(self.config.width * self.x_ratio)
        cy = int(self.config.horizon_y - self.config.height * self.y_ratio)
        color = blend_color(palette.red, palette.yellow, 0.25 + 0.25 * math.sin(t * 0.45))
        if self.config.glow:
            pygame.draw.circle(surface, palette.glow, (cx, cy), radius + 2, 2)
        if self.style == 0:
            self._draw_striped_disc(surface, cx, cy, radius, color, 7)
            pygame.draw.circle(surface, color, (cx, cy), radius, 1)
        elif self.style == 1:
            pygame.draw.circle(surface, color, (cx, cy), radius, 1)
            pygame.draw.circle(surface, palette.yellow, (cx, cy), max(4, radius // 2), 1)
            tilt = int(math.sin(t * 0.8) * 3)
            pygame.draw.line(surface, palette.cyan, (cx - radius - 8, cy + tilt), (cx + radius + 8, cy - tilt), 1)
            pygame.draw.line(surface, palette.dim, (cx - radius - 5, cy + tilt + 5), (cx + radius + 5, cy - tilt + 5), 1)
        else:
            self._draw_striped_disc(surface, cx, cy, radius, color, 9)
            pygame.draw.circle(surface, color, (cx, cy), radius, 1)
            twin = (min(self.config.width - 20, cx + radius + 18), cy + 8)
            pygame.draw.circle(surface, palette.yellow, twin, max(8, radius // 2), 1)

    def _draw_striped_disc(
        self,
        surface: pygame.Surface,
        cx: int,
        cy: int,
        radius: int,
        color: tuple[int, int, int],
        spacing: int,
    ) -> None:
        for y in range(cy - radius, cy + radius + 1, spacing):
            dy = y - cy
            dx = int(math.sqrt(max(0, radius * radius - dy * dy)))
            band_color = color if (y // spacing) % 2 == 0 else mix_color(color, -70)
            pygame.draw.line(surface, band_color, (cx - dx, y), (cx + dx, y), 1)


@dataclass
class Drone:
    phase: float
    z: float
    y: float
    size: float
    color_mode: int
    shape: int


class DroneRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.drones: list[Drone] = []
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        rng = random.Random(seed + 303)
        self.drones = [
            Drone(
                phase=rng.uniform(0.0, math.tau),
                z=rng.uniform(6.0, 14.0),
                y=-rng.uniform(2.2, 6.5),
                size=rng.uniform(0.32, 0.62),
                color_mode=rng.randint(0, 3),
                shape=rng.randint(0, 2),
            )
            for _ in range(self.config.drone_count)
        ]

    def draw(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch) -> None:
        palette = self.config.palette
        colors = (palette.red, palette.yellow, palette.cyan, palette.magenta)
        for drone in self.drones:
            x = math.sin(t * 0.42 * self.config.speed + drone.phase) * 11.0
            y = drone.y + math.sin(t * 1.1 + drone.phase) * 0.25
            z = drone.z + math.cos(t * 0.3 + drone.phase) * 1.2
            s = drone.size
            color = colors[drone.color_mode]
            if drone.shape == 1:
                top = projection.project(x, y - s * 1.6, z)
                left = projection.project(x - s * 1.5, y, z)
                right = projection.project(x + s * 1.5, y, z)
                bottom = projection.project(x, y + s * 1.2, z)
                back = projection.project(x + s * 0.7, y - s * 0.2, z + s * 1.3)
                for a, b in ((top, left), (left, bottom), (bottom, right), (right, top), (left, back), (right, back), (bottom, back)):
                    batch.add(a, b, color)
                continue
            if drone.shape == 2:
                center = projection.project(x, y, z)
                wing_l = projection.project(x - s * 2.0, y, z)
                wing_r = projection.project(x + s * 2.0, y, z)
                nose = projection.project(x, y - s * 0.9, z - s * 0.3)
                tail = projection.project(x, y + s * 0.7, z + s * 0.5)
                batch.add(wing_l, nose, color)
                batch.add(nose, wing_r, color)
                batch.add(wing_r, tail, color)
                batch.add(tail, wing_l, color)
                if center is not None:
                    pygame.draw.circle(surface, color, center, max(2, int(s * 6)), 1)
                continue
            pts = [
                projection.project(x - s, y - s, z),
                projection.project(x + s, y - s, z),
                projection.project(x + s, y + s, z),
                projection.project(x - s, y + s, z),
                projection.project(x - s * 0.45, y - s * 1.45, z + s),
                projection.project(x + s * 1.55, y - s * 1.45, z + s),
                projection.project(x + s * 1.55, y + s * 0.55, z + s),
                projection.project(x - s * 0.45, y + s * 0.55, z + s),
            ]
            edges = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
            for a, b in edges:
                batch.add(pts[a], pts[b], color)


@dataclass
class Portal:
    x: float
    z: float
    radius: float
    phase: float
    color_mode: int


class PortalRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.portals: list[Portal] = []
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        rng = random.Random(seed + 606)
        self.portals = [
            Portal(
                x=rng.uniform(7.0, 12.0),
                z=rng.uniform(12.0, 20.0),
                radius=rng.uniform(0.75, 1.35),
                phase=rng.uniform(0.0, math.tau),
                color_mode=rng.randint(0, 1),
            )
            for _ in range(1)
        ]

    def draw(self, surface: pygame.Surface, projection: Projection, t: float) -> None:
        palette = self.config.palette
        colors = (palette.cyan, palette.magenta, palette.yellow)
        for portal in self.portals:
            bob = math.sin(t * 0.9 + portal.phase) * 0.25
            center = projection.project(portal.x, -portal.radius + bob, portal.z)
            rim = projection.project(portal.x + portal.radius, -portal.radius + bob, portal.z)
            if center is None or rim is None:
                continue
            rx = max(3, abs(rim[0] - center[0]))
            ry = max(5, int(rx * 1.45))
            rect = pygame.Rect(center[0] - rx, center[1] - ry, rx * 2, ry * 2)
            color = colors[portal.color_mode]
            if self.config.glow:
                pygame.draw.ellipse(surface, palette.glow, rect.inflate(4, 4), 2)
            pygame.draw.ellipse(surface, color, rect, 1)
            pygame.draw.line(surface, color, (center[0] - rx, center[1]), (center[0] + rx, center[1]), 1)
            if int(t * 4 + portal.phase) % 2 == 0:
                pygame.draw.line(surface, palette.dim, (center[0], center[1] - ry), (center[0], center[1] + ry), 1)


class FXRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.scanline_surface = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        self.vignette_surface = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        self.flicker_surfaces: dict[int, pygame.Surface] = {}
        self.noise_frames: list[list[Point]] = []
        self.rebuild()

    def rebuild(self) -> None:
        self.scanline_surface = pygame.Surface((self.config.width, self.config.height), pygame.SRCALPHA)
        for y in range(0, self.config.height, 4):
            pygame.draw.line(self.scanline_surface, (0, 0, 0, 90), (0, y), (self.config.width, y), 1)
        self.vignette_surface = pygame.Surface((self.config.width, self.config.height), pygame.SRCALPHA)
        for i in range(18):
            alpha = int(5 + i * 3.2)
            rect = pygame.Rect(i, i, self.config.width - i * 2, self.config.height - i * 2)
            if rect.width > 0 and rect.height > 0:
                pygame.draw.rect(self.vignette_surface, (0, 0, 0, alpha), rect, 1)
        self.flicker_surfaces = {}
        for shade in range(1, 16):
            surface = pygame.Surface((self.config.width, self.config.height), pygame.SRCALPHA)
            surface.fill((shade, shade, shade, 9))
            self.flicker_surfaces[shade] = surface
        rng = random.Random(self.config.seed + 707)
        self.noise_frames = [
            [
                (rng.randrange(0, self.config.width), rng.randrange(0, self.config.height))
                for _ in range(10)
            ]
            for _ in range(16)
        ]

    def draw(self, surface: pygame.Surface, t: float) -> None:
        if self.config.flicker:
            shade = int(8 + math.sin(t * 18.0) * 5)
            if shade > 0:
                surface.blit(self.flicker_surfaces[min(15, shade)], (0, 0))
            for x, y in self.noise_frames[int(t * 14.0) & 15]:
                surface.set_at((x, y), self.config.palette.text)
        if self.config.scanlines:
            surface.blit(self.scanline_surface, (0, 0))
        surface.blit(self.vignette_surface, (0, 0))


class App:
    def __init__(self, config: Config) -> None:
        self.config = config
        pygame.init()
        pygame.display.set_caption("Retro Tron Wireframe Visualizer")
        flags = pygame.FULLSCREEN if config.fullscreen else 0
        window_size = (config.width * config.scale, config.height * config.scale)
        self.window = pygame.display.set_mode(window_size, flags)
        self.surface = pygame.Surface((config.width, config.height)).convert()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 16)
        self.projection = Projection(config)
        self.batch = LineBatch()
        self.background = BackgroundRenderer(config)
        self.grid = GridRenderer(config)
        self.terrain = TerrainRenderer(config)
        self.city = CityRenderer(config)
        self.sun = SunRenderer(config)
        self.drones = DroneRenderer(config)
        self.portals = PortalRenderer(config)
        self.fx = FXRenderer(config)
        self.running = True
        self.elapsed = 0.0
        self.next_seed_change = config.auto_seed_interval
        self.next_palette_change = config.auto_palette_interval
        self.palette_transition_start = -config.palette_transition_duration
        self.palette_from = config.palette
        self.palette_to = config.palette
        self.config.current_palette = config.palette

    def randomize_seed(self) -> None:
        self.config.seed = random.randint(1, 999_999)
        self.background.regenerate(self.config.seed)
        self.terrain.regenerate(self.config.seed)
        self.city.regenerate(self.config.seed)
        self.sun.regenerate(self.config.seed)
        self.drones.regenerate(self.config.seed)
        self.portals.regenerate(self.config.seed)

    def start_palette_transition(self, target_index: int) -> None:
        self.palette_from = self.config.palette
        self.config.palette_index = target_index % len(self.config.palettes)
        self.palette_to = self.config.palettes[self.config.palette_index]
        self.palette_transition_start = self.elapsed
        self.config.current_palette = self.palette_from

    def update_palette_transition(self) -> None:
        elapsed = self.elapsed - self.palette_transition_start
        if elapsed >= self.config.palette_transition_duration:
            self.config.current_palette = self.palette_to
            return
        t = smoothstep(elapsed / self.config.palette_transition_duration)
        self.config.current_palette = blend_palette(self.palette_from, self.palette_to, t)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_f:
                self.config.show_fps = not self.config.show_fps
            elif event.key == pygame.K_s:
                self.config.scanlines = not self.config.scanlines
            elif event.key == pygame.K_g:
                self.config.glow = not self.config.glow
            elif event.key == pygame.K_c:
                self.start_palette_transition(self.config.palette_index + 1)
            elif event.key == pygame.K_v:
                self.config.auto_variation = not self.config.auto_variation
            elif event.key == pygame.K_SPACE:
                self.randomize_seed()
            elif event.key == pygame.K_UP:
                self.config.speed = min(self.config.max_speed, self.config.speed + self.config.speed_step)
            elif event.key == pygame.K_DOWN:
                self.config.speed = max(self.config.min_speed, self.config.speed - self.config.speed_step)
            elif event.key == pygame.K_LEFT:
                self.config.horizon_ratio = max(self.config.horizon_min, self.config.horizon_ratio - 0.01)
            elif event.key == pygame.K_RIGHT:
                self.config.horizon_ratio = min(self.config.horizon_max, self.config.horizon_ratio + 0.01)

    def update(self) -> None:
        self.update_palette_transition()
        if not self.config.auto_variation:
            return
        if self.elapsed >= self.next_palette_change:
            self.start_palette_transition(self.config.palette_index + 1)
            self.next_palette_change += self.config.auto_palette_interval
        if self.elapsed >= self.next_seed_change:
            self.randomize_seed()
            self.next_seed_change += self.config.auto_seed_interval

    def draw_fps(self) -> None:
        if not self.config.show_fps:
            return
        auto = "AUTO" if self.config.auto_variation else "HOLD"
        label = f"{self.clock.get_fps():04.1f} FPS  {self.config.profile}  {self.config.palette.name}  {auto}  speed {self.config.speed:.2f}"
        text = self.font.render(label, False, self.config.palette.text)
        self.surface.blit(text, (5, 5))

    def draw(self) -> None:
        palette = self.config.palette
        self.surface.fill(palette.background)
        self.projection.refresh()
        batch = self.batch
        batch.clear()
        self.background.draw(self.surface, self.elapsed)
        self.sun.draw(self.surface, self.elapsed)
        self.terrain.draw(self.surface, self.elapsed)
        self.city.draw(self.surface, self.projection, self.elapsed, batch)
        self.grid.draw(self.surface, self.projection, self.elapsed, batch)
        self.drones.draw(self.surface, self.projection, self.elapsed, batch)
        batch.draw(self.surface, self.config.glow, palette.glow)
        self.portals.draw(self.surface, self.projection, self.elapsed)
        self.fx.draw(self.surface, self.elapsed)
        self.draw_fps()
        pygame.transform.scale(self.surface, self.window.get_size(), self.window)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.config.fps) / 1000.0
            self.elapsed += dt
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
        pygame.quit()


def parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(description="Retro Tron wireframe visualizer for Pygame.")
    parser.add_argument("--width", type=int, default=480, help="Internal render width.")
    parser.add_argument("--height", type=int, default=320, help="Internal render height.")
    parser.add_argument("--scale", type=int, default=2, help="Window scale for low-resolution output.")
    parser.add_argument("--fps", type=int, default=30, help="Frame-rate cap.")
    parser.add_argument("--seed", type=int, default=1979, help="Procedural seed.")
    parser.add_argument("--fullscreen", action="store_true", help="Launch fullscreen.")
    parser.add_argument("--no-auto", action="store_true", help="Disable automatic seed and palette variation.")
    parser.add_argument(
        "--profile",
        choices=("high", "pi", "minimal"),
        default="high",
        help="Visual/performance profile. Use 'pi' for Raspberry Pi 3.",
    )
    args = parser.parse_args(argv)

    width = max(160, args.width)
    height = max(120, args.height)
    scale = max(1, args.scale)
    fps = max(15, min(120, args.fps))
    config = Config(
        width=width,
        height=height,
        scale=scale,
        fps=fps,
        seed=args.seed,
        fullscreen=args.fullscreen,
        profile=args.profile,
        auto_variation=not args.no_auto,
    )
    apply_performance_profile(config)
    return config


def apply_performance_profile(config: Config) -> None:
    if config.profile == "pi":
        config.glow = False
        config.flicker = False
        config.mountain_count = 34
        config.city_count = 18
        config.drone_count = 4
        config.star_count = 46
        config.data_column_count = 10
        config.grid_z_far = 32.0
    elif config.profile == "minimal":
        config.glow = False
        config.scanlines = False
        config.flicker = False
        config.mountain_count = 26
        config.city_count = 14
        config.drone_count = 2
        config.star_count = 22
        config.data_column_count = 5
        config.grid_z_far = 26.0


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv if argv is not None else sys.argv[1:])
    app = App(config)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
