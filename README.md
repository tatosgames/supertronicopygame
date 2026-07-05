# Retro Tron Wireframe Visualizer

Python/Pygame visualizer for Raspberry Pi.

## Repo URL

```bash
https://github.com/tatosgames/supertronicopygame.git
```

## GPIO TFT Setup

This is the path for a GPIO-connected Cytron XPT2046 TFT, not HDMI.

Cytron driver repo:

```bash
https://github.com/CytronTechnologies/xpt2046-LCD-Driver-for-Raspberry-Pi
```

That driver repo installs the display stack by changing Pi boot/config files and Xorg config. Install and verify the panel first, then use the commands below.

## 1. Install dependencies

```bash
sudo apt update
sudo apt install -y git python3-pygame
```

If `python3-pygame` is missing on your image:

```bash
sudo apt update
sudo apt install -y git python3-venv
```

## 2. Clone the repo

```bash
cd ~
git clone https://github.com/tatosgames/supertronicopygame.git
cd supertronicopygame
```

If you want a venv:

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## 3. Run it manually

From the repo:

```bash
cd ~/supertronicopygame
bash scripts/rpi.sh --kiosk
```

That starts the app on the Cytron display path and, after exit, checks `origin/main` and pulls updates if internet is available.

To skip update for one run:

```bash
cd ~/supertronicopygame
bash scripts/rpi.sh --no-update --kiosk
```

## 4. Auto-start on boot

Install the system service:

```bash
cd ~/supertronicopygame
sudo bash scripts/install-gpio-tft-service.sh
```

Run it with `sudo`. Without it, the service install and `systemctl` steps can fail.

Enable boot to GUI:

```bash
sudo systemctl set-default graphical.target
```

Reboot:

```bash
sudo reboot
```

Check logs:

```bash
journalctl -u retro-tron-gpio.service -f
```

Stop it:

```bash
sudo systemctl stop retro-tron-gpio.service
```

Disable it:

```bash
sudo systemctl disable retro-tron-gpio.service
```

## 5. If you already cloned before and want the latest code

```bash
cd ~/supertronicopygame
git pull --ff-only origin main
```

## Alternate HDMI Path

If you want to run this on an HDMI monitor instead of the GPIO TFT, use:

```bash
cd ~/supertronicopygame
bash scripts/hdmi.sh --install
```

Then run it with:

```bash
cd ~/supertronicopygame
bash scripts/hdmi.sh
```

That path is for HDMI only. Keep using `scripts/rpi.sh` for the Cytron GPIO TFT.

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
