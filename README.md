# Retro Tron Wireframe Visualizer

Python/Pygame visualizer for Raspberry Pi.

## Repo

```bash
https://github.com/tatosgames/supertronicopygame.git
```

## Setup

```bash
sudo apt update
sudo apt install -y git python3-pygame
cd ~
git clone https://github.com/tatosgames/supertronicopygame.git
cd supertronicopygame
```

## GPIO TFT

Use this path only for the GPIO-connected Cytron XPT2046 TFT, not HDMI.

```bash
https://github.com/CytronTechnologies/xpt2046-LCD-Driver-for-Raspberry-Pi
```

Install and verify that panel first, then run:

```bash
cd ~/supertronicopygame
bash scripts/install-display.sh --target gpio
bash scripts/run-display.sh --target gpio
```

The installer creates the `tronico-screen.service` system service and starts it.

The old wrappers still work:

```bash
cd ~/supertronicopygame
bash scripts/rpi.sh --kiosk
```

Auto-start on boot is installed by `scripts/install-display.sh --target gpio`.

## HDMI 480x320

Use this path for the fixed 480x320 HDMI panel on Raspberry Pi OS 64-bit (Bookworm or Trixie).

```bash
cd ~/supertronicopygame
bash scripts/install-display.sh --target hdmi
bash scripts/run-display.sh --target hdmi
```

The installer creates the `tronico-screen.service` system service and starts it.

The old wrapper still works:

```bash
cd ~/supertronicopygame
bash scripts/hdmi.sh
```

## Utilities

Update the repo:

```bash
cd ~/supertronicopygame
git pull --ff-only origin main
```

Boot tuning: see [docs/boot.md](docs/boot.md)

## Controls

- `ESC`: quit
- `F`: toggle FPS/debug text
- `S`: toggle scanlines
- `G`: toggle fake glow
- `C`: change palette
- `V`: toggle automatic variation
- `SPACE`: randomize terrain, city, and drones
- `UP` / `DOWN`: change speed
- `LEFT` / `RIGHT`: adjust horizon

## Notes

- Use `--profile pi` on Raspberry Pi 3 or similar hardware
- Use `--profile minimal` only if the display is too slow
- The visuals are procedural, so there are no image or audio assets
