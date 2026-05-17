"""
Gravity well environmental hazard.

Pulls projectiles and (optionally) enemies toward its center.
Objects reaching the inner radius are destroyed. Creates emergent
gameplay when combined with tower placement — a gravity well near
a turret corridor becomes a kill zone where bullets orbit and shred.
"""

from __future__ import annotations
from typing import Optional

from panda3d.core import LVector3f, LColor, NodePath, PointLight
from direct.showbase.ShowBase import ShowBase

from projectiles.pool import ProjectilePool
import config


class GravityWell:
    """A point in space that exerts gravitational pull on nearby objects."""

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        position: LVector3f,
        strength: float = config.GRAVITY_WELL_STRENGTH,
        radius: float = config.GRAVITY_WELL_RADIUS,
        inner_radius: float = config.GRAVITY_WELL_INNER_RADIUS,
    ) -> None:
        self.base = base
        self.position = LVector3f(position)
        self.strength = strength
        self.radius = radius
        self.inner_radius = inner_radius
        self.active = True

        # Visual representation
        self.node = parent.attach_new_node("gravity_well")
        self.node.set_pos(position)
        self._build_visual()

    def _build_visual(self) -> None:
        """Create placeholder visual — dark sphere with purple glow."""
        # Core sphere (dark)
        sphere = self.base.loader.load_model("models/misc/sphere")
        if sphere:
            sphere.reparent_to(self.node)
            sphere.set_scale(self.inner_radius)
            sphere.set_color(LColor(0.05, 0.0, 0.1, 1.0))

        # Outer range indicator (transparent)
        range_sphere = self.base.loader.load_model("models/misc/sphere")
        if range_sphere:
            range_sphere.reparent_to(self.node)
            range_sphere.set_scale(self.radius)
            range_sphere.set_color(config.COLOR_GRAVITY_WELL)
            from panda3d.core import TransparencyAttrib
            range_sphere.set_transparency(TransparencyAttrib.M_alpha)

        # Point light for glow effect
        plight = PointLight("well_light")
        plight.set_color(LColor(0.4, 0.0, 0.8, 1.0))
        plight.set_attenuation((1, 0.1, 0.02))
        plight_np = self.node.attach_new_node(plight)
        self.node.get_parent().set_light(plight_np)

    def apply_to_projectiles(self, pool: ProjectilePool, dt: float) -> None:
        """
        Apply gravitational pull to all active projectiles within range.
        Destroy projectiles that reach the inner radius.
        """
        if not self.active:
            return

        to_kill = []
        for proj in pool.get_active():
            proj_pos = proj.node.get_pos()
            diff = self.position - proj_pos
            diff.z = 0  # 2D plane
            dist = diff.length()

            if dist < self.inner_radius:
                to_kill.append(proj)
                continue

            if dist < self.radius:
                # Inverse-square gravitational force
                force_magnitude = self.strength / max(dist * dist, 0.5)
                force_dir = diff / dist
                force = force_dir * force_magnitude
                proj.apply_force(force, dt)

        for proj in to_kill:
            pool.kill(proj)

    def apply_to_position(self, position: LVector3f, mass: float, dt: float) -> LVector3f:
        """
        Calculate gravitational force on an object at a given position.
        Returns the force vector to apply. Used for enemies.
        """
        if not self.active:
            return LVector3f(0, 0, 0)

        diff = self.position - position
        diff.z = 0
        dist = diff.length()

        if dist < self.inner_radius or dist > self.radius:
            return LVector3f(0, 0, 0)

        force_magnitude = self.strength / max(dist * dist, 0.5)
        force_dir = diff / dist
        return force_dir * force_magnitude * (1.0 / max(mass, 0.1))

    def is_inside_kill_zone(self, position: LVector3f) -> bool:
        """Check if position is within the destruction inner radius."""
        diff = self.position - position
        diff.z = 0
        return diff.length() < self.inner_radius


class GravityWellManager:
    """Manages multiple gravity wells in a level."""

    def __init__(self) -> None:
        self.wells: list[GravityWell] = []

    def add(self, well: GravityWell) -> None:
        self.wells.append(well)

    def update(self, pool: ProjectilePool, dt: float) -> None:
        """Apply all wells to all projectiles."""
        for well in self.wells:
            well.apply_to_projectiles(pool, dt)

    def get_force_at(self, position: LVector3f, mass: float, dt: float) -> LVector3f:
        """Get combined gravitational force at a position (for enemies)."""
        total = LVector3f(0, 0, 0)
        for well in self.wells:
            total += well.apply_to_position(position, mass, dt)
        return total

    def check_kill_zone(self, position: LVector3f) -> bool:
        """Check if position is inside any well's kill zone."""
        return any(well.is_inside_kill_zone(position) for well in self.wells)
