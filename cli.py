import argparse

from config import Config


def parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(description="Retro Tron wireframe visualizer for Pygame.")
    parser.add_argument("--width", type=int, default=480, help="Internal render width.")
    parser.add_argument("--height", type=int, default=320, help="Internal render height.")
    parser.add_argument("--scale", type=int, default=2, help="Window scale for low-resolution output.")
    parser.add_argument("--fps", type=int, default=30, help="Frame-rate cap.")
    parser.add_argument("--seed", type=int, default=1979, help="Procedural seed.")
    parser.add_argument("--fullscreen", action="store_true", help="Launch fullscreen.")
    parser.add_argument("--no-auto", action="store_true", help="Disable automatic seed and palette variation.")
    parser.add_argument("--no-audio", action="store_true", help="Disable microphone capture and audio reactions.")
    parser.add_argument("--profile", choices=("high", "pi", "minimal"), default="high", help="Visual/performance profile. Use 'pi' for Raspberry Pi 3.")
    args = parser.parse_args(argv)
    config = Config(
        width=max(160, args.width), height=max(120, args.height), scale=max(1, args.scale),
        fps=max(15, min(120, args.fps)), seed=args.seed, fullscreen=args.fullscreen,
        profile=args.profile, auto_variation=not args.no_auto, audio_enabled=not args.no_audio,
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
