# Retro Tron Wireframe Visualizer

Procedural Python/Pygame visualizer for Raspberry Pi and desktop development. It renders a neon wireframe world with a forward-scrolling grid, mountains, skyline, sun/moon, portal accents, stars, data rain, drones, scanlines, flicker, and glow.

The app starts immediately when launched. Keyboard controls are included for live tuning.

## Repository

Clone from:

[`https://github.com/tatosgames/supertronicopygame`](https://github.com/tatosgames/supertronicopygame)

## Raspberry Pi Install

Use this on Raspberry Pi OS with a graphical desktop. If you are on `Lite`, install the desktop edition first.

### 1. Update and install dependencies

```bash
sudo apt update
sudo apt install -y git python3-pygame xinit xserver-xorg xserver-xorg-legacy x11-xserver-utils
```

If `python3-pygame` is not available on your image, use the virtual environment path instead:

```bash
sudo apt update
sudo apt install -y git python3-venv
```

### 2. Clone the repo

```bash
cd ~
git clone https://github.com/tatosgames/supertronicopygame.git
cd supertronicopygame
```

If you want to use a virtual environment:

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the visualizer

Recommended Pi launch:

```bash
python3 main.py --profile pi --width 480 --height 320 --scale 1
```

Fullscreen:

```bash
python3 main.py --profile pi --fullscreen --width 480 --height 320
```

Small displays:

```bash
python3 main.py --profile pi --width 320 --height 240 --scale 1
python3 main.py --profile pi --width 320 --height 200 --scale 1
```

## One-Command Helper

From the repo root:

```bash
bash scripts/rpi.sh --install
```

Then start it again without install:

```bash
bash scripts/rpi.sh
```

The helper installs the Pi desktop/X11 bits when requested. If you run it from a console without a GUI session, it starts `startx` automatically and launches the visualizer fullscreen.

```bash
bash scripts/rpi.sh --fullscreen
```

You can pass extra `main.py` arguments after that, for example:

```bash
bash scripts/rpi.sh --width 320 --height 240 --scale 1
```

## GUI On Raspberry Pi

This app needs a graphical session. On Bookworm:

- `Raspberry Pi OS Desktop` already includes the GUI
- `Raspberry Pi OS Lite` does not include the GUI

If you boot to CLI, use `raspi-config` to switch to desktop boot:

```bash
sudo raspi-config
```

Then choose:

```text
System Options -> Boot -> Desktop
```

If `raspi-config` is missing:

```bash
sudo apt update
sudo apt install -y raspi-config
```

If you only want to launch the desktop for the current session and you already have the desktop packages installed, use:

```bash
sudo systemctl start display-manager
```

## Autostart On Raspberry Pi

If you want the visualizer to boot automatically in fullscreen, keep the Pi on a desktop session with autologin and use a user service.

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/retro-tron.service
```

Paste this:

```ini
[Unit]
Description=Retro Tron Wireframe Visualizer
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=%h/supertronicopygame
ExecStart=/usr/bin/python3 %h/supertronicopygame/main.py --profile pi --fullscreen --width 480 --height 320 --fps 30
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

Enable it:

```bash
systemctl --user daemon-reload
systemctl --user enable retro-tron.service
systemctl --user start retro-tron.service
```

Allow it to start at boot:

```bash
sudo loginctl enable-linger pi
```

Replace `pi` with your actual username if needed.

## Controls

- `ESC`: quit
- `F`: toggle FPS/debug text
- `S`: toggle scanlines
- `G`: toggle fake glow
- `C`: morph to the next color palette
- `V`: toggle automatic scene/palette variation
- `SPACE`: randomize terrain, city, and drones
- `UP` / `DOWN`: change animation speed
- `LEFT` / `RIGHT`: adjust horizon and perspective

## Notes

- Default internal render size is `480x320`
- Use `--profile pi` on Raspberry Pi 3 or similar hardware
- Use `--profile minimal` only if the display is too slow
- The visuals are procedural, so there are no image or audio assets
