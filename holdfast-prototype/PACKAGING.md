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
`Play Holdfast.command`. Because it's downloaded from the internet, macOS may say it's
from an *"unidentified developer"* — **right-click the file → Open → Open** the first time.
The first launch installs the game engine (~30s, one time); after that it launches instantly.
Requires Python 3.8–3.13 (the launcher detects it and points to a download if missing).

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
