"""Arc trajectory preview for manned mortar aiming."""

from __future__ import annotations

from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

import config

DOT_COUNT = 14
DOT_COLOR = LColor(1.0, 0.8, 0.4, 0.35)
DOT_SCALE = 0.08
RING_SEGMENTS = 24
RING_COLOR = LColor(1.0, 0.5, 0.2, 0.25)
RING_DOT_SCALE = 0.06


class ArcPreview:
    """Draws a parabolic arc of dots and a splash radius ring on the ground."""

    def __init__(self, base: ShowBase, parent: NodePath) -> None:
        self._root = parent.attach_new_node("arc_preview")
        self._root.set_transparency(1)
        self._root.hide()

        sphere = base.loader.load_model("models/misc/sphere")

        self._dots: list[NodePath] = []
        for _ in range(DOT_COUNT):
            dot = sphere.copy_to(self._root)
            dot.set_scale(DOT_SCALE)
            dot.set_color(DOT_COLOR)
            dot.set_light_off()
            self._dots.append(dot)

        self._ring_dots: list[NodePath] = []
        for _ in range(RING_SEGMENTS):
            dot = sphere.copy_to(self._root)
            dot.set_scale(RING_DOT_SCALE)
            dot.set_color(RING_COLOR)
            dot.set_light_off()
            self._ring_dots.append(dot)

        self._visible = False

    def update(
        self,
        start: LVector3f,
        end: LVector3f,
        arc_height: float,
        splash_radius: float,
    ) -> None:
        """Reposition dots along the parabola from start to end."""
        if not self._visible:
            self._root.show()
            self._visible = True

        for i, dot in enumerate(self._dots):
            t = (i + 1) / (DOT_COUNT + 1)
            x = start.x + (end.x - start.x) * t
            y = start.y + (end.y - start.y) * t
            z = 4.0 * arc_height * t * (1.0 - t)
            dot.set_pos(x, y, z)

        import math
        for i, dot in enumerate(self._ring_dots):
            angle = 2.0 * math.pi * i / RING_SEGMENTS
            x = end.x + math.cos(angle) * splash_radius
            y = end.y + math.sin(angle) * splash_radius
            dot.set_pos(x, y, 0.05)

    def hide(self) -> None:
        if self._visible:
            self._root.hide()
            self._visible = False

    def show(self) -> None:
        if not self._visible:
            self._root.show()
            self._visible = True

    def cleanup(self) -> None:
        self._root.remove_node()
