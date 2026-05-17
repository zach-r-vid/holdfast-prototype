"""
Dash / dodge mechanic.

Short burst of speed with invincibility frames. Essential for bullet-hell
survival. Dashes in the current movement direction (or facing direction
if standing still).
"""

from __future__ import annotations

from panda3d.core import LVector3f

from player.controller import InputState
from player.movement import PlayerMovement
import config


class DashSystem:
    """Manages dash state, cooldown, and invincibility."""

    def __init__(self, movement: PlayerMovement) -> None:
        self.movement = movement

        self.speed = config.DASH_SPEED
        self.duration = config.DASH_DURATION
        self.cooldown = config.DASH_COOLDOWN
        self.grants_invincibility = config.DASH_INVINCIBLE

        self._dash_timer: float = 0.0
        self._cooldown_timer: float = 0.0
        self._dash_direction = LVector3f(0, 0, 0)
        self._is_dashing: bool = False

    @property
    def is_dashing(self) -> bool:
        return self._is_dashing

    @property
    def is_invincible(self) -> bool:
        return self._is_dashing and self.grants_invincibility

    @property
    def can_dash(self) -> bool:
        return self._cooldown_timer <= 0 and not self._is_dashing

    @property
    def cooldown_fraction(self) -> float:
        """0.0 = ready, 1.0 = just used. For UI display."""
        if self._cooldown_timer <= 0:
            return 0.0
        return self._cooldown_timer / self.cooldown

    def update(self, input_state: InputState, dt: float) -> None:
        """Process dash input and update state."""
        # Tick cooldown
        if self._cooldown_timer > 0:
            self._cooldown_timer -= dt

        # Start dash
        if input_state.dash_pressed and self.can_dash:
            self._start_dash(input_state)

        # Continue dash
        if self._is_dashing:
            self._dash_timer -= dt
            self.movement.set_speed_override(self.speed)

            if self._dash_timer <= 0:
                self._end_dash()

    def _start_dash(self, input_state: InputState) -> None:
        """Initiate a dash in the current move direction."""
        self._is_dashing = True
        self._dash_timer = self.duration

        # Dash in movement direction if moving, otherwise in facing direction
        if input_state.move_direction.length_squared() > 0.01:
            self._dash_direction = LVector3f(input_state.move_direction)
        else:
            self._dash_direction = self.movement.get_facing()

        self._dash_direction.normalize()

        # Set velocity to dash direction at dash speed
        self.movement.velocity = self._dash_direction * self.speed

    def _end_dash(self) -> None:
        """End the dash and start cooldown."""
        self._is_dashing = False
        self._cooldown_timer = self.cooldown

        # Reduce velocity coming out of dash for snappy stop
        self.movement.velocity *= 0.3
