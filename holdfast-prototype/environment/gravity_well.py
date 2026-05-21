"""
Gravity well environmental hazard.

Three-state cycle:
  PASSIVE  — gentle pull on projectiles and enemies, weak pull on player
  ACTIVE   — strong pull, DPS to enemies and (lighter) player,
             triggered by player pressing G while nearby
  COOLDOWN — inert, recharging

Objects are no longer destroyed by the inner radius — they just get
pulled hard and take damage while the well is active.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Optional

import math
from panda3d.core import LVector3f, LColor, NodePath, PointLight, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

from projectiles.pool import ProjectilePool
import config
from utils.color import apply_color


class WellState(Enum):
    PASSIVE = auto()
    ACTIVE = auto()
    COOLDOWN = auto()


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
        self._pulse_time: float = 0.0

        # State machine
        self.state: WellState = WellState.PASSIVE
        self._active_timer: float = 0.0
        self._cooldown_timer: float = 0.0

        # Visual representation
        self.node = parent.attach_new_node("gravity_well")
        self.node.set_pos(position)
        self._core_sphere: Optional[NodePath] = None
        self._range_sphere: Optional[NodePath] = None
        self._orbit_nodes: list[NodePath] = []
        self._light_np: Optional[NodePath] = None
        self._build_visual()

    # ── Visual ───────────────────────────────────────────────────

    def _build_visual(self) -> None:
        """Core sphere, pulsing range ring, orbiting particles."""
        # Inner core sphere
        core = self.base.loader.load_model("models/misc/sphere")
        if core:
            core.reparent_to(self.node)
            core.set_scale(self.inner_radius * 0.8)
            apply_color(core, LColor(0.5, 0.2, 0.8, 1.0))
            self._core_sphere = core

        # Outer range indicator (transparent, will pulse)
        range_sphere = self.base.loader.load_model("models/misc/sphere")
        if range_sphere:
            range_sphere.reparent_to(self.node)
            range_sphere.set_scale(self.radius)
            range_sphere.set_color(LColor(0.5, 0.1, 0.8, 0.15))
            range_sphere.set_transparency(TransparencyAttrib.M_alpha)
            self._range_sphere = range_sphere

        # Orbiting particles (4 small spheres)
        orbit_parent = self.node.attach_new_node("orbit_parent")
        for _ in range(4):
            particle = self.base.loader.load_model("models/misc/sphere")
            if particle:
                particle.reparent_to(orbit_parent)
                particle.set_scale(0.15)
                apply_color(particle, LColor(0.7, 0.3, 1.0, 0.9))
                self._orbit_nodes.append(particle)

        # Point light
        plight = PointLight("well_light")
        plight.set_color(LColor(0.5, 0.1, 0.9, 1.0))
        plight.set_attenuation((1, 0.1, 0.02))
        self._light_np = self.node.attach_new_node(plight)
        self.node.get_parent().set_light(self._light_np)

    def _update_visual_state(self) -> None:
        """Update colors/intensity based on current state."""
        if self.state == WellState.PASSIVE:
            if self._core_sphere:
                apply_color(self._core_sphere, LColor(0.5, 0.2, 0.8, 1.0))
            if self._range_sphere:
                self._range_sphere.set_color(LColor(0.5, 0.1, 0.8, 0.15))
            if self._light_np:
                self._light_np.node().set_color(LColor(0.5, 0.1, 0.9, 1.0))
        elif self.state == WellState.ACTIVE:
            if self._core_sphere:
                apply_color(self._core_sphere, LColor(1.0, 0.4, 1.0, 1.0))
            if self._range_sphere:
                self._range_sphere.set_color(LColor(1.0, 0.3, 1.0, 0.35))
            if self._light_np:
                self._light_np.node().set_color(LColor(1.0, 0.3, 1.0, 1.0))
        elif self.state == WellState.COOLDOWN:
            if self._core_sphere:
                apply_color(self._core_sphere, LColor(0.2, 0.1, 0.3, 0.6))
            if self._range_sphere:
                self._range_sphere.set_color(LColor(0.2, 0.1, 0.3, 0.08))
            if self._light_np:
                self._light_np.node().set_color(LColor(0.2, 0.05, 0.3, 0.5))

    def update_visual(self, dt: float) -> None:
        """Animate pulsing range ring and orbiting particles."""
        self._pulse_time += dt

        # Pulse range sphere scale
        if self._range_sphere:
            if self.state == WellState.ACTIVE:
                pulse = 1.0 + 0.08 * math.sin(self._pulse_time * 6.0)
            elif self.state == WellState.PASSIVE:
                pulse = 1.0 + 0.04 * math.sin(self._pulse_time * 3.0)
            else:
                pulse = 1.0
            self._range_sphere.set_scale(self.radius * pulse)

        # Core breathe effect during active
        if self._core_sphere and self.state == WellState.ACTIVE:
            breathe = self.inner_radius * (0.8 + 0.15 * math.sin(self._pulse_time * 8.0))
            self._core_sphere.set_scale(breathe)

        # Orbit speed based on state
        if self.state == WellState.ACTIVE:
            orbit_speed = 5.0
        elif self.state == WellState.PASSIVE:
            orbit_speed = 2.0
        else:
            orbit_speed = 0.5

        orbit_radius = self.radius * 0.5
        for i, particle in enumerate(self._orbit_nodes):
            angle = self._pulse_time * orbit_speed + (i * math.pi / 2)
            px = math.cos(angle) * orbit_radius
            py = math.sin(angle) * orbit_radius
            particle.set_pos(px, py, 0)

    # ── State machine ────────────────────────────────────────────

    def try_activate(self, player_pos: LVector3f) -> bool:
        """Player presses G near the well to activate it.

        Returns True if activation succeeded.
        """
        if self.state != WellState.PASSIVE:
            return False
        dist = (self.position - player_pos).length()
        if dist > self.radius:
            return False

        self.state = WellState.ACTIVE
        self._active_timer = config.GRAVITY_WELL_ACTIVE_DURATION
        self._update_visual_state()
        return True

    def _tick_state(self, dt: float) -> None:
        """Advance state timers."""
        if self.state == WellState.ACTIVE:
            self._active_timer -= dt
            if self._active_timer <= 0:
                self.state = WellState.COOLDOWN
                self._cooldown_timer = config.GRAVITY_WELL_ACTIVE_COOLDOWN
                self._update_visual_state()
        elif self.state == WellState.COOLDOWN:
            self._cooldown_timer -= dt
            if self._cooldown_timer <= 0:
                self.state = WellState.PASSIVE
                self._update_visual_state()

    # ── Physics ──────────────────────────────────────────────────

    def _current_strength(self) -> float:
        """Gravity strength based on state."""
        if self.state == WellState.ACTIVE:
            return self.strength * config.GRAVITY_WELL_ACTIVE_STRENGTH_MULT
        if self.state == WellState.COOLDOWN:
            return 0.0
        return self.strength

    def apply_to_projectiles(self, pool: ProjectilePool, dt: float) -> None:
        """Apply gravitational pull to projectiles within range."""
        strength = self._current_strength()
        if strength <= 0:
            return

        for proj in pool.get_active():
            proj_pos = proj.node.get_pos()
            diff = self.position - proj_pos
            diff.z = 0
            dist = diff.length()

            if dist < self.radius and dist > 0.1:
                force_magnitude = strength / max(dist * dist, 0.5)
                force_dir = diff / dist
                proj.apply_force(force_dir * force_magnitude, dt)

    def apply_to_position(self, position: LVector3f, mass: float, dt: float) -> LVector3f:
        """Calculate gravitational force on an object at a position.

        Returns the force vector. Used for enemies.
        """
        strength = self._current_strength()
        if strength <= 0:
            return LVector3f(0, 0, 0)

        diff = self.position - position
        diff.z = 0
        dist = diff.length()

        if dist > self.radius or dist < 0.1:
            return LVector3f(0, 0, 0)

        force_magnitude = strength / max(dist * dist, 0.5)
        force_dir = diff / dist
        return force_dir * force_magnitude * (1.0 / max(mass, 0.1))

    def get_player_force(self, player_pos: LVector3f, dt: float) -> LVector3f:
        """Gravitational pull on the player (weaker via config multiplier)."""
        if not config.GRAVITY_WELL_AFFECTS_PLAYER:
            return LVector3f(0, 0, 0)

        strength = self._current_strength()
        if strength <= 0:
            return LVector3f(0, 0, 0)

        diff = self.position - player_pos
        diff.z = 0
        dist = diff.length()

        if dist > self.radius or dist < 0.1:
            return LVector3f(0, 0, 0)

        force_magnitude = strength / max(dist * dist, 0.5)
        force_dir = diff / dist
        return force_dir * force_magnitude * config.GRAVITY_WELL_PLAYER_PULL_MULT

    def get_dps_at(self, position: LVector3f) -> float:
        """Damage-per-second to enemies near the well core during ACTIVE.

        Returns 0 if not in active state or out of range.
        """
        if self.state != WellState.ACTIVE:
            return 0.0
        diff = self.position - position
        diff.z = 0
        dist = diff.length()
        if dist > self.inner_radius * 2:
            return 0.0
        return config.GRAVITY_WELL_ACTIVE_DPS

    def get_player_dps_at(self, player_pos: LVector3f) -> float:
        """Lighter DPS to the player during ACTIVE."""
        if self.state != WellState.ACTIVE:
            return 0.0
        diff = self.position - player_pos
        diff.z = 0
        dist = diff.length()
        if dist > self.inner_radius * 2:
            return 0.0
        return config.GRAVITY_WELL_ACTIVE_PLAYER_DPS

    @property
    def cooldown_fraction(self) -> float:
        """0.0 when ready, 1.0 at start of cooldown."""
        if self.state != WellState.COOLDOWN:
            return 0.0
        total = config.GRAVITY_WELL_ACTIVE_COOLDOWN
        return self._cooldown_timer / total if total > 0 else 0.0


class GravityWellManager:
    """Manages multiple gravity wells in a level."""

    def __init__(self) -> None:
        self.wells: list[GravityWell] = []

    def add(self, well: GravityWell) -> None:
        self.wells.append(well)

    def update(self, pool: ProjectilePool, dt: float) -> None:
        """Tick state, apply physics, animate visuals."""
        for well in self.wells:
            well._tick_state(dt)
            well.apply_to_projectiles(pool, dt)
            well.update_visual(dt)

    def try_activate_nearest(self, player_pos: LVector3f) -> bool:
        """Try to activate the nearest passive well within range."""
        for well in self.wells:
            if well.try_activate(player_pos):
                return True
        return False

    def get_force_at(self, position: LVector3f, mass: float, dt: float) -> LVector3f:
        """Combined gravitational force at a position (for enemies)."""
        total = LVector3f(0, 0, 0)
        for well in self.wells:
            total += well.apply_to_position(position, mass, dt)
        return total

    def get_player_force(self, player_pos: LVector3f, dt: float) -> LVector3f:
        """Combined gravitational pull on the player."""
        total = LVector3f(0, 0, 0)
        for well in self.wells:
            total += well.get_player_force(player_pos, dt)
        return total

    def get_enemy_dps_at(self, position: LVector3f) -> float:
        """Total DPS from all active wells at a position."""
        return sum(well.get_dps_at(position) for well in self.wells)

    def get_player_dps_at(self, player_pos: LVector3f) -> float:
        """Total DPS to player from all active wells."""
        return sum(well.get_player_dps_at(player_pos) for well in self.wells)

    def check_kill_zone(self, position: LVector3f) -> bool:
        """Legacy compat — now always returns False (no instant kills)."""
        return False
