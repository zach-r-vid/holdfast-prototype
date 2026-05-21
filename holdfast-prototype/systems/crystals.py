"""
Crystal drop system.

Enemies drop crystals on death. Crystals magnetically drift toward
the player and are collected by proximity. Collected crystals fill
the power meter for super abilities.
"""

from __future__ import annotations
from collections import deque
from typing import Optional

from panda3d.core import LVector3f, LColor, NodePath, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

import config
from utils.color import apply_color


class Crystal:
    """A single collectible crystal on the ground."""

    __slots__ = ("node", "position", "lifetime", "alive", "is_health")

    def __init__(self, node: NodePath, position: LVector3f, is_health: bool = False) -> None:
        self.node = node
        self.position = LVector3f(position)
        self.lifetime: float = config.CRYSTAL_LIFETIME
        self.alive: bool = True
        self.is_health: bool = is_health


class CrystalManager:
    """Manages crystal spawning, animation, magnetic pickup, and pooling."""

    def __init__(self, base: ShowBase, parent: NodePath) -> None:
        self.base = base
        self.parent = parent

        self._active: list[Crystal] = []
        self._pool: deque[NodePath] = deque()
        self._template: Optional[NodePath] = None
        self._spawn_count: int = 0  # tracks total spawned for health crystal cadence

        self._create_template()
        self._grow(30)

    def _create_template(self) -> None:
        """Small diamond-shaped crystal template."""
        model = self.base.loader.load_model("models/misc/rgbCube")
        if model:
            self._template = model
            self._template.set_scale(0.15, 0.15, 0.25)
            self._template.set_h(45)
        else:
            self._template = NodePath("crystal_template")

    def _grow(self, count: int) -> None:
        for _ in range(count):
            node = self._template.copy_to(self.parent)
            node.hide()
            node.set_transparency(TransparencyAttrib.M_alpha)
            self._pool.append(node)

    def spawn(self, position: LVector3f) -> None:
        """Drop a crystal at the given world position."""
        if not self._pool:
            self._grow(10)
        if not self._pool:
            return

        self._spawn_count += 1
        is_health = (self._spawn_count % config.HEALTH_CRYSTAL_EVERY_N == 0)

        node = self._pool.popleft()
        node.set_pos(position.x, position.y, 0.3)
        if is_health:
            apply_color(node, config.HEALTH_CRYSTAL_COLOR)
            node.set_scale(0.2, 0.2, 0.35)  # Slightly larger
        else:
            apply_color(node, LColor(0.7, 0.85, 1.0, 0.9))
            node.set_scale(0.15, 0.15, 0.25)
        node.show()

        crystal = Crystal(node, position, is_health=is_health)
        self._active.append(crystal)

    def update(self, dt: float, player_pos: LVector3f) -> tuple[int, int]:
        """Tick crystals, apply magnet pull, check collection.

        Returns (power_crystals_collected, health_crystals_collected).
        """
        power_collected = 0
        health_collected = 0
        still_active = []

        for crystal in self._active:
            if not crystal.alive:
                continue

            crystal.lifetime -= dt

            # Fade out in last 2 seconds
            if crystal.lifetime <= 0:
                crystal.alive = False
                crystal.node.hide()
                self._pool.append(crystal.node)
                continue

            if crystal.lifetime < 2.0:
                alpha = crystal.lifetime / 2.0
                crystal.node.set_color_scale(1, 1, 1, alpha)

            # Distance check
            pos = LVector3f(crystal.node.get_pos())
            diff = player_pos - pos
            diff.z = 0
            dist = diff.length()

            # Collection
            if dist < config.CRYSTAL_COLLECT_RADIUS:
                if crystal.is_health:
                    health_collected += 1
                else:
                    power_collected += 1
                crystal.alive = False
                crystal.node.hide()
                crystal.node.set_color_scale(1, 1, 1, 1)
                self._pool.append(crystal.node)
                continue

            # Magnetic pull
            if dist < config.CRYSTAL_MAGNET_RADIUS and dist > 0.1:
                pull_dir = diff / dist
                pull_speed = config.CRYSTAL_MAGNET_SPEED * (1.0 - dist / config.CRYSTAL_MAGNET_RADIUS)
                new_pos = pos + pull_dir * pull_speed * dt
                crystal.node.set_pos(new_pos.x, new_pos.y, 0.3)

            # Gentle bob animation
            import math
            bob = 0.3 + 0.1 * math.sin(crystal.lifetime * 4.0)
            crystal.node.set_z(bob)

            still_active.append(crystal)

        self._active = still_active
        return power_collected, health_collected

    def clear_all(self) -> None:
        """Remove all active crystals (wave reset)."""
        for crystal in self._active:
            crystal.node.hide()
            crystal.node.set_color_scale(1, 1, 1, 1)
            self._pool.append(crystal.node)
        self._active.clear()
        self._spawn_count = 0

    @property
    def active_count(self) -> int:
        return len(self._active)
