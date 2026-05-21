"""
Player shooting system.

Manages weapon state, fire rate timing, and projectile spawning.
Bullets inherit player velocity for that satisfying Binding-of-Isaac
momentum feel.
"""

from __future__ import annotations
import math
import random
from typing import Optional

from panda3d.core import LVector3f, LColor

from player.controller import InputState
from player.movement import PlayerMovement
from projectiles.pool import ProjectilePool
from projectiles.base_projectile import spawn_bullet
from projectiles.patterns import ring
import config


class ShootingSystem:
    """Handles weapon firing, ammo, and weapon switching."""

    def __init__(
        self,
        movement: PlayerMovement,
        projectile_pool: ProjectilePool,
    ) -> None:
        self.movement = movement
        self.pool = projectile_pool
        self._power_meter = None  # Set after power_meter init

        self.weapons: list[dict] = [
            dict(config.DEFAULT_WEAPON),
            dict(config.SHOTGUN_WEAPON),
            dict(config.SMG_WEAPON),
            dict(config.NOVA_WEAPON),
        ]
        self.weapon_index: int = 0
        self.current_weapon: dict = self.weapons[0]

        self._fire_cooldown: float = 0.0
        self._manned_fire_rate_mult: float = 1.0
        self._manned_damage_mult: float = 1.0
        self._is_manned: bool = False
        self._tower_weapon: Optional[dict] = None

    def update(self, input_state: InputState, dt: float) -> None:
        """Process shooting input each frame."""
        self._fire_cooldown -= dt

        if input_state.shooting and self._fire_cooldown <= 0:
            self._fire(input_state)

    def _fire(self, input_state: InputState) -> None:
        """Spawn projectile(s) for current weapon or tower weapon if manned."""
        # When manned, use tower weapon config
        if self._is_manned and self._tower_weapon:
            weapon = self._tower_weapon
            owner_tag = "tower_bullet"
        else:
            weapon = self.current_weapon
            owner_tag = "player_bullet"

        fire_rate = weapon["fire_rate"]
        if self._is_manned:
            fire_rate *= self._manned_fire_rate_mult
        # Super Shot power-up fire rate boost
        if self._power_meter and not self._is_manned:
            fire_rate *= self._power_meter.get_fire_rate_mult()

        self._fire_cooldown = 1.0 / fire_rate

        # Check ammo (tower weapons have infinite)
        if weapon["ammo"] == 0:
            return
        if weapon["ammo"] > 0:
            weapon["ammo"] -= 1

        pos = self.movement.get_position()
        aim_dir = self.movement.get_facing()
        player_vel = self.movement.get_velocity() if not self._is_manned else LVector3f(0, 0, 0)

        # Apply manned damage bonus
        effective_weapon = dict(weapon)
        if self._is_manned:
            effective_weapon["bullet_damage"] = int(
                weapon["bullet_damage"] * self._manned_damage_mult
            )

        # Ring pattern (Nova Burst): fire evenly around the player
        if weapon.get("ring_pattern"):
            pellets = weapon.get("pellets", 16)
            pattern = ring(count=pellets)
            for direction, speed_mult in pattern:
                spawn_pos = LVector3f(pos) + direction * 0.8
                ring_weapon = dict(effective_weapon)
                ring_weapon["bullet_speed"] = weapon["bullet_speed"] * speed_mult
                spawn_bullet(
                    pool=self.pool,
                    position=spawn_pos,
                    direction=direction,
                    weapon=ring_weapon,
                    owner_tag=owner_tag,
                )
            return

        pellets = weapon.get("pellets", 1)
        spread_mult = 1.0
        if self._power_meter and not self._is_manned:
            spread_mult = self._power_meter.get_spread_mult()
        for _ in range(pellets):
            spread = weapon.get("spread", 0.0) * spread_mult
            if spread > 0:
                angle_offset = random.uniform(-spread / 2, spread / 2)
                angle_rad = math.radians(angle_offset)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)
                rotated = LVector3f(
                    aim_dir.x * cos_a - aim_dir.y * sin_a,
                    aim_dir.x * sin_a + aim_dir.y * cos_a,
                    0,
                )
            else:
                rotated = LVector3f(aim_dir)

            spawn_pos = LVector3f(pos) + rotated * 0.8

            arc_z = 0.0
            splash = 0.0
            if effective_weapon.get("uses_arc"):
                arc_z = 8.0
                splash = effective_weapon.get("splash_radius", 3.0)

            spawn_bullet(
                pool=self.pool,
                position=spawn_pos,
                direction=rotated,
                weapon=effective_weapon,
                owner_tag=owner_tag,
                inherit_velocity=player_vel,
                arc_z_velocity=arc_z,
                splash_radius=splash,
            )

    def set_manned(
        self,
        manned: bool,
        fire_rate_mult: float = 1.0,
        damage_mult: float = 1.0,
        tower_weapon: Optional[dict] = None,
    ) -> None:
        """Toggle manned-tower state for boosted shooting."""
        self._is_manned = manned
        self._manned_fire_rate_mult = fire_rate_mult
        self._manned_damage_mult = damage_mult
        self._tower_weapon = tower_weapon

    def add_weapon(self, weapon: dict) -> None:
        """Pick up a new weapon."""
        self.weapons.append(dict(weapon))
        self.weapon_index = len(self.weapons) - 1
        self.current_weapon = self.weapons[self.weapon_index]

    def cycle_weapon(self, direction: int = 1) -> None:
        """Switch to next/previous weapon."""
        self.weapon_index = (self.weapon_index + direction) % len(self.weapons)
        self.current_weapon = self.weapons[self.weapon_index]

    def select_weapon(self, index: int) -> bool:
        """Switch to a specific weapon slot (0-indexed). Returns False if out of range."""
        if 0 <= index < len(self.weapons):
            self.weapon_index = index
            self.current_weapon = self.weapons[index]
            return True
        return False

    @property
    def ammo_display(self) -> str:
        """String for HUD ammo display."""
        ammo = self.current_weapon["ammo"]
        if ammo < 0:
            return "∞"
        return str(ammo)
