"""
Tower build menu.

Simple on-screen menu for selecting which tower to build.
Shown when player presses Tab during planning phase.
Uses keyboard shortcuts (1, 2, 3) for quick selection.
"""

from __future__ import annotations
from typing import Optional, Callable

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton
from panda3d.core import TextNode, LColor, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

import config


class TowerMenu:
    """Tower selection menu overlay."""

    def __init__(self, base: ShowBase, on_select: Callable[[str], None]) -> None:
        self.base = base
        self.on_select = on_select
        self.visible = False

        # Background frame
        self.frame = DirectFrame(
            frameColor=(0.05, 0.05, 0.1, 0.85),
            frameSize=(-0.4, 0.4, -0.42, 0.25),
            pos=(0, 0, 0),
        )
        self.frame.set_transparency(TransparencyAttrib.M_alpha)

        # Title
        self.title = OnscreenText(
            text="BUILD TOWER",
            pos=(0, 0.17),
            scale=0.06,
            align=TextNode.A_center,
            fg=(1, 1, 1, 1),
            parent=self.frame,
        )

        # Tower options
        tower_defs = [
            ("1", "turret", "Turret", config.TOWER_PLACEMENT_COST["turret"], "Steady DPS"),
            ("2", "mortar", "Mortar", config.TOWER_PLACEMENT_COST["mortar"], "AoE splash"),
            ("3", "slow_field", "Slow Field", config.TOWER_PLACEMENT_COST["slow_field"], "Area slow"),
            ("4", "sniper", "Sniper", config.TOWER_PLACEMENT_COST["sniper"], "Long range"),
        ]

        self._option_texts = []
        for i, (key, tower_type, name, cost, desc) in enumerate(tower_defs):
            y = 0.08 - i * 0.08
            text = OnscreenText(
                text=f"[{key}] {name} — ${cost} — {desc}",
                pos=(0, y),
                scale=0.04,
                align=TextNode.A_center,
                fg=(0.8, 0.8, 0.8, 1),
                parent=self.frame,
            )
            self._option_texts.append(text)

        # Repair option
        repair_y = 0.08 - len(tower_defs) * 0.08
        repair_text = OnscreenText(
            text=f"[5] Repair — ${config.REPAIR_COST} — Restore {config.REPAIR_AMOUNT} HP",
            pos=(0, repair_y),
            scale=0.04,
            align=TextNode.A_center,
            fg=(0.3, 1.0, 0.4, 1),
            parent=self.frame,
        )
        self._option_texts.append(repair_text)

        # Sell mode hint
        sell_text = OnscreenText(
            text="[X] Sell Tower (click near tower)",
            pos=(0, repair_y - 0.08),
            scale=0.04,
            align=TextNode.A_center,
            fg=(1.0, 0.4, 0.4, 1),
            parent=self.frame,
        )
        self._option_texts.append(sell_text)

        # Keys are handled by PlayerController → main.py routing
        self.hide()

    def _select(self, tower_type: str) -> None:
        """Handle tower selection."""
        if not self.visible:
            return
        self.on_select(tower_type)
        self.hide()

    def select_by_number(self, number: int) -> None:
        """Select tower by number key (1-4). Called by main game loop."""
        tower_types = ["turret", "mortar", "slow_field", "sniper"]
        if 1 <= number <= len(tower_types) and self.visible:
            self._select(tower_types[number - 1])

    def show(self) -> None:
        self.frame.show()
        self.visible = True

    def hide(self) -> None:
        self.frame.hide()
        self.visible = False

    def toggle(self) -> None:
        if self.visible:
            self.hide()
        else:
            self.show()

    def cleanup(self) -> None:
        self.frame.destroy()
