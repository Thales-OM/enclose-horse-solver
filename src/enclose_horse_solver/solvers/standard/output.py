from typing import Tuple, Sequence, Set
from dataclasses import dataclass, field
from ..base import BaseSolverOuput
from .grid import GridCellType, GridCell


@dataclass(kw_only=True)
class StandardSolverOutput(BaseSolverOuput):
    processed_grid: Sequence[Sequence[Tuple[GridCellType, int | None]]]
    enclosed_tiles: Sequence[Tuple[int, int]]

    _enclosed_tiles_lookup: Set[Tuple[int, int]] = field(init=False, repr=False)
    _walls_lookup: Set[Tuple[int, int]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._enclosed_tiles_lookup = set(self.enclosed_tiles)
        self._walls_lookup = (
            set(self.walls_to_place) if self.walls_to_place is not None else set()
        )

    def get_display_symbol(
        self,
        type_: GridCellType,
        coords: Tuple[int, int],
        portal_group: int | None = None,
    ) -> str:
        if type_ is not GridCellType.HORSE:
            if coords in self._enclosed_tiles_lookup:
                return "🔆"
            if coords in self._walls_lookup:
                return "🧱"
        return GridCell.get_display_symbol(type_=type_, portal_group=portal_group)

    def __str__(self) -> str:
        if not self.success:
            return f"Failed to find a solution.\nReason: {self.status_desc}"

        display_grid = "\n".join(
            " ".join(
                self.get_display_symbol(
                    type_=cell_type,
                    coords=(row_idx, col_idx),
                    portal_group=portal_group,
                )
                for col_idx, (cell_type, portal_group) in enumerate(row)
            )
            for row_idx, row in enumerate(self.processed_grid)
        )

        return (
            f"Max Score: {self.max_score}\n"
            f"Walls: {self.walls_to_place}\n\n"
            f"{display_grid}"
        )
