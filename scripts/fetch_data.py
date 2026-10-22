"""Download the FlyWire v783 brain files and annotations, and verify their SHA-256 checksums.

Usage:
    uv run python scripts/fetch_data.py          # download what is missing, verify all
    uv run python scripts/fetch_data.py --check  # verify only, never download

The brain files come from the Shiu et al. reference repository and the cell type
annotations from the FlyWire annotation release v2.1.0, each pinned to one commit,
so the bytes can never change under us (ADR-0013, ADR-0017). The data is FlyWire v783,
licensed CC BY 4.0 (see docs/science/citations.md). Data files are never
committed to git (CLAUDE.md section 7.1).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Pinned upstream commit of github.com/philshiu/Drosophila_brain_model (ADR-0013).
SHIU_COMMIT = "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
SHIU_RAW = f"https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/{SHIU_COMMIT}"

# Tag v2.1.0 of github.com/flyconnectome/flywire_annotations: the release matched to v783
# (ADR-0017).
ANNOTATIONS_COMMIT = "ebd66db2596fcc39c6950fb54ea3efa00f7fe8a0"
ANNOTATIONS_RAW = (
    f"https://raw.githubusercontent.com/flyconnectome/flywire_annotations/{ANNOTATIONS_COMMIT}"
)


@dataclass(frozen=True)
class DataFile:
    name: str
    url: str
    sha256: str
    size: int


FILES = (
    DataFile(
        name="Completeness_783.csv",
        url=f"{SHIU_RAW}/Completeness_783.csv",
        sha256="bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311",
        size=3_327_347,
    ),
    DataFile(
        name="Connectivity_783.parquet",
        url=f"{SHIU_RAW}/Connectivity_783.parquet",
        sha256="efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347",
        size=100_804_642,
    ),
    DataFile(
        name="neuron_annotations_v2.1.0.tsv",
        url=f"{ANNOTATIONS_RAW}/supplemental_files/Supplemental_file1_neuron_annotations.tsv",
        sha256="30be6c73975a70c56d930e27911f36455d3886e15abf383b78edd2a5d679e0b6",
        size=27_015_208,
    ),
)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid(path: Path, expected: DataFile) -> bool:
    return path.is_file() and sha256_of(path) == expected.sha256


def download(entry: DataFile, dest: Path) -> None:
    """Download to a temporary name first, so a broken download never looks finished."""
    partial = dest.with_suffix(dest.suffix + ".part")
    print(f"  downloading {entry.name} ({entry.size / 1e6:.1f} MB) ...", flush=True)
    with urllib.request.urlopen(entry.url) as response, partial.open("wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    if not is_valid(partial, entry):
        partial.unlink()
        raise RuntimeError(f"checksum mismatch for {entry.name}; the download was discarded")
    partial.replace(dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify only, do not download")
    args = parser.parse_args(argv)

    DATA_DIR.mkdir(exist_ok=True)
    ok = True
    for entry in FILES:
        path = DATA_DIR / entry.name
        if is_valid(path, entry):
            print(f"  ok        {entry.name}")
            continue
        if args.check:
            print(f"  MISSING   {entry.name}" if not path.exists() else f"  BAD HASH  {entry.name}")
            ok = False
            continue
        download(entry, path)
        print(f"  ok        {entry.name}")
    print("all files verified" if ok else "some files are missing or corrupt")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
