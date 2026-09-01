# Enclose Horse Solver

CLI tool that finds the **optimal** solution to a daily [enclose.horse](https://enclose.horse/) puzzle: place at most `N` walls on grass so that the horse is trapped inside a pen and the enclosed tiles score the maximum possible points.

```
# Standard (default) solver, 16 walls available
horse-cli solve -w 16 path/to/grid.txt

# Solver-specific parameters via subcommands
horse-cli solve -w 16 grid.txt costly-walls -c 2
```

## Game rules modelled

- Cells: **grass** (`g`), **water** (`w`), **cherry** (`c` +3), **apple** (`a` +10), **bees** (`b` −5), the **horse** (`h`), and **portals** (any digit; equal digits are a linked pair). Base points are per enclosed `GridCell.points_inside` (`src/enclose_horse_solver/solvers/standard/grid.py`).
- Movement is 4-directional (von Neumann). **Water blocks movement for free** (it is a barrier that costs nothing), walls block movement too, and walls may **only be placed on grass**.
- The horse must be fully trapped — its reachable region (water + walls block it) must **not** touch the grid border.
- **Portals** teleport the horse between same-numbered cells and act as *non-neighbour movements* in the model.

## Installation

Requires **Python 3.11+**. The project uses Poetry and a `src/` layout.

```bash
poetry install
poetry run horse-cli --help
```

### Windows note

The CLI renders emoji grid output, so on Windows run it with UTF-8 to avoid a `cp1252` printing crash:

```powershell
$env:PYTHONIOENCODING='utf-8'
poetry run horse-cli solve -w 16 tests/assets/test2.txt
```

## Architecture

The project is split between a small domain-agnostic I/O layer and a pluggable solver registry.

```
src/enclose_horse_solver/
├── cli.py            # Click entry point (console script: horse-cli)
├── cmd_factory.py    # Builds a Click subcommand from a Solver's declared params
├── input/grid.py     # Rectangular grid parsing: string / file / stdin / interactive
└── solvers/
    ├── _registry.py          # SOLVER_REGISTRY: name -> Solver class
    ├── base/                 # AbstractSolver plumbing
    │   ├── meta.py           # SolverMeta metaclass — param collection, __init__, registration
    │   ├── solver.py         # BaseSolver abstract interface
    │   ├── context.py        # SolverContext (grid_rows, max_walls)
    │   ├── output.py         # BaseSolverOuput dataclass
    │   └── params.py         # SolverParam — declare CLI params as class attributes
    ├── standard/             # Default ("standard") solver
    │   ├── grid.py           # GridCellType enum + GridCell symbol/points model
    │   ├── optimizer.py      # MILP (PuLP) weighted enclosure model
    │   └── solver.py         # StandardSolver + shared build_grid_summary()
    └── costly_walls/         # Per-wall cost extension solver
```

**Flow:** `cli.py` parses the grid via `GridInput` → the chosen `Solver.solve()` parses rows with `build_grid_summary()` (the one canonical scan step shared by all solvers) → the optimizer builds a **PuLP MILP** (`solve_weighted_enclose_horse`, `src/enclose_horse_solver/solvers/standard/optimizer.py`) that simultaneously decides which walls to place and which tiles to enclose → results are returned as a dataclass and rendered with `str()`.

Every solver returns output derived from `BaseSolverOuput` (`success`, `max_score`, `walls_to_place`, `status_desc`); `StandardSolverOutput` also exposes `processed_grid` and `enclosed_tiles`.

## Building

Release automation (`.github/workflows/release.yml`) triggers on `v*` tags and builds all of the following:

- **Binaries** — one-file PyInstaller executables on Linux, Windows and macOS:
  `pyinstaller --onefile --clean --noconfirm --paths src --name horse-solver-<os>-x64 src/enclose_horse_solver/cli.py`
- **Python package** — `python -m build` produces an `sdist` + wheel.
- **Docker image** — multi-stage Poetry build published to GHCR. Note the builder installs the root package (`poetry install --only main`, with `src/` copied in) so the runtime `ENTRYPOINT ["python", "-m", "enclose_horse_solver.cli"]` resolves; a `.dockerignore` keeps the host `.venv` and caches out of the image.

All artifacts are attached to the GitHub Release for the tag.

## Development

```bash
poetry install --with dev     # dev extras: pytest, black, flake8, pre-commit
poetry run pre-commit run --all-files
poetry run pytest
```

Golden puzzle fixtures live in `tests/assets/` as `(testN.txt, wallsN.txt)` pairs; expected scores are asserted programmatically in `tests/test_puzzles.py`.

## Writing a solver plugin

Solvers are auto-discovered and auto-registered — no manual wiring needed.

1. **Create a subpackage** `src/enclose_horse_solver/solvers/<your_solver>/` with a module that defines your solver class. The `solvers/__init__.py` imports every module in the package on import, which fires the metaclass registration.

2. **Declare the solver** — subclass `BaseSolver` and pass a POSIX-compliant `solver_name`:

   ```python
   from ..base import BaseSolver, SolverParam

   class MySolver(BaseSolver, solver_name="my-solver"):
       """Enclose the horse using my strategy."""

       threshold = SolverParam(
           "-t", "--threshold",
           type=int, default=5, help="Minimum enclosure size",
       )

       def solve(self):
           # self.context.grid_rows, self.context.max_walls, self.threshold
           # -> return a BaseSolverOuput (or a subclass)
           ...
   ```

   - `SolverParam` transparently becomes a Click option (int/float/bool/str, `choices`, flag, required). Not giving `solver_name` marks the class as **intermediate** — handy for shared base classes — and it won't be registered.
   - **You can also pass your own `click.ParamType` subclass** as `SolverParam(type=...)` for custom parsing/validation (e.g. comma-separated lists). See `WallCostType` in `costly_walls/params.py`; you just implement `convert(value, param, ctx)` and call `self.fail(...)` on invalid input.

3. **Reuse the shared grid scan** via `build_grid_summary(self.context.grid_rows)` (from `..standard.solver`); it returns a validated `GridSummary` plus the portal map.

Because registration is driven by the metaclass, new solvers light up as `solve` subcommands (`horse-cli solve -w N ... my-solver`) and in the `SOLVER_REGISTRY` without touching the CLI.

### The `SolverContext` object

Each solver receives its problem input through `self.context` — a frozen dataclass with two fields:

```python
@dataclass(frozen=True)
class SolverContext:
    grid_rows: Iterable[Sequence[str]]  # rows of raw symbols ("g", "h", "0", ...)
    max_walls: int                     # the -w/--walls budget from the CLI
```

- `grid_rows` is a **lazy iterator** of raw symbol rows. Pass it to `build_grid_summary(self.context.grid_rows)` exactly once — it is consumed as it streams, so do not iterate it twice.
- `max_walls` is the wall budget passed via `-w/--walls`.
- Only these two attributes are guaranteed to exist; don't reach for anything else on `self.context`.

### Private attributes are fine

Only attributes declared as `SolverParam` class attributes are treated as CLI parameters and set from `kwargs`. Any other instance attributes you create (in `__init__` or lazily inside `solve()`) are purely internal — use them freely for caches, precomputed tables, solver state, and so on. They are neither exposed as CLI options nor overwritten by the metaclass.

### Custom output

Every solver returns an object derived from `BaseSolverOuput`:

```python
@dataclass
class BaseSolverOuput:
    success: bool
    max_score: int | None
    walls_to_place: List[Tuple[int, int]] | None
    status_desc: str | None = None

    def __str__(self) -> str:  # default rendering
        ...
```

The CLI prints a solution by calling `str(result)` (see `cmd_factory.py`), so **your output class controls exactly how a solution is printed**. To add fields safely, inherit from `BaseSolverOuput` (or `StandardSolverOutput`) and extend — the base `success` / `max_score` / `walls_to_place` / `status_desc` fields stay compatible with the CLI and the test suite:

```python
@dataclass
class MyOutput(BaseSolverOuput):
    my_extra: int = 0

    def __str__(self) -> str:
        if not self.success:
            return f"Failed: {self.status_desc}"
        return f"Max Score: {self.max_score} (extra={self.my_extra})"
```

If you keep the default `BaseSolverOuput.__str__`, note it only prints `Max Score` and `Walls` — **no grid**. For the emoji-grid rendering, either subclass `StandardSolverOutput` (which adds `processed_grid` and `enclosed_tiles` and draws the board) or override `__str__` yourself. The contract is: read `success` first, then render a readable representation of the solution.

## License

[MIT](LICENSE)
