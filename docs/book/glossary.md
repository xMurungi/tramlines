# Glossary

Every term is defined in plain words first. The chapter that introduces it is in brackets, once that chapter exists.

**ADR (Architecture Decision Record).** A short document explaining one decision: what we chose, what else we considered, and why. See [Decisions](../decisions/index.md).

**Annotation.** A label scientists attach to a neuron: its class, type, side of the brain. [[Chapter 17](ch17-loading-flywire.md)]

**Branch.** A fork that received one extra "free will" spike, and so may grow a different future.

**Connectome.** The complete wiring diagram of a nervous system: every neuron, and which neurons connect to which.

**Descending neuron.** A neuron that carries commands from the brain down to the body.

**Determinism.** Same starting state plus same inputs gives the same result, every time.

**Divergence.** How far apart two timelines have moved.

**FlyWire.** The consortium, and the dataset it produced, that reconstructed the whole adult female fruit fly brain from electron-microscope images.

**Fingerprint.** A hash of every byte of a spike record or a brain state. Equal fingerprints mean identical, bit for bit. [[Chapter 21](ch21-the-sacred-tests.md)]

**Fork.** An independent copy of a timeline's state, continuing on its own; it shares the wiring. [[Chapter 20](ch20-forking.md)]

**Ghost.** A fork run ahead in time to predict the live fly's future.

**GRN (gustatory receptor neuron).** A taste-sensing neuron.

**Hash (SHA-256).** A short fingerprint computed from a file's bytes. Change one byte and the fingerprint changes completely. [[Chapter 17](ch17-loading-flywire.md)]

**Index (of a neuron).** A neuron's row number in the neuron list, which is its address inside the simulation. Compare *root ID*. [[Chapter 17](ch17-loading-flywire.md)]

**LIF (leaky integrate-and-fire).** A simple neuron model. Voltage leaks back towards rest, rises with input, and the neuron fires when it crosses a threshold.

**MaleCNS.** The male fruit fly central nervous system connectome (brain plus nerve cord), released in 2026.

**MN9.** A motor neuron that controls extending the proboscis, the fly's feeding "tongue".

**Poisson input.** Random spikes at a set average rate, used to stand in for a sensory stimulus.

**Program.** A list of instructions written in a language a computer can follow. [[Chapter 2](ch02-hello-world.md)]

**Refractory period.** A short time after a spike (2.2 ms here) when a neuron cannot fire and ignores all input. [[Chapter 18](ch18-the-brain-wakes-up.md)]

**Root ID.** FlyWire's unique number for one neuron in one version of the data.

**Spike.** A neuron firing; the brain's unit of signal.

**State.** Everything about a brain that changes over time: voltages, synaptic inputs, spike timers, spikes in flight, input rates and the random generator's position. [[Chapter 19](ch19-state.md)]

**Synapse.** A contact point where one neuron passes a signal to another.

**Synaptic delay.** The time a spike takes to reach the next neuron (1.8 ms here). [[Chapter 18](ch18-the-brain-wakes-up.md)]

**Terminal.** A window where you type commands to your computer as text. [[Chapter 2](ch02-hello-world.md)]

**uv.** A tool that installs Python and the packages a project needs, and runs programs with them. [[Chapter 2](ch02-hello-world.md)]
