from typing import Sequence
import click
from ..base import BaseSolver, SolverParam
from ..standard.solver import build_grid_summary
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

        summary, portal_map = build_grid_summary(self.context.grid_rows)
        # final_validation() guarantees the grid is populated.
        assert summary.grid is not None

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
