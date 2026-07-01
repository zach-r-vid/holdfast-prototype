#!/bin/bash
#
# Play Holdfast — double-click launcher for macOS.
#
# On first run this creates a small local Python environment and installs the
# game engine (Panda3D). That takes ~30 seconds and only happens once; after
# that, double-clicking launches the game instantly.
#
# Requires a Python 3.8–3.13 installation. If you only have 3.14+ (or none),
# the launcher tells you where to get a compatible one.

# Run from the folder this script lives in, no matter where it's launched from.
cd "$(dirname "$0")" || exit 1

VENV=".venv-play"

echo "======================================"
echo "   HOLDFAST"
echo "======================================"

# --- Find a Panda3D-compatible Python (3.8–3.13) ---------------------------
pick_python() {
    local candidates=(
        python3.13 python3.12 python3.11 python3.10 python3.9 python3.8
        /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3 python3
    )
    for c in "${candidates[@]}"; do
        command -v "$c" >/dev/null 2>&1 || continue
        # Accept only 3.8 <= version <= 3.13 (Panda3D 1.10.16 wheel range).
        if "$c" -c 'import sys; sys.exit(0 if (3,8) <= sys.version_info[:2] <= (3,13) else 1)' 2>/dev/null; then
            echo "$c"
            return 0
        fi
    done
    return 1
}

if [ ! -d "$VENV" ]; then
    PY="$(pick_python)"
    if [ -z "$PY" ]; then
        echo
        echo "Couldn't find a compatible Python (need 3.8–3.13)."
        echo "Install Python 3.12 from https://www.python.org/downloads/release/python-3127/"
        echo "then double-click this file again."
        echo
        read -n 1 -s -r -p "Press any key to close."
        exit 1
    fi
    echo "First-time setup using $("$PY" --version 2>&1) — installing the game engine (~30s)…"
    "$PY" -m venv "$VENV" || { echo "Failed to create environment."; read -n 1 -s -r -p "Press any key to close."; exit 1; }
    "$VENV/bin/python" -m pip install --upgrade pip >/dev/null 2>&1
    if ! "$VENV/bin/pip" install "panda3d==1.10.16"; then
        echo "Failed to install Panda3D. Check your internet connection and try again."
        rm -rf "$VENV"
        read -n 1 -s -r -p "Press any key to close."
        exit 1
    fi
fi

echo "Launching Holdfast… (close the game window to quit)"
"$VENV/bin/python" main.py
status=$?
if [ $status -ne 0 ]; then
    echo
    echo "The game exited with an error (code $status)."
    read -n 1 -s -r -p "Press any key to close."
fi
