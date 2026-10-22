"""The fetch script's checksum logic, tested without the network."""

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "fetch_data.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("fetch_data", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look their module up here
    spec.loader.exec_module(module)
    return module


def test_every_file_is_pinned_to_a_commit_and_hash() -> None:
    fetch = load_script()
    for entry in fetch.FILES:
        assert fetch.SHIU_COMMIT in entry.url
        assert len(entry.sha256) == 64


def test_is_valid_rejects_wrong_bytes(tmp_path: Path) -> None:
    fetch = load_script()
    good = b"a fly brain"
    entry = fetch.DataFile("x.bin", "unused", hashlib.sha256(good).hexdigest(), len(good))
    path = tmp_path / "x.bin"
    path.write_bytes(good)
    assert fetch.is_valid(path, entry)
    path.write_bytes(b"a fly brain, corrupted")
    assert not fetch.is_valid(path, entry)
    assert not fetch.is_valid(tmp_path / "missing.bin", entry)
