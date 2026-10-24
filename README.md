# Tramlines

*An honest Laplace's demon for a fly brain.*

Tramlines simulates the whole brain of an adult fruit fly (138,639 neurons, wired as the FlyWire connectome measured) driving a simple body in a 2D dish, next to a *ghost*: a copy of the same brain that runs ahead and predicts what the fly will do. The simulation is deterministic, so a perfect ghost is always right; that is the experiment's control, and the experiments give the ghost imperfect knowledge instead.

**Work in progress** (Phase 5 of the [roadmap](ROADMAP.md)). Please read the [honesty page](docs/honesty.md) before drawing conclusions from anything this project shows.

## The question

How much must you know about a brain to foresee it, and where does that knowledge stop mattering? A ghost that knows the simulated brain exactly is copying, not predicting ([ADR-0035](docs/decisions/0035-proposal-honest-laplaces-demon.md)). So we ask what happens when it knows a little less: the voltages blurred, one spike in flight missed, the wiring scrambled, the past unseen.

## What we have found so far

All of it is about this model, not about real flies. Each result has close neighbours in the literature ([what is new, what is not](docs/science/literature-notes.md#what-is-new-what-is-not)).

1. **Predictability horizon** ([ADR-0037](docs/decisions/0037-result-1-predictability-horizon.md), [ADR-0038](docs/decisions/0038-result-1-second-pass.md)). What the ghost must know depends on when it looks: missing one spike in flight never broke the prediction while the fly walked (6 of 6), and broke it in 17 of 18 ghosts at a decision.
2. **The brain's contribution** ([ADR-0039](docs/decisions/0039-result-2-null-brain.md)). Scramble who connects to whom and the fly does nothing, as Shiu et al. 2024 found for their model; with up to a quarter of the wiring scrambled, walking, feeding and escape still worked in every brain we tested (9), while refusing bitter-laced food held in only 1 of 9.
3. **Perturbation atlas** ([plan](docs/science/atlas-plan.md)). How often one extra spike changes what the fly does, where and when. In progress; the analysis plan was committed before the study ran.
4. **Backward horizon** ([ADR-0041](docs/decisions/0041-result-4-backward-horizon.md)). Small differences in the brain's past fade within tens to hundreds of milliseconds; differences that changed what the fly did stay in its body, and in all 92 pairs whose bodies ended up the same, the brain had forgotten by 3 s.

Results 3 and 4 were pre-registered. Mistakes found along the way are corrected on the record, in the ADRs themselves. A one-page summary: [the project at a glance](docs/overview.md).

## Run it

Requires [uv](https://docs.astral.sh/uv/) and, for the viewer, Node.js 22+.

```bash
uv sync                                  # install Python 3.12 deps
uv run python scripts/fetch_data.py      # download + verify FlyWire v783 + annotations (~130 MB)
uv run python -m tramlines.brain.data    # neurons: 138,639, connections: 15,091,983
uv run python scripts/sugar_mn9.py       # sugar → MN9, the reference model's feeding result (~5 min)
uv run pytest                            # tests (add `-m slow` for the long ones)
TRAMLINES_DETERMINISM_REPEATS=10 uv run pytest tests/test_determinism.py   # the 100/100 determinism gate
uv run mkdocs serve -a 127.0.0.1:8001    # the documentation at http://127.0.0.1:8001
cd web && npm install && npm run build   # build the viewer once
uv run python -m tramlines.server        # the viewer at http://127.0.0.1:8000
```

**In the viewer:** the gold fly is the live run, played at real speed from a timeline computed a few seconds ahead ([ADR-0030](docs/decisions/0030-projection-not-live.md)). The **"how much does the ghost know?"** slider swaps the perfect ghost (labelled *the control*) for an imperfect one and draws where it peels away from the fly ([ADR-0042](docs/decisions/0042-knowledge-slider.md)). **FREE WILL**, offered while the fly tastes something or a shadow approaches, forks the moment into 8 futures, each given one extra spike in a named neuron, and draws the fan ([ADR-0046](docs/decisions/0046-free-will-fan.md)). The first run computes before it plays, and is cached after that.

The script behind each result is named in its ADR.

## Honesty

This is a simplified model running on a real wiring diagram, not the fly. Every neuron follows the same simple equations; there are no neuromodulators, gap junctions, learning, glia or hormones; connection strengths are estimated from synapse counts, and whether a connection excites or inhibits is predicted from images. The body, the dish, which neurons count as senses and how brain activity becomes movement are our design choices. Determinism is a property of this program, not a claim about real flies or about free will, and "free will" is the name of a button: the extra spike is our intervention. The full statement: [docs/honesty.md](docs/honesty.md).

## Credits

The connectome is the work of the FlyWire consortium (Dorkenwald et al. 2024, *Nature*; Schlegel et al. 2024, *Nature*), data licensed CC BY 4.0. The neuron model is from Shiu et al. 2024, *Nature*, and our engine matches its reference code spike for spike on test networks ([ADR-0016](docs/decisions/0016-verified-neuron-model.md)). Full list, with verification status: [docs/science/citations.md](docs/science/citations.md).

## Licence

Code: [MIT](LICENSE). Documentation, figures and result data: [CC BY 4.0](LICENSE-docs.md). The FlyWire data is not included and keeps its own licence (CC BY 4.0); see [LICENSE-docs.md](LICENSE-docs.md) and [ADR-0043](docs/decisions/0043-licence.md).
