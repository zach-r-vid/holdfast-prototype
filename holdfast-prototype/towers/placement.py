"""
Tower placement system.

Handles the build menu, grid-snapped placement, selling towers,
and managing the tower roster. Only active during PLANNING phase
(plus limited repositioning during ACTION phase if desired).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from panda3d.core import LVector3f, LColor, NodePath, TransparencyAttrib
from direct.showbase.ShowBase import ShowBase

from towers.base_tower import BaseTower
from towers.turret import Turret
from towers.mortar import Mortar
from towers.slow_field import SlowField
import config

if TYPE_CHECKING:
    from environment.pathfinding import PathGrid
    from systems.economy import Economy


TOWER_CLASSES = {
    "turret": Turret,
    "mortar": Mortar,
    "slow_field": SlowField,
}


class TowerPlacement:
    """Manages building, selling, and tracking all placed towers."""

    def __init__(
        self,
        base: ShowBase,
        parent: NodePath,
        path_grid: "PathGrid",
        economy: "Economy",
    ) -> None:
        self.base = base
        self.parent = parent
        self.path_grid = path_grid
        self.economy = economy

        self.towers: list[BaseTower] = []
        self.selected_type: Optional[str] = None

        # Placement preview ghost
        self._preview: Optional[NodePath] = None
        self._preview_valid: bool = False

    def select_tower_type(self, tower_type: str) -> bool:
        """
        Select a tower type for placement. Returns False if
        player can't afford it.
        """
        cost = config.TOWER_PLACEMENT_COST.get(tower_type, 0)
        if self.economy.currency < cost:
            return False
        self.selected_type = tower_type
        self._create_preview()
        return True

    def cancel_selection(self) -> None:
        """Cancel tower placement mode."""
        self.selected_type = None
        if self._preview:
            self._preview.remove_node()
            self._preview = None

    def update_preview(self, world_pos: LVector3f) -> None:
        """Move the placement preview to the snapped grid position."""
        if not self._preview or not self.selected_type:
            return

        snapped = self.path_grid.snap_to_grid(world_pos)
        self._preview.set_pos(snapped)

        # Check if placement is valid
        self._preview_valid = self.path_grid.is_buildable(snapped)
        if self._preview_valid:
            self._preview.set_color(LColor(0.2, 1.0, 0.2, 0.5))
        else:
            self._preview.set_color(LColor(1.0, 0.2, 0.2, 0.5))

    def try_place(self, world_pos: LVector3f) -> Optional[BaseTower]:
        """
        Attempt to place the selected tower at the given position.
        Returns the placed tower, or None if placement failed.
        """
        if not self.selected_type:
            return None

        snapped = self.path_grid.snap_to_grid(world_pos)

        # Validate
        if not self.path_grid.is_buildable(snapped):
            return None

        cost = config.TOWER_PLACEMENT_COST.get(self.selected_type, 0)
        if not self.economy.spend(cost):
            return None

        # Block the grid cell (validates path reachability)
        if not self.path_grid.block_cell(snapped):
            self.economy.earn(cost)  # Refund
            return None

        # Create tower
        tower_class = TOWER_CLASSES.get(self.selected_type, Turret)
        tower = tower_class(self.base, self.parent, snapped)
        self.towers.append(tower)

        # Keep selection active for rapid placement
        # (cancel only if they can't afford another)
        remaining_cost = config.TOWER_PLACEMENT_COST.get(self.selected_type, 0)
        if self.economy.currency < remaining_cost:
            self.cancel_selection()

        return tower

    def sell_tower(self, tower: BaseTower) -> int:
        """Sell a tower, unblock the cell, refund partial cost."""
        if tower not in self.towers:
            return 0

        cost = config.TOWER_PLACEMENT_COST.get(tower.tower_type, 0)
        refund = int(cost * config.TOWER_SELL_REFUND)

        self.path_grid.unblock_cell(tower.get_position())
        self.towers.remove(tower)
        tower.cleanup()
        self.economy.earn(refund)

        return refund

    def get_tower_at(self, world_pos: LVector3f, max_dist: float = 1.5) -> Optional[BaseTower]:
        """Find the nearest tower to a world position (for manning)."""
        best_tower = None
        best_dist = max_dist

        for tower in self.towers:
            if not tower.alive:
                continue
            dist = (tower.get_position() - world_pos).length()
            if dist < best_dist:
                best_dist = dist
                best_tower = tower

        return best_tower

    def update(self, dt: float, enemies, pool) -> None:
        """Update all towers (targeting and firing)."""
        for tower in self.towers:
            tower.update(dt, enemies, pool)

    def _create_preview(self) -> None:
        """Create a transparent ghost model for placement preview."""
        if self._preview:
            self._preview.remove_node()

        self._preview = self.base.loader.load_model("models/misc/rgbCube")
        if self._preview:
            self._preview.reparent_to(self.parent)
            self._preview.set_scale(0.8, 0.8, 0.5)
            self._preview.set_color(LColor(0.2, 1.0, 0.2, 0.5))
            self._preview.set_transparency(TransparencyAttrib.M_alpha)

    @property
    def tower_count(self) -> int:
        return len(self.towers)
