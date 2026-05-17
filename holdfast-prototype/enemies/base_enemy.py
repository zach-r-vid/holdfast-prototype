"""
Base enemy class.

All enemies share: HP, path-following, a reward on death, and
damage-to-core on reaching the objective. Subclasses override
behavior (speed, special abilities, bullet patterns).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath
from direct.showbase.ShowBase import ShowBase

import config

if TYPE_CHECKING:
    from environment.pathfinding import PathGrid
    from environment.gravity_well import GravityWellManager


class BaseEnemy:
    """Path-following enemy that moves toward the core."""

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        stats: dict,
        spawn_pos: LVector3f,
    ) -> None:
        self.base = base
        self.stats = stats
        self.hp: float = stats["hp"]
        self.max_hp: float = stats["hp"]
        self.speed: float = stats["speed"]
        self.damage_to_core: int = stats["damage_to_core"]
        self.reward: int = stats["reward"]
        self.radius: float = stats["radius"]

        self.alive: bool = True
        self.reached_core: bool = False

        # Path state
        self.path: Optional[list[LVector3f]] = None
        self.path_index: int = 0
        self.current_target: Optional[LVector3f] = None

        # Slow debuff
        self._slow_factor: float = 1.0
        self._slow_timer: float = 0.0

        # Visual
        self.node = parent.attach_new_node(f"enemy_{id(self)}")
        self.node.set_pos(spawn_pos)
        self._build_visual(stats)

    def _build_visual(self, stats: dict) -> None:
        """Create placeholder visual — colored cube."""
        model = self.base.loader.load_model("models/misc/rgbCube")
        if model:
            model.reparent_to(self.node)
            model.set_scale(self.radius)
            model.set_color(stats.get("color", LColor(1, 0, 0, 1)))

    def set_path(self, path: list[LVector3f]) -> None:
        """Assign a navigation path (list of waypoints to the core)."""
        self.path = path
        self.path_index = 0
        if path:
            self.current_target = path[0]

    def update(
        self,
        dt: float,
        gravity_wells: Optional[GravityWellManager] = None,
    ) -> None:
        """
        Move along path toward core. Override in subclasses for
        special behavior (flying, teleporting, etc.).
        """
        if not self.alive:
            return

        # Tick slow debuff
        if self._slow_timer > 0:
            self._slow_timer -= dt
            if self._slow_timer <= 0:
                self._slow_factor = 1.0

        # Path following
        if self.current_target is None:
            return

        pos = self.node.get_pos()
        to_target = self.current_target - pos
        to_target.z = 0
        dist = to_target.length()

        effective_speed = self.speed * self._slow_factor

        if dist < effective_speed * dt + 0.3:
            # Reached waypoint, advance to next
            self.path_index += 1
            if self.path and self.path_index < len(self.path):
                self.current_target = self.path[self.path_index]
            else:
                # Reached end of path (the core)
                self.reached_core = True
                return
        else:
            # Move toward waypoint
            direction = to_target / dist
            movement = direction * effective_speed * dt

            # Apply gravity well force
            if gravity_wells and config.GRAVITY_WELL_AFFECTS_ENEMIES:
                grav_force = gravity_wells.get_force_at(pos, 1.0, dt)
                movement += grav_force * dt

                # Check if pulled into kill zone
                if gravity_wells.check_kill_zone(pos + movement):
                    self.take_damage(self.hp)  # Instant kill
                    return

            self.node.set_pos(pos + movement)

    def take_damage(self, amount: float) -> None:
        """Apply damage. Enemy dies when HP reaches 0."""
        if not self.alive:
            return

        self.hp -= amount

        # Visual feedback: flash white briefly
        # (In production, use AnimationPlayer or shader)
        if self.hp <= 0:
            self.hp = 0
            self.die()

    def die(self) -> None:
        """Handle death: mark dead, will be cleaned up by spawner."""
        self.alive = False
        self.node.hide()

    def apply_slow(self, factor: float, duration: float) -> None:
        """Apply a slow debuff. Stacks by taking the strongest slow."""
        if factor < self._slow_factor:
            self._slow_factor = factor
        self._slow_timer = max(self._slow_timer, duration)

    def cleanup(self) -> None:
        """Remove from scene graph."""
        self.node.remove_node()

    def get_position(self) -> LVector3f:
        return self.node.get_pos()
