"""
Bullet Hell Emitter — fires complex bullet patterns at the player.

This enemy exists to distract. While your towers handle the grunts and
rushers, emitters force you to dodge and weave, splitting your attention
between defense management and personal survival. This is where the
genre fusion either sings or falls apart.
"""

from __future__ import annotations
import random
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

from enemies.base_enemy import BaseEnemy
from projectiles.patterns import PatternSequencer, ring, spiral, aimed_burst, concentric_rings
from projectiles.base_projectile import spawn_pattern
import config
from utils.color import apply_color

if TYPE_CHECKING:
    from projectiles.pool import ProjectilePool


class BulletHellEmitter(BaseEnemy):
    """
    Walks the path AND fires bullet patterns at the player.
    Slower than grunts, tougher, and much more dangerous.
    """

    def __init__(self, base: ShowBase, parent: NodePath, spawn_pos: LVector3f) -> None:
        super().__init__(base, parent, config.BULLET_HELL_EMITTER_STATS, spawn_pos)
        self.sequencer = PatternSequencer()
        self._fire_cooldown: float = 0.0
        self._pattern_cycle: int = 0
        self._player_node: Optional[NodePath] = None
        self._pool: Optional[ProjectilePool] = None

    def _build_visual(self, stats: dict) -> None:
        """Larger, more menacing shape."""
        model = self.base.loader.load_model("models/misc/sphere")
        if model:
            model.reparent_to(self.node)
            model.set_scale(self.radius)
            apply_color(model, stats.get("color", LColor(1, 0, 0.5, 1)))

        # Inner glow sphere
        inner = self.base.loader.load_model("models/misc/sphere")
        if inner:
            inner.reparent_to(self.node)
            inner.set_scale(self.radius * 0.5)
            apply_color(inner, LColor(1, 1, 1, 0.8))

    def setup_combat(self, player_node: NodePath, pool: "ProjectilePool") -> None:
        """Give the emitter references it needs to fire at the player."""
        self._player_node = player_node
        self._pool = pool

    def update(self, dt: float, gravity_wells=None) -> None:
        """Move along path AND fire bullet patterns."""
        super().update(dt, gravity_wells)

        if not self.alive or self._pool is None:
            return

        self.sequencer.update(dt)
        self._fire_cooldown -= dt

        fire_rate = self.stats["pattern_fire_rate"]
        if self._fire_cooldown <= 0:
            self._fire_cooldown = 1.0 / fire_rate
            self._fire_pattern()

    def _fire_pattern(self) -> None:
        """Choose and fire a bullet pattern."""
        if self._pool is None:
            return

        pos = self.node.get_pos()
        stats = self.stats

        # Cycle through pattern types for variety
        pattern_type = self._pattern_cycle % 4
        self._pattern_cycle += 1

        if pattern_type == 0:
            # Rotating ring
            pattern = self.sequencer.get_ring(count=10)
        elif pattern_type == 1:
            # Aimed burst at player
            if self._player_node:
                player_pos = self._player_node.get_pos()
                pattern = aimed_burst(player_pos, pos, count=7, spread_degrees=40)
            else:
                pattern = self.sequencer.get_ring(count=8)
        elif pattern_type == 2:
            # Spiral arms
            pattern = self.sequencer.get_spiral(arms=3)
        else:
            # Concentric rings
            pattern = concentric_rings(ring_count=2, bullets_per_ring=8)

        spawn_pattern(
            pool=self._pool,
            position=pos,
            pattern=pattern,
            base_speed=stats["bullet_speed"],
            damage=stats["bullet_damage"],
            radius=stats["bullet_radius"],
            color=stats["bullet_color"],
            owner_tag="enemy_bullet",
            lifetime=3.5,
        )
