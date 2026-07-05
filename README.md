# Retro Tron Wireframe Visualizer

A small Python/Pygame procedural visualizer for Raspberry Pi 3 Model B and Windows development. It renders a low-resolution neon vector world with an infinite forward-scrolling grid, layered procedural mountains, a sparse clean masked skyline, segmented suns/moons, a small portal accent, starfields, data-rain, flying wireframe drones, scanlines, flicker, and fake glow.

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
python main.py --width 480 --height 320
python main.py --width 320 --height 240
python main.py --width 320 --height 200
python main.py --scale 2 --fps 30
python main.py --fullscreen
python main.py --no-auto
python main.py --profile pi
```

## Run On Raspberry Pi

The Raspberry Pi OS package is usually enough and avoids building wheels on-device.
These commands assume the project lives in `/home/pi/supertronicopygame`; adjust the path if you copy it somewhere else.

```bash
sudo apt update
sudo apt install -y python3-pygame git
cd /home/pi/supertronicopygame
python3 main.py --profile pi --width 480 --height 320 --scale 1
```

If you prefer a virtual environment and have a recent Python setup:

```bash
cd /home/pi/supertronicopygame
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python main.py --profile pi --width 480 --height 320 --scale 1
```

For a small display or fullscreen launch:

```bash
python3 main.py --profile pi --width 480 --height 320 --scale 1
python3 main.py --profile pi --fullscreen --width 480 --height 320
python3 main.py --profile pi --width 320 --height 240 --scale 1
python3 main.py --profile pi --width 320 --height 200 --scale 1
```

## Raspberry Pi Autorun Fullscreen

Use this when the Pi should boot directly into the visualizer. This setup is intended for Raspberry Pi OS with desktop/autologin enabled, because Pygame fullscreen needs an active display session.

1. Enable desktop autologin:

```bash
sudo raspi-config
```

Choose:

```text
System Options -> Boot / Auto Login -> Desktop Autologin
```

Then reboot once:

```bash
sudo reboot
```

2. Create a user systemd service:

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/retro-tron.service
```

Paste this service file:

```ini
[Unit]
Description=Retro Tron Wireframe Visualizer
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=/home/pi/supertronicopygame
ExecStart=/usr/bin/python3 /home/pi/supertronicopygame/main.py --profile pi --fullscreen --width 480 --height 320 --fps 30
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

Save and enable it:

```bash
systemctl --user daemon-reload
systemctl --user enable retro-tron.service
systemctl --user start retro-tron.service
```

Allow the user service to start at boot:

```bash
sudo loginctl enable-linger pi
```

Check status and logs:

```bash
systemctl --user status retro-tron.service
journalctl --user -u retro-tron.service -f
```

Stop or disable autorun:

```bash
systemctl --user stop retro-tron.service
systemctl --user disable retro-tron.service
```

If your display is `320x240` or `320x200`, change the `ExecStart` line to one of these:

```ini
ExecStart=/usr/bin/python3 /home/pi/supertronicopygame/main.py --profile pi --fullscreen --width 320 --height 240 --fps 30
ExecStart=/usr/bin/python3 /home/pi/supertronicopygame/main.py --profile pi --fullscreen --width 320 --height 200 --fps 30
```

## Controls

- `ESC`: quit
- `F`: toggle FPS/debug text
- `S`: toggle scanlines
- `G`: toggle fake glow
- `C`: smoothly morph to the next color palette
- `V`: toggle automatic scene/palette variation
- `SPACE`: randomize terrain, city, and drones
- `UP` / `DOWN`: change animation speed
- `LEFT` / `RIGHT`: adjust horizon and perspective feel

## Notes

- Internal rendering defaults to `480x320`, then scales with nearest-neighbor pixels.
- The render size is parameterized; for a 480x320 Raspberry Pi display, use `--width 480 --height 320 --scale 1` or fullscreen with the same width/height.
- All visuals are procedural; there are no image or audio assets.
- Automatic variation is enabled by default: palettes smoothly morph and the procedural seed changes over time.
- `--profile high` keeps the richest visuals, `--profile pi` is tuned for Raspberry Pi 3, and `--profile minimal` is a fallback for slow displays.
- The renderer favors cheap `pygame.draw` primitives and cached procedural geometry for Raspberry Pi 3 performance.
- Disable glow and scanlines with `G` and `S` if the target display or Pi setup needs extra headroom.
