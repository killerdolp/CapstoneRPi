#!/usr/bin/env bash
# Launch the Skin Assessment UI fullscreen on the Pi's touch display.
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland}"
export SKIN_ASSESSMENT_DATA="${SKIN_ASSESSMENT_DATA:-$HOME/skin_assessment_data}"
exec "$APP_DIR/.venv/bin/python" -m skin_assessment.main --kiosk "$@"
