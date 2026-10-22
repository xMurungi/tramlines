"""Every program in The Book runs and prints exactly what the chapter says it prints.

Convention (CLAUDE.md section 12.5): `book/chNN/name.py` is a program from chapter NN,
and `book/chNN/name.expected` holds its exact expected output. A chapter whose
code fails is a failing build. Programs whose first line is `# book: needs-data`
read the FlyWire files through `book/data` and are skipped, visibly, without them.
"""

import subprocess
import sys
from pathlib import Path

import pytest

BOOK = Path(__file__).resolve().parent.parent / "book"
PROGRAMS = sorted(p for p in BOOK.glob("ch*/*.py") if p.with_suffix(".expected").exists())
HAVE_DATA = (BOOK / "data" / "Connectivity_783.parquet").exists()


@pytest.mark.parametrize("program", PROGRAMS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_book_program_output(program: Path) -> None:
    if program.read_text().startswith("# book: needs-data") and not HAVE_DATA:
        pytest.skip("run `uv run python scripts/fetch_data.py` first")
    result = subprocess.run(
        [sys.executable, program.name],
        cwd=program.parent,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == program.with_suffix(".expected").read_text()


def test_book_has_programs() -> None:
    assert PROGRAMS, "The Book should contain at least one tested program"
