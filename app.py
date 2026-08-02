import random
import os
import time

import pygame

from config import Config
from microphone import Microphone
from renderers.actors import DroneRenderer, PortalRenderer
from renderers.background import BackgroundRenderer
from renderers.core import LineBatch, Projection, VectorDistortion, blend_palette, smoothstep
from renderers.effects import FXRenderer
from renderers.landscape import CityRenderer, GridRenderer, SunRenderer, TerrainRenderer


class App:
    """Own the Pygame lifecycle and compose the procedural renderers."""

    def __init__(self, config: Config) -> None:
        self.config = config
        if config.video_driver != "auto":
            os.environ["SDL_VIDEODRIVER"] = config.video_driver
        pygame.init()
        pygame.display.set_caption("Retro Tron Wireframe Visualizer")
        flags = pygame.FULLSCREEN if config.fullscreen else 0
        display_size = (config.width * config.scale, config.height * config.scale)
        if config.fullscreen:
            try:
                desktop_sizes = pygame.display.get_desktop_sizes()
            except pygame.error:
                desktop_sizes = []
            if desktop_sizes and all(size > 0 for size in desktop_sizes[0]):
                display_size = desktop_sizes[0]
        self.window = pygame.display.set_mode(display_size, flags)
        pygame.mouse.set_visible(False)
        internal_size = (config.width, config.height)
        self.surface = self.window if self.window.get_size() == internal_size else pygame.Surface(internal_size).convert()
        self.scene_surface = pygame.Surface((config.width, config.height)).convert()
        self.viewport_rect = self._fit_viewport(internal_size, self.window.get_size())
        self.presentation_surface = None
        if self.surface is not self.window and self.viewport_rect.size != self.window.get_size():
            self.presentation_surface = pygame.Surface(self.viewport_rect.size).convert()
        print(
            f"Video: driver={pygame.display.get_driver()} pygame={pygame.version.ver} "
            f"SDL={pygame.version.SDL} window={self.window.get_size()} "
            f"viewport={self.viewport_rect.size} direct={self.surface is self.window}",
            flush=True,
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 16)
        self.projection = Projection(config)
        self.batch = LineBatch()
        self.vector_distortion = VectorDistortion(config)
        self.background = BackgroundRenderer(config)
        self.grid = GridRenderer(config)
        self.terrain = TerrainRenderer(config)
        self.city = CityRenderer(config)
        self.sun = SunRenderer(config)
        self.drones = DroneRenderer(config)
        self.portals = PortalRenderer(config)
        self.fx = FXRenderer(config)
        self.microphone = Microphone(enabled=config.audio_enabled)
        self.microphone.start()
        if config.audio_enabled and self.microphone.available:
            print(f"Microphone input: {self.microphone.device_name}", flush=True)
        elif config.audio_enabled and self.microphone.error:
            print(f"Microphone unavailable: {self.microphone.error}", flush=True)
        self.running = True
        self.elapsed = 0.0
        self.next_seed_change = config.auto_seed_interval
        self.next_palette_change = config.auto_palette_interval
        self.palette_transition_start = -config.palette_transition_duration
        self.palette_from = config.palette
        self.palette_to = config.palette
        self.config.current_palette = config.palette
        self._closed = False
        self.update_ms = 0.0
        self.draw_ms = 0.0
        self.present_ms = 0.0

    @staticmethod
    def _fit_viewport(source_size: tuple[int, int], target_size: tuple[int, int]) -> pygame.Rect:
        source_width, source_height = source_size
        target_width, target_height = target_size
        scale = min(target_width / source_width, target_height / source_height)
        width = max(1, round(source_width * scale))
        height = max(1, round(source_height * scale))
        return pygame.Rect((target_width - width) // 2, (target_height - height) // 2, width, height)

    def randomize_seed(self) -> None:
        if self.city.transition_buildings is not None or self.terrain.transition_points is not None:
            return
        self.config.seed = random.randint(1, 999_999)
        self.city.begin_transition(self.config.seed)
        self.terrain.begin_transition(self.config.seed)
        self.grid.begin_transition()

    def start_palette_transition(self, target_index: int) -> None:
        self.palette_from = self.config.palette
        self.config.palette_index = target_index % len(self.config.palettes)
        self.palette_to = self.config.palettes[self.config.palette_index]
        self.palette_transition_start = self.elapsed
        self.config.current_palette = self.palette_from

    def toggle_microphone(self) -> None:
        self.config.audio_enabled = not self.config.audio_enabled
        self.microphone.set_enabled(self.config.audio_enabled)

    def update_palette_transition(self) -> None:
        elapsed = self.elapsed - self.palette_transition_start
        if elapsed >= self.config.palette_transition_duration:
            self.config.current_palette = self.palette_to
            return
        self.config.current_palette = blend_palette(
            self.palette_from,
            self.palette_to,
            smoothstep(elapsed / self.config.palette_transition_duration),
        )

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
            elif event.key == pygame.K_d:
                self.config.vector_distortion = not self.config.vector_distortion
            elif event.key == pygame.K_c:
                self.start_palette_transition(self.config.palette_index + 1)
            elif event.key == pygame.K_v:
                self.config.auto_variation = not self.config.auto_variation
            elif event.key == pygame.K_m:
                self.toggle_microphone()
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

    def update(self, dt: float) -> None:
        self.microphone.update(dt)
        self.city.update_transition(dt)
        self.terrain.update_transition(dt)
        transition_active = self.city.transition_buildings is not None or self.terrain.transition_points is not None
        self.grid.update(dt, transition_active)
        features = self.microphone.features
        self.config.audio_level = features.level
        self.config.audio_low = features.low
        self.config.audio_mid = features.mid
        self.config.audio_high = features.high
        self.config.audio_onset = features.onset_pulse
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
        label = f"{self.clock.get_fps():04.1f} FPS  draw {self.draw_ms:04.1f}  flip {self.present_ms:04.1f}ms"
        self.surface.blit(self.font.render(label, False, self.config.palette.text), (5, 5))

    def draw_vu_meter(self) -> None:
        if not self.config.show_fps:
            return
        palette = self.config.palette
        left, right, y = 6, self.config.width - 6, self.config.height - 7
        pygame.draw.line(self.surface, palette.dim, (left, y), (right, y), 2)
        active_right = left + int((right - left) * self.microphone.features.level)
        if active_right > left:
            pygame.draw.line(self.surface, palette.cyan, (left, y), (active_right, y), 2)

    def draw(self) -> None:
        draw_started = time.perf_counter() if self.config.show_fps else 0.0
        palette = self.config.palette
        distortion_active = self.config.vector_distortion and self.config.audio_onset > 0.0
        scene = self.scene_surface if distortion_active else self.surface
        scene.fill(palette.background)
        self.projection.refresh()
        self.batch.clear()
        self.background.draw(scene, self.elapsed)
        self.sun.draw(scene, self.elapsed)
        self.terrain.draw(scene, self.elapsed)
        self.city.draw(scene, self.projection, self.elapsed, self.batch)
        self.grid.draw(scene, self.projection, self.elapsed, self.batch)
        self.drones.draw(scene, self.projection, self.elapsed, self.batch)
        self.batch.draw(scene, self.config.glow, palette.glow, self.config.audio_onset)
        # self.portals.draw(scene, self.projection, self.elapsed)
        self.fx.draw(scene, self.elapsed)
        if distortion_active:
            self.vector_distortion.draw(scene, self.surface, palette.background, self.elapsed, self.config.audio_onset)
        self.draw_vu_meter()
        self.draw_fps()
        if self.surface is not self.window:
            if self.presentation_surface is None:
                pygame.transform.scale(self.surface, self.window.get_size(), self.window)
            else:
                pygame.transform.scale(self.surface, self.presentation_surface.get_size(), self.presentation_surface)
                self.window.fill(palette.background)
                self.window.blit(self.presentation_surface, self.viewport_rect)
        if draw_started:
            self.draw_ms = (time.perf_counter() - draw_started) * 1000.0
        present_started = time.perf_counter() if self.config.show_fps else 0.0
        pygame.display.flip()
        if present_started:
            self.present_ms = (time.perf_counter() - present_started) * 1000.0

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.microphone.stop()
        pygame.quit()

    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick(self.config.fps) / 1000.0
                self.elapsed += dt
                for event in pygame.event.get():
                    self.handle_event(event)
                update_started = time.perf_counter() if self.config.show_fps else 0.0
                self.update(dt)
                if update_started:
                    self.update_ms = (time.perf_counter() - update_started) * 1000.0
                self.draw()
        finally:
            self.close()
