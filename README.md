# Tramlines

*A real fly's brain, copied synapse by synapse, running in a machine that can see its future.*

A whole-brain simulation of the adult fruit fly, built from the FlyWire v783 connectome, with a ghost copy that runs ahead and predicts the fly's path, and a "free will" button that splits the future. **Work in progress: Phase 0 (foundations).** See [ROADMAP.md](ROADMAP.md).

Please read [docs/honesty.md](docs/honesty.md) before drawing conclusions from anything this project shows.

## Run it

Requires [uv](https://docs.astral.sh/uv/) and, for the viewer, Node.js 22+.

```bash
uv sync                                  # install Python 3.12 deps
uv run python scripts/fetch_data.py      # download + verify FlyWire v783 (~104 MB)
uv run python -m tramlines.brain.data    # neurons: 138,639, connections: 15,091,983
uv run pytest                            # tests
uv run mkdocs serve                      # docs and The Book at http://127.0.0.1:8000
cd web && npm install && npm run dev     # viewer skeleton
```

## Credits

The connectome is the work of the FlyWire consortium (Dorkenwald et al. 2024, *Nature*; Schlegel et al. 2024, *Nature*), data licensed CC BY 4.0. The neuron model is from Shiu et al. 2024, *Nature*. Full list, with verification status: [docs/science/citations.md](docs/science/citations.md).

## Licence

Not yet chosen.
