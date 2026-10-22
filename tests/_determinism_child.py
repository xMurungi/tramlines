"""Run scenarios in a fresh process and print their fingerprints, one line per seed.

    python tests/_determinism_child.py <small|full|timeline-small|timeline-full> <seed> ...

Used by test (b) in test_determinism.py: a brand-new interpreter, with nothing
shared in memory, must produce the same bits as the test process.
"""

import hashlib
import sys

from _scenarios import by_name, run, timeline_by_name

from tramlines.brain.engine import enable_determinism

enable_determinism()
name, seeds = sys.argv[1], [int(s) for s in sys.argv[2:]]
if name.startswith("timeline"):
    timelines = timeline_by_name(name)
    for seed in seeds:
        timeline = timelines.timeline(seed)
        poses = timeline.run(timelines.total_ms)
        print(seed, hashlib.sha256(repr(poses).encode()).hexdigest(), timeline.fingerprint())
else:
    scenario = by_name(name)
    for seed in seeds:
        brain = scenario.brain(seed)
        record = run(brain, scenario.total_steps)
        print(seed, record.fingerprint(), brain.state.fingerprint())
