"""Turret — steady single-target DPS tower. The workhorse."""

from __future__ import annotations
from typing import TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, PointLight
from direct.showbase.ShowBase import ShowBase

from towers.base_tower import BaseTower
from projectiles.base_projectile import spawn_bullet
import config

if TYPE_CHECKING:
    from projectiles.pool import ProjectilePool


class Turret(BaseTower):
    """Fires single projectiles at the nearest enemy. Reliable DPS."""

    def __init__(self, base: ShowBase, parent: NodePath, position: LVector3f) -> None:
        super().__init__(base, parent, position, config.TURRET_STATS, "turret")

    def _build_visual(self) -> None:
        """Turret: platform + barrel."""
        super()._build_visual()

        # Turret head (rotates toward target)
        self.turret_head = self.node.attach_new_node("turret_head")
        self.turret_head.set_pos(0, 0, 0.4)

        barrel = self.base.loader.load_model("models/misc/rgbCube")
        if barrel:
            barrel.reparent_to(self.turret_head)
            barrel.set_scale(0.15, 0.6, 0.15)
            barrel.set_pos(0, 0.3, 0)
            barrel.set_color(LColor(0.3, 0.8, 0.3, 1.0))

        # Glow light
        plight = PointLight("turret_light")
        plight.set_color(LColor(0.2, 0.6, 0.2, 1.0))
        plight.set_attenuation((1, 0.3, 0.1))
        plight_np = self.turret_head.attach_new_node(plight)
        self.node.get_parent().set_light(plight_np)

    def _fire(self, pool: "ProjectilePool") -> None:
        """Fire a single projectile at the current target."""
        if self._current_target is None:
            return

        pos = self.node.get_pos()
        target_pos = self._current_target.get_position()
        direction = target_pos - pos
        direction.z = 0
        if direction.length_squared() < 0.01:
            return
        direction.normalize()

        # Rotate turret head toward target
        self.turret_head.look_at(target_pos)

        # Calculate damage with manned bonus
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

        spawn_pos = pos + direction * 1.0
        spawn_pos.z = 0.5

        spawn_bullet(
            pool=pool,
            position=spawn_pos,
            direction=direction,
            weapon=weapon,
            owner_tag="tower_bullet",
        )
