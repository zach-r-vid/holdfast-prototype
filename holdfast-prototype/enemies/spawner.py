"""
Enemy spawner and wave composition.

Defines what enemies appear in each wave, when they spawn, and from
which spawn points. Waves escalate in difficulty by mixing enemy types
and increasing counts.
"""

from __future__ import annotations
import random
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, NodePath
from direct.showbase.ShowBase import ShowBase

from enemies.base_enemy import BaseEnemy
from enemies.grunt import Grunt
from enemies.rusher import Rusher
from enemies.bullet_hell_emitter import BulletHellEmitter
import config

if TYPE_CHECKING:
    from environment.pathfinding import PathGrid
    from projectiles.pool import ProjectilePool
    from environment.gravity_well import GravityWellManager


# ─── Wave Definitions ─────────────────────────────────────────────
# Each wave is a list of spawn groups: (enemy_type, count, delay_between)
# Groups spawn sequentially; enemies within a group spawn with delay.

WAVE_DEFINITIONS: list[list[tuple[str, int, float]]] = [
    # Wave 1: Tutorial — just grunts
    [("grunt", 6, 0.8)],

    # Wave 2: More grunts, tighter spacing
    [("grunt", 10, 0.5)],

    # Wave 3: Introduce rushers
    [("grunt", 6, 0.6), ("rusher", 4, 0.4)],

    # Wave 4: Mixed pressure
    [("grunt", 8, 0.5), ("rusher", 6, 0.3)],

    # Wave 5: Introduce bullet hell emitter
    [("grunt", 10, 0.5), ("emitter", 1, 0.0)],

    # Wave 6: Escalation
    [("rusher", 8, 0.3), ("grunt", 6, 0.5), ("emitter", 2, 2.0)],

    # Wave 7: Swarm
    [("grunt", 15, 0.3), ("rusher", 8, 0.2), ("emitter", 2, 1.5)],

    # Wave 8: Boss-level intensity
    [("grunt", 12, 0.4), ("rusher", 10, 0.25), ("emitter", 3, 1.0)],
]


class SpawnGroup:
    """A batch of enemies to spawn with timing."""

    def __init__(self, enemy_type: str, count: int, delay: float) -> None:
        self.enemy_type = enemy_type
        self.count = count
        self.delay = delay
        self.spawned: int = 0
        self.timer: float = 0.0
        self.done: bool = False

    def update(self, dt: float) -> bool:
        """Returns True when it's time to spawn the next enemy."""
        if self.done:
            return False
        self.timer -= dt
        if self.timer <= 0 and self.spawned < self.count:
            self.timer = self.delay
            return True
        return False

    def mark_spawned(self) -> None:
        self.spawned += 1
        if self.spawned >= self.count:
            self.done = True


class EnemySpawner:
    """Manages enemy lifecycle: spawning, updating, cleanup."""

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        path_grid: "PathGrid",
        projectile_pool: "ProjectilePool",
        player_node: NodePath,
    ) -> None:
        self.base = base
        self.parent = parent
        self.path_grid = path_grid
        self.pool = projectile_pool
        self.player_node = player_node

        self.enemies: list[BaseEnemy] = []
        self._spawn_groups: list[SpawnGroup] = []
        self._current_group_index: int = 0
        self._spawning_active: bool = False
        self._group_gap_timer: float = 0.0

    def start_wave(self, wave_number: int) -> None:
        """Begin spawning enemies for the given wave."""
        idx = min(wave_number, len(WAVE_DEFINITIONS) - 1)
        wave_def = WAVE_DEFINITIONS[idx]

        self._spawn_groups = [
            SpawnGroup(etype, count, delay) for etype, count, delay in wave_def
        ]
        self._current_group_index = 0
        self._spawning_active = True
        self._group_gap_timer = 0.0

    def update(self, dt: float, gravity_wells: Optional["GravityWellManager"] = None) -> None:
        """Update spawning and all living enemies."""
        # Handle spawning
        if self._spawning_active:
            self._update_spawning(dt)

        # Update enemies
        for enemy in self.enemies:
            if enemy.alive and not enemy.reached_core:
                enemy.update(dt, gravity_wells)

    def _update_spawning(self, dt: float) -> None:
        """Process spawn queue."""
        if self._current_group_index >= len(self._spawn_groups):
            self._spawning_active = False
            return

        # Brief gap between groups
        if self._group_gap_timer > 0:
            self._group_gap_timer -= dt
            return

        group = self._spawn_groups[self._current_group_index]

        if group.update(dt):
            self._spawn_enemy(group.enemy_type)
            group.mark_spawned()

        if group.done:
            self._current_group_index += 1
            self._group_gap_timer = 1.5  # Pause between groups

    def _spawn_enemy(self, enemy_type: str) -> None:
        """Create a single enemy at a random spawn point."""
        spawn_pos = random.choice(config.SPAWN_POINTS)
        spawn_pos = LVector3f(spawn_pos)  # Copy

        # Create enemy by type
        if enemy_type == "grunt":
            enemy = Grunt(self.base, self.parent, spawn_pos)
        elif enemy_type == "rusher":
            enemy = Rusher(self.base, self.parent, spawn_pos)
        elif enemy_type == "emitter":
            enemy = BulletHellEmitter(self.base, self.parent, spawn_pos)
            enemy.setup_combat(self.player_node, self.pool)
        else:
            enemy = Grunt(self.base, self.parent, spawn_pos)

        # Calculate path to core
        path = self.path_grid.get_path(spawn_pos, config.CORE_POSITION)
        if path:
            enemy.set_path(path)

        self.enemies.append(enemy)

    def get_reached_core(self) -> list[BaseEnemy]:
        """Return enemies that reached the core (to apply damage)."""
        reached = [e for e in self.enemies if e.reached_core]
        return reached

    def get_dead(self) -> list[BaseEnemy]:
        """Return enemies that died (for reward calculation)."""
        return [e for e in self.enemies if not e.alive and not e.reached_core]

    def cleanup_dead(self) -> None:
        """Remove dead and core-reached enemies from the list."""
        for enemy in self.enemies:
            if not enemy.alive or enemy.reached_core:
                enemy.cleanup()
        self.enemies = [e for e in self.enemies if e.alive and not e.reached_core]

    def is_wave_complete(self) -> bool:
        """True when all enemies are spawned and none remain alive."""
        return (
            not self._spawning_active
            and all(not e.alive or e.reached_core for e in self.enemies)
        )

    @property
    def active_count(self) -> int:
        return sum(1 for e in self.enemies if e.alive and not e.reached_core)

    def clear_all(self) -> None:
        """Remove all enemies. Used on reset."""
        for enemy in self.enemies:
            enemy.cleanup()
        self.enemies.clear()
        self._spawning_active = False
