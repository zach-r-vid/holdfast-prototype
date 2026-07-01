"""PyInstaller runtime hook. Reproduces the Panda3D startup config that a frozen
build lacks (normally in etc/Config.prc + Confauto.prc): pick the GL display and
OpenAL audio, default bare model names to .bam (the only loader present when
frozen), and register the bundled models on the search path. In a macOS .app,
data is in Contents/Resources while _MEIPASS is Contents/Frameworks, so add both.
Filename.fromOsSpecific tolerates install paths that contain spaces.
"""
import os
import sys
from panda3d.core import loadPrcFileData, getModelPath, Filename

loadPrcFileData("pyinstaller-runtime", "\n".join([
    "load-display pandagl",
    "audio-library-name p3openal_audio",
    "default-model-extension .bam",
]))

_base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.argv[0])))
for _p in (_base, os.path.normpath(os.path.join(_base, os.pardir, "Resources"))):
    getModelPath().appendDirectory(Filename.fromOsSpecific(_p))
