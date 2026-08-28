from typing import ClassVar, TypeVar
from enum import Enum
from dataclasses import dataclass
from frozendict import frozendict

T = TypeVar("T", bound="GridCell")


class GridCellType(str, Enum):
    GRASS = "grass"
    WATER = "water"
    CHERRY = "cherry"
    APPLE = "apple"
    BEES = "bees"
    PORTAL = "portal"
    HORSE = "horse"


@dataclass(frozen=True)
class GridCell:
    type_: GridCellType
    portal_group: int | None = None

    # Item points (e.g. bees = -5, cherries = +3) added to default cell points
    _POINTS_MAP: ClassVar[frozendict[GridCellType, int]] = frozendict(
        {
            GridCellType.GRASS: 1,
            GridCellType.CHERRY: 4,
            GridCellType.APPLE: 11,
            GridCellType.BEES: -4,
            GridCellType.PORTAL: 1,
            GridCellType.HORSE: 1,
            GridCellType.WATER: 0,
        }
    )

    # Portals are represented by numbers, same numbers = portal pair
    # Portals type resolution happens dynamically whithin .create_grid_cell()
    _GRID_SYMBOLS: ClassVar[frozendict[str, GridCellType]] = frozendict(
        {
            "g": GridCellType.GRASS,
            "c": GridCellType.CHERRY,
            "a": GridCellType.APPLE,
            "b": GridCellType.BEES,
            "h": GridCellType.HORSE,
            "w": GridCellType.WATER,
        }
    )

    @classmethod
    def create_grid_cell(cls: type[T], symbol: str) -> T:
        cell_type = cls._GRID_SYMBOLS.get(symbol)
        if cell_type is not None:
            return cls(type_=cell_type)
        if symbol.isdigit():
            return cls(type_=GridCellType.PORTAL, portal_group=int(symbol))
        raise ValueError(f"Unrecognizable grid symbol: {symbol}")

    @property
    def is_enclosable(self) -> bool:
        if self.type_ in (
            GridCellType.GRASS,
            GridCellType.CHERRY,
            GridCellType.APPLE,
            GridCellType.BEES,
            GridCellType.PORTAL,
            GridCellType.HORSE,
        ):
            return True
        return False

    @property
    def can_place_wall(self) -> bool:
        if self.type_ in (GridCellType.GRASS,):
            return True
        return False

    @property
    def points_inside(self) -> int:
        points = self._POINTS_MAP.get(self.type_)
        if points is None:
            raise ValueError(
                f"Cannot determine points value for a grid cell type = {self.type_}"
            )
        return points
