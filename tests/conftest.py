"""Every test runs in determinism mode, the only mode a Brain accepts (ADR-0007, ADR-0021)."""

from tramlines.brain.engine import enable_determinism

enable_determinism()
