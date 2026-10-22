"""Watch the machine while experiments run: CPU, memory, swap, thermal pressure (ADR-0029).

    uv run python scripts/monitor_system.py --label divergence &   # start
    kill %1                                                        # stop: prints the peaks

Samples every few seconds into `.private/monitoring/<label>.csv`, which is
git-ignored: readings describe the owner's machine and stay private. The point is
to learn safe load thresholds (how many workers, how long) before running bigger
experiments.

macOS only, no admin rights: CPU and memory from `top`, `sysctl` and `ps`;
thermal pressure from `ProcessInfo.thermalState` via a small helper compiled into
`.private/bin/thermal_state` (built on first use). Fan speed and temperatures need
`sudo powermetrics`, which this script does not attempt.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from types import FrameType

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / ".private"
HELPER = PRIVATE / "bin" / "thermal_state"
HELPER_SOURCE = """import Foundation
let names = ["nominal", "fair", "serious", "critical"]
print(names[ProcessInfo.processInfo.thermalState.rawValue])
"""
FIELDS = [
    "time_s",
    "cpu_user_pct",
    "cpu_sys_pct",
    "cpu_idle_pct",
    "load_1m",
    "mem_used_gb",
    "mem_compressed_gb",
    "mem_free_gb",
    "swap_used_gb",
    "mem_pressure",
    "mem_available_pct",
    "python_procs",
    "python_rss_gb",
    "python_cpu_pct",
    "thermal",
]


def _run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout


def _gb(text: str) -> float:
    number, unit = float(text[:-1]), text[-1]
    return number / {"K": 1024**2, "M": 1024, "G": 1, "T": 1 / 1024}[unit]


def thermal_state() -> str:
    if not HELPER.exists():
        HELPER.parent.mkdir(parents=True, exist_ok=True)
        source = HELPER.with_suffix(".swift")
        source.write_text(HELPER_SOURCE)
        _run("swiftc", "-O", str(source), "-o", str(HELPER))
    return _run(str(HELPER)).strip() or "unknown"


def sample(started: float, thermal: str) -> dict[str, object]:
    top = _run("top", "-l", "1", "-n", "0")
    cpu = re.search(r"CPU usage: ([\d.]+)% user, ([\d.]+)% sys, ([\d.]+)% idle", top)
    mem = re.search(r"PhysMem: (\S+) used .*?, (\S+) compressor\), (\S+) unused", top)
    swap = re.search(r"used = ([\d.]+[KMGT])", _run("sysctl", "-n", "vm.swapusage"))
    # macOS's own judgement: 1 normal, 2 warning, 4 critical. "Unused" memory near zero is
    # normal on macOS (spare memory becomes cache); pressure and swap growth are the signals.
    pressure = {"1": "normal", "2": "warning", "4": "critical"}.get(
        _run("sysctl", "-n", "kern.memorystatus_vm_pressure_level").strip(), "unknown"
    )
    available = _run("sysctl", "-n", "kern.memorystatus_level").strip()
    rss_kb, cpu_pct, count = 0, 0.0, 0
    for line in _run("ps", "-A", "-o", "rss=,%cpu=,comm=").splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and "python" in parts[2].lower():
            rss_kb, cpu_pct, count = rss_kb + int(parts[0]), cpu_pct + float(parts[1]), count + 1
    return {
        "time_s": round(time.time() - started, 1),
        "cpu_user_pct": cpu.group(1) if cpu else "",
        "cpu_sys_pct": cpu.group(2) if cpu else "",
        "cpu_idle_pct": cpu.group(3) if cpu else "",
        "load_1m": round(os.getloadavg()[0], 2),
        "mem_used_gb": round(_gb(mem.group(1)), 2) if mem else "",
        "mem_compressed_gb": round(_gb(mem.group(2)), 2) if mem else "",
        "mem_free_gb": round(_gb(mem.group(3)), 2) if mem else "",
        "swap_used_gb": round(_gb(swap.group(1)), 2) if swap else "",
        "mem_pressure": pressure,
        "mem_available_pct": available,
        "python_procs": count,
        "python_rss_gb": round(rss_kb / 1024**2, 2),
        "python_cpu_pct": round(cpu_pct, 1),
        "thermal": thermal,
    }


def summarize(rows: list[dict[str, object]]) -> str:
    def peak(key: str) -> float:
        values = [float(str(r[key])) for r in rows if r[key] != ""]
        return max(values) if values else float("nan")

    states = sorted({str(r["thermal"]) for r in rows})
    pressures = sorted({str(r["mem_pressure"]) for r in rows})
    lowest_available = min(int(str(r["mem_available_pct"]) or 100) for r in rows)
    return (
        f"{len(rows)} samples over {rows[-1]['time_s']} s | peak load {peak('load_1m')} | "
        f"peak python CPU {peak('python_cpu_pct')}% | "
        f"peak python memory {peak('python_rss_gb')} GB | "
        f"min free memory {-peak_neg(rows, 'mem_free_gb')} GB | "
        f"peak swap {peak('swap_used_gb')} GB | "
        f"memory pressure seen: {', '.join(pressures)} (lowest available {lowest_available}%) | "
        f"thermal states seen: {', '.join(states)}"
    )


def peak_neg(rows: list[dict[str, object]], key: str) -> float:
    values = [-float(str(r[key])) for r in rows if r[key] != ""]
    return max(values) if values else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", default="session")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between samples")
    parser.add_argument(
        "--seconds", type=float, default=0, help="stop after this long (0 = until killed)"
    )
    args = parser.parse_args()

    out = PRIVATE / "monitoring" / f"{args.label}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    stop = False

    def on_signal(signum: int, frame: FrameType | None) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    started = time.time()
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        while not stop and (args.seconds == 0 or time.time() - started < args.seconds):
            row = sample(started, thermal_state())
            writer.writerow(row)
            f.flush()
            rows.append(row)
            time.sleep(max(0.0, args.interval - 3.0))  # each sample itself takes about 3 s
    if rows:
        print(summarize(rows))
        (out.with_suffix(".summary.txt")).write_text(summarize(rows) + "\n")


if __name__ == "__main__":
    main()
