"""Mortar — slow-firing area-of-effect splash tower."""

from __future__ import annotations
from typing import TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

from towers.base_tower import BaseTower
from projectiles.base_projectile import spawn_bullet
import config

if TYPE_CHECKING:
    from projectiles.pool import ProjectilePool
    from enemies.base_enemy import BaseEnemy


class Mortar(BaseTower):
    """Lobs explosive shells that deal splash damage in an area."""

    def __init__(self, base: ShowBase, parent: NodePath, position: LVector3f) -> None:
        super().__init__(base, parent, position, config.MORTAR_STATS, "mortar")

    def _build_visual(self) -> None:
        """Mortar: wide base + stubby barrel."""
        super()._build_visual()

        # Wide mortar tube
        tube = self.base.loader.load_model("models/misc/rgbCube")
        if tube:
            tube.reparent_to(self.node)
            tube.set_scale(0.35, 0.35, 0.5)
            tube.set_pos(0, 0, 0.6)
            tube.set_color(LColor(0.8, 0.3, 0.1, 1.0))

    def _fire(self, pool: "ProjectilePool") -> None:
        """
        Fire a mortar shell toward the target's predicted position.
        The shell itself is a single projectile; splash damage is
        handled on impact by the collision system.
        """
        if self._current_target is None:
            return

        pos = self.node.get_pos()
        target_pos = self._current_target.get_position()

        # Lead the target slightly based on enemy speed and shell travel time
        dist = (target_pos - pos).length()
        travel_time = dist / self.stats["bullet_speed"]
        if hasattr(self._current_target, 'speed'):
            # Predict where enemy will be
            enemy_vel_dir = LVector3f(0, 0, 0)
            if self._current_target.current_target is not None:
                enemy_vel_dir = self._current_target.current_target - target_pos
                if enemy_vel_dir.length_squared() > 0.01:
                    enemy_vel_dir.normalize()
            predicted = target_pos + enemy_vel_dir * self._current_target.speed * travel_time * 0.5
        else:
            predicted = target_pos

        direction = predicted - pos
        direction.z = 0
        if direction.length_squared() < 0.01:
            return
        direction.normalize()

        weapon = {
            "bullet_speed": self.stats["bullet_speed"],
            "bullet_damage": self.stats["bullet_damage"],
            "bullet_mass": self.stats["bullet_mass"],
            "bullet_drag": self.stats["bullet_drag"],
            "bullet_radius": self.stats["bullet_radius"],
            "bullet_color": self.stats["bullet_color"],
            "bullet_lifetime": 3.0,
            "velocity_inherit": 0.0,
        }

        if self.is_manned:
            weapon["bullet_damage"] = int(
                weapon["bullet_damage"] * self.stats.get("manned_damage_mult", 1.0)
            )

        spawn_pos = pos + LVector3f(0, 0, 1.0)

        spawn_bullet(
            pool=pool,
            position=spawn_pos,
            direction=direction,
            weapon=weapon,
            owner_tag="tower_bullet",
        )

    @property
    def splash_radius(self) -> float:
        """Splash radius, potentially boosted when manned."""
        r = self.stats["splash_radius"]
        if self.is_manned:
            r *= self.stats.get("manned_splash_mult", 1.0)
        return r
