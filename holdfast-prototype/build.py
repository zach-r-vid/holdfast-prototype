#!/usr/bin/env python3
"""
Build HOLDFAST distributables for sharing.

Run from the build virtualenv (the one with Panda3D installed):

    .venv/bin/python build.py            # build both (Windows + Mac)
    .venv/bin/python build.py windows    # Windows zip only
    .venv/bin/python build.py mac        # Mac zip only

Outputs land in dist/:
    holdfast-<ver>_win_amd64.zip  — self-contained double-click Holdfast.exe
    holdfast-<ver>_mac.zip        — game source + "Play Holdfast.command"

Why two different mechanisms? Apple Silicon refuses to run unsigned arm64
binaries, and Panda3D's app packager cannot currently produce a *signable*
arm64 binary (see PACKAGING.md). So Windows ships as a frozen executable while
macOS ships as a tiny double-click launcher that runs the game from source.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "0.1.0"

# Panda3D's command-line tools (egg2bam, used to convert bundled models to
# .bam during the Windows freeze) live next to the Python interpreter.
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]

# Names excluded from the Mac source zip — build junk, envs, and packaging
# scaffolding that a player never needs.
MAC_EXCLUDE = {
    "build", "dist", "models", "__pycache__", ".git", ".gitignore",
    ".venv", "venv", ".venv-play", ".DS_Store", "build.py", "setup.py",
    "PACKAGING.md", ".pytest_cache",
    # PyInstaller (.app) build scaffolding — not needed in the source launcher zip
    "pyi_rthook.py", "pyi_models", "pyi_dist", "pyi_work", "Holdfast.spec",
}


MAC_FIRST_RUN_NOTE = """\
HOLDFAST — first-time setup on Mac
==================================

macOS blocks apps that aren't signed by a paid Apple developer account, so the
first launch takes a couple of extra clicks. You only do this once.

1. Double-click "Play Holdfast.command".
   macOS says it "could not verify... is free of malware" and only offers
   Move to Trash / Done. Click DONE (do NOT move to trash).

2. Open System Settings > Privacy & Security.

3. Scroll down to the "Security" section. You'll see:
   "Play Holdfast.command was blocked to protect your Mac."
   Click OPEN ANYWAY, then confirm with your password or Touch ID.

4. Double-click "Play Holdfast.command" again, and click OPEN on the prompt.

That's it. From now on, just double-click "Play Holdfast.command" to play.

The first launch installs the game engine (~30 seconds, one time). You need
Python 3.8-3.13; if it's missing, the launcher tells you where to download it.

-----------------------------------------------------------------------------
Comfortable with Terminal? Do it all in one step instead:
   xattr -cr "/path/to/Holdfast"      (drag the Holdfast folder onto Terminal)
then double-click "Play Holdfast.command" normally.
"""


def stage_models() -> Path:
    """Copy Panda3D's stock models into ./models so build_apps can bundle them.

    The prototype loads built-in primitives (models/misc/sphere, rgbCube) and
    uses screen-transition models (fade/iris) plus the default font (cmss12).
    These live inside the installed panda3d package, not the project, so the
    frozen app can't find them unless we stage them here first.
    """
    import panda3d
    src = Path(panda3d.__file__).parent / "models"
    dst = HERE / "models"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"[models] staged {sum(1 for _ in dst.rglob('*') if _.is_file())} files -> {dst}")
    return dst


def build_windows() -> None:
    """Freeze the game into a Windows .exe and zip it (via Panda3D bdist_apps)."""
    stage_models()
    print("[windows] running bdist_apps…")
    subprocess.check_call([sys.executable, "setup.py", "bdist_apps"], cwd=HERE)
    print("[windows] done")


def build_mac() -> None:
    """Assemble the macOS source bundle + launcher into a zip."""
    dist = HERE / "dist"
    dist.mkdir(exist_ok=True)
    stage = dist / "Holdfast"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    for item in HERE.iterdir():
        if item.name in MAC_EXCLUDE:
            continue
        dest = stage / item.name
        if item.is_dir():
            shutil.copytree(
                item, dest,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
        else:
            shutil.copy2(item, dest)

    # Ensure the launcher is executable so double-click works after unzip.
    launcher = stage / "Play Holdfast.command"
    if not launcher.exists():
        raise SystemExit("Missing 'Play Holdfast.command' — cannot build Mac bundle.")
    os.chmod(launcher, 0o755)

    # Downloaded files are quarantined by macOS, which blocks the launcher with
    # a scary "could not verify" dialog. Ship plain-text first-run instructions
    # so players can get past Gatekeeper without hunting online.
    (stage / "READ ME FIRST (Mac).txt").write_text(MAC_FIRST_RUN_NOTE)

    zip_path = dist / f"holdfast-{VERSION}_mac.zip"
    if zip_path.exists():
        zip_path.unlink()
    # ditto preserves the executable bit inside the zip (Finder's Archive
    # Utility honors it), so the .command stays double-clickable.
    subprocess.check_call(
        ["ditto", "-c", "-k", "--keepParent", str(stage), str(zip_path)]
    )
    shutil.rmtree(stage)
    print(f"[mac] wrote {zip_path.name}")


def _convert_models_to_bam(src: Path, dst: Path) -> None:
    """Copy Panda3D's stock models to dst, converting every .egg.pz to .bam.

    A frozen app has only the native Bam loader registered (the egg loader is
    normally activated by Panda3D's Confauto.prc, which isn't present), so the
    models must be shipped as .bam. egg2bam ships in the venv's bin/, which
    build.py already put on PATH.
    """
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for egg in list(dst.rglob("*.egg.pz")):
        bam = egg.with_name(egg.name[: -len(".egg.pz")] + ".bam")
        subprocess.check_call(
            ["egg2bam", "-o", str(bam), str(egg)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        egg.unlink()


def build_mac_app() -> None:
    """Build a self-contained, native-arm64 .app with PyInstaller.

    Bundles Python + Panda3D + models so players need nothing installed. The
    output is currently ad-hoc signed (runs locally, but a download still trips
    Gatekeeper). Turning it into a drag-to-Applications, no-warnings app needs a
    Developer ID signature + Apple notarization — see the "Notarized .app"
    section of PACKAGING.md for the remaining, credential-gated steps.
    """
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        raise SystemExit(
            "PyInstaller not installed. Run: .venv/bin/pip install pyinstaller"
        )
    import panda3d
    bam_models = HERE / "pyi_models"
    _convert_models_to_bam(Path(panda3d.__file__).parent / "models", bam_models)
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed",
        "--name", "Holdfast",
        "--collect-binaries", "panda3d",       # bundle all panda3d plugins/dylibs
        "--add-data", f"{bam_models}:models",   # bundled .bam models
        "--runtime-hook", "pyi_rthook.py",      # supplies frozen-only Panda3D config
        "--distpath", "pyi_dist", "--workpath", "pyi_work",
        "main.py",
    ], cwd=HERE)
    print("[mac-app] built pyi_dist/Holdfast.app (ad-hoc signed; notarization pending)")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in ("all", "windows"):
        build_windows()
    if target in ("all", "mac"):
        build_mac()
    if target == "mac-app":
        build_mac_app()
    print("\nDone. Artifacts in dist/:")
    for f in sorted((HERE / "dist").glob("*.zip")):
        print(f"  {f.name}  ({f.stat().st_size // (1024 * 1024)} MB)")


if __name__ == "__main__":
    main()
