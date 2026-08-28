from typing import Iterable, Sequence, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class BaseSolverOuput(ABC):
    success: bool
    max_score: int | None
    walls_to_place: List[Tuple[int, int]] | None
    status_desc: str | None = None

    @abstractmethod
    def __str__(self) -> str:
        """
        Printable string representation of a solution.
        Must be Implemented by children.
        """
        raise NotImplementedError(
            "Critcal Error: Calling super() on this abstract method is forbidden."
        )


@dataclass(frozen=True)
class SolverContext:
    grid_rows: Iterable[Sequence[str]]
    max_walls: int
    wall_costs: int | Sequence[int] = 0


class BaseSolver(ABC):
    @abstractmethod
    def solve(self, context: SolverContext) -> BaseSolverOuput:
        """
        Produce a perfect solution given parsed grid input.
        Must be Implemented by children.
        """
        raise NotImplementedError(
            "Critcal Error: Calling super() on this abstract method is forbidden."
        )
