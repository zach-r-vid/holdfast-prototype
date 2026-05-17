"""
Projectile spawning helpers.

The actual projectile objects live in pool.py. This module provides
convenience functions for common spawning patterns.
"""

from __future__ import annotations
import math
from typing import Optional

from panda3d.core import LVector3f, LColor

from projectiles.pool import ProjectilePool, Projectile
import config


def spawn_bullet(
    pool: ProjectilePool,
    position: LVector3f,
    direction: LVector3f,
    weapon: dict,
    owner_tag: str = "player_bullet",
    speed_mult: float = 1.0,
    inherit_velocity: Optional[LVector3f] = None,
) -> Optional[Projectile]:
    """
    Spawn a single bullet using a weapon config dict.
    Optionally inherits velocity from the shooter (player movement).
    """
    velocity = LVector3f(direction)
    velocity.normalize()
    velocity *= weapon["bullet_speed"] * speed_mult

    if inherit_velocity is not None:
        velocity += inherit_velocity * weapon.get("velocity_inherit", 0.0)

    return pool.acquire(
        position=LVector3f(position),
        velocity=velocity,
        damage=weapon["bullet_damage"],
        mass=weapon.get("bullet_mass", 0.3),
        drag=weapon.get("bullet_drag", 0.01),
        lifetime=weapon.get("bullet_lifetime", 2.5),
        radius=weapon.get("bullet_radius", 0.15),
        color=weapon.get("bullet_color", LColor(1, 1, 1, 1)),
        owner_tag=owner_tag,
    )


def spawn_pattern(
    pool: ProjectilePool,
    position: LVector3f,
    pattern: list[tuple[LVector3f, float]],
    base_speed: float,
    damage: float,
    mass: float = 0.2,
    drag: float = 0.01,
    lifetime: float = 3.0,
    radius: float = 0.1,
    color: LColor = LColor(1, 0.2, 0.6, 0.9),
    owner_tag: str = "enemy_bullet",
) -> list[Projectile]:
    """
    Spawn a full bullet pattern from a pattern generator.
    Returns list of spawned projectiles (may be shorter than pattern
    if pool is exhausted).
    """
    spawned = []
    for direction, speed_mult in pattern:
        velocity = LVector3f(direction)
        velocity.normalize()
        velocity *= base_speed * speed_mult

        proj = pool.acquire(
            position=LVector3f(position),
            velocity=velocity,
            damage=damage,
            mass=mass,
            drag=drag,
            lifetime=lifetime,
            radius=radius,
            color=color,
            owner_tag=owner_tag,
        )
        if proj is not None:
            spawned.append(proj)
    return spawned
