#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="tronico-screen.service"

usage() {
  echo "Usage: sudo bash scripts/service-control.sh pause|resume|status"
  echo
  echo "  pause   Stop and temporarily disable the display service"
  echo "  resume  Re-enable and start the display service"
  echo "  status  Show the current service state"
}

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "Run this script with sudo." >&2
    exit 1
  fi
}

command="${1:-}"

case "$command" in
  pause)
    require_root
    systemctl disable --now "$SERVICE_NAME"
    systemctl reset-failed "$SERVICE_NAME" || true
    echo "Display service paused: $SERVICE_NAME"
    echo "It will remain disabled until you run:"
    echo "  sudo bash scripts/service-control.sh resume"
    ;;
  resume)
    require_root
    systemctl enable --now "$SERVICE_NAME"
    echo "Display service resumed and enabled at boot: $SERVICE_NAME"
    ;;
  status)
    systemctl --no-pager --full status "$SERVICE_NAME" || true
    echo
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
      echo "Boot start: enabled"
    else
      echo "Boot start: disabled"
    fi
    ;;
  *)
    usage
    exit 1
    ;;
esac
