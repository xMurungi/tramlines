# book: needs-data
"""Chapter 19: everything a brain is at one instant."""

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

enable_determinism()
wiring = load_connectome()
brain = Brain(wiring, load_catalog().index_of(REFERENCE_SUGAR_GRNS), seed=0)
brain.set_input_rates(200.0)
brain.run(500)  # 50 ms of sugar

state = brain.state
print(f"the brain after {state.step} steps ({state.step / 10:.0f} ms):")
for name, tensor in [
    ("voltage", state.v_mV),
    ("synaptic input", state.g_mV),
    ("last spike", state.last_spike_step),
    ("spikes in flight", state.in_flight),
    ("input rates", state.input_rates_hz),
]:
    size = tensor.numel() * tensor.element_size()
    print(f"  {name:17} {str(list(tensor.shape)):16} {size / 1e6:5.2f} MB")
print(f"  random generator  {state.generator.get_state().numel():,} bytes of hidden state")
print(f"state in total:  {state.nbytes() / 1e6:.2f} MB")
wiring_bytes = sum(t.numel() * t.element_size() for t in (wiring.row_start, wiring.post, wiring.weight_mV))
print(f"wiring in total: {wiring_bytes / 1e6:.2f} MB (never changes)")

refractory = int(((state.step - state.last_spike_step) < brain.refractory_steps).sum())
print(f"right now: {refractory} neurons recovering, {int(state.in_flight.sum())} spikes travelling")
