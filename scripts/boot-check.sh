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

echo "== Short boot hotspots =="
systemd-analyze blame | head -20 | awk '
  /plymouth-quit-wait\.service|NetworkManager-wait-online\.service|ModemManager\.service|display-manager\.service|user@[0-9]+\.service|accounts-daemon\.service|polkit\.service/ {
    print
  }
'
echo

echo "== Plymouth =="
journalctl -b | grep -i plymouth | tail -20 || true
echo

echo "== Network wait =="
journalctl -b | grep -iE "NetworkManager-wait-online|NetworkManager" | tail -20 || true
echo

echo "== Display/session =="
journalctl -b | grep -iE "display-manager|x11|xorg|wayland|lightdm|lxsession" | tail -30 || true
echo

echo "== Driver/TFT =="
journalctl -b | grep -iE "spi|fb|drm|xpt|tft|lcd|ili" | tail -30 || true
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
if systemd-analyze blame | head -20 | grep -qi "NetworkManager-wait-online.service"; then
  echo "- NetworkManager wait-online is in the top boot delays."
fi
if journalctl -b | grep -qi "plymouth-quit-wait.service"; then
  echo "- plymouth-quit-wait.service appears in the boot path."
fi
if journalctl -b | grep -qi "display-manager.service"; then
  echo "- display-manager.service is part of the startup chain."
fi
if grep -qE 'quiet[[:space:]]+splash' /boot/firmware/cmdline.txt 2>/dev/null || grep -qE 'quiet[[:space:]]+splash' /boot/cmdline.txt 2>/dev/null; then
  echo "- cmdline.txt contains 'quiet splash'. Removing it will make boot logs visible."
fi
if systemctl is-enabled NetworkManager-wait-online.service >/dev/null 2>&1; then
  echo "- Consider: sudo systemctl disable --now NetworkManager-wait-online.service"
fi
if systemctl is-enabled ModemManager.service >/dev/null 2>&1; then
  echo "- Consider: sudo systemctl disable --now ModemManager.service"
fi
echo "- If you want less splash delay, remove 'quiet splash' from cmdline.txt."
echo
echo "Done."
