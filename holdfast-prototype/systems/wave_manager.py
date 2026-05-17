"""
Wave manager — the game phase state machine.

PLANNING → ACTION → WAVE_CLEAR → PLANNING

This is the heartbeat of the game. Planning phase lets you build.
Action phase spawns enemies and tests your defenses. Wave clear
awards currency and resets for the next round.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Callable, Optional


import config


class GamePhase(Enum):
    PLANNING = auto()
    ACTION = auto()
    WAVE_CLEAR = auto()
    GAME_OVER = auto()


class WaveManager:
    """Controls the planning → action → clear loop."""

    def __init__(self) -> None:
        self.phase: GamePhase = GamePhase.PLANNING
        self.wave_number: int = 0
        self.planning_timer: float = 0.0

        # Callbacks
        self._on_phase_change: list[Callable[[GamePhase], None]] = []
        self._on_wave_start: list[Callable[[int], None]] = []
        self._on_wave_complete: list[Callable[[int], None]] = []

    def on_phase_change(self, callback: Callable[[GamePhase], None]) -> None:
        self._on_phase_change.append(callback)

    def on_wave_start(self, callback: Callable[[int], None]) -> None:
        self._on_wave_start.append(callback)

    def on_wave_complete(self, callback: Callable[[int], None]) -> None:
        self._on_wave_complete.append(callback)

    def update(self, dt: float, wave_complete: bool, core_alive: bool) -> None:
        """Tick the state machine. Called every frame."""
        if not core_alive:
            if self.phase != GamePhase.GAME_OVER:
                self._set_phase(GamePhase.GAME_OVER)
            return

        if self.phase == GamePhase.PLANNING:
            self.planning_timer += dt

        elif self.phase == GamePhase.ACTION:
            if wave_complete:
                self._set_phase(GamePhase.WAVE_CLEAR)
                for cb in self._on_wave_complete:
                    cb(self.wave_number)

        elif self.phase == GamePhase.WAVE_CLEAR:
            # Auto-transition to planning after a brief pause
            self.planning_timer = 0.0
            self._set_phase(GamePhase.PLANNING)

    def try_start_wave(self) -> bool:
        """
        Player triggers the next wave (press Enter during planning).
        Returns True if wave was started.
        """
        if self.phase != GamePhase.PLANNING:
            return False

        if self.planning_timer < config.PLANNING_PHASE_MIN_TIME and self.wave_number > 0:
            return False

        self.wave_number += 1
        self._set_phase(GamePhase.ACTION)

        for cb in self._on_wave_start:
            cb(self.wave_number)

        return True

    def _set_phase(self, new_phase: GamePhase) -> None:
        """Transition to a new phase."""
        old = self.phase
        self.phase = new_phase
        for cb in self._on_phase_change:
            cb(new_phase)

    @property
    def is_planning(self) -> bool:
        return self.phase == GamePhase.PLANNING

    @property
    def is_action(self) -> bool:
        return self.phase == GamePhase.ACTION

    @property
    def is_game_over(self) -> bool:
        return self.phase == GamePhase.GAME_OVER

    @property
    def can_start_wave(self) -> bool:
        if self.phase != GamePhase.PLANNING:
            return False
        if self.wave_number > 0 and self.planning_timer < config.PLANNING_PHASE_MIN_TIME:
            return False
        return True
