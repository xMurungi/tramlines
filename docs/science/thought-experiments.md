# Questions and thought experiments

Questions raised while building Tramlines, with what the project's results say about each. They are scientific questions, not settled answers; claims from outside the project are marked with their source, and anything not verified is said to be so.

## Could a demon predict a real brain? (noise)
Real brains are noisy everywhere: neurons fire spontaneously, synapses fail at random, ion channels open by chance; thousands of such events happen every second. This model is silent until poked. The single extra spike of Result 3 ([ADR-0048](../decisions/0048-result-3-perturbation-atlas.md)) is the smallest possible disturbance, a ruler. A realistic next step: add continuous background noise and measure how far ahead the demon can still see. Expectation from Results 1 and 3: good prediction between decisions, odds at decisions.

## Decide now, act later (memory)
Real flies hold hunger, drives and memories in slow chemistry (neuromodulators) and changing synapses. The FlyWire map includes the memory centre (the mushroom body); what this model lacks are the learning rules and slow states, so it forgets within about a second (Result 4, [ADR-0041](../decisions/0041-result-4-backward-horizon.md)) and cannot plan "after eating, mate". Adding them is a possible later season.

## Quantum mechanics and Laplace's demon
In the real universe, the uncertainty principle means exact position and velocity cannot both be known, so Laplace's perfect demon is widely thought impossible; quantum outcomes are probabilistic. This simulation is classical, so perfect knowledge exists inside it, which is why the perfect ghost is always right. That makes imperfect knowledge the meaningful question (see the [honesty page](../honesty.md)).

## A bigger sealed lab: the solar system
Planetary orbits are predictable for centuries, yet the solar system is chaotic: small uncertainties grow so that beyond roughly 100 million years exact positions are unpredictable (Laskar). Solar flares are forecast only as probabilities, hours to days ahead; weather is limited to about two weeks (Lorenz's "butterfly effect"). Removing the rest of the universe barely helps: the limits come from chaos inside a system, quantum uncertainty and computing cost. Every scale has its predictability horizon; Tramlines measures one for a brain: under a second at a fly's decision.

## A smaller sealed lab: a real fly in a controlled chamber
External noise can be removed, but not the fly's own molecular noise; its exact state cannot be measured (synapse-level mapping destroys the brain; living recordings see only part of the activity); and genetically identical flies in identical conditions still show individual, spontaneous choices (Brembs; de Bivort and colleagues). Prediction would be probabilities. Such a chamber is also how the model could be tested against real flies: compare predicted and observed odds of feeding, escaping and turning. That needs a fly lab as collaborator.

## Brain–computer interfaces (e.g. Neuralink)
Implants record hundreds to thousands of neurons and decode intended movements around the moment they happen: a limited, real form of reading imminent action. Result 1 found a predictor needs about 99.9% of neurons observed to stay right at decisions; an implant sees a tiny fraction of a human brain. So such interfaces can give odds about imminent actions, not foresight of choices. **A thought experiment this project could run:** give the ghost only the neurons an "implant" would see, and measure the horizon.

## Living neurons as computers (biological computing)
Cultured neurons on electrode chips have learned to play Pong (Kagan et al. 2022, *Neuron*, Cortical Labs' DishBrain). Press coverage shared with the project reports commercial units of this kind (Cortical Labs' CL1) in data-centre deployments; those details are not verified here. Such a culture is a controlled, living network: a real-world version of Results 1 and 3 could record it, build a predictor, measure its horizon, and stimulate one neuron to see whether the future splits. Limits: unknown wiring (no connectome), partial recording, no body or senses, and ethical questions about human-derived neurons.

## Could we predict what people do?
Behaviour-based prediction already exists (recommendation systems). Brain-based prediction of people faces scale (about 86 billion neurons; even a mouse brain is not fully mapped at synapse level), the impossibility of mapping a living brain's synapses, and the same limit this project measured: at decision points, outcomes are odds. The ethics arrive long before the capability.
