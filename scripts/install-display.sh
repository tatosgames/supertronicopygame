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

TARGET_UID="$(id -u "$TARGET_USER")"

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

user_systemctl() {
  sudo -u "$TARGET_USER" env XDG_RUNTIME_DIR="/run/user/$TARGET_UID" systemctl --user "$@"
}

install_user_service() {
  local service_dir="$TARGET_HOME/.config/systemd/user"
  local service_path="$service_dir/$SERVICE_NAME"
  local log_path="$TARGET_HOME/${SERVICE_NAME%.service}-install.log"

  exec > >(tee "$log_path") 2>&1

  echo "Installing $SERVICE_NAME as a user service for: $TARGET_USER"
  echo "Home directory: $TARGET_HOME"
  echo "Log file: $log_path"

  mkdir -p "$service_dir"
  echo "Writing unit to: $service_path"

  if user_systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}\$"; then
    echo "Removing previous $SERVICE_NAME..."
    user_systemctl stop "$SERVICE_NAME" || true
    user_systemctl disable "$SERVICE_NAME" || true
  fi

  rm -f "$service_path"
  user_systemctl daemon-reload || true
  user_systemctl reset-failed "$SERVICE_NAME" || true

  cat > "$service_path" <<EOF
[Unit]
Description=$TARGET_DESCRIPTION
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$TARGET_HOME/supertronicopygame
Environment=DISPLAY=:0
Environment=XAUTHORITY=$TARGET_HOME/.Xauthority
Environment=SDL_VIDEODRIVER=x11
Environment=SDL_AUDIODRIVER=dummy
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash $ROOT_DIR/scripts/run-display.sh --target $TARGET_EXEC_MODE --run-app
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

  echo "Reloading user systemd..."
  user_systemctl daemon-reload
  echo "Enabling user service..."
  user_systemctl enable "$SERVICE_NAME"

  echo "Enabling linger so the user service can start at boot..."
  sudo loginctl enable-linger "$TARGET_USER"

  echo "Starting user service..."
  user_systemctl restart "$SERVICE_NAME"

  echo "Waiting for service to become active..."
  sleep 2
  if ! user_systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Service failed to start."
    user_systemctl status "$SERVICE_NAME" --no-pager || true
    journalctl --user -u "$SERVICE_NAME" -n 50 --no-pager || true
    exit 1
  fi

  echo "Installed: $service_path"
  echo "Check logs with: journalctl --user -u $SERVICE_NAME -f"
  echo "Current status:"
  user_systemctl --no-pager --full status "$SERVICE_NAME"
}

install_common_packages

case "$TARGET" in
  hdmi)
    target_spec hdmi
    install_user_service
    ;;
  gpio)
    target_spec gpio
    install_user_service
    ;;
esac
