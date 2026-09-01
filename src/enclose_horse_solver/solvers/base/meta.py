from typing import Any
import re
from abc import ABCMeta
from .._registry import SOLVER_REGISTRY
from .context import SolverContext
from .params import SolverParam

POSIX_CMD_REGEX = r"^[a-zA-Z_][a-zA-Z0-9_]*$"


class SolverMeta(ABCMeta):
    """
    Metaclass for BaseSolver.

    - If `solver_name` is provided: collect params, generate __init__, register.
    - If `solver_name` is not provided: skip registration (abstract/intermediate class).

    IMPORTANT: `solver_name` must be a POSIX compliant name for a command.
    """

    def __new__(  # type: ignore[no-untyped-def]
        mcs, name, bases, namespace, solver_name: str | None = None, **kwargs
    ):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Skip the base class itself
        if name == "BaseSolver":
            return cls

        # Only process if solver_name is explicitly provided
        if solver_name is not None:

            if not bool(re.match(POSIX_CMD_REGEX, name)):
                raise ValueError(
                    f'Provided `solver_name` = "{solver_name}" is not POSIX compliant '
                    f'("{POSIX_CMD_REGEX}")'
                )
            # Collect SolverParam instances from the class hierarchy
            params = {}
            for base in reversed(cls.__mro__):
                for attr_name, attr_value in vars(base).items():
                    if isinstance(attr_value, SolverParam):  # type: ignore[arg-type]
                        params[attr_name] = attr_value

            cls._solver_params = params  # type: ignore[attr-defined]

            # Generate __init__
            def __init__(  # type: ignore[no-untyped-def]
                self, context: SolverContext, **kwargs: Any
            ) -> None:
                self.context = context
                for param_name, param in params.items():
                    if param_name in kwargs:
                        setattr(self, param_name, kwargs[param_name])
                    elif param.default is not ...:
                        setattr(self, param_name, param.default)
                    elif param.required:
                        raise TypeError(
                            f"Missing required solver parameter: {param_name}"
                        )
                    else:
                        setattr(self, param_name, None)

            cls.__init__ = __init__  # type: ignore

            # Register
            if solver_name in SOLVER_REGISTRY:
                raise ValueError(f"Solver '{solver_name}' is already registered")

            SOLVER_REGISTRY[solver_name] = cls
            cls._solver_name = solver_name  # type: ignore[attr-defined]
        else:
            # No name provided — abstract/intermediate class, skip registration
            cls._solver_params = {}  # type: ignore[attr-defined]

        return cls
