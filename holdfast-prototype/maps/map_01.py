"""
Map 01 — Three-lane assault.

Grid is 20 columns x 15 rows (matching 40x30 arena at 2.0 cell size).
Row 0 = bottom (y = -14), Row 14 = top (y = +14).
Col 0 = left (x = -19), Col 19 = right (x = +19).

Cell types:
  W = WALL        — impassable, rendered as cube geometry
  P = PATH        — enemy walking lane, player can walk here too
  B = BUILD       — tower build zone, walkable until tower placed
  . = OPEN        — player-navigable open space, no building
  C = COVER       — decorative cover object (player space, not buildable)
  S = SPAWN       — enemy spawn point (walkable path cell)
  X = CORE        — the core objective
"""

# Cell type constants
WALL = "W"
PATH = "P"
BUILD = "B"
OPEN = "."
COVER = "C"
SPAWN = "S"
CORE = "X"

# Row 14 = top of map (y = +14), Row 0 = bottom (y = -14)
# Read top-to-bottom visually
LAYOUT = [
    # Row 14 (top): spawn entrances
    #  0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19
    ["W", "W", "W", "S", "W", "W", "W", "W", "W", "S", "S", "W", "W", "W", "W", "W", "S", "W", "W", "W"],
    # Row 13: lanes begin
    ["W", "W", "B", "P", "B", "W", "W", ".", "B", "P", "P", "B", ".", "W", "W", "B", "P", "B", "W", "W"],
    # Row 12: lanes continue, build zones flanking
    ["W", ".", "B", "P", "B", ".", ".", "B", "B", "P", "P", "B", "B", ".", ".", "B", "P", "B", ".", "W"],
    # Row 11: cross-corridor connects left and center lanes
    ["W", ".", "B", "P", "P", "P", "P", "P", "B", "P", "P", "B", "P", "P", "P", "P", "P", "B", ".", "W"],
    # Row 10: lanes continue
    ["W", ".", "B", "P", "B", ".", "C", "B", "B", "P", "P", "B", "B", "C", ".", "B", "P", "B", ".", "W"],
    # Row 9: middle section
    ["W", ".", "B", "P", "B", ".", ".", "B", "B", "P", "P", "B", "B", ".", ".", "B", "P", "B", ".", "W"],
    # Row 8: cross-corridor connects center and right lanes
    ["W", ".", "B", "P", "P", "P", "P", "P", "B", "P", "P", "B", "P", "P", "P", "P", "P", "B", ".", "W"],
    # Row 7: lanes continue
    ["W", ".", "B", "P", "B", ".", ".", "B", "B", "P", "P", "B", "B", ".", ".", "B", "P", "B", ".", "W"],
    # Row 6: build zones widen near core approach
    ["W", ".", "B", "P", "B", "C", ".", "B", "B", "P", "P", "B", "B", ".", "C", "B", "P", "B", ".", "W"],
    # Row 5: lanes converge toward core
    ["W", ".", "B", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "B", ".", "W"],
    # Row 4: narrowing approach
    ["W", ".", ".", "B", "B", ".", ".", "B", "B", "P", "P", "B", "B", ".", ".", "B", "B", ".", ".", "W"],
    # Row 3: final approach to core
    ["W", ".", ".", ".", "B", ".", ".", "B", "B", "P", "P", "B", "B", ".", ".", "B", ".", ".", ".", "W"],
    # Row 2: core row
    ["W", ".", ".", ".", ".", ".", ".", "B", "P", "P", "P", "P", "B", ".", ".", ".", ".", ".", ".", "W"],
    # Row 1: behind core (player space)
    ["W", ".", ".", ".", ".", ".", ".", ".", "P", "X", "X", "P", ".", ".", ".", ".", ".", ".", ".", "W"],
    # Row 0 (bottom): boundary wall
    ["W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W"],
]

# Flip so index 0 = bottom row (y = -14)
GRID = list(reversed(LAYOUT))

MAP_COLS = 20
MAP_ROWS = 15
CELL_SIZE = 2.0


def get_spawn_points():
    """Extract spawn point world positions from the grid."""
    spawns = []
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            if GRID[row][col] == SPAWN:
                x = (col + 0.5) * CELL_SIZE - (MAP_COLS * CELL_SIZE / 2)
                y = (row + 0.5) * CELL_SIZE - (MAP_ROWS * CELL_SIZE / 2)
                spawns.append((x, y))
    return spawns


def get_core_position():
    """Extract core world position (average of CORE cells)."""
    cx, cy, count = 0.0, 0.0, 0
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            if GRID[row][col] == CORE:
                cx += (col + 0.5) * CELL_SIZE - (MAP_COLS * CELL_SIZE / 2)
                cy += (row + 0.5) * CELL_SIZE - (MAP_ROWS * CELL_SIZE / 2)
                count += 1
    if count == 0:
        return (0.0, -12.0)
    return (cx / count, cy / count)
