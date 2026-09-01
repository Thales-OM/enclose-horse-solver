"""PyInstaller entry point for the packaged horse-cli binary.

The real CLI module (`enclose_horse_solver.cli`) uses relative imports, so
PyInstaller must load it as a package module rather than as a standalone
script. This thin wrapper imports it and hands over to the Click group.

stdout/stderr are forced to UTF-8 because the CLI renders emoji tiles; without
this, a one-file binary run against a piped/redirected stream falls back to the
locale codepage (e.g. cp1252 on Windows) and crashes while printing a solution.
"""

import sys

from enclose_horse_solver.cli import cli

if __name__ == "__main__":
    sys.stdout.reconfigure(  # pyright: ignore[reportAttributeAccessIssue]
        encoding="utf-8", errors="replace"
    )
    sys.stderr.reconfigure(  # pyright: ignore[reportAttributeAccessIssue]
        encoding="utf-8", errors="replace"
    )
    cli()
