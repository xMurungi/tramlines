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

## Determinism belongs to the simulation

The ghost is always right because the simulation is deterministic: the same starting state, with the same random seed, always produces the same result, bit for bit. That is a property of this computer program. It is **not** a claim about real flies, and it is not evidence for or against free will. Tramlines is a thought experiment you can touch, not an argument.

## Credit

The connectome is the work of hundreds of people. See [citations](science/citations.md).
