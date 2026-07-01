# Packaging & Sharing HOLDFAST

How to build the shareable bundles and hand them to friends.

## TL;DR — build both bundles

```bash
cd holdfast-prototype
.venv/bin/python build.py       # outputs dist/holdfast-0.1.0_win_amd64.zip and _mac.zip
```

> Build from `.venv` (Python 3.12). Do **not** use `venv/` (Python 3.14) — Panda3D
> 1.10.16 has no 3.14 wheels, so the freeze step can't fetch a runtime.

Outputs in `dist/`:

| Bundle | For | How the friend runs it |
|--------|-----|------------------------|
| `holdfast-0.1.0_win_amd64.zip` | Windows 10/11 (64-bit) | Unzip → double-click `Holdfast.exe` |
| `holdfast-0.1.0_mac.zip` | macOS (Apple Silicon) | Unzip → double-click `Play Holdfast.command` |

## What to tell your friends

**Windows:** Unzip anywhere, open the `holdfast` folder, double-click `Holdfast.exe`.
The first launch shows *"Windows protected your PC"* (because the app isn't code-signed) —
click **More info → Run anyway**. This is expected for a hobby build.

**Mac (Apple Silicon):** Unzip, open the `Holdfast` folder, double-click
`Play Holdfast.command`. On macOS 15+ (Sequoia/26) the old right-click→Open trick is gone;
the file shows a *"could not verify… is free of malware"* dialog with only **Move to Trash /
Done**. The one-time fix: click **Done**, then **System Settings → Privacy & Security →**
scroll to **Security → Open Anyway**. (Terminal shortcut: `xattr -cr` the folder.) These steps
ship inside the zip as `READ ME FIRST (Mac).txt`. The first launch installs the engine (~30s,
one time). Requires Python 3.8–3.13 (the launcher detects it and points to a download if missing).

## Why two different mechanisms

Windows ships as a proper frozen `.exe` (Panda3D's `build_apps`). That path does **not**
work for Mac on Apple Silicon:

- **Apple Silicon requires every arm64 binary to be code-signed** — the kernel instantly
  kills unsigned ones (`Killed: 9` / exit 137).
- **Panda3D's packager can't produce a signable arm64 binary.** In stable **1.10.16** the
  frozen game data is appended past the Mach-O's signable region, so `codesign` fails with
  *"main executable failed strict validation."* The fix exists only in **1.11 dev** builds,
  where the packaging tool itself currently crashes (`struct.error`) building arm64.

So macOS ships as a tiny double-click launcher (`Play Holdfast.command`) that runs the game
from source in a local Python environment. No signing needed, fully reliable.

If Panda3D 1.11 ships a stable release with working arm64 signing, revisit this — a native
`.app` would be nicer. Until then, the launcher is the dependable path.

## How the build works

`build.py` does three things:

1. **Stages models** — copies Panda3D's stock models (`models/misc/sphere`, `rgbCube`,
   the `fade`/`iris` screen transitions, the default `cmss12` font) from the installed
   `panda3d` package into `./models/`, so `build_apps` can bundle them. `egg2bam`
   (from the venv's `bin/`) converts them to `.bam` during the freeze. Without this the
   frozen app crashes with *"Couldn't load file models/misc/rgbCube."*
2. **Windows** — runs `setup.py bdist_apps` for `win_amd64`.
3. **Mac** — copies the game source + `Play Holdfast.command` into a `Holdfast/` folder
   and zips it with `ditto` (which preserves the launcher's executable bit).

`./models/` is generated and git-ignored; `build.py` recreates it each run.

### Startup fix baked into the source

Frozen builds (and any non-UTF-8 console) default `stdout` to ASCII, which crashed the game
on the unicode banner at launch. `main.py` reconfigures `stdout`/`stderr` to UTF-8 at
startup to prevent this — keep that guard if you refactor the top of `main.py`.

## Building just one platform

```bash
.venv/bin/python build.py windows
.venv/bin/python build.py mac
```

## Notarized native .app for macOS (work in progress)

The launcher above works but isn't the "download → drag to Applications → no
warnings" experience (that requires an Apple-notarized app). We have the hard
part working: a self-contained, native-arm64 `.app` built with **PyInstaller**
that bundles Python + Panda3D + models — no Python install needed, and verified
to run after being moved. What's left is signing + notarization, which is gated
on Apple Developer credentials.

### Build the .app

```bash
.venv/bin/pip install pyinstaller      # one-time
.venv/bin/python build.py mac-app      # -> pyi_dist/Holdfast.app
```

How it works (all in `build.py` / `pyi_rthook.py`):
- `--collect-binaries panda3d` bundles every Panda3D dylib, including the
  `pandagl` / `openal` plugins that Panda3D loads dynamically at runtime.
- Stock models are converted to `.bam` (the only loader a frozen app has) and
  bundled via `--add-data`.
- `pyi_rthook.py` supplies the startup config a frozen build lacks (normally in
  Panda3D's `etc/Config.prc`): `load-display pandagl`, the audio library,
  `default-model-extension .bam`, and the bundled models' search path.

At this point `pyi_dist/Holdfast.app` is **ad-hoc signed** — it runs locally,
but a downloaded copy still trips Gatekeeper. To finish:

### Remaining steps (need Apple Developer credentials)

1. **Create a "Developer ID Application" certificate** — Xcode → Settings →
   Accounts → Manage Certificates → **+** → Developer ID Application. Verify with
   `security find-identity -v -p codesigning` (look for a *Developer ID
   Application* line; an *Apple Development* cert is **not** sufficient).
2. **Store notarization credentials** (generate an app-specific password at
   appleid.apple.com first):
   ```bash
   xcrun notarytool store-credentials "holdfast-notary" \
     --apple-id "YOUR_APPLE_ID" --team-id "3RH8XHJ3AS" --password "APP-SPECIFIC-PW"
   ```
3. **Sign, notarize, staple, package** (to be scripted once the cert exists):
   ```bash
   codesign --force --deep --options runtime --timestamp \
     --sign "Developer ID Application: <name> (3RH8XHJ3AS)" pyi_dist/Holdfast.app
   # zip it, then:
   xcrun notarytool submit Holdfast.zip --keychain-profile "holdfast-notary" --wait
   xcrun stapler staple pyi_dist/Holdfast.app
   # then wrap in a drag-to-Applications .dmg
   ```

Once notarized, this becomes the primary macOS download and the launcher zip can
retire.
