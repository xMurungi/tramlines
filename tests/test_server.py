"""The server: ghost-versus-live scoring, messages, and the WebSocket stream (ADR-0033)."""

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from tramlines.brain.data import DATA_DIR
from tramlines.brain.neurons import ANNOTATIONS_FILE
from tramlines.server import app as server
from tramlines.server.history import RunHistory
from tramlines.server.protocol import Chunk, decode_indices, encode_indices


def rows(
    start: int, end: int, x0: float = 0.0
) -> list[tuple[int, float, float, float, bool, bool]]:
    return [(t, x0 + t * 0.01, 0.0, 0.0, False, False) for t in range(start, end)]


def chunk(start: int, end: int) -> Chunk:
    return Chunk(
        t0_ms=start, poses=rows(start + 1, end + 1), fired=encode_indices(np.array([1])), spikes=1
    )


def test_indices_round_trip() -> None:
    indices = np.array([0, 7, 138_638], dtype=np.uint32)
    assert decode_indices(encode_indices(indices)).tolist() == indices.tolist()


def test_ghost_scored_against_live_exactly_once() -> None:
    history = RunHistory()
    history.add_ghost(0, rows(1, 201))  # predicted 200 ms ahead, before live exists
    assert (history.compared_ms, history.matched_ms) == (0, 0)
    history.add_chunk(chunk(0, 100))
    assert (history.compared_ms, history.matched_ms) == (100, 100)
    history.add_chunk(chunk(100, 200))
    assert (history.compared_ms, history.matched_ms) == (200, 200)
    history.add_chunk(chunk(100, 200))  # a repeat changes nothing
    assert history.compared_ms == 200


def test_a_wrong_ghost_is_counted_as_a_miss() -> None:
    history = RunHistory()
    history.add_chunk(chunk(0, 100))
    history.add_ghost(0, rows(1, 101, x0=1e-12))  # off by a trillionth of a millimetre
    assert (history.compared_ms, history.matched_ms) == (100, 0)


@pytest.mark.skipif(not (DATA_DIR / ANNOTATIONS_FILE).exists(), reason="needs fetch_data.py")
def test_stream_replays_a_cached_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAMLINES_ARENA", "default")
    monkeypatch.setenv("TRAMLINES_SECONDS", "0.2")
    monkeypatch.setenv("TRAMLINES_HORIZON_MS", "100")
    monkeypatch.setattr(server, "PROJECTIONS", tmp_path)
    cached = {
        "chunks": [chunk(0, 100).model_dump(), chunk(100, 200).model_dump()],
        "ghosts": [[100, rows(101, 201)]],
    }
    (tmp_path / f"{server.Settings().key}.json").write_text(json.dumps(cached))
    with TestClient(server.app) as client, client.websocket_connect("/stream") as ws:
        kinds = [json.loads(ws.receive_text()) for _ in range(6)]
    assert [k["type"] for k in kinds] == ["hello", "chunk", "chunk", "ghost", "match", "status"]
    assert kinds[0]["n_neurons"] == 138_639
    assert (kinds[4]["compared_ms"], kinds[4]["matched_ms"]) == (100, 100)
    assert kinds[5]["cached"] is True and kinds[5]["computing"] is False
