from typing import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SolverContext:
    grid_rows: Iterable[Sequence[str]]
    max_walls: int
