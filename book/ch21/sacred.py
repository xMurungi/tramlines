# book: needs-data
"""Chapter 21: three ways to start from the same moment, and proof they agree."""

import subprocess
import sys
import tempfile
from pathlib import Path

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import Brain, enable_determinism
from tramlines.brain.neurons import REFERENCE_SUGAR_GRNS, load_catalog

enable_determinism()
wiring = load_connectome()
sugar = load_catalog().index_of(REFERENCE_SUGAR_GRNS)


def future(seed: int) -> str:
    """Run 50 ms of sugar from the start and fingerprint everything that happened."""
    brain = Brain(wiring, sugar, seed=seed)
    brain.set_input_rates(200.0)
    return brain.run(500).fingerprint() + brain.state.fingerprint()


if sys.argv[1:] == ["child"]:  # the fresh-process copy of this program
    print(future(seed=3))
    sys.exit()

# (a) Fork in the middle; both halves must agree.
brain = Brain(wiring, sugar, seed=3)
brain.set_input_rates(200.0)
brain.run(200)
twin = brain.fork()
same = brain.run(300).fingerprint() == twin.run(300).fingerprint()
print("fork:          ", "identical" if same else "DIFFERENT")

# (b) A brand-new Python process, sharing nothing with this one.
child = subprocess.run([sys.executable, __file__, "child"], capture_output=True, text=True)
same = child.stdout.strip() == future(seed=3)
print("fresh process: ", "identical" if same else "DIFFERENT")

# (c) Save to disk at 20 ms, load into a new brain, continue.
brain = Brain(wiring, sugar, seed=3)
brain.set_input_rates(200.0)
brain.run(200)
path = Path(tempfile.mkdtemp()) / "moment.pt"
brain.save(path)
restored = Brain.load(path, wiring)
same = brain.run(300).fingerprint() == restored.run(300).fingerprint()
print("save and load: ", "identical" if same else "DIFFERENT")
