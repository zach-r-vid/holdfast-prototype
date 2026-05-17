"""
Base tower class.

Towers are autonomous defense units that target and fire at enemies
within range. The player can "man" a tower for boosted performance.
Tower placement affects enemy pathing — this is the core TD mechanic.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, PointLight
from direct.showbase.ShowBase import ShowBase

import config

if TYPE_CHECKING:
    from enemies.base_enemy import BaseEnemy
    from projectiles.pool import ProjectilePool


class BaseTower:
    """Abstract base for all tower types."""

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        position: LVector3f,
        stats: dict,
        tower_type: str,
    ) -> None:
        self.base = base
        self.stats = dict(stats)
        self.tower_type = tower_type
        self.hp: float = stats["hp"]
        self.range: float = stats["range"]

        self.is_manned: bool = False
        self.alive: bool = True

        # Scene node
        self.node = parent.attach_new_node(f"tower_{tower_type}_{id(self)}")
        self.node.set_pos(position)

        # Target tracking
        self._current_target: Optional[BaseEnemy] = None
        self._fire_cooldown: float = 0.0

        self._build_visual()

    def _build_visual(self) -> None:
        """Create placeholder tower visual. Override in subclasses."""
        # Base platform
        platform = self.base.loader.load_model("models/misc/rgbCube")
        if platform:
            platform.reparent_to(self.node)
            platform.set_scale(0.8, 0.8, 0.3)
            platform.set_pos(0, 0, 0.15)
            platform.set_color(LColor(0.4, 0.4, 0.5, 1.0))

    def update(
        self,
        dt: float,
        enemies: list["BaseEnemy"],
        pool: "ProjectilePool",
    ) -> None:
        """Update targeting and firing. Override fire() in subclasses."""
        if not self.alive:
            return

        self._fire_cooldown -= dt

        # Acquire or validate target
        self._update_target(enemies)

        # Fire if ready and has target
        if self._current_target and self._fire_cooldown <= 0:
            self._fire(pool)
            fire_rate = self.stats["fire_rate"]
            if self.is_manned:
                fire_rate *= self.stats.get("manned_fire_rate_mult", 1.0)
            self._fire_cooldown = 1.0 / fire_rate

    def _update_target(self, enemies: list["BaseEnemy"]) -> None:
        """Find the closest enemy in range, or keep tracking current."""
        pos = self.node.get_pos()

        # Validate current target
        if self._current_target:
            if not self._current_target.alive or self._current_target.reached_core:
                self._current_target = None
            else:
                dist = (self._current_target.get_position() - pos).length()
                if dist > self.range:
                    self._current_target = None

        # Find new target if needed
        if self._current_target is None:
            best_dist = self.range
            best_enemy = None
            for enemy in enemies:
                if not enemy.alive or enemy.reached_core:
                    continue
                dist = (enemy.get_position() - pos).length()
                if dist < best_dist:
                    best_dist = dist
                    best_enemy = enemy
            self._current_target = best_enemy

    def _fire(self, pool: "ProjectilePool") -> None:
        """Fire at current target. Override in subclasses for different behaviors."""
        pass  # Implemented by subclasses

    def take_damage(self, amount: float) -> None:
        """Towers can be damaged by disruptor enemies."""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.die()

    def die(self) -> None:
        self.alive = False
        self.node.hide()

    def set_manned(self, manned: bool) -> None:
        """Toggle manned state."""
        self.is_manned = manned

    def get_position(self) -> LVector3f:
        return self.node.get_pos()

    def cleanup(self) -> None:
        self.node.remove_node()
