"""Bind all finished-floor consumer reads to one unchanged source state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.thin_bolted_finished_floor_steel import (
    ROOT,
    aggregate,
    consume_finished_state,
    sha,
    summarize,
)


def consume_bound_state(demand_path: Path) -> dict:
    payload = demand_path.read_bytes()
    expected_sha = hashlib.sha256(payload).hexdigest()
    expected_state = json.loads(payload)["state_id"]
    relative = str(demand_path.resolve().relative_to(ROOT))
    report = consume_finished_state(demand_path)
    if sha(demand_path) != expected_sha or report["source_sha256"].get(relative) != expected_sha:
        raise ValueError("demand source changed between support and component reads")
    if report["state"]["state_id"] != expected_state:
        raise ValueError("component state differs from initially audited source identity")
    report["source_sha256"][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    report["unchanged_input_binding"] = {"source_sha256_before_and_after": expected_sha,
                                         "state_id_before_and_after": expected_state,
                                         "component_report_source_and_state_match": True}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demands", type=Path)
    mode.add_argument("--aggregate", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued component evidence")
    report = consume_bound_state(args.demands) if args.demands else aggregate(args.aggregate)
    report["source_sha256"][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "summary": summarize(report) if args.demands else
                      {"states": len(report["state_summaries"]), "governing_index": report["governing_sampled_flange_yield_index"]}}, indent=2))


if __name__ == "__main__":
    main()
