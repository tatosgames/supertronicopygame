#!/usr/bin/env bash
set -euo pipefail
set -E

TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
TARGET_UID="$(id -u "$TARGET_USER")"

trap 'echo "Error on line $LINENO. Aborting." >&2' ERR

if [[ -z "$TARGET_HOME" ]]; then
  echo "Could not resolve home directory for user: $TARGET_USER"
  exit 1
fi

SERVICE_DIR="$TARGET_HOME/.config/systemd/user"
SERVICE_PATH="$SERVICE_DIR/retro-tron-gpio.service"
LOG_PATH="$TARGET_HOME/retro-tron-gpio-install.log"

user_systemctl() {
  sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="/run/user/$TARGET_UID" systemctl --user "$@"
}

exec > >(tee "$LOG_PATH") 2>&1

echo "Installing retro-tron-gpio.service as a user service for: $TARGET_USER"
echo "Home directory: $TARGET_HOME"
echo "Log file: $LOG_PATH"

mkdir -p "$SERVICE_DIR"
echo "Writing unit to: $SERVICE_PATH"

if user_systemctl list-unit-files 2>/dev/null | grep -q '^retro-tron-gpio\.service'; then
  echo "Removing previous retro-tron-gpio.service..."
  user_systemctl stop retro-tron-gpio.service || true
  user_systemctl disable retro-tron-gpio.service || true
fi

rm -f "$SERVICE_PATH"
user_systemctl daemon-reload || true
user_systemctl reset-failed retro-tron-gpio.service || true

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

echo "Waiting for service to become active..."
sleep 2
if ! user_systemctl is-active --quiet retro-tron-gpio.service; then
  echo "Service failed to start."
  user_systemctl status retro-tron-gpio.service --no-pager || true
  journalctl --user -u retro-tron-gpio.service -n 50 --no-pager || true
  exit 1
fi

echo "Installed: $SERVICE_PATH"
echo "Check logs with: journalctl --user -u retro-tron-gpio.service -f"
echo "Current status:"
user_systemctl --no-pager --full status retro-tron-gpio.service
