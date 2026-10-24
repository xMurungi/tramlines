# Literature notes

What the work this project builds on already did, and what that means for our claims. Started 2026-10-24; the full literature check (Phase 6) extends it. Our words; short quotations only.

## Shiu et al. 2024 — the model we use
Shiu, P. K. et al. "A *Drosophila* computational brain model reveals sensorimotor processing." *Nature* 634, 210–219 (2024). [doi:10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9). Open access (CC BY 4.0).

**What they did.** A leaky integrate-and-fire model of the whole central brain (FlyWire v630, 127,400 proofread neurons; we use v783, 138,639), with one free parameter, w_syn = 0.275 mV, chosen so 100 Hz sugar input gives about 80% of maximal MN9 firing. They used it to predict feeding (sugar, water, bitter, Ir94e) and antennal grooming circuits, tested many predictions with optogenetics, calcium imaging and behaviour, and report 91% of 164 testable predictions consistent with experiment (84% excluding their split-GAL4 screen). Open-loop: neurons are stimulated, firing rates read; no body, no world.

**What overlaps with our results**
- **Shuffled wiring (our Result 2, ADR-0039).** They shuffled connection weights "while maintaining the global connectivity weight distribution": sugar drove MN9 in 100% of simulations with the real connectome and 1 of 100 shuffled ones. Our full null brain repeats this finding with a different null (degree-preserving receiver shuffle, weights and signs kept with their senders) at the level of behaviour. **Their test is prior work and must be cited**; what Result 2 adds is the closed loop and body, partial rewiring (how much damage behaviour survives, and that the bitter veto breaks first), runaway activity in partly rewired brains, convergence measurements and the decoder-free check.
- **Robustness to the model's assumptions.** w_syn ±30%: 90–95% of predictions unchanged. Inhibitory:excitatory strength ratio ±50%: 95–96% unchanged. **Glutamate treated as excitatory** (instead of inhibitory): "the computational result that bitter and Ir94e are inhibitory is eliminated", and false positives in their screen rise from 1% to 16%. They did not vary the resting potential, threshold, membrane time constant, delay or refractory period, arguing these mostly scale firing rates.
  - For us: the same checks on our headline results (w_syn ±30%; glutamate excitatory) are a natural robustness test, and the glutamate result predicts that our laced-food decision depends on that assumption.
- **Their stated limits** match our honesty page: every neuron treated alike; no morphology, receptor dynamics, gap junctions, non-spiking neurons, internal state or neuropeptides; zero baseline firing, so "inhibitory connections to an inactive neuron have no effect"; accuracy "limited by the underlying synapse and neurotransmitter prediction accuracy".

**What they did not do** (so far as this paper goes): a closed loop with a body; prediction under imperfect knowledge of the state (our Result 1); single-spike perturbations followed to behaviour (Result 3); recovering the past (Result 4). Novelty is still to be checked against the wider literature.

**Sources this paper points to that we need**
- Buhmann, J. et al. "Automatic detection of synaptic partners in a whole-brain *Drosophila* electron microscopy data set." *Nat. Methods* 18, 771–774 (2021): synapse detection accuracy (owner decision 22).
- Eckstein, N. et al. "Neurotransmitter classification from electron microscopy images at synaptic sites in *Drosophila melanogaster*." *Cell* 187, 2574–2594 (2024): neurotransmitter prediction accuracy (decision 22).
- Lappalainen, J. K. et al. "Connectome-constrained networks predict neural activity across the fly visual system." *Nature* (2024): another connectome-constrained model.
- Sapkal, N. et al. (*Nature*, 2024): used this model for walking and halting circuits.
- Randi, F. et al. "Neural signal propagation atlas of *Caenorhabditis elegans*." *Nature* 623, 406–414 (2023): measured propagation not well predicted by anatomy alone.

## Still to read for the write-up
- London, M. et al. "Sensitivity to perturbations in vivo implies high noise and suggests rate coding in cortex." *Nature* 466, 123–127 (2010): one extra spike in rat cortex (Result 3).
- van Vreeswijk, C. & Sompolinsky, H. "Chaos in neuronal networks with balanced excitatory and inhibitory activity." *Science* 274, 1724–1726 (1996) (Results 1 and 3).
- Landauer, R. "Irreversibility and heat generation in the computing process." *IBM J. Res. Dev.* 5, 183–191 (1961) (Result 4).
- Dorkenwald et al. 2024 and Schlegel et al. 2024 (*Nature*): the connectome and its annotations; error rates.
