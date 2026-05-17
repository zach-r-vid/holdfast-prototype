"""
Arena environment setup.

Creates the play area: floor, boundary walls, the core to defend,
grid visualization for tower placement, and any environmental props.
All placeholder geometry — colored primitives with basic materials.
"""

from __future__ import annotations
from typing import Optional

from panda3d.core import (
    LVector3f, LColor, LPoint3f,
    NodePath, CardMaker, GeomNode,
    AmbientLight, DirectionalLight,
    TransparencyAttrib,
)
from direct.showbase.ShowBase import ShowBase

import config


class Arena:
    """The playable arena with floor, walls, core, and grid overlay."""

    def __init__(self, base: ShowBase) -> None:
        self.base = base
        self.root = base.render.attach_new_node("arena")
        self.core_node: Optional[NodePath] = None
        self.core_hp: int = 500

        self._build_floor()
        self._build_walls()
        self._build_core()
        self._build_grid_overlay()
        self._setup_lighting()

    def _build_floor(self) -> None:
        """Create the arena floor plane."""
        cm = CardMaker("floor")
        half_w = config.ARENA_WIDTH / 2
        half_h = config.ARENA_HEIGHT / 2
        cm.set_frame(-half_w, half_w, -half_h, half_h)
        floor = self.root.attach_new_node(cm.generate())
        floor.set_p(-90)  # Rotate to lie flat on XY plane
        floor.set_pos(0, 0, -0.01)  # Slightly below Z=0
        floor.set_color(config.COLOR_ARENA_FLOOR)

    def _build_walls(self) -> None:
        """Create boundary walls around the arena."""
        half_w = config.ARENA_WIDTH / 2
        half_h = config.ARENA_HEIGHT / 2
        wall_height = 1.5
        wall_thickness = 0.5

        walls_node = self.root.attach_new_node("walls")

        wall_defs = [
            # (pos_x, pos_y, scale_x, scale_y) — using cubes stretched
            (0, half_h + wall_thickness / 2, config.ARENA_WIDTH + wall_thickness * 2, wall_thickness),   # top
            (0, -half_h - wall_thickness / 2, config.ARENA_WIDTH + wall_thickness * 2, wall_thickness),  # bottom
            (-half_w - wall_thickness / 2, 0, wall_thickness, config.ARENA_HEIGHT),                       # left
            (half_w + wall_thickness / 2, 0, wall_thickness, config.ARENA_HEIGHT),                        # right
        ]

        for px, py, sx, sy in wall_defs:
            wall = self.base.loader.load_model("models/misc/rgbCube")
            if wall is None:
                continue
            wall.reparent_to(walls_node)
            wall.set_scale(sx / 2, sy / 2, wall_height / 2)
            wall.set_pos(px, py, wall_height / 2)
            wall.set_color(config.COLOR_WALL)

    def _build_core(self) -> None:
        """Create the core — the thing you're defending."""
        core = self.base.loader.load_model("models/misc/sphere")
        if core is None:
            core = self.root.attach_new_node("core_fallback")
        else:
            core.reparent_to(self.root)

        core.set_pos(config.CORE_POSITION)
        core.set_scale(1.2)
        core.set_color(config.COLOR_CORE)
        self.core_node = core

        # Pulsing glow effect would go here in production
        # For now, it's just a green sphere

    def _build_grid_overlay(self) -> None:
        """
        Draw the tower placement grid as a transparent overlay.
        Only visible during planning phase (toggled by wave manager).
        """
        self.grid_node = self.root.attach_new_node("grid_overlay")
        self.grid_node.set_transparency(TransparencyAttrib.M_alpha)

        half_w = config.ARENA_WIDTH / 2
        half_h = config.ARENA_HEIGHT / 2
        cell = config.GRID_CELL_SIZE

        # Draw grid lines using cards (thin quads)
        cm = CardMaker("gridline")
        line_width = 0.03

        # Vertical lines
        x = -half_w
        while x <= half_w + 0.01:
            cm.set_frame(x - line_width, x + line_width, -half_h, half_h)
            line = self.grid_node.attach_new_node(cm.generate())
            line.set_p(-90)
            line.set_pos(0, 0, 0.01)
            line.set_color(config.COLOR_GRID)
            x += cell

        # Horizontal lines
        y = -half_h
        while y <= half_h + 0.01:
            cm.set_frame(-half_w, half_w, y - line_width, y + line_width)
            line = self.grid_node.attach_new_node(cm.generate())
            line.set_p(-90)
            line.set_pos(0, 0, 0.01)
            line.set_color(config.COLOR_GRID)
            y += cell

    def show_grid(self) -> None:
        """Show placement grid (planning phase)."""
        self.grid_node.show()

    def hide_grid(self) -> None:
        """Hide placement grid (action phase)."""
        self.grid_node.hide()

    def damage_core(self, amount: int) -> None:
        """Enemy reached the core."""
        self.core_hp -= amount
        if self.core_hp <= 0:
            self.core_hp = 0
            # Flash red
            if self.core_node:
                self.core_node.set_color(LColor(1, 0, 0, 1))

    def is_core_alive(self) -> bool:
        return self.core_hp > 0

    def _setup_lighting(self) -> None:
        """Basic 3-point-ish lighting for the arena."""
        # Ambient
        ambient = AmbientLight("ambient")
        ambient.set_color(config.AMBIENT_LIGHT_COLOR)
        ambient_np = self.root.attach_new_node(ambient)
        self.root.set_light(ambient_np)

        # Directional (main light — slight angle for shadows/depth)
        sun = DirectionalLight("sun")
        sun.set_color(config.DIRECTIONAL_LIGHT_COLOR)
        sun_np = self.root.attach_new_node(sun)
        sun_np.set_hpr(30, -60, 0)
        self.root.set_light(sun_np)

        # Fill light (dimmer, opposite side)
        fill = DirectionalLight("fill")
        fill.set_color(LColor(0.3, 0.3, 0.4, 1.0))
        fill_np = self.root.attach_new_node(fill)
        fill_np.set_hpr(-150, -30, 0)
        self.root.set_light(fill_np)
