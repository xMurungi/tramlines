"""Our engine reproduces Brian2, the reference simulator, spike for spike (ADR-0016).

Golden files come from `scripts/reference/brian2_golden.py`. Floating-point sums run
in a different order in the two simulators, so voltages may differ in the last bits;
spikes must not differ at all.
"""

from pathlib import Path

import numpy as np
import pytest
import torch

from tramlines.brain.connectome import from_arrays
from tramlines.brain.engine import Brain, enable_determinism

GOLDEN = sorted((Path(__file__).parent / "golden").glob("brian2_net*.npz"))


@pytest.mark.parametrize("golden", GOLDEN, ids=lambda p: p.stem)
def test_identical_spikes_to_brian2(golden: Path) -> None:
    enable_determinism()
    ref = np.load(golden)
    n = len(ref["v0_mV"])
    brain = Brain(
        from_arrays(n, ref["pre"], ref["post"], ref["signed_synapses"]),
        torch.from_numpy(ref["inputs"]),
        seed=0,
    )
    brain.state.v_mV[:] = torch.from_numpy(ref["v0_mV"])
    brain.state.g_mV[:] = torch.from_numpy(ref["g0_mV"])
    brain.set_input_rates(10_000.0)

    record = brain.run(5000)

    ours = sorted(zip(record.steps.tolist(), record.neurons.tolist(), strict=True))
    theirs = sorted(zip(ref["spike_steps"].tolist(), ref["spike_neurons"].tolist(), strict=True))
    assert ours == theirs
    np.testing.assert_allclose(brain.state.v_mV.numpy(), ref["v_end_mV"], rtol=0, atol=1e-9)
    np.testing.assert_allclose(brain.state.g_mV.numpy(), ref["g_end_mV"], rtol=0, atol=1e-9)


def test_golden_files_exist() -> None:
    assert len(GOLDEN) == 2
