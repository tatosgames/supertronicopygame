#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
TARGET_UID="$(id -u "$TARGET_USER")"

if [[ -z "$TARGET_HOME" ]]; then
  echo "Could not resolve home directory for user: $TARGET_USER"
  exit 1
fi

SERVICE_DIR="$TARGET_HOME/.config/systemd/user"
SERVICE_PATH="$SERVICE_DIR/retro-tron-gpio.service"

user_systemctl() {
  sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="/run/user/$TARGET_UID" systemctl --user "$@"
}

echo "Installing retro-tron-gpio.service as a user service for: $TARGET_USER"
echo "Home directory: $TARGET_HOME"

mkdir -p "$SERVICE_DIR"

if user_systemctl list-unit-files 2>/dev/null | grep -q '^retro-tron-gpio\.service'; then
  echo "Removing previous retro-tron-gpio.service..."
  user_systemctl stop retro-tron-gpio.service >/dev/null 2>&1 || true
  user_systemctl disable retro-tron-gpio.service >/dev/null 2>&1 || true
fi

rm -f "$SERVICE_PATH"
user_systemctl daemon-reload >/dev/null 2>&1 || true
user_systemctl reset-failed retro-tron-gpio.service >/dev/null 2>&1 || true

cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Retro Tron Wireframe Visualizer (GPIO TFT)
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$TARGET_HOME/supertronicopygame
Environment=DISPLAY=:0
Environment=XAUTHORITY=$TARGET_HOME/.Xauthority
Environment=SDL_VIDEODRIVER=x11
Environment=SDL_AUDIODRIVER=dummy
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash $TARGET_HOME/supertronicopygame/scripts/rpi.sh --kiosk
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

echo "Reloading user systemd..."
user_systemctl daemon-reload
echo "Enabling user service..."
user_systemctl enable retro-tron-gpio.service

echo "Enabling linger so the user service can start at boot..."
sudo loginctl enable-linger "$TARGET_USER"

echo "Starting user service..."
user_systemctl restart retro-tron-gpio.service

echo "Installed: $SERVICE_PATH"
echo "Check logs with: journalctl --user -u retro-tron-gpio.service -f"
echo "Current status:"
user_systemctl --no-pager --full status retro-tron-gpio.service
