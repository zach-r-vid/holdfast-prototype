"""
Bullet-hell pattern generators.

Each pattern is a generator function that yields (direction, speed_mult)
tuples. The caller spawns projectiles using these directions from the
emitter's position. Patterns can be composed and layered.
"""

from __future__ import annotations
import math
from typing import Generator

from panda3d.core import LVector3f


PatternOutput = tuple[LVector3f, float]  # (direction_unit_vec, speed_multiplier)


def ring(
    count: int = 12,
    offset_angle: float = 0.0,
) -> list[PatternOutput]:
    """
    Single ring of evenly spaced bullets radiating outward.
    Classic bullet-hell building block.
    """
    results = []
    step = 360.0 / count
    for i in range(count):
        angle = math.radians(offset_angle + step * i)
        direction = LVector3f(math.cos(angle), math.sin(angle), 0)
        results.append((direction, 1.0))
    return results


def spiral(
    arms: int = 3,
    bullets_per_arm: int = 5,
    spread_degrees: float = 10.0,
    base_angle: float = 0.0,
) -> list[PatternOutput]:
    """
    Multi-arm spiral pattern. Each arm fans out slightly from base angle.
    Rotating base_angle over time creates the classic spiral effect.
    """
    results = []
    arm_step = 360.0 / arms
    for arm in range(arms):
        arm_angle = base_angle + arm * arm_step
        for b in range(bullets_per_arm):
            angle = math.radians(arm_angle + b * spread_degrees)
            direction = LVector3f(math.cos(angle), math.sin(angle), 0)
            speed_mult = 0.8 + 0.1 * b  # outer bullets slightly faster
            results.append((direction, speed_mult))
    return results


def aimed_burst(
    target_pos: LVector3f,
    source_pos: LVector3f,
    count: int = 5,
    spread_degrees: float = 30.0,
) -> list[PatternOutput]:
    """
    Fan of bullets aimed toward a target position.
    Like a shotgun blast directed at the player.
    """
    diff = target_pos - source_pos
    diff.z = 0
    if diff.length_squared() < 0.01:
        diff = LVector3f(0, -1, 0)
    diff.normalize()

    base_angle = math.atan2(diff.y, diff.x)
    half_spread = math.radians(spread_degrees / 2)

    results = []
    if count == 1:
        results.append((LVector3f(diff), 1.0))
    else:
        for i in range(count):
            frac = i / (count - 1)  # 0 to 1
            angle = base_angle - half_spread + frac * 2 * half_spread
            direction = LVector3f(math.cos(angle), math.sin(angle), 0)
            results.append((direction, 1.0))
    return results


def concentric_rings(
    ring_count: int = 3,
    bullets_per_ring: int = 10,
    ring_delay_speed: float = 0.7,
) -> list[PatternOutput]:
    """
    Multiple concentric rings fired simultaneously at different speeds.
    Creates a wall-of-bullets effect that's satisfying to dodge through.
    """
    results = []
    for r in range(ring_count):
        offset = (360.0 / bullets_per_ring / ring_count) * r  # Stagger rings
        speed_mult = 1.0 - r * (1.0 - ring_delay_speed) / max(ring_count - 1, 1)
        for direction, _ in ring(bullets_per_ring, offset_angle=offset):
            results.append((direction, speed_mult))
    return results


def cross(
    arms: int = 4,
    bullets_per_arm: int = 4,
    base_angle: float = 0.0,
) -> list[PatternOutput]:
    """
    Cross/plus pattern — lines of bullets along cardinal or diagonal axes.
    Rotate base_angle over time for a spinning cross effect.
    """
    results = []
    arm_step = 360.0 / arms
    for arm in range(arms):
        angle = math.radians(base_angle + arm * arm_step)
        direction = LVector3f(math.cos(angle), math.sin(angle), 0)
        for b in range(bullets_per_arm):
            speed_mult = 0.6 + 0.3 * (b / max(bullets_per_arm - 1, 1))
            results.append((LVector3f(direction), speed_mult))
    return results


def wave_sine(
    count: int = 15,
    amplitude_degrees: float = 30.0,
    frequency: float = 2.0,
    base_angle: float = 0.0,
    time: float = 0.0,
) -> list[PatternOutput]:
    """
    Line of bullets that forms a sine wave pattern.
    The 'time' parameter should increase each call to animate the wave.
    """
    results = []
    for i in range(count):
        frac = i / max(count - 1, 1)
        sine_offset = math.sin(frac * frequency * math.pi * 2 + time) * amplitude_degrees
        angle = math.radians(base_angle + (frac - 0.5) * 120 + sine_offset)
        direction = LVector3f(math.cos(angle), math.sin(angle), 0)
        results.append((direction, 0.8 + 0.4 * frac))
    return results


class PatternSequencer:
    """
    Manages timed pattern sequences for an enemy emitter.
    Tracks rotation state for spinning patterns.
    """

    def __init__(self) -> None:
        self.time: float = 0.0
        self.rotation: float = 0.0
        self.rotation_speed: float = 45.0  # degrees per second
        self.pattern_index: int = 0

    def update(self, dt: float) -> None:
        """Advance time and rotation."""
        self.time += dt
        self.rotation += self.rotation_speed * dt

    def get_ring(self, count: int = 12) -> list[PatternOutput]:
        """Ring that rotates over time."""
        return ring(count, offset_angle=self.rotation)

    def get_spiral(self, arms: int = 3) -> list[PatternOutput]:
        """Spiral that rotates over time."""
        return spiral(arms, base_angle=self.rotation)

    def get_aimed_burst(
        self, target_pos: LVector3f, source_pos: LVector3f
    ) -> list[PatternOutput]:
        """Aimed burst at current player position."""
        return aimed_burst(target_pos, source_pos)

    def get_concentric(self) -> list[PatternOutput]:
        """Concentric rings pattern."""
        return concentric_rings()

    def get_cross(self, arms: int = 4) -> list[PatternOutput]:
        """Spinning cross."""
        return cross(arms, base_angle=self.rotation)
