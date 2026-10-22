# book: needs-data
"""Chapter 20: copy a mind without copying its wiring."""

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

enable_determinism()
sugar = load_catalog().index_of(REFERENCE_SUGAR_GRNS)
brain = Brain(load_connectome(), sugar, seed=7)
brain.set_input_rates(200.0)
brain.run(300)  # 30 ms

twin = brain.fork()
print("shares the wiring:", twin.connectome is brain.connectome)
print("has its own voltages:", twin.state.v_mV is not brain.state.v_mV)

a = brain.run(700)  # 70 ms more, each on its own
b = twin.run(700)
print(f"original: {a.neurons.numel()} spikes, twin: {b.neurons.numel()} spikes")
print("identical spikes:", a.fingerprint() == b.fingerprint())
print("identical final state:", brain.state.fingerprint() == twin.state.fingerprint())

# Now nudge the twin: one sugar neuron fires one extra time.
nudged = brain.fork()
nudged.state.v_mV[int(sugar[0])] = 0.0
c = brain.run(700)
d = nudged.run(700)
print(f"after one extra spike: {c.neurons.numel()} spikes vs {d.neurons.numel()} spikes")
print("identical spikes:", c.fingerprint() == d.fingerprint())
