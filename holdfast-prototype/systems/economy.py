"""
Economy system.

Tracks currency earned from kills and wave completions.
Spent on tower placement and upgrades.
"""

from __future__ import annotations

import config


class Economy:
    """Simple currency tracker."""

    def __init__(self) -> None:
        self.currency: int = config.STARTING_CURRENCY
        self.total_earned: int = config.STARTING_CURRENCY
        self.total_spent: int = 0

    def earn(self, amount: int) -> None:
        """Add currency."""
        self.currency += amount
        self.total_earned += amount

    def spend(self, amount: int) -> bool:
        """Attempt to spend currency. Returns False if insufficient."""
        if self.currency < amount:
            return False
        self.currency -= amount
        self.total_spent += amount
        return True

    def on_enemy_killed(self, reward: int, killed_by_player: bool) -> int:
        """
        Award currency for a kill. Player kills get a bonus
        to incentivize action over pure tower play.
        """
        amount = reward
        if killed_by_player:
            amount = int(amount * config.KILL_CURRENCY_PLAYER_MULT)
        self.earn(amount)
        return amount

    def on_wave_complete(self) -> int:
        """Bonus currency for completing a wave."""
        self.earn(config.WAVE_COMPLETE_BONUS)
        return config.WAVE_COMPLETE_BONUS
