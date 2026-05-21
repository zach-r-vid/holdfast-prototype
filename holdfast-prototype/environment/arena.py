"""
Arena environment built from map data.

Reads the active map layout and creates: wall geometry for WALL cells,
highlighted floor tiles for BUILD_ZONE cells, path markings for enemy
lanes, cover objects, spawn indicators, and the core objective.
"""

from __future__ import annotations
from typing import Optional

from panda3d.core import (
    LVector3f, LColor, LPoint3f,
    NodePath, CardMaker, GeomNode,
    AmbientLight, DirectionalLight, PointLight,
    TransparencyAttrib,
)
from direct.showbase.ShowBase import ShowBase

from maps.map_01 import (
    GRID, MAP_ROWS, MAP_COLS, CELL_SIZE,
    WALL, PATH, BUILD, OPEN, COVER, SPAWN, CORE,
    get_spawn_points, get_core_position,
)
import config
from utils.color import apply_color


def _cell_to_world(row: int, col: int) -> LVector3f:
    """Convert grid row/col to world-space center of cell."""
    half_w = MAP_COLS * CELL_SIZE / 2
    half_h = MAP_ROWS * CELL_SIZE / 2
    x = (col + 0.5) * CELL_SIZE - half_w
    y = (row + 0.5) * CELL_SIZE - half_h
    return LVector3f(x, y, 0)


class Arena:
    """The playable arena built from map data."""

    def __init__(self, base: ShowBase) -> None:
        self.base = base
        self.root = base.render.attach_new_node("arena")
        self.core_node: Optional[NodePath] = None
        self.core_hp: int = 500

        self._build_floor()
        self._build_map_geometry()
        self._build_core()
        self._build_spawn_indicators()
        self._build_lane_markers()
        self._build_grid_overlay()
        self._setup_lighting()

    # ── Floor ──────────────────────────────────────────────────────

    def _build_floor(self) -> None:
        """Dark floor plane spanning the full arena."""
        cm = CardMaker("floor")
        half_w = config.ARENA_WIDTH / 2
        half_h = config.ARENA_HEIGHT / 2
        cm.set_frame(-half_w, half_w, -half_h, half_h)
        floor = self.root.attach_new_node(cm.generate())
        floor.set_p(-90)
        floor.set_pos(0, 0, -0.01)
        floor.set_color(config.COLOR_ARENA_FLOOR)

    # ── Map geometry (walls, build zones, cover) ──────────────────

    def _build_map_geometry(self) -> None:
        """Walk the grid and create geometry for each cell type."""
        self._walls_node = self.root.attach_new_node("walls")
        self._build_zones_node = self.root.attach_new_node("build_zones")
        self._build_zones_node.set_transparency(TransparencyAttrib.M_alpha)
        self._cover_node = self.root.attach_new_node("cover")

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                cell = GRID[row][col]
                pos = _cell_to_world(row, col)

                if cell == WALL:
                    self._place_wall(pos)
                elif cell == BUILD:
                    self._place_build_zone(pos)
                elif cell == COVER:
                    self._place_cover(pos)

    def _place_wall(self, pos: LVector3f) -> None:
        wall = self.base.loader.load_model("models/misc/rgbCube")
        if wall is None:
            return
        wall.reparent_to(self._walls_node)
        hs = CELL_SIZE / 2
        wall.set_scale(hs, hs, 1.0)
        wall.set_pos(pos.x, pos.y, 1.0)
        apply_color(wall, config.COLOR_WALL)

    def _place_build_zone(self, pos: LVector3f) -> None:
        """Subtle highlighted floor tile showing where towers can go."""
        cm = CardMaker("build_tile")
        margin = 0.1
        hs = CELL_SIZE / 2 - margin
        cm.set_frame(-hs, hs, -hs, hs)
        tile = self._build_zones_node.attach_new_node(cm.generate())
        tile.set_p(-90)
        tile.set_pos(pos.x, pos.y, 0.02)
        tile.set_color(LColor(0.15, 0.25, 0.15, 0.4))

    def _place_cover(self, pos: LVector3f) -> None:
        """Waist-high cover object — visual reference, no gameplay blocking."""
        cover = self.base.loader.load_model("models/misc/rgbCube")
        if cover is None:
            return
        cover.reparent_to(self._cover_node)
        cover.set_scale(0.5, 0.5, 0.6)
        cover.set_pos(pos.x, pos.y, 0.6)
        apply_color(cover, LColor(0.35, 0.35, 0.4, 1.0))

    # ── Core ──────────────────────────────────────────────────────

    def _build_core(self) -> None:
        core = self.base.loader.load_model("models/misc/sphere")
        if core is None:
            core = self.root.attach_new_node("core_fallback")
        else:
            core.reparent_to(self.root)
        core.set_pos(config.CORE_POSITION)
        core.set_scale(1.2)
        apply_color(core, config.COLOR_CORE)
        self.core_node = core

        # Core glow light
        plight = PointLight("core_glow")
        plight.set_color(LColor(0.1, 0.8, 0.3, 1))
        plight.set_attenuation((1, 0.2, 0.05))
        plight_np = self.core_node.attach_new_node(plight)
        self.root.set_light(plight_np)

    # ── Spawn indicators ─────────────────────────────────────────

    def _build_spawn_indicators(self) -> None:
        """Glowing ring at each spawn point."""
        self._spawn_indicators: list[tuple[NodePath, NodePath]] = []
        for sx, sy in get_spawn_points():
            pos = LVector3f(sx, sy, 0)
            # Ring = flattened sphere
            ring = self.base.loader.load_model("models/misc/sphere")
            if ring is None:
                continue
            ring.reparent_to(self.root)
            ring.set_pos(pos.x, pos.y, 0.05)
            ring.set_scale(1.2, 1.2, 0.08)
            apply_color(ring, LColor(1.0, 0.4, 0.1, 0.7))
            ring.set_transparency(TransparencyAttrib.M_alpha)

            # Point light for glow
            plight = PointLight(f"spawn_glow_{id(ring)}")
            plight.set_color(LColor(1.0, 0.3, 0.0, 1))
            plight.set_attenuation((1, 0.5, 0.3))
            plight_np = ring.attach_new_node(plight)
            self.root.set_light(plight_np)

            self._spawn_indicators.append((ring, plight_np))

    def pulse_spawn_indicators(self, active_spawns: list[int] | None = None) -> None:
        """Pulse specific spawn indicators during planning phase.
        active_spawns: indices into spawn list, or None for all."""
        import math, time
        t = time.time()
        pulse = 0.6 + 0.4 * math.sin(t * 4.0)
        for i, (ring, _) in enumerate(self._spawn_indicators):
            if active_spawns is None or i in active_spawns:
                ring.set_color(LColor(1.0, 0.4, 0.1, pulse * 0.8))
            else:
                ring.set_color(LColor(1.0, 0.4, 0.1, 0.3))

    def flash_spawn(self, spawn_index: int) -> None:
        """Bright flash when enemies actively spawn from a point."""
        if 0 <= spawn_index < len(self._spawn_indicators):
            ring, _ = self._spawn_indicators[spawn_index]
            ring.set_color(LColor(1.0, 0.8, 0.3, 1.0))

    # ── Lane markers ─────────────────────────────────────────────

    def _build_lane_markers(self) -> None:
        """Faint arrows/dashes on PATH cells pointing toward the core."""
        self._lane_node = self.root.attach_new_node("lane_markers")
        self._lane_node.set_transparency(TransparencyAttrib.M_alpha)

        core_pos = config.CORE_POSITION
        cm = CardMaker("lane_dash")

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                cell = GRID[row][col]
                if cell not in (PATH, SPAWN):
                    continue

                pos = _cell_to_world(row, col)
                # Point arrow toward core
                to_core = core_pos - pos
                to_core.z = 0
                if to_core.length_squared() < 1.0:
                    continue

                # Small dash mark on the floor
                dash_len = 0.4
                dash_w = 0.08
                cm.set_frame(-dash_w, dash_w, -dash_len, dash_len)
                dash = self._lane_node.attach_new_node(cm.generate())
                dash.set_p(-90)
                dash.set_pos(pos.x, pos.y, 0.015)
                dash.set_color(LColor(0.25, 0.25, 0.3, 0.35))

                # Rotate to point toward core
                import math
                to_core.normalize()
                angle = math.degrees(math.atan2(-to_core.x, to_core.y))
                dash.set_r(angle)

    # ── Grid overlay ─────────────────────────────────────────────

    def _build_grid_overlay(self) -> None:
        """Build zone grid outlines (visible during planning phase)."""
        self.grid_node = self.root.attach_new_node("grid_overlay")
        self.grid_node.set_transparency(TransparencyAttrib.M_alpha)

        cm = CardMaker("grid_cell")
        line_w = 0.04
        hs = CELL_SIZE / 2

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                if GRID[row][col] != BUILD:
                    continue
                pos = _cell_to_world(row, col)

                # Draw 4 edges as thin cards on the ground
                for dx, dy, sx, sy in [
                    (0, hs, hs, line_w),    # top
                    (0, -hs, hs, line_w),   # bottom
                    (-hs, 0, line_w, hs),   # left
                    (hs, 0, line_w, hs),    # right
                ]:
                    cm.set_frame(-sx, sx, -sy, sy)
                    edge = self.grid_node.attach_new_node(cm.generate())
                    edge.set_p(-90)
                    edge.set_pos(pos.x + dx, pos.y + dy, 0.015)
                    edge.set_color(config.COLOR_GRID)

    def show_grid(self) -> None:
        self.grid_node.show()

    def hide_grid(self) -> None:
        self.grid_node.hide()

    # ── Core HP ──────────────────────────────────────────────────

    def damage_core(self, amount: int) -> None:
        self.core_hp -= amount
        if self.core_hp <= 0:
            self.core_hp = 0
            if self.core_node:
                apply_color(self.core_node, LColor(1, 0, 0, 1))

    def is_core_alive(self) -> bool:
        return self.core_hp > 0

    # ── Lighting ─────────────────────────────────────────────────

    def _setup_lighting(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.set_color(config.AMBIENT_LIGHT_COLOR)
        ambient_np = self.root.attach_new_node(ambient)
        self.root.set_light(ambient_np)

        sun = DirectionalLight("sun")
        sun.set_color(config.DIRECTIONAL_LIGHT_COLOR)
        sun_np = self.root.attach_new_node(sun)
        sun_np.set_hpr(30, -60, 0)
        self.root.set_light(sun_np)

        fill = DirectionalLight("fill")
        fill.set_color(LColor(0.3, 0.3, 0.4, 1.0))
        fill_np = self.root.attach_new_node(fill)
        fill_np.set_hpr(-150, -30, 0)
        self.root.set_light(fill_np)
