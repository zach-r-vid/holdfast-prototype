"""
Camera system.

Fixed top-down perspective with dynamic zoom: pulls out during intense
waves for readability, tightens during tower manning for intimacy.
Subtle shake on explosions.
"""

from __future__ import annotations
import random

from panda3d.core import LVector3f, LPoint3f, NodePath
from direct.showbase.ShowBase import ShowBase

import config


class CameraSystem:
    """Manages game camera position, angle, zoom, and shake."""

    def __init__(self, base: ShowBase) -> None:
        self.base = base

        # State
        self._target_height = config.CAMERA_HEIGHT
        self._target_angle = config.CAMERA_ANGLE
        self._current_height = config.CAMERA_HEIGHT
        self._current_angle = config.CAMERA_ANGLE

        # Shake
        self._shake_intensity: float = 0.0
        self._shake_offset = LVector3f(0, 0, 0)

        # Follow target (usually player)
        self._follow_target: NodePath | None = None
        self._follow_offset = LVector3f(0, 0, 0)

        # Manning state
        self._is_manned = False

        # Initial setup
        self._setup()

    def _setup(self) -> None:
        """Position camera for top-down view."""
        self.base.disableMouse()
        self._apply_camera()

    def set_follow_target(self, target: NodePath) -> None:
        """Set the node the camera loosely follows."""
        self._follow_target = target

    def set_manned(self, manned: bool) -> None:
        """Switch between normal and manned camera modes."""
        self._is_manned = manned
        if manned:
            self._target_height = config.CAMERA_MANNED_HEIGHT
            self._target_angle = config.CAMERA_MANNED_ANGLE
        else:
            self._target_height = config.CAMERA_HEIGHT
            self._target_angle = config.CAMERA_ANGLE

    def add_shake(self, intensity: float | None = None) -> None:
        """Trigger camera shake (e.g., on explosion)."""
        if intensity is None:
            intensity = config.CAMERA_SHAKE_INTENSITY
        self._shake_intensity = max(self._shake_intensity, intensity)

    def update(self, dt: float, active_enemy_count: int = 0) -> None:
        """Update camera position each frame."""
        # Dynamic zoom based on enemy count
        if not self._is_manned:
            if active_enemy_count > config.CAMERA_ZOOM_OUT_THRESHOLD:
                zoom_frac = min(
                    (active_enemy_count - config.CAMERA_ZOOM_OUT_THRESHOLD) / 20.0,
                    1.0,
                )
                self._target_height = config.CAMERA_HEIGHT + config.CAMERA_ZOOM_OUT_AMOUNT * zoom_frac
            else:
                self._target_height = config.CAMERA_HEIGHT

        # Smooth height/angle transitions
        speed = config.CAMERA_ZOOM_SPEED * dt
        self._current_height += (self._target_height - self._current_height) * speed
        self._current_angle += (self._target_angle - self._current_angle) * speed

        # Shake decay
        if self._shake_intensity > 0.01:
            self._shake_offset = LVector3f(
                random.uniform(-1, 1) * self._shake_intensity,
                random.uniform(-1, 1) * self._shake_intensity,
                0,
            )
            self._shake_intensity *= (1.0 - config.CAMERA_SHAKE_DECAY * dt)
        else:
            self._shake_intensity = 0
            self._shake_offset = LVector3f(0, 0, 0)

        self._apply_camera()

    def _apply_camera(self) -> None:
        """Set the actual camera transform."""
        cam = self.base.cam

        # Base position: above the arena center (or follow target)
        look_at = LPoint3f(0, 0, 0)
        if self._follow_target:
            target_pos = self._follow_target.get_pos()
            # Loosely follow — don't center exactly on player
            look_at = LPoint3f(target_pos.x * 0.3, target_pos.y * 0.3, 0)

        import math
        angle_rad = math.radians(self._current_angle)
        cam_y_offset = self._current_height * math.sin(angle_rad)
        cam_z = self._current_height * math.cos(angle_rad) if abs(angle_rad) < math.pi / 2 else self._current_height

        cam.set_pos(
            look_at.x + self._shake_offset.x,
            look_at.y + cam_y_offset + self._shake_offset.y,
            cam_z,
        )
        cam.look_at(look_at)
