"""Grunt — basic path-following enemy. Cannon fodder."""

from __future__ import annotations
from panda3d.core import LVector3f, NodePath
from direct.showbase.ShowBase import ShowBase

from enemies.base_enemy import BaseEnemy
import config


class Grunt(BaseEnemy):
    """Walks the path. Dies to towers. Tests your coverage."""

    def __init__(self, base: ShowBase, parent: NodePath, spawn_pos: LVector3f) -> None:
        super().__init__(base, parent, config.GRUNT_STATS, spawn_pos)
