# Retro Tron Wireframe Visualizer

A small Python/Pygame procedural visualizer for Raspberry Pi 3 Model B and Windows development. It renders a low-resolution neon vector world with an infinite scrolling grid, layered procedural mountains, varied skyline, segmented suns/moons, portals, starfields, data-rain, flying wireframe drones, scanlines, flicker, and fake glow.

The app runs automatically as soon as it starts. Keyboard controls are included for debugging and live tuning.

## Run On Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Useful launch options:

```powershell
python main.py --width 320 --height 240
python main.py --width 320 --height 200
python main.py --scale 4 --fps 30
python main.py --fullscreen
python main.py --no-auto
```

## Run On Raspberry Pi

The Raspberry Pi OS package is usually enough and avoids building wheels on-device:

```bash
sudo apt update
sudo apt install python3-pygame
python3 main.py
```

If you prefer a virtual environment and have a recent Python setup:

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python main.py
```

For a small display:

```bash
python3 main.py --width 320 --height 240 --scale 1
python3 main.py --width 320 --height 200 --scale 1
python3 main.py --fullscreen --width 320 --height 240
```

## Controls

- `ESC`: quit
- `F`: toggle FPS/debug text
- `S`: toggle scanlines
- `G`: toggle fake glow
- `C`: cycle color palettes
- `V`: toggle automatic scene/palette variation
- `SPACE`: randomize terrain, city, and drones
- `UP` / `DOWN`: change animation speed
- `LEFT` / `RIGHT`: adjust horizon and perspective feel

## Notes

- Internal rendering defaults to `320x240`, then scales with nearest-neighbor pixels.
- All visuals are procedural; there are no image or audio assets.
- Automatic variation is enabled by default: palettes cycle and the procedural seed changes over time.
- The renderer favors cheap `pygame.draw` primitives and cached procedural geometry for Raspberry Pi 3 performance.
- Disable glow and scanlines with `G` and `S` if the target display or Pi setup needs extra headroom.
