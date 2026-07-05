#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
TARGET_GROUP="$(id -gn "$TARGET_USER")"

if [[ -z "$TARGET_HOME" ]]; then
  echo "Could not resolve home directory for user: $TARGET_USER"
  exit 1
fi

SERVICE_PATH="/etc/systemd/system/retro-tron-gpio.service"

echo "Installing retro-tron-gpio.service for user: $TARGET_USER"
echo "Using primary group: $TARGET_GROUP"
echo "Home directory: $TARGET_HOME"

sudo tee "$SERVICE_PATH" >/dev/null <<EOF
[Unit]
Description=Retro Tron Wireframe Visualizer (GPIO TFT)
After=graphical.target display-manager.service
Wants=graphical.target

[Service]
Type=simple
User=$TARGET_USER
Group=$TARGET_GROUP
SupplementaryGroups=video,input,render
WorkingDirectory=$TARGET_HOME/supertronicopygame
Environment=SDL_VIDEODRIVER=x11
Environment=SDL_AUDIODRIVER=dummy
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash $TARGET_HOME/supertronicopygame/scripts/rpi.sh --kiosk
Restart=always
RestartSec=3

[Install]
WantedBy=graphical.target
EOF

echo "Reloading systemd..."
sudo systemctl daemon-reload
echo "Enabling service..."
sudo systemctl enable retro-tron-gpio.service
echo "Starting service..."
sudo systemctl restart retro-tron-gpio.service

echo "Installed: $SERVICE_PATH"
echo "Check logs with: journalctl -u retro-tron-gpio.service -f"
echo "Current status:"
sudo systemctl --no-pager --full status retro-tron-gpio.service
