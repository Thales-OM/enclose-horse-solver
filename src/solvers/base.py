from typing import Callable, Iterable, Sequence, Tuple
from dataclasses import dataclass
from ..optimizers import EnclosureResult


@dataclass
class BaseSolverOuput:
    result: EnclosureResult
    grid_width: int
    grid_height: int
    horse: Tuple[int, int]


GridInputLines = Iterable[Sequence[str]]
BaseSolver = Callable[[GridInputLines, int, int | Sequence[int]], BaseSolverOuput]
