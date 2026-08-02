import math
import random
from dataclasses import dataclass

import pygame

from config import Config
from renderers.core import LineBatch, Point, Projection, blend_color, clamp, mix_color


class GridRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._rng = random.Random(config.seed + 808)
        self.turn_current = 0.0
        self.turn_target = self._rng.choice((-0.8, -0.55, 0.0, 0.55, 0.8))
        self._turn_elapsed = 0.0
        self._next_turn_change = config.grid_curve_change_interval * 0.6

    def update(self, dt: float) -> None:
        dt = max(0.0, dt)
        self._turn_elapsed += dt
        if self._turn_elapsed >= self._next_turn_change:
            self.turn_target = self._rng.choice((-0.8, -0.55, 0.0, 0.55, 0.8))
            self._next_turn_change += self.config.grid_curve_change_interval * self._rng.uniform(0.75, 1.25)
        response = min(1.0, dt * self.config.grid_curve_response)
        self.turn_current += (self.turn_target - self.turn_current) * response

    def _project_curved(self, projection: Projection, x: float, floor_y: float, z: float) -> Point | None:
        point = projection.project(x, floor_y, z)
        if point is None:
            return None
        depth = clamp(
            1.0 - (z - self.config.grid_z_near) / (self.config.grid_z_far - self.config.grid_z_near),
            0.0,
            1.0,
        )
        offset = int(round(self.turn_current * self.config.grid_curve_max_pixels * depth * depth))
        return point[0] + offset, point[1]

    def _add_curved_depth_line(
        self,
        batch: LineBatch,
        projection: Projection,
        x_near: float,
        x_far: float,
        floor_y: float,
        color: tuple[int, int, int],
        glow: bool,
    ) -> None:
        previous: Point | None = None
        segments = max(1, self.config.grid_curve_segments)
        for index in range(segments + 1):
            progress = index / segments
            z = self.config.grid_z_near + (self.config.grid_z_far - self.config.grid_z_near) * progress
            x = x_near + (x_far - x_near) * progress
            point = self._project_curved(projection, x, floor_y, z)
            if previous is not None:
                batch.add(previous, point, color, glow=glow)
            previous = point

    def draw(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch) -> None:
        palette = self.config.palette
        audio_speed = 1.0 + self.config.audio_low * 0.1
        scroll = (t * self.config.grid_scroll_rate * self.config.speed * audio_speed) % self.config.grid_spacing_z
        floor_y = 1.25
        z = self.config.grid_z_near + ((self.config.grid_spacing_z - scroll) % self.config.grid_spacing_z)
        if z <= self.config.grid_z_near + 0.01:
            z += self.config.grid_spacing_z
        while z <= self.config.grid_z_far:
            fade = 1.0 - (z / self.config.grid_z_far) * 0.75
            color = mix_color(palette.green, int(-70 * (1.0 - fade)))
            batch.add(
                self._project_curved(projection, -self.config.grid_extent_x, floor_y, z),
                self._project_curved(projection, self.config.grid_extent_x, floor_y, z),
                color,
            )
            z += self.config.grid_spacing_z
        x = -self.config.grid_extent_x
        while x <= self.config.grid_extent_x + 0.01:
            self._add_curved_depth_line(batch, projection, x, x, floor_y, palette.dim, glow=False)
            x += self.config.grid_spacing_x
        for rail_x in (-4.0, 4.0):
            self._add_curved_depth_line(batch, projection, rail_x, rail_x * 0.35, floor_y, palette.green, glow=True)
        for stripe_x in (-0.35, 0.35):
            self._add_curved_depth_line(batch, projection, stripe_x, stripe_x * 0.25, floor_y, palette.cyan, glow=True)


class TerrainRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.points: list[tuple[float, float]] = []
        self.far_points: list[tuple[float, float]] = []
        self.transition_points: list[tuple[float, float]] | None = None
        self.transition_far_points: list[tuple[float, float]] | None = None
        self.transition_seed: int | None = None
        self.transition_elapsed = 0.0
        self.seed = -1
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        self.seed = seed
        self.points = self._make_profile(seed + 101, 0.25, 0)
        self.far_points = self._make_profile(seed + 111, 0.14, -8)

    def begin_transition(self, seed: int) -> None:
        if self.transition_points is not None:
            return
        self.transition_seed = seed
        self.transition_points = self._make_profile(seed + 101, 0.25, 0)
        self.transition_far_points = self._make_profile(seed + 111, 0.14, -8)
        self.transition_elapsed = 0.0

    def update_transition(self, dt: float) -> None:
        if self.transition_points is None or self.transition_far_points is None:
            return
        self.transition_elapsed += max(0.0, dt)
        if self.transition_elapsed < self.config.skyline_transition_duration:
            return
        self.points = self.transition_points
        self.far_points = self.transition_far_points
        self.seed = self.transition_seed if self.transition_seed is not None else self.seed
        self.transition_points = None
        self.transition_far_points = None
        self.transition_seed = None
        self.transition_elapsed = 0.0

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
        if self.transition_points is not None and self.transition_far_points is not None:
            progress = min(1.0, self.transition_elapsed / self.config.skyline_transition_duration)
            span = self.config.width + 24.0
            self._draw_transition_layer(surface, self.far_points, t * 0.45, palette.dim, palette.glow, horizon - 7, span * progress)
            self._draw_transition_layer(surface, self.far_points, t * 0.45, palette.dim, palette.glow, horizon - 7, span * progress + self.config.width)
            self._draw_transition_layer(surface, self.transition_far_points, t * 0.45, palette.dim, palette.glow, horizon - 7, span * (progress - 1.0))
            self._draw_transition_layer(surface, self.points, t, palette.green, palette.glow, horizon, span * progress)
            self._draw_transition_layer(surface, self.points, t, palette.green, palette.glow, horizon, span * progress + self.config.width)
            self._draw_transition_layer(surface, self.transition_points, t, palette.green, palette.glow, horizon, span * (progress - 1.0))
            return
        self._draw_layer(surface, self.far_points, t * 0.45, palette.dim, palette.glow, horizon - 7)
        self._draw_layer(surface, self.points, t, palette.green, palette.glow, horizon)

    def _draw_transition_layer(self, surface: pygame.Surface, points: list[tuple[float, float]], t: float, color: tuple[int, int, int], glow_color: tuple[int, int, int], horizon: int, transition_shift: float) -> None:
        offset = (t * 8.0 * self.config.speed) % self.config.width
        pygame.draw.line(surface, glow_color, (0, horizon), (self.config.width, horizon), 2)
        pygame.draw.line(surface, color, (0, horizon), (self.config.width, horizon), 1)
        self._draw_profile_range(surface, points, 0, len(points), -offset + transition_shift, t * 0.7, color, glow_color, horizon)

    def _draw_layer(self, surface: pygame.Surface, points: list[tuple[float, float]], t: float, color: tuple[int, int, int], glow_color: tuple[int, int, int], horizon: int) -> None:
        offset = (t * 8.0 * self.config.speed) % self.config.width
        pygame.draw.line(surface, glow_color, (0, horizon), (self.config.width, horizon), 2)
        pygame.draw.line(surface, color, (0, horizon), (self.config.width, horizon), 1)
        wave_t = t * 0.7
        step = points[1][0] - points[0][0]
        split = max(0, min(len(points) - 1, int(offset / step)))
        self._draw_profile_range(surface, points, split, len(points), -offset, wave_t, color, glow_color, horizon)
        self._draw_profile_range(surface, points, 0, split + 2, self.config.width - offset, wave_t, color, glow_color, horizon)

    def _draw_profile_range(self, surface: pygame.Surface, points: list[tuple[float, float]], start: int, end: int, shift: float, wave_t: float, color: tuple[int, int, int], glow_color: tuple[int, int, int], horizon: int) -> None:
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
        self.transition_buildings: list[Building] | None = None
        self.transition_seed: int | None = None
        self.transition_elapsed = 0.0
        self.transition_elapsed = 0.0
        self.seed = -1
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        self.seed = seed
        self.buildings = self._make_buildings(seed)

    def _make_buildings(self, seed: int) -> list[Building]:
        rng = random.Random(seed + 202)
        buildings: list[Building] = []
        x = -17.5
        while x < 17.5 and len(buildings) < self.config.city_count:
            w = rng.uniform(0.95, 2.35)
            h = rng.uniform(1.4, 7.4)
            buildings.append(Building(x, w, h, rng.choice([0, 0, 0, 1, 2]), rng.choice([0, 0, 1, 1, 2]), rng.choice([0, 0, 1, 1, 2]), rng.choice([0, 0, 0, 0, 1, 2]), rng.choice([0, 0, 0, 1, 2])))
            x += w + rng.uniform(0.75, 1.65)
        return buildings

    def begin_transition(self, seed: int) -> None:
        if self.transition_buildings is not None:
            return
        self.transition_seed = seed
        self.transition_buildings = self._make_buildings(seed)
        self.transition_elapsed = 0.0

    def update_transition(self, dt: float) -> None:
        if self.transition_buildings is None:
            return
        self.transition_elapsed += max(0.0, dt)
        if self.transition_elapsed < self.config.skyline_transition_duration:
            return
        self.buildings = self.transition_buildings
        self.seed = self.transition_seed if self.transition_seed is not None else self.seed
        self.transition_buildings = None
        self.transition_seed = None
        self.transition_elapsed = 0.0

    def draw(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch) -> None:
        z = 21.5
        building_sets: list[tuple[list[Building], float]] = [(self.buildings, 0.0)]
        if self.transition_buildings is not None:
            progress = min(1.0, self.transition_elapsed / self.config.skyline_transition_duration)
            span = (self.config.width + 24.0) * z / self.config.focal_length + 2.0
            building_sets = [(self.buildings, span * progress), (self.transition_buildings, span * (progress - 1.0))]
        for buildings, transition_shift in building_sets:
            self._draw_building_set(surface, projection, t, batch, z, buildings, transition_shift)

    def _draw_building_set(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch, z: float, buildings: list[Building], transition_shift: float) -> None:
        palette = self.config.palette
        parallax = math.sin(t * 0.10 * self.config.speed) * 0.45
        ground_y = 1.25
        for building in buildings:
            x0 = building.x + parallax + transition_shift
            x1 = x0 + building.w
            top_y = ground_y - building.h
            p0, p1 = projection.project(x0, ground_y, z), projection.project(x1, ground_y, z)
            p2, p3 = projection.project(x1, top_y, z), projection.project(x0, top_y, z)
            self._fill_mask(surface, palette.background, (p0, p1, p2, p3))
            accent_colors = (palette.green, palette.cyan, palette.magenta)
            color = accent_colors[building.color_mode] if building.h > 5.8 else palette.green
            if building.h <= 2.8:
                color = palette.dim
            if self.config.audio_mid > 0.0:
                color = mix_color(color, int(90 * self.config.audio_mid))
            batch.add(p0, p1, color); batch.add(p1, p2, color); batch.add(p2, p3, color); batch.add(p3, p0, color)
            for band in range(1, building.bands + 1):
                y = ground_y - building.h * band / (building.bands + 1)
                batch.add(projection.project(x0, y, z), projection.project(x1, y, z), palette.dim, glow=False)
            for col in range(1, building.columns + 1):
                x = x0 + building.w * col / (building.columns + 1)
                batch.add(projection.project(x, ground_y, z), projection.project(x, top_y, z), palette.dim, glow=False)
            if building.roof == 1:
                apex = projection.project((x0 + x1) * 0.5, top_y - building.w * 1.2, z)
                self._fill_mask(surface, palette.background, (p3, p2, apex)); batch.add(p3, apex, color); batch.add(apex, p2, color)
            elif building.roof == 2:
                spire = projection.project((x0 + x1) * 0.5, top_y - building.h * 0.45, z)
                batch.add(projection.project((x0 + x1) * 0.5, top_y, z), spire, palette.yellow if building.h > 6.5 else color)
            mid_x = (x0 + x1) * 0.5
            if building.ornament == 1 and building.h > 5.0:
                tip = projection.project(mid_x, top_y - 1.2, z)
                batch.add(projection.project(mid_x - building.w * 0.25, top_y, z), tip, palette.cyan)
                batch.add(tip, projection.project(mid_x + building.w * 0.25, top_y, z), palette.cyan)
            elif building.ornament == 2 and building.h > 6.2:
                mast = projection.project(mid_x, top_y - 1.6, z)
                batch.add(projection.project(mid_x, top_y, z), mast, palette.dim, glow=False)
                beacon = projection.project(mid_x, top_y - 1.8 + math.sin(t * 4.0) * 0.12, z)
                if beacon is not None:
                    pygame.draw.circle(surface, palette.red, beacon, 1)

    @staticmethod
    def _fill_mask(surface: pygame.Surface, color: tuple[int, int, int], points: tuple[Point | None, ...]) -> None:
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
        self.style, self.x_ratio, self.y_ratio = rng.randint(0, 2), rng.choice([0.28, 0.34, 0.42, 0.64, 0.72]), rng.uniform(0.18, 0.28)

    def draw(self, surface: pygame.Surface, t: float) -> None:
        palette = self.config.palette
        radius = int(self.config.height * (0.135 + math.sin(t * 1.3) * 0.006 + self.config.audio_level * 0.04))
        cx, cy = int(self.config.width * self.x_ratio), int(self.config.horizon_y - self.config.height * self.y_ratio)
        color = blend_color(palette.red, palette.yellow, 0.25 + 0.25 * math.sin(t * 0.45))
        if self.config.glow:
            pygame.draw.circle(surface, palette.glow, (cx, cy), radius + 2 + int(self.config.audio_onset * 3), 2)
        if self.style == 0:
            self._draw_striped_disc(surface, cx, cy, radius, color, 7); pygame.draw.circle(surface, color, (cx, cy), radius, 1)
        elif self.style == 1:
            pygame.draw.circle(surface, color, (cx, cy), radius, 1); pygame.draw.circle(surface, palette.yellow, (cx, cy), max(4, radius // 2), 1)
            tilt = int(math.sin(t * 0.8) * 3)
            pygame.draw.line(surface, palette.cyan, (cx - radius - 8, cy + tilt), (cx + radius + 8, cy - tilt), 1)
            pygame.draw.line(surface, palette.dim, (cx - radius - 5, cy + tilt + 5), (cx + radius + 5, cy - tilt + 5), 1)
        else:
            self._draw_striped_disc(surface, cx, cy, radius, color, 9); pygame.draw.circle(surface, color, (cx, cy), radius, 1)
            pygame.draw.circle(surface, palette.yellow, (min(self.config.width - 20, cx + radius + 18), cy + 8), max(8, radius // 2), 1)

    @staticmethod
    def _draw_striped_disc(surface: pygame.Surface, cx: int, cy: int, radius: int, color: tuple[int, int, int], spacing: int) -> None:
        for y in range(cy - radius, cy + radius + 1, spacing):
            dx = int(math.sqrt(max(0, radius * radius - (y - cy) * (y - cy))))
            pygame.draw.line(surface, color if (y // spacing) % 2 == 0 else mix_color(color, -70), (cx - dx, y), (cx + dx, y), 1)
