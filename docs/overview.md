# The project at a glance

*Last updated 2026-10-24. For day-to-day status see [`ROADMAP.md`](https://github.com/xMurungi/tramlines/blob/develop/ROADMAP.md), [what remains](remaining-and-suggestions.md) and the [owner decisions](owner-decisions.md).*

## The question
Tramlines simulates a fruit fly's whole brain (138,639 neurons, wired exactly as the FlyWire connectome measured) driving a body in a small dish. The simulation is **deterministic**: the same starting state always gives the same future. So a perfect copy of the brain, the *ghost*, always predicts the fly correctly. That is Laplace's demon in its original form, and it is true by construction, so the project shows it openly as the **control**, not as a result ([ADR-0035](decisions/0035-proposal-honest-laplaces-demon.md)).

The real question is the demon's: **how much must you know about a brain to foresee it, and where does that knowledge stop mattering?**

## The answers, one result at a time

| Result | The demon's question | What we found |
|---|---|---|
| **1** · [ADR-0037](decisions/0037-result-1-predictability-horizon.md), [0038](decisions/0038-result-1-second-pass.md) | How precisely must it know the brain's state? | Not every decimal, but every spike, and it depends on *when* it looks: at a decision, one missed spike breaks the prediction. |
| **2** · [ADR-0039](decisions/0039-result-2-null-brain.md) | Must it know the wiring? | Yes: scramble who connects to whom and the fly does nothing (as Shiu et al. found for their model). Yet with up to a quarter of the wiring scrambled, walking, eating and escape never failed in the brains tested (9), while judgement (refusing bitter-laced food) held in only 1 of 9. |
| **3** · [plan](science/atlas-plan.md) | Which tiny events can it not afford to miss, where and when? | The perturbation atlas: tens of thousands of single extra spikes across neurons and moments. In progress. |
| **4** · [ADR-0041](decisions/0041-result-4-backward-horizon.md) | Can it know the past? | The brain forgets within a second; the body remembers, and keeps the brain from forgetting when the body ends up somewhere that feels different. |
| **Proposed** · owner decision 22 | How accurate must its map of the wiring be, given real measurement errors? | Being prepared: realistic connectome errors (missed or false synapses, wrong neurotransmitters), not random ones. |

Every result was checked against controls; Result 4 and Result 3 were pre-registered (the analysis plan merged before the study ran); mistakes found along the way are corrected on the record (for example ADR-0036, 0037 and 0038).

## Is it worth doing? An honest assessment
**Where the value is.**
- Result 3 (and the proposed connectome-error study) ask questions neuroscientists already ask: does a single extra spike change a brain's future (London et al. 2010, in rat cortex)? How accurate must a connectome be for a model built from it to behave correctly? Doing this in a whole-brain, connectome-built model with a body, down to the animal's choices, may be new; the literature check found close neighbours for each result taken alone, and nothing combining them in behaviour ([what is new, what is not](science/literature-notes.md#what-is-new-what-is-not)). Embodied whole-brain flies themselves already exist, so we never claim to be the first.
- The method: predictions written before results, controls, a test that does not rely on our own body and decoder, exact-arithmetic validation, public corrections.
- The public value: it makes determinism, predictability and "free will" concrete without overclaiming.

**Where its limits are.**
- It is about this model, not about flies: every neuron shares the same simple equations, with no neuromodulators, learning or glia, and the body and decoder are our design ([honesty page](honesty.md)). Some findings follow from those simplifications.
- Some results were expected (scrambled wiring fails; a leaky system forgets). Their value is the measured numbers and the method.
- Novelty is not yet confirmed, and the model is validated against real flies only through Shiu et al.'s tests (sugar drives MN9 here too).

**Verdict.** A rigorous, open computational experiment with a modest but real scientific contribution, likely suitable for a preprint and useful to people building brain models from connectomes. Not a breakthrough, and not to be framed as one. What would raise it: the literature check early; the connectome-error study; robustness to the model's assumptions (Shiu et al.'s own checks: w_syn ±30%, glutamate treated as excitatory); a direct comparison with London et al.'s numbers. See [literature notes](science/literature-notes.md).

## Where it is headed
One coherent piece of work: **an honest Laplace's demon for a fly brain**. Four (perhaps five) measured answers, a viewer where anyone can feel them (the ghost peeling away, the future splitting, the slider of how much the ghost knows), a write-up with data and scripts, and a short clip.

**Launch** means making it public all at once, at the end (owner's decision, Phase 8): the repository goes public; a link opens the viewer in a browser from precomputed runs (decision 19); the write-up (possibly a preprint after the literature check); a 30–60 s clip; announcements on the channels the owner chooses.

**The name.** "Tramlines" (rails a tram cannot leave: a future laid down in advance) still fits: the project shows where the rails hold, where they split, and what the past leaves behind. It is a common word (a music festival and businesses use it), so a subtitle helps people find it, for example *"Tramlines: an honest Laplace's demon for a fly brain"*. Check for clashes before launch (owner decision 6).

## Licence and going public
Code: MIT. Documentation, figures and result data: CC BY 4.0 ([ADR-0043](decisions/0043-licence.md)). Once public, anyone may use, change and share the code and results, with credit; nobody may remove the credit, imply the project endorses them, or hold its authors liable. Making the repository public is the owner's step; a full-history privacy scan before that was clean (2026-10-24).
