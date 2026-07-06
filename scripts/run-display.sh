#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET=""
RUN_APP=0
AUTO_UPDATE=1
APP_FORWARD_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      shift
      TARGET="${1:-}"
      ;;
    --target=*)
      TARGET="${1#*=}"
      ;;
    --run-app|--kiosk)
      RUN_APP=1
      ;;
    --no-update)
      AUTO_UPDATE=0
      ;;
    --)
      shift
      APP_FORWARD_ARGS+=("$@")
      break
      ;;
    *)
      APP_FORWARD_ARGS+=("$1")
      ;;
  esac
  shift
done

case "$TARGET" in
  hdmi|gpio)
    ;;
  *)
    echo "Usage: bash scripts/run-display.sh --target hdmi|gpio [--run-app] [app args...]"
    exit 1
    ;;
esac

APP_ARGS=(--profile pi --fullscreen --width 480 --height 320 --scale 1)

maybe_update_repo() {
  if [[ "$AUTO_UPDATE" -ne 1 ]]; then
    return 0
  fi

  if ! command -v git >/dev/null 2>&1; then
    return 0
  fi

  if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  if ! git -C "$ROOT_DIR" fetch --quiet origin main; then
    echo "Auto-update skipped: network unavailable or remote unreachable."
    return 0
  fi

  local local_head remote_head
  local_head="$(git -C "$ROOT_DIR" rev-parse HEAD)"
  remote_head="$(git -C "$ROOT_DIR" rev-parse origin/main)"

  if [[ "$local_head" == "$remote_head" ]]; then
    echo "Already up to date."
    return 0
  fi

  echo "Updating repo from origin/main..."
  if git -C "$ROOT_DIR" pull --ff-only origin main; then
    echo "Update complete."
  else
    echo "Auto-update failed; local changes may be blocking a fast-forward pull."
  fi
}

cd "$ROOT_DIR"

if [[ "$RUN_APP" -eq 1 || -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]]; then
  env SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}" python3 main.py "${APP_ARGS[@]}" "${APP_FORWARD_ARGS[@]}"
  app_status=$?
  maybe_update_repo
  exit "$app_status"
fi

if ! command -v startx >/dev/null 2>&1; then
  echo "startx not found. Run: bash scripts/install-display.sh --target $TARGET"
  exit 1
fi

STARTX_ARGS=(--target "$TARGET" --run-app)
if [[ "$AUTO_UPDATE" -eq 0 ]]; then
  STARTX_ARGS+=(--no-update)
fi
STARTX_ARGS+=("${APP_FORWARD_ARGS[@]}")

startx /bin/bash "$SCRIPT_DIR/run-display.sh" "${STARTX_ARGS[@]}"
app_status=$?
maybe_update_repo
exit "$app_status"
