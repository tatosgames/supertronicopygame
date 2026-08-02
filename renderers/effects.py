import math
import random

import pygame

from config import Config
from renderers.core import Point


class FXRenderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.scanline_surface = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        self.vignette_surface = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        self.combined_overlay = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
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
        self.combined_overlay = pygame.Surface((self.config.width, self.config.height), pygame.SRCALPHA)
        self.combined_overlay.blit(self.scanline_surface, (0, 0))
        self.combined_overlay.blit(self.vignette_surface, (0, 0))
        self.flicker_surfaces = {}
        for shade in range(1, 16):
            flicker = pygame.Surface((self.config.width, self.config.height), pygame.SRCALPHA)
            flicker.fill((shade, shade, shade, 9))
            self.flicker_surfaces[shade] = flicker
        rng = random.Random(self.config.seed + 707)
        self.noise_frames = [[(rng.randrange(0, self.config.width), rng.randrange(0, self.config.height)) for _ in range(10)] for _ in range(16)]

    def draw(self, surface: pygame.Surface, t: float) -> None:
        if self.config.flicker:
            shade = int(8 + math.sin(t * 18.0) * 5)
            if shade > 0:
                surface.blit(self.flicker_surfaces[min(15, shade)], (0, 0))
            for x, y in self.noise_frames[int(t * 14.0) & 15]:
                surface.set_at((x, y), self.config.palette.text)
        if self.config.scanlines:
            surface.blit(self.combined_overlay, (0, 0))
        else:
            surface.blit(self.vignette_surface, (0, 0))
