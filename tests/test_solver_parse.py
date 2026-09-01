"""Unit tests for the shared grid-scan step (build_grid_summary)."""

import pytest

from enclose_horse_solver.solvers.standard.grid import GridCellType
from enclose_horse_solver.solvers.standard.solver import build_grid_summary


def test_build_summary_basic() -> None:
    rows = [
        ["g", "g", "g"],
        ["g", "h", "g"],
        ["g", "g", "g"],
    ]
    summary, portal_map = build_grid_summary(rows)

    assert summary.grid_width == 3
    assert summary.grid_height == 3
    assert summary.horse_pos == (1, 1)
    # No portals on this board, so an empty portal map.
    assert portal_map == {}
    # Water-free board => nothing non-enclosable and all grass is wall-able.
    assert summary.not_enclosable == []
    assert summary.cannot_place_walls == [(1, 1)]  # only the horse tile


def test_portal_map_connects_pairs() -> None:
    rows = [
        ["1", "g", "1"],
        ["g", "h", "g"],
    ]
    summary, portal_map = build_grid_summary(rows)

    assert set(summary.portal_groups) == {1}
    assert (0, 0) in portal_map and (0, 2) in portal_map[0, 0]
    assert (0, 2) in portal_map and (0, 0) in portal_map[0, 2]


def test_non_rectangular_grid_raises() -> None:
    with pytest.raises(ValueError):
        build_grid_summary([["g", "g"], ["g"]])


def test_missing_horse_raises() -> None:
    with pytest.raises(ValueError):
        build_grid_summary([["g", "g"], ["g", "g"]])


def test_single_portal_without_pair_raises() -> None:
    with pytest.raises(ValueError):
        build_grid_summary([["1", "g"], ["g", "h"]])


def test_special_tiles_are_recorded() -> None:
    rows = [
        ["a", "b", "g"],
        ["g", "h", "c"],
    ]
    summary, _ = build_grid_summary(rows)

    assert summary.custom_enclosure_points[(0, 0)] == 11  # apple
    assert summary.custom_enclosure_points[(0, 1)] == -4  # bees
    assert summary.custom_enclosure_points[(1, 2)] == 4  # cherry
    # Plain grass and the horse are not special-cased.
    assert (0, 2) not in summary.custom_enclosure_points
    assert (1, 1) not in summary.custom_enclosure_points


def test_processed_grid_matches_types() -> None:
    rows = [["h", "1", "w"], ["1", "g", "g"]]
    summary, _ = build_grid_summary(rows)

    assert summary.grid is not None
    assert summary.grid[0][0][0] is GridCellType.HORSE
    assert summary.grid[0][1] == (GridCellType.PORTAL, 1)
    assert summary.grid[0][2][0] is GridCellType.WATER
