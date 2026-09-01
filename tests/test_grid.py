"""Unit tests for GridCell parsing and classification."""

import pytest

from enclose_horse_solver.solvers.standard.grid import GridCell, GridCellType


@pytest.mark.parametrize(
    "symbol, expected_type",
    [
        ("g", GridCellType.GRASS),
        ("w", GridCellType.WATER),
        ("c", GridCellType.CHERRY),
        ("a", GridCellType.APPLE),
        ("b", GridCellType.BEES),
        ("h", GridCellType.HORSE),
    ],
)
def test_basic_symbol_to_type(symbol: str, expected_type: GridCellType) -> None:
    assert GridCell.create_grid_cell(symbol).type_ is expected_type


@pytest.mark.parametrize("num", ["0", "3", "12"])
def test_digit_symbols_are_portals(num: str) -> None:
    cell = GridCell.create_grid_cell(num)
    assert cell.type_ is GridCellType.PORTAL
    assert cell.portal_group == int(num)


def test_unknown_symbol_raises() -> None:
    with pytest.raises(ValueError):
        GridCell.create_grid_cell("x")


def test_wall_placement_rules() -> None:
    # Only plain grass can host a wall.
    for symbol, allowed in [
        ("g", True),
        ("h", False),
        ("w", False),
        ("c", False),
        ("a", False),
        ("b", False),
    ]:
        cell = GridCell.create_grid_cell(symbol)
        assert cell.can_place_wall is allowed, symbol


def test_enclosable_rules() -> None:
    for symbol, enclosable in [
        ("g", True),
        ("h", True),
        ("c", True),
        ("a", True),
        ("b", True),
        ("1", True),  # portals are enclosable
        ("w", False),  # water is a barrier, never scored
    ]:
        cell = GridCell.create_grid_cell(symbol)
        assert cell.is_enclosable is enclosable, symbol


@pytest.mark.parametrize(
    "symbol, points",
    [
        ("g", 1),
        ("h", 1),
        ("c", 4),  # +3 bonus over grass
        ("a", 11),  # +10 bonus over grass
        ("b", -4),  # -5 penalty over grass
        ("1", 1),  # portals score as plain tiles
    ],
)
def test_points_inside(symbol: str, points: int) -> None:
    assert GridCell.create_grid_cell(symbol).points_inside == points


def test_water_has_zero_points() -> None:
    # Water is not enclosable, so its points should never feed the objective.
    assert not GridCell.create_grid_cell("w").is_enclosable
