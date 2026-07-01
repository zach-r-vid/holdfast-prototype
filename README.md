# HOLDFAST

A twin-stick shooter × tower-defense hybrid. Place towers, then jump in and
fight alongside them — dodge bullet-hell patterns, man your turrets for boosted
damage, and hold the line wave after wave.

This is an early **prototype** (Python + Panda3D). Placeholder art, real gameplay.

## Download & play

Grab the latest build from the **[Releases page »](../../releases/latest)**

### Windows
1. Download `holdfast-<version>_win_amd64.zip`
2. Unzip it, open the `holdfast` folder, double-click **`Holdfast.exe`**
3. First launch shows *"Windows protected your PC"* (the app isn't signed) →
   click **More info → Run anyway**

### macOS (Apple Silicon)
1. Download `holdfast-<version>_mac.zip`
2. Unzip it, open the `Holdfast` folder, **right-click `Play Holdfast.command` → Open → Open**
   (right-click is only needed the first time, to get past Gatekeeper)
3. The first launch installs the game engine (~30s, one time), then plays instantly.
   Requires Python 3.8–3.13 — the launcher checks and points you to a download if needed.

## Controls

| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Aim |
| Left Click | Shoot |
| Shift / Right Click | Dash |
| E | Enter/exit tower |
| Tab | Build menu (planning phase) |
| 1 / 2 / 3 | Select tower type |
| Enter | Start next wave |
| Esc | Pause |

## Running from source

```bash
cd holdfast-prototype
pip install -r requirements.txt
python main.py
```

## Building the shareable bundles

See **[holdfast-prototype/PACKAGING.md](holdfast-prototype/PACKAGING.md)**.
