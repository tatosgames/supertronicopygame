#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"

if [[ -z "$TARGET_HOME" ]]; then
  echo "Could not resolve home directory for user: $TARGET_USER"
  exit 1
fi

LOG_PATH="${TARGET_HOME}/retro-tron-boot-speedup.log"

exec > >(tee "$LOG_PATH") 2>&1

echo "Retro Tron boot speedup"
echo "Log: $LOG_PATH"
echo

CMDLINE_PATH=""
if [[ -f /boot/firmware/cmdline.txt ]]; then
  CMDLINE_PATH="/boot/firmware/cmdline.txt"
elif [[ -f /boot/cmdline.txt ]]; then
  CMDLINE_PATH="/boot/cmdline.txt"
fi

if [[ -z "$CMDLINE_PATH" ]]; then
  echo "cmdline.txt not found."
  exit 1
fi

echo "Using cmdline: $CMDLINE_PATH"

backup_path="${CMDLINE_PATH}.bak.$(date +%Y%m%d-%H%M%S)"
sudo cp "$CMDLINE_PATH" "$backup_path"
echo "Backup written to: $backup_path"

current_cmdline="$(sudo cat "$CMDLINE_PATH")"
new_cmdline="$(
  printf '%s\n' "$current_cmdline" \
    | tr ' ' '\n' \
    | grep -vE '^(quiet|splash)$' \
    | awk 'NF' \
    | paste -sd ' ' -
)"

if [[ -z "$new_cmdline" ]]; then
  echo "Refusing to write empty cmdline."
  exit 1
fi

if [[ "$new_cmdline" != "$current_cmdline" ]]; then
  echo "Removing quiet/splash from cmdline."
  printf '%s\n' "$new_cmdline" | sudo tee "$CMDLINE_PATH" >/dev/null
else
  echo "cmdline.txt already clean."
fi

echo
echo "Disabling NetworkManager-wait-online..."
sudo systemctl disable --now NetworkManager-wait-online.service || true
sudo systemctl mask NetworkManager-wait-online.service || true

echo
echo "Masking Plymouth units if present..."
for unit in plymouth-start.service plymouth-quit-wait.service plymouth-quit.service plymouth-read-write.service plymouth-switch-root.service; do
  if systemctl list-unit-files "$unit" >/dev/null 2>&1; then
    sudo systemctl mask "$unit" || true
  fi
done

echo
echo "Disabling common desktop toast/autostart entries..."
toast_files=(
  "$TARGET_HOME/.config/lxsession/LXDE-pi/autostart"
  "$TARGET_HOME/.config/lxsession/LXDE-pi/desktop-items-0.conf"
  "$TARGET_HOME/.config/autostart/nm-applet.desktop"
  "$TARGET_HOME/.config/autostart/dunst.desktop"
  "$TARGET_HOME/.config/autostart/notification-daemon.desktop"
  "$TARGET_HOME/.config/autostart/xfce4-notifyd.desktop"
  "$TARGET_HOME/.config/autostart/lxqt-notificationd.desktop"
)

for file in "${toast_files[@]}"; do
  if [[ -f "$file" ]]; then
    backup_file="${file}.bak.$(date +%Y%m%d-%H%M%S)"
    sudo cp "$file" "$backup_file"
    echo "- Backed up $file -> $backup_file"
    sudo sed -i \
      -e 's/^[[:space:]]*@dunst/#@dunst/' \
      -e 's/^[[:space:]]*@notification-daemon/#@notification-daemon/' \
      -e 's/^[[:space:]]*@xfce4-notifyd/#@xfce4-notifyd/' \
      -e 's/^[[:space:]]*@lxqt-notificationd/#@lxqt-notificationd/' \
      -e 's/^[[:space:]]*@nm-applet/#@nm-applet/' \
      "$file"
  fi
done

echo
echo "Reloading boot-related services..."
sudo systemctl daemon-reload || true

echo
echo "Current status:"
systemctl is-enabled NetworkManager-wait-online.service >/dev/null 2>&1 && echo "- NetworkManager-wait-online: enabled" || echo "- NetworkManager-wait-online: disabled/masked"
systemctl list-unit-files | grep -E '^plymouth-(start|quit-wait|quit|read-write|switch-root)\.service' || true

echo
echo "Done. Reboot to apply:"
echo "sudo reboot"
