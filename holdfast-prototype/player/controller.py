"""
Player input controller.

Handles keyboard + mouse (prototype) and gamepad (when available).
Maps raw input to normalized direction vectors for movement and aim.

Keyboard mapping (prototype):
  WASD = move
  Mouse position = aim direction
  Left click / Space = shoot
  Right click / Shift = dash
  E = interact (man tower, etc.)
"""

from __future__ import annotations
from typing import Optional

from panda3d.core import LVector3f, LPoint3f, Plane, LPoint2f
from direct.showbase.ShowBase import ShowBase


class InputState:
    """Snapshot of player input for one frame."""

    __slots__ = (
        "move_direction", "aim_direction", "aim_world_pos",
        "shooting", "dash_pressed", "interact_pressed",
        "tower_menu_toggle", "next_wave_pressed",
        "sell_mode_toggle", "weapon_cycle",
        "scroll_zoom",
        "power_activate", "power_cycle",
        "gravity_activate",
        "number_key",
        "mouse_pos",
    )

    def __init__(self) -> None:
        self.move_direction = LVector3f(0, 0, 0)
        self.aim_direction = LVector3f(0, 1, 0)
        self.aim_world_pos = LPoint3f(0, 0, 0)
        self.shooting: bool = False
        self.dash_pressed: bool = False
        self.interact_pressed: bool = False
        self.tower_menu_toggle: bool = False
        self.next_wave_pressed: bool = False
        self.sell_mode_toggle: bool = False
        self.weapon_cycle: int = 0
        self.scroll_zoom: int = 0
        self.power_activate: bool = False
        self.power_cycle: bool = False
        self.gravity_activate: bool = False
        self.number_key: int = 0  # 0=none, 1-4=pressed
        self.mouse_pos = LPoint2f(0, 0)


class PlayerController:
    """
    Reads raw input devices and produces an InputState each frame.
    Decoupled from movement/shooting so those systems can be tested independently.
    """

    def __init__(self, base: ShowBase) -> None:
        self.base = base
        self._keys: dict[str, bool] = {}
        self._just_pressed: dict[str, bool] = {}
        self._ground_plane = Plane(LVector3f(0, 0, 1), LPoint3f(0, 0, 0))

        self._wheel_direction: int = 0
        self._bind_keys()

    def _bind_keys(self) -> None:
        """Set up key bindings."""
        self.base.accept("wheel_up", self._wheel_up)
        self.base.accept("wheel_down", self._wheel_down)
        key_list = [
            "w", "a", "s", "d",            # movement
            "mouse1", "space",               # shoot
            "mouse3", "lshift",              # dash
            "e",                             # interact
            "tab",                           # tower menu
            "enter",                         # next wave
            "x",                             # sell mode
            "q",                             # cycle weapon
            "f",                             # activate power-up
            "r",                             # cycle power ability
            "g",                             # activate gravity well
            "1", "2", "3", "4", "5",          # weapon / tower select / repair
        ]
        for key in key_list:
            self._keys[key] = False
            self._just_pressed[key] = False
            self.base.accept(key, self._key_down, [key])
            self.base.accept(f"{key}-up", self._key_up, [key])

    def _key_down(self, key: str) -> None:
        if not self._keys[key]:
            self._just_pressed[key] = True
        self._keys[key] = True

    def _key_up(self, key: str) -> None:
        self._keys[key] = False

    def _wheel_up(self) -> None:
        self._wheel_direction = 1

    def _wheel_down(self) -> None:
        self._wheel_direction = -1

    def get_input(self) -> InputState:
        """Sample current input state. Call once per frame."""
        state = InputState()

        # ── Movement ──
        move = LVector3f(0, 0, 0)
        if self._keys.get("w"):
            move.y += 1
        if self._keys.get("s"):
            move.y -= 1
        if self._keys.get("a"):
            move.x -= 1
        if self._keys.get("d"):
            move.x += 1
        if move.length_squared() > 0:
            move.normalize()
        state.move_direction = move

        # ── Aim (mouse → world position on ground plane) ──
        if self.base.mouseWatcherNode.has_mouse():
            mouse = self.base.mouseWatcherNode.get_mouse()
            state.mouse_pos = LPoint2f(mouse.x, mouse.y)

            # Ray from camera through mouse into the scene
            near_point = LPoint3f()
            far_point = LPoint3f()
            self.base.camLens.extrude(mouse, near_point, far_point)

            # Transform to world space
            near_world = self.base.render.get_relative_point(
                self.base.cam, near_point
            )
            far_world = self.base.render.get_relative_point(
                self.base.cam, far_point
            )

            # Intersect with ground plane (Z=0)
            hit_point = LPoint3f()
            if self._ground_plane.intersects_line(
                hit_point,
                near_world,
                far_world - near_world,
            ):
                state.aim_world_pos = hit_point

        # ── Aim direction (will be set relative to player pos by movement.py) ──
        # For now just store the world position; movement system computes direction

        # ── Actions ──
        state.shooting = self._keys.get("mouse1", False) or self._keys.get("space", False)
        state.dash_pressed = self._just_pressed.get("mouse3", False) or self._just_pressed.get("lshift", False)
        state.interact_pressed = self._just_pressed.get("e", False)
        state.tower_menu_toggle = self._just_pressed.get("tab", False)
        state.next_wave_pressed = self._just_pressed.get("enter", False)
        state.sell_mode_toggle = self._just_pressed.get("x", False)
        state.weapon_cycle = 0
        if self._just_pressed.get("q", False):
            state.weapon_cycle = 1

        # Power-up
        state.power_activate = self._just_pressed.get("f", False)
        state.power_cycle = self._just_pressed.get("r", False)
        state.gravity_activate = self._just_pressed.get("g", False)

        # Number keys (1-4) — context-dependent (weapon or tower)
        state.number_key = 0
        for n in range(1, 6):
            if self._just_pressed.get(str(n), False):
                state.number_key = n
                break

        # Scroll wheel → camera zoom
        state.scroll_zoom = 0
        if self._wheel_direction != 0:
            state.scroll_zoom = self._wheel_direction
            self._wheel_direction = 0

        # Clear just-pressed flags
        for key in self._just_pressed:
            self._just_pressed[key] = False

        return state
