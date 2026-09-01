"""
Solver package. Auto-discovers and registers all solver modules on import.
"""

import pkgutil
import importlib
from pathlib import Path
from ._registry import SOLVER_REGISTRY

DEFAULT_SOLVER_NAME = "standard"

__all__ = ["SOLVER_REGISTRY", "DEFAULT_SOLVER_NAME"]

# Scan all modules in this package and import them
# This triggers all SolverMeta metaclass calls
package_dir = Path(__file__).parent
# TODO: Add iteration over submodules, so that developers
#   don't have to bring Solver classes up to top-level modules
for module_info in pkgutil.iter_modules([str(package_dir)]):
    importlib.import_module(f"{__name__}.{module_info.name}")
