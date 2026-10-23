# book: needs-data
"""Chapter 22: send a copy of the fly one second ahead, then watch the fly catch up."""

from tramlines.brain.connectome import load_connectome
from tramlines.brain.engine import enable_determinism
from tramlines.brain.neurons import load_catalog
from tramlines.timeline.timeline import Timeline
from tramlines.world.arena import DECISION_ARENA
from tramlines.world.decoder import FlyDecoder
from tramlines.world.fly import DEFAULT_START
from tramlines.world.senses import FlySenses

enable_determinism()
catalog = load_catalog()
fly = Timeline(
    load_connectome(),
    DECISION_ARENA,
    FlySenses.from_catalog(catalog),
    FlyDecoder.from_catalog(catalog),
    seed=0,
    start=DEFAULT_START,
)
fly.run(500)  # half a second of life

ghost = fly.fork()
prophecy = ghost.run(1000)  # the ghost lives the next second first

print(f"now: t = {fly.fly.time_ms} ms, fly at ({fly.fly.x_mm:.2f}, {fly.fly.y_mm:.2f}) mm")
end = prophecy[-1]
print(f"the ghost says: at t = {end.time_ms} ms it will be at ({end.x_mm:.2f}, {end.y_mm:.2f}) mm")

reality = fly.run(1000)  # now the fly lives that second itself
end = reality[-1]
print(f"the fly:        at t = {end.time_ms} ms it is at   ({end.x_mm:.2f}, {end.y_mm:.2f}) mm")

matched = sum(p == q for p, q in zip(prophecy, reality, strict=True))
print(f"milliseconds predicted: {len(prophecy)}, matched exactly: {matched}")
print("brains identical at the end:", fly.fingerprint() == ghost.fingerprint())
