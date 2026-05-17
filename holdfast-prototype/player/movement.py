"""
Player movement system.

Target feel: Geometry Wars — instant response on input, smooth deceleration
on release, slight momentum that makes movement feel weighty without being
floaty. The player should feel like a sports car, not an ice skater.
"""

from __future__ import annotations

from panda3d.core import LVector3f, LPoint3f, NodePath

from player.controller import InputState
import config


class PlayerMovement:
    """Physics-based movement with tunable acceleration and friction."""

    def __init__(self, node: NodePath) -> None:
        self.node = node
        self.velocity = LVector3f(0, 0, 0)
        self.facing = LVector3f(0, 1, 0)  # direction player model faces (aim)

        self.max_speed = config.PLAYER_MAX_SPEED
        self.acceleration = config.PLAYER_ACCELERATION
        self.friction = config.PLAYER_FRICTION

        self._speed_override: float | None = None

    def update(self, input_state: InputState, dt: float) -> None:
        """
        Update player position based on input.
        Call once per frame during ACTION phase.
        """
        move_dir = input_state.move_direction

        if move_dir.length_squared() > 0.01:
            # Accelerate toward input direction
            target_velocity = move_dir * self.max_speed
            diff = target_velocity - self.velocity
            accel = diff * min(self.acceleration * dt, 1.0)
            self.velocity += accel
        else:
            # No input → friction stops you
            self.velocity *= self.friction

        # Apply speed override (e.g., from dash)
        if self._speed_override is not None:
            if self.velocity.length_squared() > 0.01:
                self.velocity.normalize()
                self.velocity *= self._speed_override
            self._speed_override = None

        # Clamp to max speed
        speed = self.velocity.length()
        if speed > self.max_speed * 1.5:  # Allow slight overshoot for dash
            self.velocity = self.velocity / speed * self.max_speed * 1.5

        # Kill tiny velocities to prevent drift
        if self.velocity.length_squared() < 0.01:
            self.velocity = LVector3f(0, 0, 0)

        # Integrate position
        pos = self.node.get_pos()
        pos += self.velocity * dt
        pos.z = 0  # Lock to ground plane

        # Clamp to arena bounds
        half_w = config.ARENA_WIDTH / 2 - 0.5
        half_h = config.ARENA_HEIGHT / 2 - 0.5
        pos.x = max(-half_w, min(half_w, pos.x))
        pos.y = max(-half_h, min(half_h, pos.y))

        self.node.set_pos(pos)

        # Update facing direction (toward aim position)
        aim_dir = input_state.aim_world_pos - pos
        aim_dir.z = 0
        if aim_dir.length_squared() > 0.1:
            aim_dir.normalize()
            self.facing = aim_dir

    def set_speed_override(self, speed: float) -> None:
        """Used by dash to temporarily force a speed."""
        self._speed_override = speed

    def get_velocity(self) -> LVector3f:
        """Current velocity vector (used for bullet velocity inheritance)."""
        return LVector3f(self.velocity)

    def get_position(self) -> LPoint3f:
        """Current world position."""
        return self.node.get_pos()

    def get_facing(self) -> LVector3f:
        """Current aim direction (normalized)."""
        return LVector3f(self.facing)

    def teleport(self, position: LVector3f) -> None:
        """Instantly move player (no physics). Used for respawn."""
        self.node.set_pos(position)
        self.velocity = LVector3f(0, 0, 0)
