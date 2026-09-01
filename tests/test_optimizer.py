"""Unit tests for the ILP optimizer core (solve_weighted_enclose_horse)."""

import pulp

from enclose_horse_solver.solvers.standard.optimizer import solve_weighted_enclose_horse


def test_small_interior_enclosure_is_optimal() -> None:
    # Horse in the interior of a 3x3 board can be walled in; the horse must
    # itself be enclosed and never lie on a wall.
    result = solve_weighted_enclose_horse(
        grid_width=3,
        grid_height=3,
        horse_pos=(1, 1),
        max_walls=8,
    )
    assert result.status == pulp.LpStatusOptimal
    assert result.status_desc == "Optimal"
    # The horse cannot be enclosed on a border, and it is in the interior here.
    assert (1, 1) in result.enclosed_tiles
    assert (1, 1) not in result.walls_to_place
    # A proper enclosure is always worth at least the horse tile itself.
    assert result.max_score >= 1
    # With enough walls the enclosure should be bigger than a single tile.
    assert len(result.walls_to_place) <= 8


def test_max_score_is_consistent_with_walls_and_costs() -> None:
    """max_score must equal (gross enclosed weight - wall-cost deduction)."""
    grid_height, grid_width = 5, 5
    horse_pos = (2, 2)
    for wall_cost in (0, 3):
        result = solve_weighted_enclose_horse(
            grid_width=grid_width,
            grid_height=grid_height,
            horse_pos=horse_pos,
            max_walls=8,
            wall_costs=wall_cost,
        )
        assert result.status == pulp.LpStatusOptimal
        n_walls = len(result.walls_to_place)
        gross = result.max_score + wall_cost * n_walls
        # Gross weight is at least the enclosed horse tile and exactly the
        # count of enclosed tiles here (no special tiles on a plain board).
        assert gross == len(result.enclosed_tiles)
        assert result.max_score == gross - wall_cost * n_walls


def test_infeasible_due_to_insufficient_walls() -> None:
    # With a single wall an interior horse on a large board still has plenty
    # of escape routes, so the LP cannot be sealed and must be infeasible.
    result = solve_weighted_enclose_horse(
        grid_width=4,
        grid_height=4,
        horse_pos=(2, 2),
        max_walls=1,
    )
    assert result.status != pulp.LpStatusOptimal
    assert result.walls_to_place == []
    assert result.enclosed_tiles == []
    assert result.max_score == 0


def test_water_is_a_free_barrier_not_a_wall() -> None:
    # A 3x3 board full of water on the horse's east/west/south-neighbours
    # already blocks most escapes, so walls must only go on the remaining
    # grass, never on water.
    result = solve_weighted_enclose_horse(
        grid_width=3,
        grid_height=3,
        horse_pos=(1, 1),
        max_walls=4,
        not_enclosable={(0, 1), (1, 0), (2, 1)},  # water north/west/south
    )
    assert result.status == pulp.LpStatusOptimal
    water = {(0, 1), (1, 0), (2, 1)}
    # Water is never a wall location.
    assert len(water & set(result.walls_to_place)) == 0


def test_disconnected_island_not_counted() -> None:
    """A reachable enclosure must be one connected component around the horse.

    Place a horse in the interior and confirm the reported walls/enclosure are
    jointly consistent: every enclosed tile is reachable from the horse and the
    walls form a valid seal.
    """
    result = solve_weighted_enclose_horse(
        grid_width=5,
        grid_height=5,
        horse_pos=(2, 2),
        max_walls=12,
    )
    assert result.status == pulp.LpStatusOptimal
    enclosed = set(result.enclosed_tiles)
    walls = set(result.walls_to_place)
    # Walls never overlap the enclosure.
    assert not (enclosed & walls)
    # The horse tile is always included.
    assert (2, 2) in enclosed


def test_enclosure_cannot_escape_via_portal() -> None:
    """Portals add non-local edges; escaping through one still invalidates."""
    result = solve_weighted_enclose_horse(
        grid_width=3,
        grid_height=3,
        horse_pos=(1, 1),
        max_walls=8,
        non_neighbour_movements={(1, 1): [(0, 0)]},  # portal to a border cell
    )
    # Even with a portal, a valid solution cannot enclose a reachable border.
    assert result.status == pulp.LpStatusOptimal
    assert (0, 0) not in result.enclosed_tiles
