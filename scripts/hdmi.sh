#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--install" ]]; then
  shift
  exec /bin/bash "$SCRIPT_DIR/install-display.sh" --target hdmi "$@"
fi

exec /bin/bash "$SCRIPT_DIR/run-display.sh" --target hdmi "$@"
