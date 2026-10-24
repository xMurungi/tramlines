# What this is, and what it is not

Tramlines shows a fly whose future can be read in advance. That is a striking thing to watch, and it is easy to read more into it than is there. This page says plainly what you are looking at.

## What it is

A computer simulation driven by the measured wiring of a real adult fruit fly brain. Every one of its 138,639 neurons, and every connection between them, comes from the FlyWire consortium's reconstruction of one fly's brain from electron-microscope images. That is 15 million connections and 54 million synapses, traced by machine learning and checked by hundreds of people.

## What it is not

**It is not the fly.** It is a deliberately simple model running on a real wiring diagram:

- Every neuron follows the same simple rule (a "leaky integrate-and-fire" model) with the same numbers. Real neurons come in thousands of types that behave very differently.
- There are no neuromodulators (such as dopamine or octopamine), no gap junctions (electrical synapses), no learning, no glia and no hormones.
- The strength of each connection is estimated from how many synapses it has, not measured.
- Whether a connection excites or inhibits is *predicted* from microscope images of the synapses, not measured.
- "Stimulating" a sense means forcing chosen sensory neurons to fire at a set rate, much as a scientist might do with light in a real fly. It is not a simulation of sugar molecules or light hitting an eye.

## The body is ours, not the fly's

FlyWire is a brain only. It does not include the nerve cord that drives the legs, nor the body. The 2D world, the fly's body, which neurons count as its senses, and how brain activity becomes walking and turning are **design decisions made by this project**, each recorded in a [decision record](decisions/index.md). Much of the fly's "behaviour" on screen depends on those choices.

## What the fly senses, and how it moves

Every link between the brain and the 2D world is listed in [ADR-0028](decisions/0028-senses-and-decoder-chosen.md), with the history of how it was chosen ([decision history](decisions/history.md)). In short:

- **Senses.** Standing on food forces 21 sugar-sensing neurons to fire; standing on a bitter patch forces 42 bitter-sensing neurons to fire; a looming shadow forces looming-detector neurons (LPLC2) on that side to fire.
- **Walking is ours; its speed is the brain's.** The simulated brain is completely silent without input, so we continuously drive four central neurons (type CB2777) that feed the "walking command" neurons (P9). We read P9 for speed but never drive it, and a test makes sure no neuron is both driven and read, so speed is the brain's answer to our push ([ADR-0036](decisions/0036-walking-drive-upstream-of-p9.md)). Left alone in a silent world, this brain walks straight; the wall of the dish is what turns it.
- **Movement is our translation.** We read a handful of descending neurons and turn their firing into speed, turning, an escape jump and feeding, using constants we chose.
- **It cannot find food.** This model has no smell or sight of food, so the fly only finds food by walking onto it. In our demonstration runs we chose a starting point whose path crosses the food.

What *does* come from the measured wiring: sugar driving the feeding motor neuron, bitter suppressing it, a looming shadow driving the escape neuron on the correct side, and how fast the walking-command neurons answer the drive. We tested this: with every neuron, connection count and synapse weight kept but the connections scrambled (a "null brain"), the fly does none of these things; its senses still excite a few dozen neurons, but the signal does not travel on to the neurons that move the body ([ADR-0039](decisions/0039-result-2-null-brain.md)). Our readouts were chosen on the real brain, which is why we also checked without them.

## Why the ghost is always right, and what that does and does not show

The ghost runs the same code from the same saved state with the same random numbers, so it **must** match the live fly; 100% is what deterministic means. It is the experiment's **control**, a check that nothing has gone wrong, not a feat of prediction. The interesting questions start where the control ends: how long a ghost stays right when it knows the brain *slightly* imperfectly, and where one spike changes what the fly does. In this model, a single extra spike changes the fly's behaviour only at rare moments where its brain is on a threshold. The moments shown in the viewer were found by measurement and placed on the fly's path on purpose ([ADR-0032](decisions/0032-decision-points.md)).

The viewer's "how much does the ghost know?" slider gives the ghost imperfect knowledge instead ([ADR-0042](decisions/0042-knowledge-slider.md)): every voltage blurred by a set amount, the state rounded to single precision, a fraction of neurons unseen, or one spike in transit missed (offered only at moments when a spike is in transit). These are imitations of measurement errors *inside the model*: the imperfect ghost still runs the same simulated brain, with the body, the arena and the senses' random numbers known exactly. It says nothing about how well a real fly could be predicted. Each setting shows one random draw of its error. Result 1 found that the same kind of error can be harmless in one draw and decisive in another ([ADR-0038](decisions/0038-result-1-second-pass.md)), so what you watch is one example, not a rate.

The **FREE WILL** button forks the moment on screen into 8 futures, each given exactly one extra spike, in a different neuron that is receiving input from the world at that moment ([ADR-0046](decisions/0046-free-will-fan.md)). The spike is *aimed*: a spike in a neuron chosen at random almost never changes anything in this model ([ADR-0029](decisions/0029-divergence-batching-monitoring.md)), so the button is offered only while the fly is on food or bitter or a shadow is approaching, and the screen names every neuron that got a spike, and every one the engine refused. "Free will" is the name of a button, not a claim: an extra spike is our intervention in a deterministic program, not a choice the fly makes, and nothing here bears on free will in real animals. One fan is one moment of one run; how often a spike changes behaviour, and where, is what the perturbation atlas (Result 3) measures.

## Determinism belongs to the simulation

The ghost is always right because the simulation is deterministic: the same starting state, with the same random seed, always produces the same result, bit for bit. That is a property of this computer program. It is **not** a claim about real flies, and it is not evidence for or against free will. Tramlines is a thought experiment you can touch, not an argument.

**What about quantum mechanics?** In the real universe, Heisenberg's uncertainty principle means a particle's exact position and velocity cannot both be known, which is why Laplace's perfect demon is widely thought impossible in reality. This simulation is a classical computer program, so inside it perfect knowledge is possible, and that is exactly why the perfect ghost is always right (the control). It also explains why the project asks about *imperfect* knowledge: any real predictor would have some, so the meaningful question is how much imprecision a prediction survives (Results 1 and 3). Whether quantum effects matter directly in brains is contested; at the scale of neurons, ordinary thermal noise is usually thought to dominate.

The same goes for the past. In this model, small differences in the brain fade within about a second, and a perfect observer of the brain can no longer tell which past happened, unless the difference moved the fly somewhere that feels different ([ADR-0041](decisions/0041-result-4-backward-horizon.md)). This model has no learning or memory, so it is built to forget; real brains store memories in their wiring. Whether the faintest differences vanish or freeze is decided by the computer's rounding, not by the model.

## Credit

The connectome is the work of hundreds of people. See [citations](science/citations.md).
