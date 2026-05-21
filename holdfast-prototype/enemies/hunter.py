"""
Hunter — player-targeting enemy.

Ignores the core entirely and chases the player. Recalculates its
path periodically so it tracks the player's movement. Forces the
player to stay mobile and makes manning towers risky.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, CardMaker, TransparencyAttrib, PointLight
from direct.showbase.ShowBase import ShowBase

import math
from enemies.base_enemy import BaseEnemy
import config
from utils.color import apply_color

if TYPE_CHECKING:
    from environment.pathfinding import PathGrid
    from environment.gravity_well import GravityWellManager


class Hunter(BaseEnemy):
    """Enemy that hunts the player instead of pathing to the core."""

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        spawn_pos: LVector3f,
    ) -> None:
        super().__init__(base, parent, config.HUNTER_STATS, spawn_pos)
        self._retarget_timer: float = 0.0
        self._retarget_interval: float = config.HUNTER_STATS["retarget_interval"]
        self._player_node: Optional[NodePath] = None
        self._path_grid: Optional["PathGrid"] = None
        self.damage_to_player: int = config.HUNTER_STATS.get("damage_to_player", 15)
        self._indicator: Optional[NodePath] = None

        # Hunters never "reach the core" — they die or get killed
        self.damage_to_core = 0

    def _build_visual(self, stats: dict) -> None:
        """Teal diamond-shaped enemy (rotated cube) with targeting indicator and glow."""
        model = self.base.loader.load_model("models/misc/rgbCube")
        if model:
            model.reparent_to(self.node)
            model.set_scale(self.radius)
            apply_color(model, stats.get("color", LColor(0.0, 1.0, 0.9, 1)))
            model.set_h(45)  # Rotated for distinct silhouette

        # Glow light so the hunter stands out against dark floors
        plight = PointLight(f"hunter_glow_{id(self)}")
        color = stats.get("color", LColor(0.0, 1.0, 0.9, 1.0))
        plight.set_color(LColor(color.x * 0.5, color.y * 0.5, color.z * 0.5, 1.0))
        plight.set_attenuation((1, 0.6, 0.3))
        plight_np = self.node.attach_new_node(plight)
        self.node.get_parent().set_light(plight_np)

        # Targeting indicator — small arrow card that points at the player
        cm = CardMaker("hunter_arrow")
        cm.set_frame(-0.08, 0.08, 0, 0.6)
        self._indicator = self.node.attach_new_node(cm.generate())
        self._indicator.set_p(-90)
        self._indicator.set_pos(0, 0, 0.02)
        self._indicator.set_color(LColor(1.0, 0.3, 0.3, 0.8))
        self._indicator.set_transparency(TransparencyAttrib.M_alpha)

    def setup_targeting(self, player_node: NodePath, path_grid: "PathGrid") -> None:
        """Give the hunter references it needs for player-tracking."""
        self._player_node = player_node
        self._path_grid = path_grid

    def update(
        self,
        dt: float,
        gravity_wells: Optional["GravityWellManager"] = None,
    ) -> None:
        """Chase the player, recalculating path periodically."""
        if not self.alive:
            return

        # Retarget periodically
        self._retarget_timer -= dt
        if self._retarget_timer <= 0 and self._player_node and self._path_grid:
            self._retarget_timer = self._retarget_interval
            player_pos = self._player_node.get_pos()
            path = self._path_grid.get_path(self.node.get_pos(), player_pos)
            if path:
                self.set_path(path)

        # Use base path-following movement
        super().update(dt, gravity_wells)

        # Rotate targeting indicator toward the player
        if self._indicator and self._player_node:
            to_player = self._player_node.get_pos() - self.node.get_pos()
            to_player.z = 0
            if to_player.length_squared() > 0.1:
                angle = math.degrees(math.atan2(-to_player.x, to_player.y))
                self._indicator.set_r(angle)

        # Hunters don't "reach core" — override the flag
        # (they might walk to end of path near player, but that's not core)
        self.reached_core = False
