from typing import Dict, Tuple, Sequence, Set, List
from dataclasses import dataclass, field
import itertools
from .base import GridInputLines, BaseSolverOuput
from ..grid import GridCell, GridCellType
from ..optimizers import solve_weighted_enclose_horse


@dataclass
class GridSummary:
    grid_width: int
    grid_height: int
    horse_pos: Tuple[int, int] | None = None
    portal_groups: Dict[int, Set[Tuple[int, int]]] = field(default_factory=dict)
    custom_enclosure_points: Dict[Tuple[int, int], int] = field(default_factory=dict)
    cannot_place_walls: List[Tuple[int, int]] = field(default_factory=list)
    not_enclosable: List[Tuple[int, int]] = field(default_factory=list)

    def final_validation(self) -> None:
        if self.grid_width <= 0:
            raise ValueError("Supplied Grid width <= 0")
        if self.grid_height <= 0:
            raise ValueError("Supplied Grid height <= 0")
        if self.horse_pos is None:
            raise ValueError("No horse found on the Grid")
        for portal_idx, portal_group in self.portal_groups.items():
            if len(portal_group) == 1:
                # TODO: is it safe to pop failed element here?
                raise ValueError(
                    f"Portal without a pair at symbol = {portal_idx}, "
                    f"coordinates = {portal_group.pop()}"
                )


def standard_solver(
    input_lines: GridInputLines, max_walls: int, wall_costs: int | Sequence[int] = 0
) -> BaseSolverOuput:
    summary = GridSummary(grid_width=-1, grid_height=0)

    for row_idx, row in enumerate(input_lines):
        summary.grid_height += 1

        if summary.grid_width != -1 and summary.grid_width != len(row):
            raise ValueError(
                "Invalid Grid input, "
                f"different len among rows: {summary.grid_width} != {len(row)}"
            )
        summary.grid_width = len(row)

        for col_idx, symbol in enumerate(row):
            cell_coord = (row_idx, col_idx)
            grid_cell = GridCell.create_grid_cell(symbol=symbol)

            if grid_cell.type_ is GridCellType.HORSE:
                summary.horse_pos = cell_coord

            if grid_cell.points_inside != 1:
                summary.custom_enclosure_points[cell_coord] = grid_cell.points_inside

            if grid_cell.type_ is GridCellType.PORTAL:
                if grid_cell.portal_group is None:
                    raise ValueError(
                        "[Internal Error] Parsed a grid cell "
                        f'of type="{grid_cell.type_}" with empty `portal_group` '
                        f"at coordinates {cell_coord}"
                    )
                summary.portal_groups.setdefault(grid_cell.portal_group, set()).add(
                    cell_coord
                )

            if not grid_cell.is_enclosable:
                summary.not_enclosable.append(cell_coord)
            if not grid_cell.can_place_wall:
                summary.cannot_place_walls.append(cell_coord)

    summary.final_validation()

    portal_map: Dict[Tuple[int, int], List[Tuple[int, int]]] = dict()
    for portal_group in summary.portal_groups.values():
        for start_portal, end_portal in itertools.permutations(portal_group, 2):
            portal_map.setdefault(start_portal, list()).append(end_portal)

    optimizer_result = solve_weighted_enclose_horse(
        grid_width=summary.grid_width,
        grid_height=summary.grid_height,
        horse_pos=summary.horse_pos,  # type: ignore[arg-type]
        max_walls=max_walls,
        wall_costs=wall_costs,
        cannot_place_walls=summary.cannot_place_walls,
        not_enclosable=summary.not_enclosable,
        enclosure_weights=summary.custom_enclosure_points,
        non_neighbour_movements=portal_map,
    )

    return BaseSolverOuput(
        result=optimizer_result,
        grid_width=summary.grid_width,
        grid_height=summary.grid_height,
        horse=summary.horse_pos,  # type: ignore[arg-type]
    )
