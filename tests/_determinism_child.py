"""Run scenarios in a fresh process and print their fingerprints, one line per seed.

    python tests/_determinism_child.py <small|full> <seed> [<seed> ...]

Used by test (b) in test_determinism.py: a brand-new interpreter, with nothing
shared in memory, must produce the same bits as the test process.
"""

import sys

from _scenarios import by_name, run

from tramlines.brain.engine import enable_determinism

enable_determinism()
scenario = by_name(sys.argv[1])
for seed in map(int, sys.argv[2:]):
    brain = scenario.brain(seed)
    record = run(brain, scenario.total_steps)
    print(seed, record.fingerprint(), brain.state.fingerprint())
