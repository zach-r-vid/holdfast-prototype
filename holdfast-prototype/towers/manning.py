"""
Tower manning system.

When the player walks up to a tower and presses interact, they "enter"
it. The player takes direct control: aiming with the mouse and firing
the tower's weapon (not the player's). The tower stops auto-firing.
Damage and fire rate are boosted. The tradeoff: you're stationary
and not covering other areas of the map.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, NodePath

from towers.base_tower import BaseTower

if TYPE_CHECKING:
    from player.movement import PlayerMovement
    from player.shooting import ShootingSystem
    from towers.placement import TowerPlacement


class ManningSystem:
    """Manages the player-in-tower state transition."""

    def __init__(
        self,
        player_movement: "PlayerMovement",
        player_shooting: "ShootingSystem",
        tower_placement: "TowerPlacement",
    ) -> None:
        self.movement = player_movement
        self.shooting = player_shooting
        self.placement = tower_placement

        self._manned_tower: Optional[BaseTower] = None
        self._saved_weapon_index: int = 0
        self._saved_weapon: Optional[dict] = None

    @property
    def is_manned(self) -> bool:
        return self._manned_tower is not None

    @property
    def current_tower(self) -> Optional[BaseTower]:
        return self._manned_tower

    def try_toggle(self) -> bool:
        """Toggle manning state. Returns True if state changed."""
        if self._manned_tower is not None:
            self._exit_tower()
            return True
        else:
            return self._enter_nearest_tower()

    def _enter_nearest_tower(self) -> bool:
        """Find the nearest tower and enter it."""
        player_pos = self.movement.get_position()
        tower = self.placement.get_tower_at(player_pos, max_dist=2.5)

        if tower is None:
            return False

        self._manned_tower = tower
        tower.set_manned(True)

        # Lock player position to tower
        self.movement.teleport(tower.get_position())
        self.movement.velocity = LVector3f(0, 0, 0)

        # Save current player weapon and switch to tower's weapon
        self._saved_weapon_index = self.shooting.weapon_index
        self._saved_weapon = self.shooting.current_weapon

        tower_weapon = tower.get_weapon_config()
        self.shooting.set_manned(
            True,
            fire_rate_mult=tower.stats.get("manned_fire_rate_mult", 1.5),
            damage_mult=tower.stats.get("manned_damage_mult", 1.3),
            tower_weapon=tower_weapon,
        )

        return True

    def _exit_tower(self) -> None:
        """Leave the current tower."""
        if self._manned_tower:
            self._manned_tower.set_manned(False)
            self._manned_tower = None

        self.shooting.set_manned(False)

        # Restore player weapon
        if self._saved_weapon is not None:
            self.shooting.weapon_index = self._saved_weapon_index
            self.shooting.current_weapon = self._saved_weapon
            self._saved_weapon = None

    def update(self) -> None:
        """Check if manned tower was destroyed."""
        if self._manned_tower and not self._manned_tower.alive:
            self._exit_tower()
