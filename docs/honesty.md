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
- **Walking is commanded by us.** The simulated brain is completely silent without input, so we continuously drive four "walking command" neurons (P9). The fly walks because we tell it to. Its brain then adjusts where it goes.
- **Movement is our translation.** We read a handful of descending neurons and turn their firing into speed, turning, an escape jump and feeding, using constants we chose.
- **It cannot find food.** This model has no smell or sight of food, so the fly only finds food by walking onto it. In our demonstration runs we chose a starting point whose path crosses the food.

What *does* come from the measured wiring: sugar driving the feeding motor neuron, bitter suppressing it, a looming shadow driving the escape neuron on the correct side, and the small turning biases of the walk.

## Determinism belongs to the simulation

The ghost is always right because the simulation is deterministic: the same starting state, with the same random seed, always produces the same result, bit for bit. That is a property of this computer program. It is **not** a claim about real flies, and it is not evidence for or against free will. Tramlines is a thought experiment you can touch, not an argument.

## Credit

The connectome is the work of hundreds of people. See [citations](science/citations.md).
