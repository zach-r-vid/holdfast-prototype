"""Rusher — fast, fragile enemy that punishes gaps in your maze."""

from __future__ import annotations
from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

from enemies.base_enemy import BaseEnemy
import config


class Rusher(BaseEnemy):
    """Zooms down the path. Low HP but hard to catch."""

    def __init__(self, base: ShowBase, parent: NodePath, spawn_pos: LVector3f) -> None:
        super().__init__(base, parent, config.RUSHER_STATS, spawn_pos)

    def _build_visual(self, stats: dict) -> None:
        """Smaller, pointier shape to convey speed."""
        model = self.base.loader.load_model("models/misc/rgbCube")
        if model:
            model.reparent_to(self.node)
            # Elongated in movement direction
            model.set_scale(self.radius * 0.7, self.radius * 1.4, self.radius * 0.7)
            model.set_color(stats.get("color", LColor(1, 0.8, 0, 1)))
