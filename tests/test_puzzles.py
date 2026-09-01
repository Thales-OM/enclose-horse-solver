"""End-to-end tests against the bundled example puzzles.

Each fixture is a (testN.txt, wallsN.txt) pair at the project root whose
optimal score was independently established by an authoritative reachability
analysis. We assert the solver's programmatic output against those goldens and
against a solver-agnostic validation of enclosure validity.
"""

import pytest

from enclose_horse_solver.solvers.base import SolverContext
from enclose_horse_solver.solvers.standard.solver import StandardSolver

from .helpers import (
    does_escape,
    enclosed_score,
    is_disjoint,
    load_puzzle,
    reachable_from_horse,
    water_cells,
)

# Golden best scores for each bundled puzzle (see tests/README in docs).
PUZZLES = [
    pytest.param(1, 56, id="test1"),
    pytest.param(2, 20, id="test2"),
    pytest.param(3, 82, id="test3"),
    pytest.param(4, 66, id="test4"),
    pytest.param(5, 55, id="test5"),
]


@pytest.mark.parametrize(("puzzle_number", "expected_score"), PUZZLES)
def test_puzzle_optimal_score(puzzle_number: int, expected_score: int) -> None:
    grid, wall_budget = load_puzzle(puzzle_number)
    result = StandardSolver(
        context=SolverContext(grid_rows=grid, max_walls=wall_budget)
    ).solve()

    assert result.success is True
    assert result.status_desc == "Optimal"
    assert result.walls_to_place is not None
    assert result.max_score == expected_score


@pytest.mark.parametrize(("puzzle_number", "expected_score"), PUZZLES)
def test_puzzle_valid_enclosure(puzzle_number: int, expected_score: int) -> None:
    """A returned solution must be a legal, connected, maximally-valued pen."""
    grid, wall_budget = load_puzzle(puzzle_number)
    result = StandardSolver(
        context=SolverContext(grid_rows=grid, max_walls=wall_budget)
    ).solve()

    assert result.success is True
    assert result.walls_to_place is not None
    assert result.enclosed_tiles is not None
    walls = set(result.walls_to_place)
    enclosed = set(result.enclosed_tiles)

    # Walls budget is respected.
    assert len(walls) <= wall_budget

    # Walls only ever go on grass (never water/horse/items).
    assert len(walls - water_cells(grid)) == len(walls)
    # No tile is both a wall and counted as enclosed.
    assert is_disjoint(walls, enclosed)

    # The horse must be fully trapped: it cannot reach the border.
    assert does_escape(grid, walls) is False

    # Authoritative score matches the scored tiles (only reachable grass/items).
    reachable = reachable_from_horse(grid, walls)
    assert enclosed == reachable
    assert enclosed_score(grid, enclosed) == result.max_score
    assert result.max_score == expected_score


def test_trivial_example_test2() -> None:
    """The small all-grass board in test2.txt is solvable with 12 walls."""
    grid = [
        line.split()
        for line in open("test2.txt", encoding="utf-8").read().splitlines()
        if line.strip()
    ]
    result = StandardSolver(context=SolverContext(grid_rows=grid, max_walls=12)).solve()

    assert result.success is True
    assert result.walls_to_place is not None
    assert result.enclosed_tiles is not None
    assert result.max_score == 12
    assert len(result.walls_to_place) == 12
    assert does_escape(grid, result.walls_to_place) is False
    # 12 tiles enclosed: the horse tile + 11 grass.
    assert len(result.enclosed_tiles) == 12
