"""Capture a monotonic first-state DAT extension without altering the prefix."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    folder = Path(__file__).resolve().parent
    capture = json.loads((folder / "capture.json").read_text())
    run = Path(capture["source_run"])
    target = folder / "pilot.dat.angular-extension"
    report_path = folder / "angular-extension.json"
    if target.exists() or report_path.exists():
        raise RuntimeError("preserve existing extension evidence")
    observed = json.loads(subprocess.check_output(
        ["docker", "inspect", capture["container_id"]], text=True
    ))[0]
    if observed["Id"] != capture["container_id"] or not observed["State"]["Running"]:
        raise RuntimeError("expected exact live native container")
    if observed["Mounts"] != capture["mounts"]:
        raise RuntimeError("native mounts changed")
    for name, expected in capture["input_sha256"].items():
        if digest(run / name) != expected:
            raise RuntimeError(f"input changed: {name}")
    initial = folder / "pilot.dat"
    initial_info = capture["output_prefixes"]["pilot.dat"]
    if initial.stat().st_size != initial_info["bytes"] or digest(initial) != initial_info["sha256"]:
        raise RuntimeError("initial DAT prefix changed")
    parser_path = folder.parent / "first-state-contact-output-audit-attempt01/audit_first_state_contact_output.py"
    parser_sha = digest(parser_path)
    spec = importlib.util.spec_from_file_location("angular_parser", parser_path)
    assert spec and spec.loader
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    parser.CASE = run
    pairs = parser.input_pairs()
    # Only read through the last first-state angular numeric row. Later states
    # and their potentially buffered tails are deliberately not captured.
    content = bytearray()
    last_header_seen = False
    with (run / "pilot.dat").open("rb") as stream:
        for line in stream:
            content.extend(line)
            decoded = line.decode("ascii").rstrip("\r\n")
            if last_header_seen and decoded.strip():
                fields = decoded.split()
                if len(fields) != 3 or not all(Decimal(x).is_finite() for x in fields):
                    raise RuntimeError("last angular row malformed")
                break
            match = parser.ANGULAR_RE.fullmatch(decoded)
            if match:
                groups = match.groupdict()
                if abs(Decimal(groups["time"]) - Decimal.from_float(.0005)) > parser.half_quantum(groups["time"]):
                    raise RuntimeError("second state before complete first-state angular output")
                last_header_seen = (
                    groups["variable"].strip() == "CFS"
                    and groups["role"].strip() == "pair_offset_couple"
                    and int(groups["tie"]) == 35
                )
        else:
            raise RuntimeError("first-state angular output not complete yet")
    n = initial_info["bytes"]
    if len(content) <= n or hashlib.sha256(content[:n]).hexdigest() != initial_info["sha256"]:
        raise RuntimeError("live DAT is not a strict extension of the frozen prefix")
    with target.open("xb") as stream:
        stream.write(content)
    records, coverage = parser.read_angular(target, pairs, Decimal(".0005"))
    for name, expected in capture["input_sha256"].items():
        if digest(run / name) != expected:
            raise RuntimeError(f"input changed during capture: {name}")
    with (run / "pilot.dat").open("rb") as stream:
        if hashlib.sha256(stream.read(len(content))).hexdigest() != digest(target):
            raise RuntimeError("native prefix changed during capture")
    report = {
        "schema": "parent_authenticated_angular_prefix_extension/v1",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "source_run": str(run),
        "container_id": capture["container_id"],
        "container_state_observed": observed["State"],
        "original_capture_sha256": digest(folder / "capture.json"),
        "original_prefix": initial_info,
        "extended_prefix": {"path": target.name, "bytes": len(content), "sha256": digest(target)},
        "appended_bytes": len(content) - n,
        "producer_sha256": digest(Path(__file__)),
        "angular_parser_sha256": parser_sha,
        "inputs_unchanged_before_and_after": True,
        "original_prefix_preserved": True,
        "selected_state": {"step": 1, "increment": 1, "time": ".0005"},
        "angular_coverage": coverage,
        "finite_numeric_value_count": sum(len(row["values"]) for row in records.values()),
        "terminal_execution": False,
        "angular_equilibrium_checked": False,
        "whole_horizon_success": False,
        "mechanical_acceptance": False,
    }
    with report_path.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
