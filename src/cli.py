import click
import io
import os
import sys
from typing import Iterator, Tuple, Union, Generator, List
from .solvers.standard import standard_solver
from .solvers.base import BaseSolverOuput


def draw_grid(solver_output: BaseSolverOuput) -> None:
    grid = [
        ["🌱" for _ in range(solver_output.grid_width)]
        for _ in range(solver_output.grid_height)
    ]
    for wall in solver_output.result.walls_to_place:
        grid[wall[0]][wall[1]] = "🧱"
    for enclosure in solver_output.result.enclosed_tiles:
        grid[enclosure[0]][enclosure[1]] = "🔆"
    grid[solver_output.horse[0]][solver_output.horse[1]] = "🐴"
    output = "\n".join(" ".join([cell for cell in row]) for row in grid)
    print(output)


class WallCostType(click.ParamType):  # type: ignore[type-arg]
    """Parses wall cost as int or comma-separated ints."""

    name = "wall_cost"

    def convert(  # type: ignore[no-untyped-def]
        self, value, param, ctx
    ) -> int | Tuple[int, ...]:
        if isinstance(value, (int, tuple)):
            return value

        value = str(value).strip()
        if "," in value:
            parts = value.split(",")
            try:
                costs = tuple(int(p.strip()) for p in parts)
            except ValueError:
                self.fail(f"Invalid wall cost format: {value}", param, ctx)
            if any(c < 0 for c in costs):
                self.fail("All wall costs must be >= 0", param, ctx)
            return costs
        else:
            try:
                cost = int(value)
            except ValueError:
                self.fail(f"Invalid wall cost: {value}", param, ctx)
            if cost < 0:
                self.fail(f"Wall cost must be >= 0, got {cost}", param, ctx)
            return cost


def stream_grid_lines(lines: Iterator[str]) -> Iterator[List[str]]:
    """
    Stream grid lines with on-the-fly validation.
    Yields lines as parsed List of strings.
    """
    expected_width = None

    for row_idx, line in enumerate(lines):
        line = line.rstrip("\n\r")
        if not line:
            continue

        if "  " in line:
            raise click.BadParameter(
                f"Line {row_idx + 1}: consecutive spaces not allowed"
            )

        cells = line.split(" ")

        if expected_width is None:
            expected_width = len(cells)
        elif len(cells) != expected_width:
            raise click.BadParameter(
                f"Line {row_idx + 1}: expected {expected_width} cells, got {len(cells)}"
            )

        yield cells

    if expected_width is None:
        raise click.BadParameter("Empty grid")


def get_grid_stream_from_file(file_path: str) -> Iterator[List[str]]:
    """Stream grid from file without loading into memory."""
    if not os.path.isfile(file_path):
        raise click.BadParameter(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        yield from stream_grid_lines(f)


def get_grid_stream_from_string(grid_str: str) -> Iterator[List[str]]:
    """Stream grid from string."""
    source = io.StringIO(grid_str)
    yield from stream_grid_lines(source)


def get_grid_stream_interactive() -> Iterator[List[str]]:
    """Stream grid from interactive input."""
    click.echo("Enter grid (empty line to finish):")

    def line_generator() -> Generator[str, None, None]:
        while True:
            try:
                line = input()
                if not line:
                    break
                yield line
            except EOFError:
                break

    yield from stream_grid_lines(line_generator())


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
    walls: int,
    wall_cost: Union[int, Tuple[int, ...]],
) -> None:
    """Solve the enclose horse problem."""
    ctx.ensure_object(dict)

    if isinstance(wall_cost, tuple) and len(wall_cost) != walls:
        raise click.BadParameter(
            f"wall-cost length ({len(wall_cost)}) must equal walls ({walls})"
        )

    try:
        if input_data is None:
            grid_stream = get_grid_stream_interactive()
        elif input_data == "-":
            grid_stream = stream_grid_lines(sys.stdin)
        elif os.path.isfile(input_data):
            grid_stream = get_grid_stream_from_file(input_data)
        else:
            grid_stream = get_grid_stream_from_string(input_data)
    except click.BadParameter as e:
        raise click.UsageError(str(e))

    ctx.obj["grid_stream"] = grid_stream
    ctx.obj["walls"] = walls
    ctx.obj["wall_cost"] = wall_cost

    if ctx.invoked_subcommand is not None:
        return

    # Default solver
    click.echo(f"🔮 Running default solver with {walls} walls...")

    result = standard_solver(
        input_lines=grid_stream, max_walls=walls, wall_costs=wall_cost
    )
    print(result.result)
    print()
    print("Grid:")
    draw_grid(solver_output=result)
    click.echo("✓ Processed rows")


# @solve_group.command(name="example")
# @click.pass_context
# def example_subcommand(ctx: click.Context) -> None:
#     """Example subcommand."""
#     walls = ctx.obj["walls"]
#     grid_stream = ctx.obj["grid_stream"]

#     click.echo(f"🔮 Running example with {walls} walls...")

#     row_count = 0
#     for row_idx, cells in grid_stream:
#         row_count += 1
#         # Process row

#     click.echo(f"✓ Processed {row_count} rows")


if __name__ == "__main__":
    cli()
