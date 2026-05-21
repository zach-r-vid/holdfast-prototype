"""
Power-up meter system.

Crystals collected from enemy drops fill a meter. When full the
player can activate one of two abilities:
  • Super Shot — massive fire-rate boost, wider spread, piercing rounds
  • Bomb — radial blast that damages enemies and clears hostile bullets
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Optional

from panda3d.core import LVector3f, LColor

import config


class PowerAbility(Enum):
    SUPER_SHOT = auto()
    BOMB = auto()


class PowerMeter:
    """Tracks crystal charge and manages power-up activation."""

    def __init__(self) -> None:
        self.crystals: int = 0
        self.max_crystals: int = config.CRYSTALS_FOR_POWER_UP
        self.selected: PowerAbility = PowerAbility.SUPER_SHOT

        # Super Shot active state
        self.super_shot_active: bool = False
        self._super_shot_timer: float = 0.0

    # ── Charging ─────────────────────────────────────────────────

    def add_crystals(self, count: int) -> None:
        """Add collected crystals to the meter."""
        self.crystals = min(self.crystals + count, self.max_crystals)

    @property
    def is_full(self) -> bool:
        return self.crystals >= self.max_crystals

    @property
    def fraction(self) -> float:
        """0.0 → 1.0 charge level."""
        return self.crystals / self.max_crystals if self.max_crystals > 0 else 0.0

    # ── Ability selection ────────────────────────────────────────

    def cycle_ability(self) -> None:
        """Toggle between Super Shot and Bomb."""
        if self.selected == PowerAbility.SUPER_SHOT:
            self.selected = PowerAbility.BOMB
        else:
            self.selected = PowerAbility.SUPER_SHOT

    # ── Activation ───────────────────────────────────────────────

    def try_activate(self) -> Optional[PowerAbility]:
        """Consume the meter and return the ability to fire, or None."""
        if not self.is_full:
            return None
        if self.super_shot_active:
            return None  # Already active

        ability = self.selected
        self.crystals = 0

        if ability == PowerAbility.SUPER_SHOT:
            self.super_shot_active = True
            self._super_shot_timer = config.POWER_SUPER_SHOT_DURATION

        return ability

    # ── Per-frame update ─────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Tick down active ability timers."""
        if self.super_shot_active:
            self._super_shot_timer -= dt
            if self._super_shot_timer <= 0:
                self.super_shot_active = False
                self._super_shot_timer = 0.0

    @property
    def super_shot_remaining(self) -> float:
        return self._super_shot_timer

    # ── Weapon modifiers (applied by ShootingSystem) ─────────────

    def get_fire_rate_mult(self) -> float:
        """Multiplier on fire rate while Super Shot is active."""
        if self.super_shot_active:
            return config.POWER_SUPER_SHOT_FIRE_RATE_MULT
        return 1.0

    def get_spread_mult(self) -> float:
        """Multiplier on spread while Super Shot is active."""
        if self.super_shot_active:
            return config.POWER_SUPER_SHOT_SPREAD_MULT
        return 1.0

    @property
    def is_piercing(self) -> bool:
        """Whether bullets should pierce through enemies."""
        return self.super_shot_active and config.POWER_SUPER_SHOT_PIERCING

    # ── Display ──────────────────────────────────────────────────

    @property
    def display_text(self) -> str:
        """String for HUD display."""
        pct = int(self.fraction * 100)
        ability_name = "SHOT" if self.selected == PowerAbility.SUPER_SHOT else "BOMB"
        if self.super_shot_active:
            return f"POWER: ACTIVE {self._super_shot_timer:.1f}s"
        if self.is_full:
            return f"POWER: READY [{ability_name}] (F)"
        return f"POWER: {pct}% [{ability_name}]"

    def reset(self) -> None:
        """Reset for game restart."""
        self.crystals = 0
        self.super_shot_active = False
        self._super_shot_timer = 0.0
        self.selected = PowerAbility.SUPER_SHOT
