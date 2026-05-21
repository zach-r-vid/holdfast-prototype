"""Mortar — slow-firing area-of-effect splash tower."""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

from towers.base_tower import BaseTower, predict_intercept
from projectiles.base_projectile import spawn_bullet
import config
from utils.color import apply_color

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

        tube = self.base.loader.load_model("models/misc/rgbCube")
        if tube:
            tube.reparent_to(self.node)
            tube.set_scale(0.35, 0.35, 0.5)
            tube.set_pos(0, 0, 0.6)
            apply_color(tube, LColor(0.8, 0.3, 0.1, 1.0))

    def _fire(self, pool: "ProjectilePool") -> None:
        if self._current_target is None:
            return

        pos = self.node.get_pos()
        target_pos = self._current_target.get_position()

        predicted = predict_intercept(
            pos, target_pos,
            self._current_target.get_velocity(),
            self.stats["bullet_speed"],
        )

        direction = predicted - pos
        direction.z = 0
        dist = direction.length()
        if dist < 0.01:
            return
        direction /= dist

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

        spawn_pos = pos + LVector3f(0, 0, 0.5)

        # Z velocity scales with distance so the arc looks right
        z_vel = 5.0 + dist * 0.8

        spawn_bullet(
            pool=pool,
            position=spawn_pos,
            direction=direction,
            weapon=weapon,
            owner_tag="tower_bullet",
            arc_z_velocity=z_vel,
            splash_radius=self.splash_radius,
        )

    def get_manned_target(self, aim_world_pos: LVector3f) -> LVector3f:
        """Get the clamped landing position for manned firing.

        Both the arc preview and fire_at_position must use this
        so the shell always lands where the preview shows.
        """
        pos = self.node.get_pos()
        to_aim = LVector3f(aim_world_pos.x - pos.x, aim_world_pos.y - pos.y, 0)
        dist = to_aim.length()
        max_range = self.stats["range"]
        if dist > max_range and dist > 0.01:
            to_aim = to_aim / dist * max_range
        return LVector3f(pos.x + to_aim.x, pos.y + to_aim.y, 0)

    def fire_at_position(
        self, pool: "ProjectilePool", target_pos: LVector3f, damage_mult: float = 1.0
    ) -> None:
        """Fire a shell to an explicit ground position (manned mode)."""
        pos = self.node.get_pos()
        direction = LVector3f(target_pos.x - pos.x, target_pos.y - pos.y, 0)
        dist = direction.length()
        if dist < 0.5:
            return
        direction.normalize()

        weapon = {
            "bullet_speed": self.stats["bullet_speed"],
            "bullet_damage": int(self.stats["bullet_damage"] * damage_mult),
            "bullet_mass": self.stats["bullet_mass"],
            "bullet_drag": self.stats["bullet_drag"],
            "bullet_radius": self.stats["bullet_radius"],
            "bullet_color": self.stats["bullet_color"],
            "bullet_lifetime": 3.0,
            "velocity_inherit": 0.0,
        }

        spawn_pos = pos + LVector3f(0, 0, 0.5)
        z_vel = 5.0 + dist * 0.8

        spawn_bullet(
            pool=pool,
            position=spawn_pos,
            direction=direction,
            weapon=weapon,
            owner_tag="tower_bullet",
            arc_z_velocity=z_vel,
            splash_radius=self.splash_radius,
        )

    def get_weapon_config(self) -> dict:
        cfg = super().get_weapon_config()
        cfg["uses_arc"] = True
        cfg["splash_radius"] = self.splash_radius
        return cfg

    @property
    def splash_radius(self) -> float:
        r = self.stats["splash_radius"]
        if self.is_manned:
            r *= self.stats.get("manned_splash_mult", 1.0)
        return r
