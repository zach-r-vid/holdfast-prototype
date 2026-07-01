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
1. Download `holdfast-<version>_mac.zip` and unzip it.
2. Open the `Holdfast` folder and double-click **`Play Holdfast.command`**.
3. macOS will say it *"could not verify... is free of malware"* and only offer
   **Move to Trash / Done** — click **Done**. This is expected (the app isn't
   signed by a paid Apple developer account). To allow it, one time:
   - Open **System Settings → Privacy & Security**
   - Scroll to the **Security** section — you'll see *"Play Holdfast.command was
     blocked…"* with an **Open Anyway** button. Click it, confirm with Touch ID/password.
   - Double-click `Play Holdfast.command` again → **Open**.
4. First launch installs the game engine (~30s, one time), then plays instantly.
   Requires Python 3.8–3.13 — the launcher checks and points you to a download if needed.

> Prefer Terminal? Skip the dialogs entirely: `xattr -cr` on the unzipped
> `Holdfast` folder, then double-click normally. (Full steps are in the
> `READ ME FIRST (Mac).txt` inside the zip.)

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
