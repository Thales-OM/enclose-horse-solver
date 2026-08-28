from typing import Sequence, Tuple, Dict, Iterable, List, Mapping
from dataclasses import dataclass
import pulp  # type: ignore[import-untyped]


@dataclass(frozen=True)
class EnclosureResult:
    status: int
    status_desc: str
    max_score: int
    walls_to_place: List[Tuple[int, int]]
    enclosed_tiles: List[Tuple[int, int]]


def solve_weighted_enclose_horse(
    grid_width: int,
    grid_height: int,
    horse_pos: Tuple[int, int],
    max_walls: int,
    wall_costs: int | Sequence[int] = 0,
    cannot_place_walls: Iterable[Tuple[int, int]] | None = None,
    not_enclosable: Iterable[Tuple[int, int]] | None = None,
    enclosure_weights: Dict[Tuple[int, int], int] | None = None,
    non_neighbour_movements: (
        Mapping[Tuple[int, int], Iterable[Tuple[int, int]]] | None
    ) = None,
) -> EnclosureResult:
    """
    Solves the optimal enclosure for enclose.horse taking item weights
        and wall costs into account.

    Args:
        grid_width (int): Grid width (>0)
        grid_height (int): Grid height (>0)
        horse_pos (Tuple[int, int]): Horse coordinates within the Grid (0-start)
        max_walls (int): Max number of walls that can be placed
        wall_costs (int | Sequence[int], optional): Marginal wall cost.
            Provide full Sequence if non-constant. Defaults to 0.
        cannot_place_walls (Iterable[Tuple[int, int]] | None, optional):
            Grid cells where walls cannot be placed. Defaults to None.
        not_enclosable (Iterable[Tuple[int, int]] | None, optional):
            Grid cells which do not count towards enclosure (e.g. obstacles/water).
            Defaults to None.
        enclosure_weights (Dict[Tuple[int, int], int] | None, optional):
            Special points gained by enclosing a grid cell, for other cells points = 1.
            Defaults to None.
        non_neighbour_movements
            (Dict[Tuple[int, int], Iterable[Tuple[int, int]]]  |  None, optional):
            Special movement possibilities (e.g. portals),
            directional: A -> B != B -> A.
            Defaults to None.

    Raises:
        ValueError: If the input data is invalid. This happens when:
            - `wall_costs` Sequence len != max_walls
            - Grid width / height <= 0
            - Horse coordinates are not on the grid

    Returns:
        EnclosureResult: Optimization results.
    """
    # 0. Input validation and casting
    if grid_width <= 0 or grid_height <= 0:
        raise ValueError("Grid dimensions must be positive")

    if not (0 <= horse_pos[0] < grid_height and 0 <= horse_pos[1] < grid_width):
        raise ValueError("Horse position out of bounds")

    if not isinstance(wall_costs, int) and len(wall_costs) != max_walls:
        raise ValueError(
            "When providing `wall_costs` as `Sequence[int]` "
            "its `len` must equal `max_walls`"
        )

    cannot_place_walls = (
        set() if cannot_place_walls is None else set(cannot_place_walls)
    )
    not_enclosable = set() if not_enclosable is None else set(not_enclosable)
    if enclosure_weights is None:
        enclosure_weights = {}
    if non_neighbour_movements is None:
        non_neighbour_movements = {}

    # 1. Initialize the optimization problem
    prob = pulp.LpProblem("Weighted_Enclose_Horse_Solver", pulp.LpMaximize)

    all_tiles = [(x, y) for x in range(grid_height) for y in range(grid_width)]

    def is_border(x: int, y: int) -> bool:
        return x == 0 or y == 0 or x == grid_height - 1 or y == grid_width - 1

    # 2. Define decision variables
    W = pulp.LpVariable.dicts("Wall", all_tiles, cat="Binary")
    E = pulp.LpVariable.dicts("Enclosed", all_tiles, cat="Binary")

    # Auxiliary variables: y[k-1] = 1 means "at least k walls placed"
    y = pulp.LpVariable.dicts("Y", range(max_walls), cat="Binary")

    # Sequential constraint: y[k] >= y[k+1]
    for k in range(max_walls - 1):
        prob += y[k] >= y[k + 1]

    # Link to actual wall count and set wall budget
    prob += pulp.lpSum(W[tile] for tile in all_tiles) == pulp.lpSum(
        y[k] for k in range(max_walls)
    )

    # 3. Define objective function with weights

    idx_wall_costs = (
        (wall_costs,) * max_walls if isinstance(wall_costs, int) else tuple(wall_costs)
    )  # e.g. (1, 2, 5)

    # If item_weights doesn't have the tile, it defaults to a standard score of 1.
    # Subtract total wall cost term at the end
    prob += pulp.lpSum(
        E[tile] * enclosure_weights.get(tile, 1) for tile in all_tiles
    ) - pulp.lpSum(idx_wall_costs[k] * y[k] for k in range(len(idx_wall_costs)))

    # 4. Apply tile-specific constraints
    # Constraint A: Horse rules
    prob += E[horse_pos] == 1
    prob += W[horse_pos] == 0

    for x, y in all_tiles:
        # Constraint B: Hardcoded map obstacles
        if (x, y) in cannot_place_walls:
            prob += W[(x, y)] == 0

        if (x, y) in not_enclosable:
            prob += E[(x, y)] == 0
            continue

        # Constraint C: Border escape prevention
        if is_border(x, y):
            prob += E[(x, y)] == 0
            continue

        # Constraint D: Flow/Adjacency Logic
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid_height and 0 <= ny < grid_width:
                neighbors.append((nx, ny))

        neighbors.extend(non_neighbour_movements.get((x, y), tuple()))

        for nx, ny in neighbors:
            prob += E[(x, y)] - E[(nx, ny)] <= W[(nx, ny)]

    # 5. Execute Solver
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # 6. Extract Results
    # Add tolerance just to be sure
    wall_locations = [tile for tile in all_tiles if pulp.value(W[tile]) >= 0.5]
    enclosed_tiles = [tile for tile in all_tiles if pulp.value(E[tile]) >= 0.5]

    # Recalculate score using the weights to verify
    total_score = sum(enclosure_weights.get(tile, 1) for tile in enclosed_tiles)

    return EnclosureResult(
        status=prob.status,
        status_desc=pulp.LpStatus[prob.status],
        max_score=int(total_score),
        walls_to_place=wall_locations,
        enclosed_tiles=enclosed_tiles,
    )
