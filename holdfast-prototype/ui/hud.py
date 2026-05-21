"""
Heads-up display.

Shows: player HP, currency, wave number, ammo, dash cooldown,
active enemy count, core HP. Uses Panda3D's DirectGUI.
"""

from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectWaitBar
from panda3d.core import TextNode, LColor
from direct.showbase.ShowBase import ShowBase


class HUD:
    """Game HUD with all status displays."""

    def __init__(self, base: ShowBase) -> None:
        self.base = base
        self._elements: list = []

        # ── Top-left: Wave / Phase ──
        self.wave_text = self._text(
            "WAVE 0 — PLANNING",
            pos=(-1.3, 0.95),
            scale=0.06,
            align=TextNode.A_left,
            color=(0.8, 0.8, 0.8, 1),
        )

        # ── Top-right: Currency ──
        self.currency_text = self._text(
            "$ 150",
            pos=(1.3, 0.95),
            scale=0.06,
            align=TextNode.A_right,
            color=(1.0, 0.85, 0.2, 1),
        )

        # ── Bottom-left: HP ──
        self.hp_text = self._text(
            "HP: 100/100",
            pos=(-1.3, -0.9),
            scale=0.05,
            align=TextNode.A_left,
            color=(0.3, 0.9, 0.3, 1),
        )

        # ── Bottom-center: Weapon / Ammo ──
        self.weapon_text = self._text(
            "Pulse Rifle  ∞",
            pos=(0, -0.9),
            scale=0.045,
            align=TextNode.A_center,
            color=(0.5, 0.8, 1.0, 1),
        )

        # ── Bottom-right: Dash cooldown ──
        self.dash_text = self._text(
            "DASH: READY",
            pos=(1.3, -0.9),
            scale=0.045,
            align=TextNode.A_right,
            color=(0.9, 0.5, 1.0, 1),
        )

        # ── Top-center: Core HP ──
        self.core_text = self._text(
            "CORE: 500",
            pos=(0, 0.95),
            scale=0.05,
            align=TextNode.A_center,
            color=(0.2, 1.0, 0.5, 1),
        )

        # ── Center: Phase banner (shown briefly) ──
        self.banner_text = self._text(
            "",
            pos=(0, 0.2),
            scale=0.1,
            align=TextNode.A_center,
            color=(1, 1, 1, 1),
        )
        self._banner_timer: float = 0.0

        # ── Bottom-left-2: Power meter ──
        self.power_text = self._text(
            "POWER: 0% [SHOT]",
            pos=(-1.3, -0.83),
            scale=0.045,
            align=TextNode.A_left,
            color=(0.7, 0.85, 1.0, 1),
        )

        # ── Controls hint ──
        self.controls_text = self._text(
            "WASD:Move  Click:Shoot  Shift:Dash  Q:Weapon  Scroll:Zoom  E:Man Tower  Tab:Build(1-4)  X:Sell  F:Power  R:Cycle  Enter:Wave  Esc:Pause",
            pos=(0, -0.97),
            scale=0.03,
            align=TextNode.A_center,
            color=(0.5, 0.5, 0.5, 1),
        )

    def _text(self, text: str, pos, scale, align, color) -> OnscreenText:
        """Create an on-screen text element."""
        t = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            align=align,
            fg=color,
            shadow=(0, 0, 0, 0.5),
            mayChange=True,
        )
        self._elements.append(t)
        return t

    def update(
        self,
        dt: float,
        wave_number: int,
        phase_name: str,
        currency: int,
        player_hp: int,
        player_max_hp: int,
        weapon_name: str,
        ammo_display: str,
        weapon_slot: int = 0,
        dash_fraction: float = 0.0,
        core_hp: int = 500,
        enemy_count: int = 0,
        power_display: str = "",
        power_ready: bool = False,
        power_active: bool = False,
    ) -> None:
        """Refresh all HUD elements."""
        self.wave_text.setText(f"WAVE {wave_number} — {phase_name}  [{enemy_count} enemies]")
        self.currency_text.setText(f"$ {currency}")
        self.hp_text.setText(f"HP: {player_hp}/{player_max_hp}")
        self.weapon_text.setText(f"[{weapon_slot}] {weapon_name}  {ammo_display}")

        if dash_fraction <= 0:
            self.dash_text.setText("DASH: READY")
            self.dash_text["fg"] = (0.9, 0.5, 1.0, 1)
        else:
            pct = int((1 - dash_fraction) * 100)
            self.dash_text.setText(f"DASH: {pct}%")
            self.dash_text["fg"] = (0.5, 0.3, 0.6, 1)

        # Power meter
        if power_display:
            self.power_text.setText(power_display)
        if power_active:
            self.power_text["fg"] = (1.0, 0.9, 0.3, 1)
        elif power_ready:
            self.power_text["fg"] = (0.3, 1.0, 0.5, 1)
        else:
            self.power_text["fg"] = (0.7, 0.85, 1.0, 1)

        self.core_text.setText(f"CORE: {core_hp}")
        if core_hp < 200:
            self.core_text["fg"] = (1.0, 0.3, 0.2, 1)

        # Banner fade
        if self._banner_timer > 0:
            self._banner_timer -= dt
            alpha = min(1.0, self._banner_timer / 0.5)
            self.banner_text["fg"] = (1, 1, 1, alpha)
            if self._banner_timer <= 0:
                self.banner_text.setText("")

    def show_banner(self, text: str, duration: float = 2.0) -> None:
        """Show a centered banner message (e.g., 'WAVE 3')."""
        self.banner_text.setText(text)
        self.banner_text["fg"] = (1, 1, 1, 1)
        self._banner_timer = duration

    def cleanup(self) -> None:
        for elem in self._elements:
            elem.destroy()
