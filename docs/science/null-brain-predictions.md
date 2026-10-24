# Result 2: predictions written before the 75% and 90% runs finished

Written 2026-10-24 while `null_brain_study.py --fractions 0.75 0.9` was still running and
before any of its output existed, so these can be checked honestly. Criteria are the
ones in `scripts/plot_null_brain.py` (walks: > 10 mm in the arena; feeds: any feeding on
food; refuses laced food: no feeding; escapes: a jump under the shadow; quiet: fewer
than 3,000 neurons active in the arena). Three null brains per share.

| Rewired | walks | feeds on food | refuses laced | escapes | quiet |
|---|---|---|---|---|---|
| 75% | 1–3 of 3 | 0–1 of 3 | 3 of 3 (nothing drives MN9) | 1–2 of 3 | 0–2 of 3 |
| 90% | 0–1 of 3 | 0 of 3 | 3 of 3 | 0–1 of 3 | 2–3 of 3 (activity dying out, as at 100%) |

Reasoning: at 50% feeding is already weak (MN9 5–12 Hz) and the shadow's drive to GF has
halved; at 100% everything is silent. If the results differ from this table, the
write-up reports the difference.

## Decoder-free test: predictions written before it was built or run

Written 2026-10-24, before `scripts/decoder_free_study.py` existed. The test ignores the
readouts and decoder. Held in four situations (walking ground, food, bitter, shadow; 1 s,
3 seeds), it counts neurons (excluding every driven input neuron) that respond to a sense
(≥ 5 Hz above walking ground on average, and above it in every seed), groups them by
synapses from that sense, and asks whether the situation can be read from neurons two or
more synapses from any input (hold out one seed; chance 25%).

- **Real wiring:** tens to hundreds of responsive neurons per sense, many 2+ synapses deep;
  the situation read correctly from deep neurons in 12/12 held-out trials.
- **Full null brains:** responsive neurons mostly 1 synapse from the sense, few at 2, almost
  none at 3+. The situation is still read above chance (activity reaches hundreds of
  non-input neurons), most likely 75–100%, i.e. **random wiring carries sense-specific
  signals, just not to the neurons that move the body.** If instead it is near chance, the
  null brain's failure is not only a decoder artefact.
- **Partial rewiring (10%, 50%, 90%):** in between, closer to real at 10%.
