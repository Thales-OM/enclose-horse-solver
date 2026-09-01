import click
from .solvers import SOLVER_REGISTRY, DEFAULT_SOLVER_NAME
from .solvers.base import SolverContext
from .input.grid import InputType, GridInput
from .cmd_factory import make_solver_command

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
@click.pass_context
def solve_group(
    ctx: click.Context,
    input_data: str | None,
    input_type: InputType,
    walls: int,
) -> None:
    """Solve the enclose horse problem."""
    ctx.ensure_object(dict)

    # Build GridInput with explicit mode
    try:
        grid_input = GridInput(input_data, mode=input_type)
    except click.BadParameter as e:
        raise click.UsageError(str(e))

    # Store in context
    ctx.obj["grid_input"] = grid_input
    ctx.obj["input_type"] = input_type
    ctx.obj["walls"] = walls

    if ctx.invoked_subcommand is not None:
        return

    # Run default solver
    default_cls = SOLVER_REGISTRY[DEFAULT_SOLVER_NAME]
    solver_context = SolverContext(
        grid_rows=grid_input.iter_rows(),
        max_walls=walls,
    )
    default_solver = default_cls(context=solver_context)
    solution = default_solver.solve()

    click.echo(str(solution))


# Register all solvers as subcommands
for solver_name in SOLVER_REGISTRY:
    solve_group.add_command(make_solver_command(solver_name), solver_name)

if __name__ == "__main__":
    cli()
