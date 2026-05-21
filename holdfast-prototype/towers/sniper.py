"""Sniper — long-range, slow-firing, high-damage tower."""

from __future__ import annotations
from typing import TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, PointLight
from direct.showbase.ShowBase import ShowBase

from towers.base_tower import BaseTower, predict_intercept
from projectiles.base_projectile import spawn_bullet
import config
from utils.color import apply_color

if TYPE_CHECKING:
    from projectiles.pool import ProjectilePool


class Sniper(BaseTower):
    """One shot every two seconds. One-shots grunts. Slow tracking."""

    def __init__(self, base: ShowBase, parent: NodePath, position: LVector3f) -> None:
        super().__init__(base, parent, position, config.SNIPER_STATS, "sniper")

    def _build_visual(self) -> None:
        """Sniper: tall narrow platform + long thin barrel."""
        super()._build_visual()

        self.turret_head = self.node.attach_new_node("sniper_head")
        self.turret_head.set_pos(0, 0, 0.4)

        barrel = self.base.loader.load_model("models/misc/rgbCube")
        if barrel:
            barrel.reparent_to(self.turret_head)
            barrel.set_scale(0.08, 0.9, 0.08)
            barrel.set_pos(0, 0.45, 0)
            apply_color(barrel, LColor(1.0, 1.0, 0.5, 1.0))

        scope = self.base.loader.load_model("models/misc/sphere")
        if scope:
            scope.reparent_to(self.turret_head)
            scope.set_scale(0.12)
            scope.set_pos(0, 0.2, 0.1)
            apply_color(scope, LColor(0.8, 0.8, 0.2, 1.0))

        plight = PointLight("sniper_light")
        plight.set_color(LColor(0.6, 0.6, 0.2, 1.0))
        plight.set_attenuation((1, 0.3, 0.1))
        plight_np = self.turret_head.attach_new_node(plight)
        self.node.get_parent().set_light(plight_np)

    def _fire(self, pool: "ProjectilePool") -> None:
        """Fire a single high-speed round at the predicted intercept position."""
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
        if direction.length_squared() < 0.01:
            return
        direction.normalize()

        self.turret_head.look_at(predicted)

        weapon = {
            "bullet_speed": self.stats["bullet_speed"],
            "bullet_damage": self.stats["bullet_damage"],
            "bullet_mass": self.stats["bullet_mass"],
            "bullet_drag": self.stats["bullet_drag"],
            "bullet_radius": self.stats["bullet_radius"],
            "bullet_color": self.stats["bullet_color"],
            "bullet_lifetime": 2.0,
            "velocity_inherit": 0.0,
        }

        if self.is_manned:
            weapon["bullet_damage"] = int(
                weapon["bullet_damage"] * self.stats.get("manned_damage_mult", 1.0)
            )

        spawn_pos = pos + direction * 1.2
        spawn_pos.z = 0.5

        spawn_bullet(
            pool=pool,
            position=spawn_pos,
            direction=direction,
            weapon=weapon,
            owner_tag="tower_bullet",
        )
