# Agent context

## Project identity

This repository contains a procedural Python/Pygame visualizer, not a complete
game. The application creates a retro-Tron wireframe scene in real time:
perspective grid, terrain, city skyline, sun, drones, portals, stars, scanlines,
glow and palette transitions. There are no sprites, image assets, audio assets,
levels, collisions, networking or save files.

## Hardware target

The primary target is:

- Raspberry Pi 3 or similar;
- Raspberry Pi OS 64-bit, documented for Bookworm/Trixie;
- fixed 480x320 HDMI display.

The hardware launch configuration is fullscreen, 480x320, `scale=1`, 30 FPS and
`--profile pi`. The default `Config` values are more general-purpose, but the
display scripts override them for the target hardware.

An older/alternative hardware path exists for a Cytron XPT2046 TFT connected via
GPIO. The external panel driver is not part of this repository.

## Code map

- `main.py` is the entrypoint and owns Pygame initialization, the event/update/
  draw loop, procedural renderers, CLI parsing and performance-profile selection.
- `config.py` defines palettes, dimensions, timing, renderer counts, visual flags
  and derived projection values.
- `scripts/run-display.sh` launches the application, passes the hardware video
  arguments and can auto-update from `origin/main` unless `--no-update` is used.
- `scripts/install-display.sh` installs `tronico-screen.service` for the selected
  display label and starts it after the graphical display manager. The generated
  unit uses `Restart=on-failure`: an explicit clean exit must stay stopped, while
  crashes are restarted.
- `scripts/hdmi.sh` and `scripts/rpi.sh` are convenience wrappers for HDMI and
  GPIO-TFT startup respectively.
- `scripts/service-control.sh` temporarily pauses or resumes the systemd display
  service. `pause` uses `disable --now`; `resume` uses `enable --now`.

## Display behavior

`--target hdmi` and `--target gpio` currently select startup/service labels, not
different renderers or display APIs. Both paths execute the same `main.py` with
the same 480x320 fullscreen arguments. The service explicitly uses X11 through
`DISPLAY=:0` and `SDL_VIDEODRIVER=x11`.

Do not claim that GPIO display support is configured by this code alone: the
Cytron/XPT2046 driver and panel setup must be installed separately.

## Performance constraints

Use `--profile pi` for Raspberry Pi 3-class hardware. It reduces the number of
mountains, buildings, drones, stars and data columns and disables expensive
effects. Use `--profile minimal` only when the target is still too slow. Preserve
the frame-rate-independent timing in the main loop and avoid adding per-frame
work that is not scaled or bounded.

## Audio and USB microphone status

The repository currently has no microphone capture or audio-reactive behavior.
The USB microphone is an intended future input device only. ALSA commands such
as `arecord -l` and a short `arecord`/`aplay` round trip can verify it on the
Raspberry Pi. A future Python capture implementation should use an input-audio
library such as `sounddevice`, not assume that `pygame.mixer` records input.

The systemd service sets `SDL_AUDIODRIVER=dummy`, so the current application does
not produce audio through Pygame. Do not document microphone support as working
until code, dependencies, service behavior and a Raspberry Pi test are added.

## Maintenance rules

- Keep the HDMI 480x320 Raspberry Pi 3 path as the primary documented use case.
- Treat the GPIO TFT path as an alternative unless the driver integration is
  added to this repository.
- Do not call this project a full game; describe it as a visualizer unless the
  code gains gameplay systems.
- Do not modify Pygame behavior when making documentation-only changes.
- Keep README commands aligned with the actual scripts and CLI arguments.
