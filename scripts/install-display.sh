#!/usr/bin/env bash
set -euo pipefail
set -E

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET=""
DEBUG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      shift
      TARGET="${1:-}"
      ;;
    --target=*)
      TARGET="${1#*=}"
      ;;
    --debug)
      DEBUG=1
      ;;
    --)
      break
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: bash scripts/install-display.sh --target hdmi|gpio [--debug]"
      exit 1
      ;;
  esac
  shift
done

case "$TARGET" in
  hdmi|gpio)
    ;;
  *)
    echo "Usage: bash scripts/install-display.sh --target hdmi|gpio [--debug]"
    exit 1
    ;;
esac

if [[ "$DEBUG" -eq 1 ]]; then
  set -x
fi

TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
SERVICE_NAME="tronico-screen.service"

trap 'echo "Error on line $LINENO. Aborting." >&2' ERR

if [[ -z "$TARGET_HOME" ]]; then
  echo "Could not resolve home directory for user: $TARGET_USER"
  exit 1
fi

install_common_packages() {
  sudo apt update
  sudo apt install -y python3-pygame xinit xserver-xorg xserver-xorg-legacy x11-xserver-utils
}

target_spec() {
  case "$1" in
    hdmi)
      TARGET_DESCRIPTION="Retro Tron Wireframe Visualizer (HDMI)"
      TARGET_EXEC_MODE="hdmi"
      ;;
    gpio)
      TARGET_DESCRIPTION="Retro Tron Wireframe Visualizer (GPIO TFT)"
      TARGET_EXEC_MODE="gpio"
      ;;
  esac
}

system_service_path="/etc/systemd/system/$SERVICE_NAME"

install_system_service() {
  local log_path="/var/log/${SERVICE_NAME%.service}-install.log"

  exec > >(tee "$log_path") 2>&1

  echo "Installing $SERVICE_NAME as a system service for: $TARGET_USER"
  echo "Home directory: $TARGET_HOME"
  echo "Log file: $log_path"

  echo "Writing unit to: $system_service_path"

  if systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}\$"; then
    echo "Removing previous $SERVICE_NAME..."
    sudo systemctl stop "$SERVICE_NAME" || true
    sudo systemctl disable "$SERVICE_NAME" || true
  fi

  sudo rm -f "$system_service_path"
  sudo systemctl daemon-reload || true
  sudo systemctl reset-failed "$SERVICE_NAME" || true

  sudo tee "$system_service_path" >/dev/null <<EOF
[Unit]
Description=$TARGET_DESCRIPTION
After=display-manager.service
Wants=display-manager.service

[Service]
Type=simple
User=$TARGET_USER
Group=$TARGET_USER
WorkingDirectory=$ROOT_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=$TARGET_HOME/.Xauthority
Environment=SDL_VIDEODRIVER=x11
Environment=SDL_AUDIODRIVER=dummy
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash $ROOT_DIR/scripts/run-display.sh --target $TARGET_EXEC_MODE --run-app
Restart=always
RestartSec=3

[Install]
WantedBy=graphical.target
EOF

  echo "Reloading system systemd..."
  sudo systemctl daemon-reload
  echo "Enabling system service..."
  sudo systemctl enable "$SERVICE_NAME"

  echo "Starting system service..."
  sudo systemctl restart "$SERVICE_NAME"

  echo "Waiting for service to become active..."
  sleep 2
  if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Service failed to start."
    sudo systemctl status "$SERVICE_NAME" --no-pager || true
    journalctl -u "$SERVICE_NAME" -n 50 --no-pager || true
    exit 1
  fi

  echo "Installed: $system_service_path"
  echo "Check logs with: journalctl -u $SERVICE_NAME -f"
  echo "Current status:"
  sudo systemctl --no-pager --full status "$SERVICE_NAME"
}

install_common_packages

case "$TARGET" in
  hdmi)
    target_spec hdmi
    install_system_service
    ;;
  gpio)
    target_spec gpio
    install_system_service
    ;;
esac
