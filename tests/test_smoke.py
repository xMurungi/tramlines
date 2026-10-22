"""Phase 0 smoke tests: the toolchain works and the package imports."""

import sys

import torch

import tramlines
import tramlines.brain.data


def test_python_is_312() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_package_imports() -> None:
    assert tramlines.__doc__
    assert tramlines.brain.data.COMPLETENESS_FILE.endswith("_783.csv")


def test_torch_float64_on_cpu() -> None:
    # Determinism mode (ADR-0007) runs on CPU in float64; make sure that combination works.
    x = torch.ones(3, dtype=torch.float64)
    assert x.sum().item() == 3.0
