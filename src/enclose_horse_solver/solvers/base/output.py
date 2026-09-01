from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class BaseSolverOuput:
    """
    Dataclass representing Solver solution output.
    Can be used by Solver implementations as is, or inherited from and modified.
    When displaying a solution `str()` is called on class instance.
    """

    success: bool
    max_score: int | None
    walls_to_place: List[Tuple[int, int]] | None
    status_desc: str | None = None

    def __str__(self) -> str:
        """
        Printable string representation of a solution.
        """
        if not self.success:
            return f"Failed to find a solution. Reason: {self.status_desc or 'Unknown'}"
        return (
            "Solution found ✅\n"
            f"Max Score: {self.max_score}\n"
            f"Walls: {self.walls_to_place}\n\n"
        )
