"""Every program in The Book runs and prints exactly what the chapter says it prints.

Convention (CLAUDE.md section 12.5): `book/chNN/name.py` is a program from chapter NN,
and `book/chNN/name.expected` holds its exact expected output. A chapter whose
code fails is a failing build.
"""

import subprocess
import sys
from pathlib import Path

import pytest

BOOK = Path(__file__).resolve().parent.parent / "book"
PROGRAMS = sorted(p for p in BOOK.glob("ch*/*.py") if p.with_suffix(".expected").exists())


@pytest.mark.parametrize("program", PROGRAMS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_book_program_output(program: Path) -> None:
    result = subprocess.run(
        [sys.executable, program.name],
        cwd=program.parent,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == program.with_suffix(".expected").read_text()


def test_book_has_programs() -> None:
    assert PROGRAMS, "The Book should contain at least one tested program"
