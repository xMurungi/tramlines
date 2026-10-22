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

## Cell type annotations (ADR-0017)

Source: `https://raw.githubusercontent.com/flyconnectome/flywire_annotations/ebd66db2596fcc39c6950fb54ea3efa00f7fe8a0/supplemental_files/Supplemental_file1_neuron_annotations.tsv` (tag v2.1.0, 2024-07-30; Schlegel et al. 2024).

| File (local name) | Bytes | SHA-256 |
|---|---|---|
| `neuron_annotations_v2.1.0.tsv` | 27,015,208 | `30be6c73975a70c56d930e27911f36455d3886e15abf383b78edd2a5d679e0b6` |

139,255 rows, all v783 root IDs; contains all 138,639 neurons of the brain files. (Tag v3.2.0 lacks 14 of them, so it is not used.)
