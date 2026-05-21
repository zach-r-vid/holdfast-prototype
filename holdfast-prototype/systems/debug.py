"""
Debug mode overlay and cheats.

Toggle with backtick (`). Provides infinite currency, wave skipping,
kill-all, and a stats overlay for rapid iteration.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from direct.showbase.ShowBase import ShowBase

import config

if TYPE_CHECKING:
    from systems.economy import Economy
    from systems.wave_manager import WaveManager
    from enemies.spawner import EnemySpawner
    from projectiles.pool import ProjectilePool


class DebugSystem:
    """Debug tools toggled by backtick key."""

    def __init__(
        self,
        base: ShowBase,
        economy: "Economy",
        wave_manager: "WaveManager",
        spawner: "EnemySpawner",
        pool: "ProjectilePool",
    ) -> None:
        self.base = base
        self.economy = economy
        self.wave_manager = wave_manager
        self.spawner = spawner
        self.pool = pool

        self.active = False
        self.god_mode = False

        self._watermark = OnscreenText(
            text="DEBUG",
            pos=(-1.3, 0.85),
            scale=0.05,
            align=TextNode.A_left,
            fg=(1, 0.3, 0.3, 0.8),
            shadow=(0, 0, 0, 0.5),
            mayChange=True,
        )

        self._stats_text = OnscreenText(
            text="",
            pos=(-1.3, 0.78),
            scale=0.035,
            align=TextNode.A_left,
            fg=(0.7, 0.7, 0.7, 0.9),
            shadow=(0, 0, 0, 0.5),
            mayChange=True,
        )

        self._watermark.hide()
        self._stats_text.hide()

        # Backtick binding is handled by main.py to coordinate with dev menu
        # self.base.accept("`", self.toggle)
        self._bind_debug_keys()

    def _bind_debug_keys(self) -> None:
        self.base.accept("k", self._kill_all)
        self.base.accept("h", self._toggle_god_mode)
        self.base.accept("shift-n", self._skip_wave)
        self.base.accept("shift-r", self._restart_wave)

    def toggle(self) -> None:
        """Toggle debug mode on/off. Returns True if debug is now active."""
        self.active = not self.active
        if self.active:
            self._watermark.show()
            self._stats_text.show()
        else:
            self._watermark.hide()
            self._stats_text.hide()
            self.god_mode = False
        return self.active

    def update(self) -> None:
        """Called every frame. Applies debug effects when active."""
        if not self.active:
            return

        self.economy.currency = 99999

        # God mode: force HP to max every frame
        if self.god_mode:
            game = self.base
            game.player_hp = config.PLAYER_MAX_HP
            game.arena.core_hp = 500

        god_label = "  GOD MODE" if self.god_mode else ""
        self._stats_text.setText(
            f"Projectiles: {self.pool.active_count}/{self.pool.pool_count + self.pool.active_count}  "
            f"Enemies: {self.spawner.active_count}{god_label}"
        )

    def _toggle_god_mode(self) -> None:
        if not self.active:
            return
        self.god_mode = not self.god_mode

    def _kill_all(self) -> None:
        if not self.active:
            return
        for enemy in self.spawner.enemies:
            if enemy.alive:
                enemy.take_damage(enemy.hp)

    def _skip_wave(self) -> None:
        if not self.active:
            return
        self._kill_all()
        if self.wave_manager.is_planning:
            self.wave_manager.try_start_wave()

    def _restart_wave(self) -> None:
        if not self.active:
            return
        self.spawner.clear_all()
        self.pool.clear_all()
        if self.wave_manager.is_action:
            wave_num = self.wave_manager.wave_number
            self.spawner.start_wave(wave_num - 1)
