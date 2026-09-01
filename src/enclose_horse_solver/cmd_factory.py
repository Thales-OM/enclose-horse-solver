from typing import Dict, TypeVar, Any
import click
from .solvers import SOLVER_REGISTRY
from .solvers.base.context import SolverContext

_T = TypeVar("_T")


def _infer_click_type(
    py_type: click.ParamType[_T] | type,
) -> click.ParamType[_T] | type:
    if py_type is int:
        return int
    if py_type is float:
        return float
    if py_type is bool:
        return bool
    return str


def make_default_option_long_name(param_name: str) -> str:
    return "--" + param_name.replace("_", "-")


def build_click_options_for(solver_cls: type) -> list[click.Option]:
    """Build Click options from SolverParam class attributes."""
    options: list[click.Option] = []

    solver_params: Dict[str, type] | None = getattr(  # noqa: B009
        solver_cls, "_solver_params"
    )
    if solver_params is None:
        raise RuntimeError(
            f"._solver_params was not found on Solver class: {solver_cls.__name__}"
        )
    for _, param in solver_params.items():
        click_type = param.type  # type: ignore[attr-defined]
        choices = param.choices  # type: ignore[attr-defined]
        is_flag = param.is_flag  # type: ignore[attr-defined]

        if choices:
            click_type = click.Choice(choices, case_sensitive=False)
        elif not isinstance(click_type, click.ParamType):
            click_type = _infer_click_type(click_type)

        default = None
        if param.default is not ...:  # type: ignore[attr-defined]
            default = param.default  # type: ignore[attr-defined]

        if is_flag or click_type is bool:
            options.append(
                click.Option(
                    param.param_decls,  # type: ignore[attr-defined]
                    is_flag=True,
                    default=bool(default) if default is not None else False,
                    help=param.help,  # type: ignore[attr-defined]
                )
            )
        else:
            options.append(
                click.Option(
                    param.param_decls,  # type: ignore[attr-defined]
                    type=click_type,
                    default=default,
                    required=param.required,  # type: ignore[attr-defined]
                    help=param.help,  # type: ignore[attr-defined]
                )
            )

    return options


def get_solver_param_names(solver_cls: type) -> list[str]:
    solver_params: Dict[str, type] | None = getattr(  # noqa: B009
        solver_cls, "_solver_params"
    )
    if solver_params is None:
        raise RuntimeError(
            f"._solver_params was not found on Solver class: {solver_cls.__name__}"
        )
    return list(solver_params.keys())


# ---------------------------------------------------------------------------
# Subcommand factory
# ---------------------------------------------------------------------------


def make_solver_command(name: str) -> click.Command:
    """Build a Click subcommand for a registered solver."""
    solver_cls = SOLVER_REGISTRY[name]
    solver_options = build_click_options_for(solver_cls)
    solver_param_names = get_solver_param_names(solver_cls)

    def callback(ctx: click.Context, **kwargs: Any) -> None:
        grid_input = ctx.obj["grid_input"]
        walls = ctx.obj["walls"]

        solver_context = SolverContext(
            grid_rows=grid_input.iter_rows(),
            max_walls=walls,
        )

        solver_kwargs = {k: v for k, v in kwargs.items() if k in solver_param_names}

        # Instantiate solver with context + solver params
        solver = solver_cls(context=solver_context, **solver_kwargs)

        click.echo(f"🔮 Running '{name}' solver...")
        result = solver.solve()
        click.echo(str(result))

    cmd = click.Command(
        name=name,
        callback=click.pass_context(callback),
        help=solver_cls.__doc__ or f"Run the {name} solver.",
    )

    for opt in solver_options:
        cmd.params.append(opt)

    return cmd
