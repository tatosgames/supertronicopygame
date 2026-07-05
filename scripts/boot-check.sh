#!/usr/bin/env bash
set -euo pipefail

FULL=0
LOG_PATH="${HOME}/retro-tron-boot-check.log"

if [[ "${1:-}" == "--full" ]]; then
  FULL=1
  shift
fi

if [[ "${1:-}" == "--log" && -n "${2:-}" ]]; then
  LOG_PATH="$2"
  shift 2
fi

exec > >(tee "$LOG_PATH") 2>&1

echo "Retro Tron boot check"
echo "Log: $LOG_PATH"
echo

run_cmd() {
  local title="$1"
  shift
  echo "== $title =="
  "$@"
  echo
}

run_cmd "Boot timing" systemd-analyze time

echo "== Top boot delays =="
systemd-analyze blame | head -20
echo

echo "== Critical chain =="
systemd-analyze critical-chain
echo

echo "== Plymouth logs =="
journalctl -b | grep -i plymouth || true
echo

echo "== Graphic session logs =="
journalctl -b | grep -iE "display-manager|x11|xorg|wayland|lightdm|lxsession" || true
echo

echo "== Display/driver logs =="
journalctl -b | grep -iE "spi|fb|drm|xpt|tft|lcd|ili" || true
echo

if [[ "$FULL" -eq 1 ]]; then
  echo "== Full boot blame =="
  systemd-analyze blame
  echo

  echo "== Full journal (filtered) =="
  journalctl -b | tail -300
  echo
fi

echo "== Quick hints =="
if journalctl -b | grep -qi "plymouth-quit-wait.service"; then
  echo "- plymouth-quit-wait.service appears in the boot path."
fi
if grep -qE 'quiet[[:space:]]+splash' /boot/firmware/cmdline.txt 2>/dev/null || grep -qE 'quiet[[:space:]]+splash' /boot/cmdline.txt 2>/dev/null; then
  echo "- cmdline.txt contains 'quiet splash'. Removing it will make boot logs visible."
fi
echo
echo "Done."
