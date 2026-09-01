import click
import io
import os
import sys
from typing import Iterator, List, Literal
from collections.abc import Generator, Iterable
from contextlib import contextmanager

InputType = Literal["string", "file", "stdin", "interactive", "auto"]


class GridInput:
    """
    Domain-agnostic grid input handler.
    Provides streaming access to parsed grid data without domain-specific knowledge.
    """

    def __init__(self, input_data: str | None, mode: InputType = "auto"):
        """
        Args:
            input_data: Grid data (string, file path, or None for interactive)
            mode: "auto" (detect), "string", "file", "stdin", or "interactive"
        """
        self._input_data = input_data
        self._mode = mode
        self._width: int | None = None
        self._height: int | None = None

        # Detect mode
        if mode == "auto":
            if input_data is None:
                self._mode = "interactive"
            elif os.path.isfile(input_data):
                self._mode = "file"
            else:
                self._mode = "string"

    @contextmanager
    def _get_line_iterator(self) -> Generator[Iterable[str], None, None]:
        """
        Context manager, handles stream open/closure.
        Yields a line iterable based on input mode.
        """
        if self._mode == "interactive":
            yield self._interactive_lines()
        elif self._mode == "stdin":
            yield sys.stdin
        elif self._mode == "file":
            if not os.path.isfile(self._input_data or ""):
                raise click.BadParameter(f"File not found: {self._input_data}")
            with open(self._input_data or "", "r") as input_file:
                yield input_file
        elif self._mode == "string":
            yield io.StringIO(self._input_data)
        else:
            raise ValueError(f"Unknown mode: {self._mode}")

    def _interactive_lines(self) -> Generator[str, None, None]:
        """Generator for interactive input."""
        click.echo("Enter grid (empty line to finish):")
        while True:
            try:
                line = input()
                if not line:
                    break
                yield line
            except EOFError:
                break

    def iter_lines(self) -> Generator[str, None, None]:
        """
        Stream raw lines with validation.
        Validates rectangular shape and no consecutive spaces.
        """
        expected_width = None
        expected_height = 0

        with self._get_line_iterator() as line_iterator:
            for line_num, raw_line in enumerate(line_iterator):
                expected_height += 1
                line = raw_line.rstrip("\n\r")
                if not line:
                    continue

                # Validate no consecutive spaces
                if "  " in line:
                    raise click.BadParameter(
                        f"Line {line_num}: consecutive spaces not allowed"
                    )

                # Validate rectangular shape
                row = line.split(" ")
                if expected_width is None:
                    expected_width = len(row)
                elif len(row) != expected_width:
                    raise click.BadParameter(
                        f"Line {line_num}: expected {expected_width} cells, "
                        f"got {len(row)}"
                    )

                yield line

        if expected_width is None:
            raise click.BadParameter("Empty grid")

        self._width = expected_width
        self._height = expected_height

    def iter_rows(self) -> Iterator[List[str]]:
        """
        Stream parsed rows from a rectangular grid.
        """
        for line in self.iter_lines():
            yield line.split(" ")

    @property
    def width(self) -> int:
        """Grid width. Only available after iteration."""
        if self._width is None:
            raise RuntimeError("Grid dimensions not yet determined. Iterate first.")
        return self._width

    @property
    def height(self) -> int:
        """Grid height. Only available after iteration."""
        if self._height is None:
            raise RuntimeError("Grid dimensions not yet determined. Iterate first.")
        return self._height

    def __repr__(self) -> str:
        if self._width is not None and self._height is not None:
            return f"GridInput({self._width}x{self._height})"
        return f"GridInput(mode={self._mode})"
