# Reference model notes

How the two reference implementations load the data, build the weights and run the model. Studied in Phase 0 (2026-10-22) so that Phase 1 copies *behaviour*, not guesses.

| Repository | Commit studied | Licence | Role for us |
|---|---|---|---|
| [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model) | `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` (2024-09-14) | MIT | **The reference.** Brian2 code that produced Shiu et al. 2024. Where anything disagrees, this wins. |
| [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain) | `a3db62f9436074e485c0278290c2164ed6150808` (2026-08-29) | GPL-2.0-or-later (Shiu files inside remain MIT) | A multi-backend port, including PyTorch. Useful for structure and for cross-checking spike counts. |

!!! warning "Licence boundary"
    Eon's code is GPL-2.0-or-later. Tramlines' own licence is still undecided (an owner question). Until it is decided, we **read** Eon's code to understand it but do **not copy** from it. Shiu's code is MIT: adapting it is allowed, with its copyright notice kept. Our engine is written from the equations.

## 1. Data loading

Both use the same two v783 files ([ADR-0013](../decisions/0013-data-files-and-source.md)).

**Completeness file** (`Completeness_783.csv`): one row per neuron. The first (unnamed) column is the FlyWire root ID; a second column `Completed` is `True` for all 138,639 rows. **The row number is the simulator's neuron index.** Both implementations build `flyid2i = {root_id: row}` and its inverse from this file.

**Connectivity file** (`Connectivity_783.parquet`): one row per connected pair, 15,091,983 rows, sorted by presynaptic index.

| Column | Meaning |
|---|---|
| `Presynaptic_ID`, `Postsynaptic_ID` | v783 root IDs |
| `Presynaptic_Index`, `Postsynaptic_Index` | row numbers in the completeness file (we verified they agree with the IDs for every row) |
| `Connectivity` | synapse count, 1 to 2,405 |
| `Excitatory` | +1 or −1, the sign from the predicted neurotransmitter |
| `Excitatory x Connectivity` | signed synapse count, the `W_ij` of CLAUDE.md 7.2 (range −2,405 to +1,897) |

The sign rule (acetylcholine positive; GABA and glutamate negative) has already been applied upstream. We use the signed column as given; we do not re-derive it.

## 2. Building the weights

**Shiu (Brian2):** one `Synapses` object, `on_pre='g += w'`, delay `t_dly = 1.8 ms`, and per connection `w = (Excitatory x Connectivity) × w_syn` with `w_syn = 0.275 mV`.

**Eon (PyTorch):** a sparse matrix of shape `[post, pre]` from the signed counts, converted to CSR, cached as pickles. Each step computes `spikes @ Wᵀ`, then multiplies by 0.275.

**For Tramlines (Phase 1):** a CSR matrix in the same `[post, pre]` orientation, float64 on CPU, built once and shared by every fork ([ADR-0008](../decisions/0008-fork-shares-weights.md)). Cache it with a safe format (`torch.save` of plain tensors, or `.npz`), never pickle. Note: Eon caches weights as pickles; do not load pickles you did not create yourself. The Shiu repo also ships a `sez_neurons.pickle`, for the same reason we do not load it.

## 3. The neuron model as the reference runs it

From `model.py`, `default_params`:

```text
dv/dt = (v_0 − v + g) / t_mbr     (unless refractory)
dg/dt = −g / tau                  (unless refractory)
threshold:  v > v_th
reset:      v = v_rst; g = 0
refractory: t_rfc (2.2 ms), except Poisson targets: 0 ms
synapse:    on spike arrival (after 1.8 ms):  g += w
integration: Brian2 method='linear' (exact for these linear equations), dt = 0.1 ms
```

| Parameter | Reference value | CLAUDE.md 7.2 | Match |
|---|---|---|---|
| `v_0` (V_rest) | −52 mV | −52 mV | yes |
| `v_rst` (V_reset) | −52 mV | −52 mV | yes |
| `v_th` (V_th) | −45 mV | −45 mV | yes |
| `t_mbr` (τ_m) | 20 ms | 20 ms | yes |
| `tau` (τ_syn) | 5 ms | 5 ms | yes |
| `t_rfc` (t_ref) | 2.2 ms | 2.2 ms | yes |
| `t_dly` (t_delay) | 1.8 ms | 1.8 ms | yes |
| `w_syn` | 0.275 mV | 0.275 mV | yes |
| `f_poi` (Poisson scale) | 250 | "as in reference code" | — |
| `r_poi` (default rate) | 150 Hz | 150–200 Hz | yes |
| dt | 0.1 ms (Brian2 default clock) | 0.1 ms | yes |

The parameter **values** all match. Five **structural details** differ from CLAUDE.md 7.2. They are recorded in [ADR-0014 (Challenge)](../decisions/0014-challenge-reference-model-details.md). The most important one: **Poisson input goes into `v`, not `g`**, with a weight of 0.275 × 250 = 68.75 mV per event, enough to make the target fire on every event.

Two questions from Phase 0 were settled in Phase 1 by running Brian2 2.10.1 itself ([ADR-0016](../decisions/0016-verified-neuron-model.md)):

- **Refractory neurons ignore input.** We had expected `on_pre` (`g += w`) to keep adding to a refractory neuron's g. Running Brian2 showed the opposite: arrivals during refractoriness are discarded. Our Phase 0 reading was wrong.
- **`w = 0` in `eq_rst`** assigns to a throwaway local variable and has no effect.

## 4. Stimulation (Poisson input)

**Shiu:** for each stimulated neuron, one `PoissonInput(target_var='v', N=1, rate=r_poi, weight=w_syn*f_poi)`. In each 0.1 ms step this adds 68.75 mV with probability `rate × dt` (0.015 at 150 Hz). The stimulated neuron's refractory period is set to 0. A second group can be stimulated at `r_poi2`.

**Eon:** `torch.bernoulli(rates × dt/1000)` per step, times 250, times 0.275, added to `v`. Same as Shiu in distribution.

**Silencing (Shiu):** sets every outgoing weight of the silenced neuron to 0. For us this must produce a *new* weight matrix, never edit the shared one.

## 5. Running and recording

**Shiu:** `n_run = 30` trials of `t_run = 1000 ms`, run in parallel with joblib. The model is rebuilt for every trial. All spikes are recorded with a `SpikeMonitor` and saved as parquet (`t`, `trial`, `flywire_id`, `exp_name`). Rates are spike count ÷ trial duration, averaged over trials (`utils.get_rate`). There is **no explicit seed**: trials differ through Brian2's own random state. For us, every timeline needs an explicit seeded generator ([ADR-0007](../decisions/0007-determinism-first.md)).

**Eon:** trials are batched along a first tensor dimension (`[batch, neurons]`), which is the same layout CLAUDE.md suggests for batched free-will branches in Phase 5.

## 6. How Eon's PyTorch step differs from Brian2

Worth knowing, so we do not copy a port's quirks by accident:

1. **Euler, not exact integration.** `v += dt/τ_m × (g − (v − V_rest))`, `g ← g × (1 − dt/τ_syn)`. Brian2 `linear` uses the exact exponential solution. With dt = 0.1 ms the difference is small but real.
2. **float32**, on GPU when available.
3. **Arrivals during refractory are dropped**, by multiplying the delayed input by a "not refractory" mask. *Phase 1 update:* this matches Brian2 (we had first thought it differed).
4. **v is not explicitly frozen** during refractory. In practice it stays at rest, because g was reset to 0 and arrivals are masked.
5. Delay is a rolling buffer of `int(1.8 / 0.1) + 1 = 19` slots, rolled with `torch.roll` every step. A ring-buffer index is cheaper and is planned for Tramlines.

## 7. The canonical experiment (for Phase 1, section 7.3)

The Shiu example notebook stimulates 21 right-hemisphere sugar GRNs and reads MN9.

- **The notebook's IDs are FlyWire v630 IDs.** 20 of the 21 also exist in v783; one (`720575940620900446`) does not. Eon's v783 version of the list replaces it with `720575940639259967`.
- The MN9 ID used in the notebook, `720575940660219265`, exists in both v630 and v783.
- Overall, only 106,220 of the 127,400 v630 root IDs survive unchanged into v783.

Per CLAUDE.md 7.1, **none of these hand-written IDs will be used.** Phase 1 looks up sugar GRNs and MN9 by cell type in a recorded annotation release, then compares the result against these lists as a sanity check.

## 8. Open items for Phase 1

- [x] Annotation source: `flywire_annotations` v2.1.0 ([ADR-0017](../decisions/0017-annotations-and-neuron-sets.md)).
- [x] Integration: exact, as Brian2 `linear` does ([ADR-0016](../decisions/0016-verified-neuron-model.md)). Euler was not adopted, since exact integration is what the reference runs and lets us match it spike for spike.
- [x] Brian2 behaviours from section 3 confirmed by running Brian2 (one corrected).
- [ ] Owner acknowledgement of [ADR-0014](../decisions/0014-challenge-reference-model-details.md) ([owner decisions](../owner-decisions.md), item 1).
- [x] Verified parameter table: [ADR-0016](../decisions/0016-verified-neuron-model.md) and `tramlines/brain/params.py`.
