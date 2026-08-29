import click
from typing import Tuple, Union
from .solvers.standard import StandardSolver
from .solvers.base import SolverContext
from .input.args import WallCostType
from .input.grid import InputType, GridInput

INPUT_TYPE_CHOICES = ["string", "file", "stdin", "interactive", "auto"]


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Enclose Horse Solver CLI."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(1)


@cli.group(name="solve", invoke_without_command=True)
@click.argument("input_data", required=False)
@click.option(
    "-t",
    "--input-type",
    type=click.Choice(INPUT_TYPE_CHOICES, case_sensitive=False),
    default="auto",
    show_default=True,
    help=(
        "How to interpret INPUT_DATA:\n"
        "  string      - treat INPUT_DATA as a literal grid string\n"
        "  file        - treat INPUT_DATA as a path to a grid file\n"
        "  stdin       - ignore INPUT_DATA, read grid from stdin\n"
        "  interactive - ignore INPUT_DATA, prompt for grid line by line\n"
        "  auto        - detect from INPUT_DATA (file if path exists, "
        "else string; if INPUT_DATA is omitted, interactive)"
    ),
)
@click.option(
    "-w",
    "--walls",
    required=True,
    type=click.IntRange(min=1),
    help="Maximum number of walls (required, > 0)",
)
@click.option(
    "-c",
    "--wall-cost",
    default=0,
    type=WallCostType(),
    help="Wall cost: int >= 0 or comma-separated ints (default: 0)",
)
@click.pass_context
def solve_group(
    ctx: click.Context,
    input_data: str | None,
    input_type: InputType,
    walls: int,
    wall_cost: Union[int, Tuple[int, ...]],
) -> None:
    """Solve the enclose horse problem."""
    ctx.ensure_object(dict)

    # Validate wall_cost length if it's a sequence
    if isinstance(wall_cost, tuple) and len(wall_cost) != walls:
        raise click.BadParameter(
            f"wall-cost length ({len(wall_cost)}) must equal walls ({walls})"
        )

    # Build GridInput with explicit mode
    try:
        grid_input = GridInput(input_data, mode=input_type)
    except click.BadParameter as e:
        raise click.UsageError(str(e))

    # Store in context
    ctx.obj["grid_input"] = grid_input
    ctx.obj["input_type"] = input_type
    ctx.obj["walls"] = walls
    ctx.obj["wall_cost"] = wall_cost

    if ctx.invoked_subcommand is not None:
        return

    solution = StandardSolver().solve(
        context=SolverContext(
            grid_rows=grid_input.iter_rows(), max_walls=walls, wall_costs=wall_cost
        )
    )

    click.echo(str(solution))


if __name__ == "__main__":
    cli()
