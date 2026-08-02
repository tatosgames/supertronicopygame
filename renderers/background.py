import math
import random
from dataclasses import dataclass

import pygame

from config import Config


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
            Star(rng.uniform(0, self.config.width), rng.uniform(0, sky_h), rng.uniform(1.0, 8.0), rng.uniform(0.0, math.tau), rng.randint(0, 3))
            for _ in range(self.config.star_count)
        ]
        self.columns = [
            DataColumn(rng.randrange(0, self.config.width, 8), rng.uniform(-sky_h, sky_h), rng.uniform(8.0, 24.0), rng.randint(8, 24), rng.randint(9, 18))
            for _ in range(self.config.data_column_count)
        ]

    def draw(self, surface: pygame.Surface, t: float) -> None:
        palette = self.config.palette
        sky_h = max(24, self.config.horizon_y - 4)
        colors = (palette.dim, palette.green, palette.cyan, palette.magenta)
        for star in self.stars:
            x = int((star.x - t * star.speed * self.config.speed * 0.22) % self.config.width)
            pulse = math.sin(t * 3.0 + star.phase) + self.config.audio_high * 1.4
            color = colors[star.color_mode]
            if pulse > 0.55:
                length = 1 + int(self.config.audio_high * 2.0)
                pygame.draw.line(surface, color, (x - length, int(star.y)), (x + length, int(star.y)), 1)
            else:
                surface.set_at((x, int(star.y)), color)
        for col in self.columns:
            y = (col.y + t * col.speed * self.config.speed) % (sky_h + col.height * 2) - col.height * 2
            color = palette.dim if int((col.x + t) // 16) % 2 else palette.green
            for i in range(0, col.height, col.gap):
                yy = int(y + i)
                if 0 <= yy < sky_h:
                    pygame.draw.line(surface, color, (col.x, yy), (col.x, min(sky_h, yy + 3)), 1)
