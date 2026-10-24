# Citations and credits

The FlyWire data is licensed CC BY 4.0, which requires attribution. Every entry below must be checked against the publisher's page (authors, title, venue, year) before anything is published. The *Verified* column records that check.

**What "verified" means here.** The authors, title, journal, volume, pages (or article number), year and DOI were checked against the DOI's Crossref record (DataCite for Zenodo, arXiv for arXiv preprints) on the date given. It does not mean the paper was read; how much of each was read is recorded in the [literature notes](literature-notes.md). Where the year printed on the issue differs from the online date, the issue year is given and the online date noted.

| Work | Citation (as currently known) | Verified |
|---|---|---|
| FlyWire connectome | Dorkenwald, S., Matsliah, A., Sterling, A. R., Schlegel, P. et al. (294 authors, FlyWire Consortium). "Neuronal wiring diagram of an adult brain." *Nature* 634, 124–138 (2024). [doi:10.1038/s41586-024-07558-y](https://doi.org/10.1038/s41586-024-07558-y) | **verified 2026-10-24** (Crossref) |
| FlyWire annotations | Schlegel, P., Yin, Y., Bates, A. S., Dorkenwald, S. et al. (307 authors). "Whole-brain annotation and multi-connectome cell typing of *Drosophila*." *Nature* 634, 139–152 (2024). [doi:10.1038/s41586-024-07686-5](https://doi.org/10.1038/s41586-024-07686-5). Data: [flyconnectome/flywire_annotations](https://github.com/flyconnectome/flywire_annotations), tag v2.1.0. | **verified 2026-10-24** (Crossref; the data tag was not re-checked) |
| Brian2 | Stimberg, M., Brette, R. & Goodman, D. F. M. "Brian 2, an intuitive and efficient neural simulator." *eLife* 8, e47314 (2019). [doi:10.7554/eLife.47314](https://doi.org/10.7554/eLife.47314). Used (not bundled) to verify our engine. | **verified 2026-10-24** (Crossref) |
| Whole-brain LIF model | Shiu, P. K., Sterne, G. R., … Seeds, A. M., Scott, K. (27 authors). "A *Drosophila* computational brain model reveals sensorimotor processing." *Nature* 634, 210–219 (2024). [doi:10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9). Code: [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model) (MIT). | **verified 2026-10-24** (Crossref: title, journal, volume, pages, year) |
| MaleCNS | Janelia / Google and collaborators, 2026 release and *Cell* paper. Details to be filled in. | not yet |
| Eon Systems fly-brain | [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain) (GPL-2.0-or-later). | not yet |
| JRC2018 templates | Bogovic, J. A., Otsuna, H., Heinrich, L., Ito, M. et al. (11 authors). "An unbiased template of the *Drosophila* brain and ventral nerve cord." *PLoS ONE* 15, e0236495 (2020). [doi:10.1371/journal.pone.0236495](https://doi.org/10.1371/journal.pone.0236495). Reference only; not bundled. | **verified 2026-10-24** (Crossref) |
| Virtual Fly Brain | [virtualflybrain.org](https://www.virtualflybrain.org/) | not yet |
| natverse | [natverse.org](https://natverse.org/) | not yet |
| Movement literature | Bidaye et al. 2014 (MDN, backward walking), Bidaye et al. 2020 (P9 / BPN, forward walking), Rayshubskiy et al. 2020 (DNa02 steering), giant fiber escape literature. To be completed in Phase 3. Giant fiber: see von Reyn et al. 2014 below. | not yet |

## Connectome accuracy (owner decision 22)
Used in [`connectome-error-rates.md`](connectome-error-rates.md) and ADR-0047.

| Work | Citation | Verified |
|---|---|---|
| Synapse detection | Buhmann, J., Sheridan, A., Malin-Mayor, C., Schlegel, P. et al. (17 authors). "Automatic detection of synaptic partners in a whole-brain *Drosophila* electron microscopy data set." *Nat. Methods* 18, 771–774 (2021). [doi:10.1038/s41592-021-01183-7](https://doi.org/10.1038/s41592-021-01183-7) | **verified 2026-10-24** (Crossref) |
| Neurotransmitter prediction | Eckstein, N., Bates, A. S., Champion, A., Du, M. et al. (23 authors). "Neurotransmitter classification from electron microscopy images at synaptic sites in *Drosophila melanogaster*." *Cell* 187, 2574–2594.e23 (2024). [doi:10.1016/j.cell.2024.03.016](https://doi.org/10.1016/j.cell.2024.03.016) | **verified 2026-10-24** (Crossref) |
| Hemibrain | Scheffer, L. K., Xu, C. S., Januszewski, M., Lu, Z. et al. (108 authors). "A connectome and analysis of the adult *Drosophila* central brain." *eLife* 9, e57443 (2020). [doi:10.7554/eLife.57443](https://doi.org/10.7554/eLife.57443) | **verified 2026-10-24** (Crossref) |
| Reconstruction errors | Schneider-Mizell, C. M., Gerhard, S., Longair, M., Kazimiers, T. et al. (11 authors). "Quantitative neuroanatomy for connectomics in *Drosophila*." *eLife* 5, e12059 (2016). [doi:10.7554/eLife.12059](https://doi.org/10.7554/eLife.12059) | **verified 2026-10-24** (Crossref) |

## Literature check for the write-up (Phase 6)
All entries below were added on 2026-10-24 and checked against Crossref, DataCite or arXiv that day. What each says and how much of it was read: [literature notes](literature-notes.md). **Preprint** = not peer reviewed.

### Single spikes, chaos and stability
| Citation | Verified |
|---|---|
| London, M., Roth, A., Beeren, L., Häusser, M. & Latham, P. E. "Sensitivity to perturbations in vivo implies high noise and suggests rate coding in cortex." *Nature* 466, 123–127 (2010). [doi:10.1038/nature09086](https://doi.org/10.1038/nature09086) | **verified** |
| Monteforte, M. & Wolf, F. "Dynamic flux tubes form reservoirs of stability in neuronal circuits." *Phys. Rev. X* 2, 041007 (2012). [doi:10.1103/PhysRevX.2.041007](https://doi.org/10.1103/PhysRevX.2.041007) | **verified** |
| Monteforte, M. & Wolf, F. "Dynamical entropy production in spiking neuron networks in the balanced state." *Phys. Rev. Lett.* 105, 268104 (2010). [doi:10.1103/PhysRevLett.105.268104](https://doi.org/10.1103/PhysRevLett.105.268104) | **verified** |
| Nolte, M., Reimann, M. W., King, J. G., Markram, H. & Muller, E. B. "Cortical reliability amid noise and chaos." *Nat. Commun.* 10, 3792 (2019). [doi:10.1038/s41467-019-11633-8](https://doi.org/10.1038/s41467-019-11633-8) | **verified** |
| van Vreeswijk, C. & Sompolinsky, H. "Chaos in neuronal networks with balanced excitatory and inhibitory activity." *Science* 274, 1724–1726 (1996). [doi:10.1126/science.274.5293.1724](https://doi.org/10.1126/science.274.5293.1724) | **verified** |
| van Vreeswijk, C. & Sompolinsky, H. "Chaotic balanced state in a model of cortical circuits." *Neural Comput.* 10, 1321–1371 (1998). [doi:10.1162/089976698300017214](https://doi.org/10.1162/089976698300017214) | **verified** |
| Jahnke, S., Memmesheimer, R.-M. & Timme, M. "Stable irregular dynamics in complex neural networks." *Phys. Rev. Lett.* 100, 048102 (2008). [doi:10.1103/PhysRevLett.100.048102](https://doi.org/10.1103/PhysRevLett.100.048102) | **verified** |
| Zillmer, R., Livi, R., Politi, A. & Torcini, A. "Desynchronization in diluted neural networks." *Phys. Rev. E* 74, 036203 (2006). [doi:10.1103/PhysRevE.74.036203](https://doi.org/10.1103/PhysRevE.74.036203) | **verified** |
| Politi, A., Livi, R., Oppo, G.-L. & Kapral, R. "Unpredictable behaviour in stable systems." *Europhys. Lett.* 22, 571–576 (1993). [doi:10.1209/0295-5075/22/8/003](https://doi.org/10.1209/0295-5075/22/8/003) | **verified** (not read) |
| Politi, A. & Torcini, A. "Stable chaos." arXiv:0902.2545 (2009), review. [arXiv](https://arxiv.org/abs/0902.2545) | **verified, read** (2026-10-24; preprint/review) |
| Lajoie, G., Lin, K. K. & Shea-Brown, E. "Chaos and reliability in balanced spiking networks with temporal drive." *Phys. Rev. E* 87, 052901 (2013). [doi:10.1103/PhysRevE.87.052901](https://doi.org/10.1103/PhysRevE.87.052901) | **verified** |
| Houweling, A. R. & Brecht, M. "Behavioural report of single neuron stimulation in somatosensory cortex." *Nature* 451, 65–68 (2008; online 19 Dec 2007). [doi:10.1038/nature06447](https://doi.org/10.1038/nature06447) | **verified** |
| Dalgleish, H. W. P., Russell, L. E., Packer, A. M., Roth, A. et al. (8 authors). "How many neurons are sufficient for perception of cortical activity?" *eLife* 9, e58889 (2020). [doi:10.7554/eLife.58889](https://doi.org/10.7554/eLife.58889) | **verified** |
| von Reyn, C. R., Breads, P., Peek, M. Y., Zheng, G. Z. et al. (8 authors). "A spike-timing mechanism for action selection." *Nat. Neurosci.* 17, 962–970 (2014). [doi:10.1038/nn.3741](https://doi.org/10.1038/nn.3741) | **verified** |
| Cande, J., Namiki, S., Qiu, J., Korff, W. et al. (8 authors). "Optogenetic dissection of descending behavioral control in *Drosophila*." *eLife* 7, e34275 (2018). [doi:10.7554/eLife.34275](https://doi.org/10.7554/eLife.34275) | **verified** |
| Wilting, J. & Priesemann, V. "Inferring collective dynamical states from widely unobserved systems." *Nat. Commun.* 9, 2325 (2018). [doi:10.1038/s41467-018-04725-4](https://doi.org/10.1038/s41467-018-04725-4) | **verified** |

### Predictability
| Citation | Verified |
|---|---|
| Boffetta, G., Cencini, M., Falcioni, M. & Vulpiani, A. "Predictability: a way to characterize complexity." *Phys. Rep.* 356, 367–474 (2002). [doi:10.1016/S0370-1573(01)00025-4](https://doi.org/10.1016/S0370-1573(01)00025-4) | **verified** (the Crossref record lists only the first author; the four authors are from the arXiv record, nlin/0101029) |
| Aurell, E., Boffetta, G., Crisanti, A., Paladin, G. & Vulpiani, A. "Predictability in the large: an extension of the concept of Lyapunov exponent." *J. Phys. A* 30, 1–26 (1997). [doi:10.1088/0305-4470/30/1/003](https://doi.org/10.1088/0305-4470/30/1/003) | **verified** |
| Beiran, M. & Litwin-Kumar, A. "Prediction of neural activity in connectome-constrained recurrent networks." *Nat. Neurosci.* 28, 2561–2574 (2025). [doi:10.1038/s41593-025-02080-4](https://doi.org/10.1038/s41593-025-02080-4) | **verified** |

### Wiring, null models and connectome accuracy
| Citation | Verified |
|---|---|
| Maslov, S. & Sneppen, K. "Specificity and stability in topology of protein networks." *Science* 296, 910–913 (2002). [doi:10.1126/science.1065103](https://doi.org/10.1126/science.1065103) | **verified** |
| Lin, A., Yang, R., Dorkenwald, S., Matsliah, A. et al. (15 authors). "Network statistics of the whole-brain connectome of *Drosophila*." *Nature* 634, 153–165 (2024). [doi:10.1038/s41586-024-07968-y](https://doi.org/10.1038/s41586-024-07968-y) | **verified** |
| Randi, F., Sharma, A. K., Dvali, S. & Leifer, A. M. "Neural signal propagation atlas of *Caenorhabditis elegans*." *Nature* 623, 406–414 (2023). [doi:10.1038/s41586-023-06683-4](https://doi.org/10.1038/s41586-023-06683-4) | **verified** |
| Lappalainen, J. K., Tschopp, F. D., Prakhya, S., McGill, M. et al. (10 authors). "Connectome-constrained networks predict neural activity across the fly visual system." *Nature* 634, 1132–1140 (2024). [doi:10.1038/s41586-024-07939-3](https://doi.org/10.1038/s41586-024-07939-3) | **verified** |
| Chen, W.-Q. & Xi, W. "Whole-brain connectomics of *Drosophila* reveals a robust, distributed architecture for the suppression of feeding during escape." **Preprint**, bioRxiv (posted 16 Dec 2025). [doi:10.64898/2025.12.14.694122](https://doi.org/10.64898/2025.12.14.694122) | **verified** (bioRxiv page) |
| Li, Q., Ping, W., Zhang, K. & Wang, C. "Connectome-constrained modeling identifies neurons and synapses that sustain spontaneous activity in *Drosophila*." **Preprint**, bioRxiv (posted 25 Aug 2026). [doi:10.64898/2026.08.21.745055](https://doi.org/10.64898/2026.08.21.745055) | **verified** (bioRxiv page) |
| Yad, M. A. A. & Nabila, N. T. "Reconstruction differences rival individual differences in the fly compass connectome and break trained circuit models." **Preprint**, arXiv:2610.29205 (21 Oct 2026). [arxiv.org/abs/2610.29205](https://arxiv.org/abs/2610.29205) | **verified** (arXiv page) |
| Karaneen, C., Schomburg, E. W. & Chklovskii, D. "Reproducibility and model-selection stability in connectome-constrained circuit modeling." **Preprint**, bioRxiv (posted 20 Apr 2026). [doi:10.64898/2026.04.18.717873](https://doi.org/10.64898/2026.04.18.717873) | **verified** (bioRxiv page) |

### Fly models and bodies
| Citation | Verified |
|---|---|
| Sapkal, N., Mancini, N., Kumar, D. S., Spiller, N. et al. (13 authors). "Neural circuit mechanisms underlying context-specific halting in *Drosophila*." *Nature* 634, 191–200 (2024). [doi:10.1038/s41586-024-07854-7](https://doi.org/10.1038/s41586-024-07854-7) | **verified** |
| Pospisil, D. A., Aragon, M. J., Dorkenwald, S., Matsliah, A. et al. (13 authors). "The fly connectome reveals a path to the effectome." *Nature* 634, 201–209 (2024). [doi:10.1038/s41586-024-07982-0](https://doi.org/10.1038/s41586-024-07982-0) | **verified** |
| Lobato-Rios, V., Ramalingasetty, S. T., Özdil, P. G., Arreguit, J., Ijspeert, A. J. & Ramdya, P. "NeuroMechFly, a neuromechanical model of adult *Drosophila melanogaster*." *Nat. Methods* 19, 620–627 (2022). [doi:10.1038/s41592-022-01466-7](https://doi.org/10.1038/s41592-022-01466-7) | **verified** |
| Wang-Chen, S., Stimpfling, V. A., Lam, T. K. C., Özdil, P. G., Genoud, L., Hurtak, F. & Ramdya, P. "NeuroMechFly v2: simulating embodied sensorimotor control in adult *Drosophila*." *Nat. Methods* 21, 2353–2362 (2024). [doi:10.1038/s41592-024-02497-y](https://doi.org/10.1038/s41592-024-02497-y) | **verified** |
| Vaxenburg, R., Siwanowicz, I., Merel, J., Robie, A. A. et al. (14 authors). "Whole-body physics simulation of fruit fly locomotion." *Nature* 643, 1312–1320 (2025). [doi:10.1038/s41586-025-09029-4](https://doi.org/10.1038/s41586-025-09029-4) | **verified** |
| Jin, Z., Zhu, Y., Zhang, C. & Sui, Y. "Whole-brain connectomic graph model enables whole-body locomotion control in fruit fly." **Preprint**, arXiv:2602.17997 (v1 20 Feb 2026; v3 14 Jun 2026). [arxiv.org/abs/2602.17997](https://arxiv.org/abs/2602.17997) | **verified** (arXiv page) |
| Rojas Aliaga, E. M. "Emergent individuality and neural integration in whole-brain connectome simulations of *Drosophila melanogaster*." **Preprint**, Zenodo (21 Mar 2026). [doi:10.5281/zenodo.19152238](https://doi.org/10.5281/zenodo.19152238) | **verified** (DataCite) |
| Eon Systems, embodied fly announcement (March 2026). No primary technical source found. | **not verified** (press coverage only) |
| Izquierdo, E. J. & Beer, R. D. "Connecting a connectome to behavior: an ensemble of neuroanatomical models of *C. elegans* klinotaxis." *PLoS Comput. Biol.* 9, e1002890 (2013). [doi:10.1371/journal.pcbi.1002890](https://doi.org/10.1371/journal.pcbi.1002890) | **verified** |
| Zhao, M., Wang, N., Jiang, X., Ma, X. et al. (9 authors). "An integrative data-driven model simulating *C. elegans* brain, body and environment interactions." *Nat. Comput. Sci.* 4, 978–990 (2024). [doi:10.1038/s43588-024-00738-w](https://doi.org/10.1038/s43588-024-00738-w) | **verified** |

### Memory, forgetting and irreversibility
| Citation | Verified |
|---|---|
| Landauer, R. "Irreversibility and heat generation in the computing process." *IBM J. Res. Dev.* 5, 183–191 (1961). [doi:10.1147/rd.53.0183](https://doi.org/10.1147/rd.53.0183) | **verified, read** (2026-10-24) |
| Bennett, C. H. "Logical reversibility of computation." *IBM J. Res. Dev.* 17, 525–532 (1973). [doi:10.1147/rd.176.0525](https://doi.org/10.1147/rd.176.0525) | **verified, read** (2026-10-24) |
| Bérut, A., Arakelyan, A., Petrosyan, A., Ciliberto, S., Dillenschneider, R. & Lutz, E. "Experimental verification of Landauer's principle linking information and thermodynamics." *Nature* 483, 187–189 (2012). [doi:10.1038/nature10872](https://doi.org/10.1038/nature10872) | **verified** |
| Maass, W., Natschläger, T. & Markram, H. "Real-time computing without stable states: a new framework for neural computation based on perturbations." *Neural Comput.* 14, 2531–2560 (2002). [doi:10.1162/089976602760407955](https://doi.org/10.1162/089976602760407955) | **verified** |
| Ganguli, S., Huh, D. & Sompolinsky, H. "Memory traces in dynamical systems." *Proc. Natl Acad. Sci. USA* 105, 18970–18975 (2008). [doi:10.1073/pnas.0804451105](https://doi.org/10.1073/pnas.0804451105) | **verified** |
| Boghosian, B. M., Coveney, P. V. & Wang, H. "A new pathology in the simulation of chaotic dynamical systems on digital computers." *Adv. Theory Simul.* 2, 1900125 (2019). [doi:10.1002/adts.201900125](https://doi.org/10.1002/adts.201900125) | **verified** |
| Clark, A. & Chalmers, D. "The extended mind." *Analysis* 58, 7–19 (1998). [doi:10.1093/analys/58.1.7](https://doi.org/10.1093/analys/58.1.7) | **verified, read** (2026-10-24) |

### Framing
| Citation | Verified |
|---|---|
| Brembs, B. "Towards a scientific concept of free will as a biological trait: spontaneous actions and decision-making in invertebrates." *Proc. R. Soc. B* 278, 930–939 (2011; online 15 Dec 2010). [doi:10.1098/rspb.2010.2325](https://doi.org/10.1098/rspb.2010.2325) | **verified** |

## Data used in this repository

FlyWire v783 public release, as redistributed by the Shiu et al. repository at commit `91bdd1e7`. Files and checksums: `data/MANIFEST.md`. Decision: [ADR-0013](../decisions/0013-data-files-and-source.md).
