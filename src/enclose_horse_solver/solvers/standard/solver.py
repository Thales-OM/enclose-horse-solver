from typing import Dict, Tuple, Set, List, Sequence, Iterable
from dataclasses import dataclass, field
import itertools
from ..base import BaseSolver
from .grid import GridCell, GridCellType
from .optimizer import solve_weighted_enclose_horse
from .output import StandardSolverOutput


@dataclass
class GridSummary:
    grid_width: int
    grid_height: int
    grid: Sequence[Sequence[Tuple[GridCellType, int | None]]] | None = None
    horse_pos: Tuple[int, int] | None = None
    portal_groups: Dict[int, Set[Tuple[int, int]]] = field(default_factory=dict)
    custom_enclosure_points: Dict[Tuple[int, int], int] = field(default_factory=dict)
    cannot_place_walls: List[Tuple[int, int]] = field(default_factory=list)
    not_enclosable: List[Tuple[int, int]] = field(default_factory=list)

    def final_validation(self) -> None:
        if self.grid is None:
            raise ValueError("No Grid has been scanned. Empty Grid provided?")
        if self.grid_width <= 0:
            raise ValueError("Supplied Grid width <= 0")
        if self.grid_height <= 0:
            raise ValueError("Supplied Grid height <= 0")
        if self.horse_pos is None:
            raise ValueError("No horse found on the Grid")
        for portal_idx, portal_group in self.portal_groups.items():
            if len(portal_group) == 1:
                raise ValueError(
                    f"Portal without a pair at symbol = {portal_idx}, "
                    f"coordinates = {next(iter(portal_group))}"
                )


def build_grid_summary(
    grid_rows: Iterable[Sequence[str]],
) -> Tuple[GridSummary, Dict[Tuple[int, int], List[Tuple[int, int]]]]:
    """Scan raw grid rows into a validated GridSummary plus the portal map.

    This is the canonical grid-parsing step shared by all solvers, so the
    (previously duplicated) scan logic only has to be correct in one place.
    """
    summary = GridSummary(grid_width=-1, grid_height=0)
    grid: List[List[Tuple[GridCellType, int | None]]] = []

    for row_idx, row in enumerate(grid_rows):
        summary.grid_height += 1
        grid_row: List[Tuple[GridCellType, int | None]] = []

        if summary.grid_width != -1 and summary.grid_width != len(row):
            raise ValueError(
                "Invalid Grid input, "
                f"different len among rows: {summary.grid_width} != {len(row)}"
            )
        summary.grid_width = len(row)

        for col_idx, symbol in enumerate(row):
            cell_coord = (row_idx, col_idx)
            grid_cell = GridCell.create_grid_cell(symbol=symbol)

            grid_row.append((grid_cell.type_, grid_cell.portal_group))

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

        grid.append(grid_row)

    summary.grid = grid
    summary.final_validation()

    portal_map: Dict[Tuple[int, int], List[Tuple[int, int]]] = dict()
    for portal_group in summary.portal_groups.values():
        for start_portal, end_portal in itertools.permutations(portal_group, 2):
            portal_map.setdefault(start_portal, list()).append(end_portal)

    return summary, portal_map


class StandardSolver(BaseSolver, solver_name="standard"):
    """Solve a standard enclose.horse problem"""

    def solve(self) -> StandardSolverOutput:
        summary, portal_map = build_grid_summary(self.context.grid_rows)
        # final_validation() guarantees the grid is populated.
        assert summary.grid is not None

        optimizer_result = solve_weighted_enclose_horse(
            grid_width=summary.grid_width,
            grid_height=summary.grid_height,
            horse_pos=summary.horse_pos,  # type: ignore[arg-type]
            max_walls=self.context.max_walls,
            cannot_place_walls=summary.cannot_place_walls,
            not_enclosable=summary.not_enclosable,
            enclosure_weights=summary.custom_enclosure_points,
            non_neighbour_movements=portal_map,
        )

        return StandardSolverOutput(
            success=optimizer_result.status == 1,
            max_score=optimizer_result.max_score,
            walls_to_place=optimizer_result.walls_to_place,
            status_desc=optimizer_result.status_desc,
            processed_grid=summary.grid,
            enclosed_tiles=optimizer_result.enclosed_tiles,
        )
