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

    _CELL_DISPLAY_SYMBOLS: ClassVar[frozendict[GridCellType, str]] = frozendict(
        {
            GridCellType.GRASS: "🌱",
            GridCellType.CHERRY: "🍒",
            GridCellType.APPLE: "🍎",
            GridCellType.BEES: "🐝",
            GridCellType.HORSE: "🐴",
            GridCellType.WATER: "🌊",
            GridCellType.PORTAL: "🌀",
        }
    )

    @classmethod
    def determine_type(cls, symbol: str) -> GridCellType:
        cell_type = cls._GRID_SYMBOLS.get(symbol)
        if cell_type is None:
            if symbol.isdigit():
                return GridCellType.PORTAL
            raise ValueError(f"Unrecognizable grid symbol: {symbol}")
        return cell_type

    @classmethod
    def create_grid_cell(cls: type[T], symbol: str) -> T:
        cell_type = cls.determine_type(symbol=symbol)
        if cell_type is GridCellType.PORTAL:
            if not symbol.isdigit():
                raise ValueError(
                    f"Cell recognized as {cell_type} but is not and integer"
                )
            return cls(type_=cell_type, portal_group=int(symbol))
        return cls(type_=cell_type)

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

    @classmethod
    def get_display_symbol(
        cls, type_: GridCellType, portal_group: int | None = None
    ) -> str:
        dsymbol = cls._CELL_DISPLAY_SYMBOLS.get(type_)
        if dsymbol is None:
            raise ValueError(
                f"Cannot determine display symbol for grid cell type: {type_}"
            )
        return dsymbol
