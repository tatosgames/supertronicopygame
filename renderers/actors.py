import math
import random
from dataclasses import dataclass

import pygame

from config import Config
from renderers.core import LineBatch, Point, Projection


@dataclass
class Drone:
    x: float
    phase: float
    z: float
    y: float
    size: float
    color_mode: int
    shape: int
    y_amplitude: float
    y_speed: float
    z_amplitude: float
    z_speed: float
    rotation_phase: tuple[float, float, float]
    rotation_speed: tuple[float, float, float]


class DroneRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.drones: list[Drone] = []
        self.regenerate(config.seed)

    def regenerate(self, seed: int) -> None:
        rng = random.Random(seed + 303)
        drones: list[Drone] = []
        spawn_horizon = max(1, self.config.horizon_y - 2)
        for _ in range(self.config.drone_count):
            phase = rng.uniform(0.0, math.tau)
            z_amplitude = 1.2 * 1.2 * rng.uniform(0.8, 1.2)
            y_amplitude = 0.25 * 1.2 * rng.uniform(0.8, 1.2)
            y_speed = 1.1 * 1.2 * rng.uniform(0.8, 1.2)
            z_speed = 0.3 * 1.2 * rng.uniform(0.8, 1.2)
            spawn_x = rng.uniform(0.0, self.config.width)
            spawn_y = rng.uniform(4.0, float(spawn_horizon))
            spawn_z = rng.uniform(6.0, 14.0)
            focal_length = self.config.focal_length
            world_x = ((spawn_x - self.config.width * 0.5) / focal_length) * spawn_z
            world_y = ((spawn_y - self.config.horizon_y) / focal_length) * spawn_z
            x_amplitude = 11.0
            rotation_speed = tuple(rng.choice((-1.0, 1.0)) * rng.uniform(0.18, 0.65) * 1.2 for _ in range(3))
            drones.append(Drone(
                x=world_x - math.sin(phase) * x_amplitude,
                phase=phase,
                z=spawn_z - math.cos(phase) * z_amplitude,
                y=world_y - math.sin(phase) * y_amplitude,
                size=rng.uniform(0.32, 0.62), color_mode=rng.randint(0, 3), shape=rng.randint(0, 2),
                y_amplitude=y_amplitude, y_speed=y_speed, z_amplitude=z_amplitude, z_speed=z_speed,
                rotation_phase=(rng.uniform(0.0, math.tau), rng.uniform(0.0, math.tau), rng.uniform(0.0, math.tau)),
                rotation_speed=rotation_speed,
            ))
        self.drones = drones

    @staticmethod
    def _rotate(local: tuple[float, float, float], angles: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = local
        ax, ay, az = angles
        cos_x, sin_x = math.cos(ax), math.sin(ax)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
        cos_y, sin_y = math.cos(ay), math.sin(ay)
        x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
        cos_z, sin_z = math.cos(az), math.sin(az)
        return x * cos_z - y * sin_z, x * sin_z + y * cos_z, z

    def _project_local(self, projection: Projection, origin: tuple[float, float, float], local: tuple[float, float, float], angles: tuple[float, float, float]) -> Point | None:
        rx, ry, rz = self._rotate(local, angles)
        return projection.project(origin[0] + rx, origin[1] + ry, origin[2] + rz)

    def draw(self, surface: pygame.Surface, projection: Projection, t: float, batch: LineBatch) -> None:
        colors = (self.config.palette.red, self.config.palette.yellow, self.config.palette.cyan, self.config.palette.magenta)
        for drone in self.drones:
            x = drone.x + math.sin(t * 0.42 * self.config.speed + drone.phase) * 11.0
            y = drone.y + math.sin(t * drone.y_speed + drone.phase) * drone.y_amplitude
            z = drone.z + math.cos(t * drone.z_speed + drone.phase) * drone.z_amplitude
            s, color = drone.size, colors[drone.color_mode]
            angles = tuple(phase + t * speed * self.config.speed for phase, speed in zip(drone.rotation_phase, drone.rotation_speed))
            origin = (x, y, z)
            if drone.shape == 1:
                top = self._project_local(projection, origin, (0.0, -s * 1.6, 0.0), angles)
                left = self._project_local(projection, origin, (-s * 1.5, 0.0, 0.0), angles)
                right = self._project_local(projection, origin, (s * 1.5, 0.0, 0.0), angles)
                bottom = self._project_local(projection, origin, (0.0, s * 1.2, 0.0), angles)
                back = self._project_local(projection, origin, (s * 0.7, -s * 0.2, s * 1.3), angles)
                for a, b in ((top, left), (left, bottom), (bottom, right), (right, top), (left, back), (right, back), (bottom, back)):
                    batch.add(a, b, color)
                continue
            if drone.shape == 2:
                center = projection.project(x, y, z)
                wing_l = self._project_local(projection, origin, (-s * 2.0, 0.0, 0.0), angles)
                wing_r = self._project_local(projection, origin, (s * 2.0, 0.0, 0.0), angles)
                nose = self._project_local(projection, origin, (0.0, -s * 0.9, -s * 0.3), angles)
                tail = self._project_local(projection, origin, (0.0, s * 0.7, s * 0.5), angles)
                batch.add(wing_l, nose, color); batch.add(nose, wing_r, color); batch.add(wing_r, tail, color); batch.add(tail, wing_l, color)
                if center is not None:
                    pygame.draw.circle(surface, color, center, max(2, int(s * 6)), 1)
                continue
            pts = [
                self._project_local(projection, origin, (-s, -s, 0.0), angles), self._project_local(projection, origin, (s, -s, 0.0), angles),
                self._project_local(projection, origin, (s, s, 0.0), angles), self._project_local(projection, origin, (-s, s, 0.0), angles),
                self._project_local(projection, origin, (-s * 0.45, -s * 1.45, s), angles), self._project_local(projection, origin, (s * 1.55, -s * 1.45, s), angles),
                self._project_local(projection, origin, (s * 1.55, s * 0.55, s), angles), self._project_local(projection, origin, (-s * 0.45, s * 0.55, s), angles),
            ]
            for a, b in ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)):
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
        self.portals = [Portal(rng.uniform(7.0, 12.0), rng.uniform(12.0, 20.0), rng.uniform(0.75, 1.35), rng.uniform(0.0, math.tau), rng.randint(0, 1)) for _ in range(1)]

    def draw(self, surface: pygame.Surface, projection: Projection, t: float) -> None:
        palette = self.config.palette
        colors = (palette.cyan, palette.magenta, palette.yellow)
        for portal in self.portals:
            bob = math.sin(t * 0.9 + portal.phase) * (0.25 + self.config.audio_mid * 0.45)
            center, rim = projection.project(portal.x, -portal.radius + bob, portal.z), projection.project(portal.x + portal.radius, -portal.radius + bob, portal.z)
            if center is None or rim is None:
                continue
            rx = max(3, int(abs(rim[0] - center[0]) * (1.0 + self.config.audio_mid * 0.55)))
            ry = max(5, int(rx * 1.45))
            rect = pygame.Rect(center[0] - rx, center[1] - ry, rx * 2, ry * 2)
            color = colors[portal.color_mode]
            if self.config.glow:
                pygame.draw.ellipse(surface, palette.glow, rect.inflate(4, 4), 2)
            pygame.draw.ellipse(surface, color, rect, 1)
            pygame.draw.line(surface, color, (center[0] - rx, center[1]), (center[0] + rx, center[1]), 1)
            if int(t * 4 + portal.phase) % 2 == 0:
                pygame.draw.line(surface, palette.dim, (center[0], center[1] - ry), (center[0], center[1] + ry), 1)
