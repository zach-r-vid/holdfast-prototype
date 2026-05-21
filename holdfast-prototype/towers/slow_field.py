"""Slow Field — area that reduces enemy speed. Support tower."""

from __future__ import annotations
from typing import TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

from towers.base_tower import BaseTower
import config
from utils.color import apply_color

if TYPE_CHECKING:
    from enemies.base_enemy import BaseEnemy
    from projectiles.pool import ProjectilePool


class SlowField(BaseTower):
    """
    Doesn't fire projectiles. Instead, continuously slows all enemies
    within range. When manned, also deals damage-over-time.
    """

    def __init__(self, base: ShowBase, parent: NodePath, position: LVector3f) -> None:
        super().__init__(base, parent, position, config.SLOW_FIELD_STATS, "slow_field")
        self._dot_damage: float = 0.0

    def _build_visual(self) -> None:
        """Slow field: low platform + transparent area indicator."""
        super()._build_visual()

        # Range indicator (transparent dome)
        indicator = self.base.loader.load_model("models/misc/sphere")
        if indicator:
            indicator.reparent_to(self.node)
            indicator.set_scale(self.range)
            apply_color(indicator, LColor(0.2, 0.5, 1.0, 0.15))
            indicator.set_transparency(TransparencyAttrib.M_alpha)
            indicator.set_pos(0, 0, 0)

        # Center crystal
        crystal = self.base.loader.load_model("models/misc/rgbCube")
        if crystal:
            crystal.reparent_to(self.node)
            crystal.set_scale(0.25, 0.25, 0.6)
            crystal.set_pos(0, 0, 0.5)
            apply_color(crystal, LColor(0.3, 0.6, 1.0, 1.0))
            crystal.set_h(45)  # Rotated for diamond look

    def update(
        self,
        dt: float,
        enemies: list["BaseEnemy"],
        pool: "ProjectilePool",
    ) -> None:
        """Apply slow (and optional DoT) to enemies in range."""
        if not self.alive:
            return

        pos = self.node.get_pos()
        effective_range = self.range
        if self.is_manned:
            effective_range *= self.stats.get("manned_range_mult", 1.0)

        slow_factor = self.stats["slow_factor"]
        dot = self.stats.get("manned_adds_dot", 0.0) if self.is_manned else 0.0

        for enemy in enemies:
            if not enemy.alive or enemy.reached_core:
                continue
            dist = (enemy.get_position() - pos).length()
            if dist < effective_range:
                enemy.apply_slow(slow_factor, 0.5)
                if dot > 0:
                    enemy.take_damage(dot * dt)

    def _fire(self, pool: "ProjectilePool") -> None:
        """Slow field doesn't fire projectiles."""
        pass
