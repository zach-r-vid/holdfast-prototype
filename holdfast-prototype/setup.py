"""
Packaging config for distributing HOLDFAST as a standalone application.

Build runnable apps for the current machine:
    python setup.py build_apps

Build distributable .zip bundles for every target platform:
    python setup.py bdist_apps

Output lands in build/ (loose apps) and dist/ (zipped bundles).
See PACKAGING.md for the full workflow.
"""

from setuptools import setup

setup(
    name="holdfast",
    version="0.1.0",
    options={
        "build_apps": {
            # Each entry becomes a windowed (no console) executable.
            "gui_apps": {
                "Holdfast": "main.py",
            },
            # Bundle the game's assets tree plus Panda3D's stock models
            # (models/misc/sphere, rgbCube, fade/iris transitions, default
            # font). These are staged into ./models by build.py before the
            # build and converted to .bam. See PACKAGING.md.
            "include_patterns": [
                "assets/**",
                "models/**",
            ],
            # Runtime plugins to bundle: GL renderer + OpenAL for future audio.
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            # Windows: fully packaged, double-click .exe (no signing needed).
            # macOS Apple Silicon builds are handled separately — see
            # PACKAGING.md — because Panda3D's packager can't produce a
            # signed arm64 binary, which Apple Silicon requires to run.
            "platforms": [
                "win_amd64",
            ],
            # Write a log next to the user's app data instead of failing
            # silently if the windowed app hits an error.
            "log_filename": "$USER_APPDATA/Holdfast/output.log",
            "log_append": False,
        }
    },
)
