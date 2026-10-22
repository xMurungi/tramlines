# Data manifest

Data files are **not committed**. Fetch and verify them with:

```bash
uv run python scripts/fetch_data.py
```

## FlyWire v783 brain (ADR-0013)

Source: `https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/<file>`
Dataset: FlyWire public release v783, licensed CC BY 4.0 (attribution: docs/science/citations.md).

| File | Bytes | SHA-256 |
|---|---|---|
| `Completeness_783.csv` | 3,327,347 | `bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311` |
| `Connectivity_783.parquet` | 100,804,642 | `efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347` |

Equivalent copies (not used): Eon `data/2025_Connectivity_783.parquet` is byte-identical. Eon `data/2025_Completeness_783.csv` (SHA-256 `52b0ac60…99ea4`) has the same content with CRLF line endings.

### Measured contents (2026-10-22)

| Quantity | Value |
|---|---|
| Neurons | 138,639 |
| Connections (distinct pre→post pairs) | 15,091,983 |
| Synapses (sum of `Connectivity`) | 54,492,922 |
| Excitatory / inhibitory connections | 9,059,302 / 6,032,681 |
| Neurons with outgoing / incoming connections | 138,005 / 137,090 |
| Synapse count per connection | 1 to 2,405 |
| Self-loops, duplicate pairs | 0, 0 |

## Cell type annotations

Not yet chosen. To be recorded here in Phase 1 (release, URL, SHA-256).
