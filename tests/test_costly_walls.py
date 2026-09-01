"""Tests for the costly-walls solver (per-wall point deduction mode)."""

import click
import pytest

from enclose_horse_solver.solvers.base import SolverContext
from enclose_horse_solver.solvers.costly_walls.solver import CostlyWallsSolver

from .helpers import does_escape, load_puzzle


def test_wall_cost_deduction_matches_golden_free_score() -> None:
    # test3 with 16 walls: free-mode optimal is 82 (16 walls on grass).
    grid, wall_budget = load_puzzle(3)
    free = CostlyWallsSolver(
        context=SolverContext(grid_rows=grid, max_walls=wall_budget),
        wall_cost=0,
    ).solve()
    assert free.success is True
    assert free.walls_to_place is not None
    assert free.max_score == 82

    # Same board, each wall costs 1 point: the gross score is 98
    # (82 gross from the enclosure) minus 16 walls.
    costly = CostlyWallsSolver(
        context=SolverContext(grid_rows=grid, max_walls=wall_budget),
        wall_cost=1,
    ).solve()
    assert costly.success is True
    assert costly.walls_to_place is not None
    assert costly.max_score == free.max_score - len(free.walls_to_place)


def test_costly_walls_produces_valid_enclosure() -> None:
    grid, wall_budget = load_puzzle(4)
    result = CostlyWallsSolver(
        context=SolverContext(grid_rows=grid, max_walls=wall_budget),
        wall_cost=1,
    ).solve()
    assert result.success is True
    assert result.walls_to_place is not None
    assert len(result.walls_to_place) <= wall_budget
    assert does_escape(grid, result.walls_to_place) is False


def test_wall_cost_length_mismatch_raises() -> None:
    grid, wall_budget = load_puzzle(1)
    solver = CostlyWallsSolver(
        context=SolverContext(grid_rows=grid, max_walls=wall_budget),
        # Provide a sequence whose length does not match the wall budget.
        wall_cost=(1, 2, 3),
    )
    with pytest.raises(click.BadParameter):
        solver.solve()
