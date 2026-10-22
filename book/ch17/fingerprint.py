# book: needs-data
import hashlib
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

for name in ["Completeness_783.csv", "Connectivity_783.parquet"]:
    contents = (DATA / name).read_bytes()
    fingerprint = hashlib.sha256(contents).hexdigest()
    print(f"{name}: {len(contents):,} bytes, sha256 {fingerprint[:16]}...")
