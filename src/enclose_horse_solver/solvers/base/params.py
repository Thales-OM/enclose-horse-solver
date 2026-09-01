import builtins
from typing import TYPE_CHECKING, TypeVar, Any, overload, Iterable
import click

_T = TypeVar("_T")

if TYPE_CHECKING:
    # Type-checker overloads
    @overload
    def SolverParam(
        *param_decls: str,
        type: type[_T],
        default: _T = ...,
        help: str = "",
        choices: Iterable[Any] | None = None,
        required: bool = False,
        is_flag: bool = False,
    ) -> _T: ...

    @overload
    def SolverParam(
        *param_decls: str,
        type: click.ParamType[_T],
        default: Any = ...,
        help: str = "",
        choices: Iterable[Any] | None = None,
        required: bool = False,
        is_flag: bool = False,
    ) -> _T: ...

    # Implementation stub
    def SolverParam(
        *param_decls: str,
        type: Any,
        default: Any = ...,
        help: str = "",
        choices: Iterable[Any] | None = None,
        required: bool = False,
        is_flag: bool = False,
    ) -> Any:
        """Type-checker stub."""
        ...

else:
    # Runtime definition and implementation
    class SolverParam:
        """
        Declare a solver-specific CLI parameter as a class attribute.

        Usage:
            class MySolver(BaseSolver):
                threshold = SolverParam(int, default=5, help="Min points")
        """

        def __init__(
            self,
            *param_decls: str,
            type: click.ParamType | builtins.type,  # type: ignore[type-arg]
            default: Any = ...,
            help: str = "",
            choices: Iterable[str] | None = None,
            required: bool = False,
            is_flag: bool = False,
        ):
            self.param_decls = list(param_decls)
            self.type = type
            self.default = default
            self.help = help
            self.choices = choices
            self.required = required
            self.is_flag = is_flag
