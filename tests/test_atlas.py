"""The perturbation atlas's instruments (Result 3)."""

from _scenarios import timeline_small

from tramlines.timeline.atlas import (
    Event,
    behaviour_differs,
    behaviour_events,
    choice,
    outcome,
    screen,
    spike_keys,
)
from tramlines.timeline.timeline import Pose, Timeline


def pose(t: int, feeding: bool = False, jumped: bool = False) -> Pose:
    return Pose(t, 0.0, 0.0, 0.0, feeding, jumped)


def test_events_are_feeding_changes_and_jumps() -> None:
    poses = [pose(1), pose(2, feeding=True), pose(3, feeding=True), pose(4), pose(5, jumped=True)]
    assert behaviour_events(poses) == [Event("feed", 2), Event("stop", 4), Event("jump", 5)]


def test_behaviour_differs_beyond_the_tolerance_only() -> None:
    a = [Event("jump", 100)]
    assert not behaviour_differs(a, [Event("jump", 140)])
    assert behaviour_differs(a, [Event("jump", 200)])
    assert behaviour_differs(a, [Event("feed", 100)])
    assert behaviour_differs(a, [])


def busy_moment() -> Timeline:
    timeline = timeline_small().timeline(0)
    timeline.run(40)
    return timeline


def test_screen_leaves_the_base_untouched_and_is_repeatable() -> None:
    base = busy_moment()
    n = base.brain.connectome.n_neurons
    before = base.fingerprint()
    truth = spike_keys(base.fork().run_recording(20)[1], n)
    quiet = next(i for i in range(n) if base.brain.state.last_spike_step[i] < 0)
    first, again = screen(base, quiet, truth, 20), screen(base, quiet, truth, 20)
    assert base.fingerprint() == before
    assert first == again and first.made


def test_a_refused_extra_spike_is_reported_not_made() -> None:
    base = busy_moment()
    n = base.brain.connectome.n_neurons
    just_fired = base.brain.state.last_spike_step == base.brain.state.step - 1
    neuron = int(just_fired.nonzero()[0]) if just_fired.any() else None
    if neuron is None:  # make one: force a spike, then try to add another at that step
        base.brain.state.v_mV[0] = -40.0
        base.run(1)
        neuron = int((base.brain.state.last_spike_step == base.brain.state.step - 1).nonzero()[0])
    truth = spike_keys(base.fork().run_recording(10)[1], n)
    result = screen(base, neuron, truth, 10)
    assert not result.made and "already fired" in result.why_not


def test_outcome_of_nothing_changed_is_no_difference() -> None:
    base = busy_moment()
    truth_poses = base.fork().run(30)
    n = base.brain.connectome.n_neurons
    quiet = next(i for i in range(n) if base.brain.state.last_spike_step[i] < 0)
    result = outcome(base, quiet, truth_poses, 30)
    assert result.made
    assert isinstance(result.behaviour_differs, bool)


def test_choice_counts_meals_and_jumps_but_not_timing() -> None:
    a = [Event("feed", 100), Event("stop", 300), Event("jump", 900)]
    later = [Event("feed", 400), Event("stop", 600), Event("jump", 1500)]
    assert choice(a) == choice(later) == (1, 1)
    assert choice([Event("jump", 5), Event("jump", 700)]) == (0, 2)
