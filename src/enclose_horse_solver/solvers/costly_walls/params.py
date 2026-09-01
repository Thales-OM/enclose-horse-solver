import click
from typing import Tuple


class WallCostType(click.ParamType[int | Tuple[int, ...]]):
    """
    Parses wall cost as int or comma-separated ints.
    Allows single per-wall cost, or a somma-separated
        sequence of marginal costs for each subsequent wall.
    """

    name = "wall_cost"

    def convert(  # type: ignore[no-untyped-def]
        self, value, param, ctx
    ) -> int | Tuple[int, ...]:
        if isinstance(value, (int, tuple)):
            return value

        value = str(value).strip()
        if "," in value:
            parts = value.split(",")
            try:
                costs = tuple(int(p.strip()) for p in parts)
            except ValueError:
                self.fail(f"Invalid wall cost format: {value}", param, ctx)
            if any(c < 0 for c in costs):
                self.fail("All wall costs must be >= 0", param, ctx)
            return costs
        else:
            try:
                cost = int(value)
            except ValueError:
                self.fail(f"Invalid wall cost: {value}", param, ctx)
            if cost < 0:
                self.fail(f"Wall cost must be >= 0, got {cost}", param, ctx)
            return cost
