# Tramlines

*A real fly's brain, copied synapse by synapse, running in a machine that can see its future.*

A whole-brain simulation of the adult fruit fly, built from the FlyWire v783 connectome, with a ghost copy that runs ahead and predicts the fly's path, and a "free will" button that splits the future. **Work in progress: Phase 4: the viewer runs, with the live fly, an independently computed ghost, and a match meter at 100.000%.** See [ROADMAP.md](ROADMAP.md).

Please read [docs/honesty.md](docs/honesty.md) before drawing conclusions from anything this project shows.

## Run it

Requires [uv](https://docs.astral.sh/uv/) and, for the viewer, Node.js 22+.

```bash
uv sync                                  # install Python 3.12 deps
uv run python scripts/fetch_data.py      # download + verify FlyWire v783 + annotations (~130 MB)
uv run python -m tramlines.brain.data    # neurons: 138,639, connections: 15,091,983
uv run python book/ch18/wake_up.py       # sugar on the tongue: MN9 fires 98 times in 1 s
uv run python scripts/sugar_mn9.py       # the full sugar → MN9 experiment (~5 min)
uv run pytest                            # tests (add `-m slow` for the long ones)
TRAMLINES_DETERMINISM_REPEATS=10 uv run pytest tests/test_determinism.py   # the 100/100 determinism gate
uv run mkdocs serve                      # docs and The Book at http://127.0.0.1:8000
cd web && npm install && npm run build   # build the viewer once
uv run python -m tramlines.server        # the viewer at http://127.0.0.1:8000 (first run computes; then cached)
```

## Credits

The connectome is the work of the FlyWire consortium (Dorkenwald et al. 2024, *Nature*; Schlegel et al. 2024, *Nature*), data licensed CC BY 4.0. The neuron model is from Shiu et al. 2024, *Nature*. Full list, with verification status: [docs/science/citations.md](docs/science/citations.md).

## Licence

Code: [MIT](LICENSE). Documentation, figures and result data: [CC BY 4.0](LICENSE-docs.md). The FlyWire data is not included and keeps its own licence (CC BY 4.0); see [LICENSE-docs.md](LICENSE-docs.md) and [docs/decisions/0043-licence.md](docs/decisions/0043-licence.md).
