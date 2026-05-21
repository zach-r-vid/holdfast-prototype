"""
Pause menu overlay.

Escape pauses the game and shows Resume / Restart / Quit.
"""

from __future__ import annotations
from typing import Callable

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from panda3d.core import TextNode, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase


class PauseMenu:
    """Fullscreen pause overlay with Resume, Restart, Quit."""

    def __init__(
        self,
        base: ShowBase,
        on_resume: Callable[[], None],
        on_restart: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.base = base
        self._on_resume = on_resume
        self._on_restart = on_restart
        self._on_quit = on_quit
        self.visible = False

        self.frame = DirectFrame(
            frameColor=(0.0, 0.0, 0.0, 0.7),
            frameSize=(-2, 2, -2, 2),
            pos=(0, 0, 0),
            sortOrder=100,
        )
        self.frame.set_transparency(TransparencyAttrib.M_alpha)

        OnscreenText(
            text="PAUSED",
            pos=(0, 0.3),
            scale=0.12,
            align=TextNode.A_center,
            fg=(1, 1, 1, 1),
            parent=self.frame,
        )

        options = [
            ("[R] Resume", 0.1),
            ("[N] Restart", -0.05),
            ("[Q] Quit", -0.2),
        ]
        for label, y in options:
            OnscreenText(
                text=label,
                pos=(0, y),
                scale=0.06,
                align=TextNode.A_center,
                fg=(0.8, 0.8, 0.8, 1),
                parent=self.frame,
            )

        self.base.accept("r", self._handle_resume)
        self.base.accept("n", self._handle_restart)
        self.base.accept("q", self._handle_quit)

        self.hide()

    def _handle_resume(self) -> None:
        if self.visible:
            self._on_resume()

    def _handle_restart(self) -> None:
        if self.visible:
            self._on_restart()

    def _handle_quit(self) -> None:
        if self.visible:
            self._on_quit()

    def show(self) -> None:
        self.frame.show()
        self.visible = True

    def hide(self) -> None:
        self.frame.hide()
        self.visible = False

    def toggle(self) -> None:
        if self.visible:
            self._on_resume()
        else:
            self.show()

    def cleanup(self) -> None:
        self.frame.destroy()
