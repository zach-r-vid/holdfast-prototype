"""
Developer menu for live stat tweaking.

Toggle with backtick (`) when debug mode is active, then press
backtick again to open the dev menu. Game pauses while open.
Arrow keys or mouse to navigate, +/- or Enter to adjust values.
R to reset all to defaults.
"""

from __future__ import annotations
from typing import Any

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectScrolledFrame,
)
from panda3d.core import TextNode, LColor, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

import config


# ── Tweakable stat definitions ──────────────────────────────────
# Each entry: (label, config_attr_or_path, step, fmt)
# For nested dicts like GRUNT_STATS["hp"], use a tuple path.

_STAT_DEFS: list[tuple[str, str | tuple, float, str]] = [
    # Player
    ("Player Speed",      "PLAYER_MAX_SPEED",    1.0,  ".1f"),
    ("Player Accel",      "PLAYER_ACCELERATION", 10.0, ".0f"),
    ("Dash Speed",        "DASH_SPEED",          2.0,  ".0f"),
    ("Dash Cooldown",     "DASH_COOLDOWN",       0.05, ".2f"),
    # Turret
    ("Turret Fire Rate",  ("TURRET_STATS", "fire_rate"),   0.5, ".1f"),
    ("Turret Damage",     ("TURRET_STATS", "bullet_damage"), 2, ".0f"),
    ("Turret Range",      ("TURRET_STATS", "range"),       1.0, ".1f"),
    # Mortar
    ("Mortar Damage",     ("MORTAR_STATS", "bullet_damage"), 5, ".0f"),
    ("Mortar Splash",     ("MORTAR_STATS", "splash_radius"), 0.5, ".1f"),
    ("Mortar Fire Rate",  ("MORTAR_STATS", "fire_rate"),   0.1, ".1f"),
    # Sniper
    ("Sniper Damage",     ("SNIPER_STATS", "bullet_damage"), 10, ".0f"),
    ("Sniper Range",      ("SNIPER_STATS", "range"),       1.0, ".1f"),
    # Enemies
    ("Grunt HP",          ("GRUNT_STATS", "hp"),           5, ".0f"),
    ("Grunt Speed",       ("GRUNT_STATS", "speed"),        0.5, ".1f"),
    ("Rusher Speed",      ("RUSHER_STATS", "speed"),       0.5, ".1f"),
    ("Rusher HP",         ("RUSHER_STATS", "hp"),          5, ".0f"),
    ("Hunter HP",         ("HUNTER_STATS", "hp"),          5, ".0f"),
    ("Hunter Speed",      ("HUNTER_STATS", "speed"),       0.5, ".1f"),
    ("Emitter HP",        ("BULLET_HELL_EMITTER_STATS", "hp"), 10, ".0f"),
    ("Slug HP",           ("SLUG_STATS", "hp"),            10, ".0f"),
]


def _get_value(path: str | tuple) -> float:
    """Read a config value by attribute name or (dict_attr, key) tuple."""
    if isinstance(path, tuple):
        d = getattr(config, path[0])
        return float(d[path[1]])
    return float(getattr(config, path))


def _set_value(path: str | tuple, value: float) -> None:
    """Write a config value."""
    if isinstance(path, tuple):
        d = getattr(config, path[0])
        # Preserve int type if the original was int
        if isinstance(d[path[1]], int):
            d[path[1]] = int(round(value))
        else:
            d[path[1]] = value
    else:
        orig = getattr(config, path)
        if isinstance(orig, int):
            setattr(config, path, int(round(value)))
        else:
            setattr(config, path, value)


class DevMenu:
    """In-game developer console for adjusting config values live."""

    def __init__(self, base: ShowBase) -> None:
        self.base = base
        self.visible = False

        # Snapshot defaults on startup for reset
        self._defaults: dict[str | tuple, float] = {}
        for _, path, _, _ in _STAT_DEFS:
            self._defaults[path if isinstance(path, str) else tuple(path)] = _get_value(path)

        # ── Build GUI ──
        self.frame = DirectFrame(
            frameColor=(0.03, 0.03, 0.08, 0.92),
            frameSize=(-0.55, 0.55, -0.7, 0.45),
            pos=(0, 0, 0.1),
        )
        self.frame.set_transparency(TransparencyAttrib.M_alpha)

        # Title
        OnscreenText(
            text="DEV MENU (` to close)",
            pos=(0, 0.37),
            scale=0.05,
            align=TextNode.A_center,
            fg=(1, 0.8, 0.3, 1),
            parent=self.frame,
        )

        # Stat rows
        self._value_texts: list[OnscreenText] = []
        self._rows: list[tuple[str, str | tuple, float, str]] = list(_STAT_DEFS)

        y_start = 0.28
        row_height = 0.055

        for i, (label, path, step, fmt) in enumerate(self._rows):
            y = y_start - i * row_height

            # Label
            OnscreenText(
                text=label,
                pos=(-0.48, y),
                scale=0.035,
                align=TextNode.A_left,
                fg=(0.7, 0.7, 0.7, 1),
                parent=self.frame,
            )

            # Minus button
            DirectButton(
                text="-",
                text_scale=0.04,
                text_fg=(1, 1, 1, 1),
                frameSize=(-0.03, 0.03, -0.015, 0.025),
                frameColor=(0.4, 0.15, 0.15, 0.8),
                relief=1,
                pos=(0.22, 0, y),
                parent=self.frame,
                command=self._adjust,
                extraArgs=[i, -1],
            )

            # Value display
            val_text = OnscreenText(
                text="0",
                pos=(0.33, y),
                scale=0.035,
                align=TextNode.A_center,
                fg=(1, 1, 1, 1),
                parent=self.frame,
                mayChange=True,
            )
            self._value_texts.append(val_text)

            # Plus button
            DirectButton(
                text="+",
                text_scale=0.04,
                text_fg=(1, 1, 1, 1),
                frameSize=(-0.03, 0.03, -0.015, 0.025),
                frameColor=(0.15, 0.4, 0.15, 0.8),
                relief=1,
                pos=(0.44, 0, y),
                parent=self.frame,
                command=self._adjust,
                extraArgs=[i, 1],
            )

        # Reset button
        reset_y = y_start - len(self._rows) * row_height - 0.02
        DirectButton(
            text="[R] Reset All to Defaults",
            text_scale=0.04,
            text_fg=(1, 0.5, 0.3, 1),
            frameSize=(-0.25, 0.25, -0.02, 0.03),
            frameColor=(0.2, 0.1, 0.05, 0.8),
            relief=1,
            pos=(0, 0, reset_y),
            parent=self.frame,
            command=self._reset_all,
        )

        # Key binding for reset
        self.base.accept("r", self._reset_key)

        self._refresh_all()
        self.hide()

    def _adjust(self, row_index: int, direction: int) -> None:
        """Adjust a stat value by one step in the given direction."""
        if not self.visible:
            return
        _, path, step, fmt = self._rows[row_index]
        current = _get_value(path)
        new_val = current + step * direction
        # Clamp to non-negative
        new_val = max(0, new_val)
        _set_value(path, new_val)
        self._refresh_row(row_index)

    def _refresh_row(self, index: int) -> None:
        """Update display for one row."""
        _, path, _, fmt = self._rows[index]
        val = _get_value(path)
        self._value_texts[index].setText(f"{val:{fmt}}")

    def _refresh_all(self) -> None:
        """Update all value displays."""
        for i in range(len(self._rows)):
            self._refresh_row(i)

    def _reset_all(self) -> None:
        """Reset all values to startup defaults."""
        for path, default in self._defaults.items():
            _set_value(path, default)
        self._refresh_all()

    def _reset_key(self) -> None:
        """R key handler — only works when dev menu is visible."""
        if self.visible:
            self._reset_all()

    def show(self) -> None:
        self.frame.show()
        self.visible = True
        self._refresh_all()

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
