"""Grunt — basic path-following enemy. Cannon fodder."""

from __future__ import annotations
from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

from enemies.base_enemy import BaseEnemy
import config
from utils.color import apply_color


class Grunt(BaseEnemy):
    """Walks the path. Dies to towers. Tests your coverage."""

    def __init__(self, base: ShowBase, parent: NodePath, spawn_pos: LVector3f) -> None:
        super().__init__(base, parent, config.GRUNT_STATS, spawn_pos)

    def _build_visual(self, stats: dict) -> None:
        """Stocky cube — the bread-and-butter enemy silhouette."""
        model = self.base.loader.load_model("models/misc/rgbCube")
        if model:
            model.reparent_to(self.node)
            # Slightly taller than wide to read as a walking block
            model.set_scale(self.radius, self.radius, self.radius * 1.3)
            model.set_pos(0, 0, self.radius * 0.3)
            apply_color(model, stats.get("color", LColor(0.9, 0.2, 0.2, 1)))
