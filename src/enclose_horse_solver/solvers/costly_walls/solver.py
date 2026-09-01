from typing import Sequence, List, Tuple, Dict
import itertools
import click
from ..base import BaseSolver, SolverParam
from ..standard.grid import GridCellType, GridCell
from ..standard.solver import GridSummary
from .params import WallCostType
from .output import CostlyWallsSolverOutput
from .optimizer import solve_costly_walls_problem


class CostlyWallsSolver(BaseSolver, solver_name="costly-walls"):
    wall_cost: int | Sequence[int] = SolverParam(
        "-c",
        "--wall-cost",
        type=WallCostType(),
        default=6,
        help="Wall cost: int >= 0 or comma-separated ints (default: 6)",
        required=True,
    )

    def solve(self) -> CostlyWallsSolverOutput:
        # TODO: move validation outside from .solve() logic
        # Validate wall_cost length if it's a sequence
        if (
            isinstance(self.wall_cost, tuple)
            and len(self.wall_cost) != self.context.max_walls
        ):
            raise click.BadParameter(
                f"wall-cost length ({len(self.wall_cost)}) must equal "
                f"walls ({self.context.max_walls})"
            )

        summary = GridSummary(grid_width=-1, grid_height=0)
        grid: List[List[Tuple[GridCellType, int | None]]] = []

        for row_idx, row in enumerate(self.context.grid_rows):
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
                    summary.custom_enclosure_points[cell_coord] = (
                        grid_cell.points_inside
                    )

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

        optimizer_result = solve_costly_walls_problem(
            grid_width=summary.grid_width,
            grid_height=summary.grid_height,
            horse_pos=summary.horse_pos,  # type: ignore[arg-type]
            max_walls=self.context.max_walls,
            wall_costs=self.wall_cost,
            cannot_place_walls=summary.cannot_place_walls,
            not_enclosable=summary.not_enclosable,
            enclosure_weights=summary.custom_enclosure_points,
            non_neighbour_movements=portal_map,
        )

        return CostlyWallsSolverOutput(
            success=optimizer_result.status == 1,
            max_score=optimizer_result.max_score,
            walls_to_place=optimizer_result.walls_to_place,
            status_desc=optimizer_result.status_desc,
            processed_grid=summary.grid,
            enclosed_tiles=optimizer_result.enclosed_tiles,
        )
