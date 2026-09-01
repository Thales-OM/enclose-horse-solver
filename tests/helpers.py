"""Solver-agnostic helpers used by the test-suite.

These deliberately re-implement the game rules (von Neumann movement, water as
free barrier, walls block movement, grid edge is open) independently of the
optimizer, so tests can verify a solver output without trusting its internals.
"""

from collections import deque
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Base value per tile symbol, matching enclose.horse scoring rules
# (cherry +3 over grass => 4, apple +10 over grass => 11, bee -5 over grass
#  => -4).
TILE_VALUE = {"g": 1, "h": 1, "c": 4, "a": 11, "b": -4}


def load_puzzle(puzzle_number: int) -> Tuple[List[List[str]], int]:
    """Load a puzzle's grid and its wall budget from the project-root files."""
    tests_dir = Path(__file__).resolve().parent
    assets_dir = tests_dir / "assets"
    grid = [
        line.split()
        for line in (assets_dir / f"test{puzzle_number}.txt").read_text().splitlines()
        if line.strip()
    ]
    wall_budget = int((assets_dir / f"walls{puzzle_number}.txt").read_text().strip())
    return grid, wall_budget


def find_horse(grid: Sequence[Sequence[str]]) -> Tuple[int, int]:
    for row_idx, row in enumerate(grid):
        for col_idx, symbol in enumerate(row):
            if symbol == "h":
                return (row_idx, col_idx)
    raise AssertionError("No horse found on the grid")


def water_cells(grid: Sequence[Sequence[str]]) -> Set[Tuple[int, int]]:
    return {
        (row_idx, col_idx)
        for row_idx, row in enumerate(grid)
        for col_idx, symbol in enumerate(row)
        if symbol == "w"
    }


def reachable_from_horse(
    grid: Sequence[Sequence[str]],
    walls: Iterable[Tuple[int, int]],
) -> Set[Tuple[int, int]]:
    """Return everything the horse can move to (walls and water block it)."""
    height = len(grid)
    width = len(grid[0])
    wall_set = set(walls)
    blocked = water_cells(grid) | wall_set

    horse = find_horse(grid)
    seen = {horse}
    queue = deque([horse])
    while queue:
        x, y = queue.popleft()
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < height and 0 <= ny < width):
                continue
            if (nx, ny) in seen or (nx, ny) in blocked:
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def does_escape(
    grid: Sequence[Sequence[str]], walls: Iterable[Tuple[int, int]]
) -> bool:
    """The horse escapes iff its reachable region touches the grid border."""
    height = len(grid)
    width = len(grid[0])
    reachable = reachable_from_horse(grid, walls)
    return any(
        x == 0 or y == 0 or x == height - 1 or y == width - 1 for x, y in reachable
    )


def is_disjoint(a: Set[Tuple[int, int]], b: Set[Tuple[int, int]]) -> bool:
    return not (a & b)


def enclosed_score(
    grid: Sequence[Sequence[str]],
    enclosed: Iterable[Tuple[int, int]],
) -> int:
    """Authoritative score from the enclosed tile values only."""
    return sum(TILE_VALUE[grid[x][y]] for x, y in enclosed)
