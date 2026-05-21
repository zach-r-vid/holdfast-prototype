"""
Grid-based A* pathfinding for enemy navigation.

Reads the map layout to determine walkability. Enemies walk on PATH,
SPAWN, CORE, and BUILD cells. BUILD cells become blocked when a tower
is placed on them. WALL, OPEN, and COVER cells are impassable to enemies
(OPEN/COVER are player-only space).
"""

from __future__ import annotations
import heapq
from typing import Optional

from panda3d.core import LVector3f

from maps.map_01 import (
    GRID, MAP_ROWS, MAP_COLS, CELL_SIZE,
    WALL, PATH, BUILD, OPEN, COVER, SPAWN, CORE,
)
import config

# Cells enemies can walk on (before tower placement)
_ENEMY_WALKABLE = {PATH, BUILD, SPAWN, CORE}


class PathGrid:
    """
    2D grid for pathfinding. Cell walkability is derived from
    the map layout. Towers block BUILD cells.
    """

    def __init__(self) -> None:
        self.cell_size = CELL_SIZE
        self.cols = MAP_COLS
        self.rows = MAP_ROWS

        # blocked[row][col] = True means a tower is on this BUILD cell
        self._blocked: list[list[bool]] = [
            [False for _ in range(self.cols)] for _ in range(self.rows)
        ]

        self._path_cache: dict[tuple[int, int], list[tuple[int, int]]] = {}
        self._dirty = True

    def _is_enemy_walkable(self, row: int, col: int) -> bool:
        """Can an enemy walk on this cell right now?"""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False
        cell = GRID[row][col]
        if cell not in _ENEMY_WALKABLE:
            return False
        if self._blocked[row][col]:
            return False
        return True

    def world_to_grid(self, world_pos: LVector3f) -> tuple[int, int]:
        """Convert world position to grid cell."""
        half_w = self.cols * self.cell_size / 2
        half_h = self.rows * self.cell_size / 2
        col = int((world_pos.x + half_w) / self.cell_size)
        row = int((world_pos.y + half_h) / self.cell_size)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return (row, col)

    def grid_to_world(self, row: int, col: int) -> LVector3f:
        """Convert grid cell to world position (center of cell)."""
        half_w = self.cols * self.cell_size / 2
        half_h = self.rows * self.cell_size / 2
        x = (col + 0.5) * self.cell_size - half_w
        y = (row + 0.5) * self.cell_size - half_h
        return LVector3f(x, y, 0)

    def block_cell(self, world_pos: LVector3f) -> bool:
        """
        Block a cell (tower placed). Returns False if cell can't be
        blocked or if blocking would make the core unreachable.
        """
        row, col = self.world_to_grid(world_pos)
        if GRID[row][col] != BUILD:
            return False
        if self._blocked[row][col]:
            return False

        # Temporarily block and check reachability
        self._blocked[row][col] = True

        core_cell = self.world_to_grid(config.CORE_POSITION)
        reachable = False
        for spawn_pos in config.SPAWN_POINTS:
            spawn_cell = self.world_to_grid(spawn_pos)
            path = self._astar(spawn_cell, core_cell)
            if path is not None:
                reachable = True
                break

        if not reachable:
            self._blocked[row][col] = False
            return False

        self._dirty = True
        self._path_cache.clear()
        return True

    def unblock_cell(self, world_pos: LVector3f) -> None:
        """Unblock a cell (tower removed)."""
        row, col = self.world_to_grid(world_pos)
        self._blocked[row][col] = False
        self._dirty = True
        self._path_cache.clear()

    def is_walkable(self, world_pos: LVector3f) -> bool:
        """Check if a world position is walkable for enemies."""
        row, col = self.world_to_grid(world_pos)
        return self._is_enemy_walkable(row, col)

    def is_player_walkable(self, world_pos: LVector3f) -> bool:
        """Check if the player can walk here (wider set of cells)."""
        row, col = self.world_to_grid(world_pos)
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False
        cell = GRID[row][col]
        return cell != WALL

    def is_buildable(self, world_pos: LVector3f) -> bool:
        """Check if a tower can be placed at this position."""
        row, col = self.world_to_grid(world_pos)
        if GRID[row][col] != BUILD:
            return False
        if self._blocked[row][col]:
            return False
        return True

    def get_path(self, from_pos: LVector3f, to_pos: LVector3f) -> Optional[list[LVector3f]]:
        """Get an A* path between two world positions."""
        start = self.world_to_grid(from_pos)
        goal = self.world_to_grid(to_pos)

        cache_key = (start[0], start[1])
        if cache_key in self._path_cache:
            grid_path = self._path_cache[cache_key]
        else:
            grid_path = self._astar(start, goal)
            if grid_path is not None:
                self._path_cache[cache_key] = grid_path

        if grid_path is None:
            return None

        return [self.grid_to_world(r, c) for r, c in grid_path]

    def _astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> Optional[list[tuple[int, int]]]:
        """A* pathfinding on the grid."""
        if not self._is_enemy_walkable(start[0], start[1]):
            return None
        if not self._is_enemy_walkable(goal[0], goal[1]):
            return None

        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor in self._neighbors(current):
                dr = abs(neighbor[0] - current[0])
                dc = abs(neighbor[1] - current[1])
                move_cost = 1.414 if (dr + dc == 2) else 1.0

                tentative_g = g_score[current] + move_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        return None

    def _neighbors(self, cell: tuple[int, int]) -> list[tuple[int, int]]:
        """Get walkable neighbors (8-directional)."""
        row, col = cell
        result = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if not self._is_enemy_walkable(nr, nc):
                    continue
                # Diagonal: both adjacent cardinal cells must be walkable
                if abs(dr) + abs(dc) == 2:
                    if not self._is_enemy_walkable(row + dr, col):
                        continue
                    if not self._is_enemy_walkable(row, col + dc):
                        continue
                result.append((nr, nc))
        return result

    @staticmethod
    def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        """Octile distance heuristic for 8-directional movement."""
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])
        return max(dr, dc) + 0.414 * min(dr, dc)

    def snap_to_grid(self, world_pos: LVector3f) -> LVector3f:
        """Snap a world position to the nearest grid cell center."""
        row, col = self.world_to_grid(world_pos)
        return self.grid_to_world(row, col)
