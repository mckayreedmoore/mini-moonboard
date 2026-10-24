"""Complete the preserved v6 bolt review's same-receiver pair census.

Reuse the issued occurrence checks without changing their forces, geometry or
producer. Neighboring shafts are enumerated by each shared wood receiver,
independently of their other receivers or shaft direction. Unclassified
connection relationships receive no invented spacing rule or capacity factor.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from scripts import eoere_bolt_pair_census as census
from scripts import eoere_v6_bolt_geometry_review as previous
from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha

OWN = Path(__file__).resolve()
OUT = previous.analysis.BASE / "bolt-geometry-review-v2"
PUBLIC = (
    ROOT / "docs/bolted-frame-development/owner-frame-v6/bolt-geometry-review-v2.json"
)


def upgrade_case(case, shafts):
    """Apply the complete same-host census to one authenticated field."""
    result = copy.deepcopy(case)
    neighbors = census.pair_census(
        shafts, result["wood_occurrences"], result["receiver_pairs"]
    )
    result["same_host_pairs"] = neighbors
    for row in result["wood_occurrences"]:
        row["reconstructed_affine_endpoint_pressures_on_host_N_per_mm"] = row.pop(
            "raw_affine_endpoint_pressures_on_host_N_per_mm"
        )
    for row in result["receiver_pairs"]:
        row["case_id"] = result["case_id"]
    added = [p for p in neighbors if not p["existing_connection_group_pair"]]
    for row in result["axes"]:
        if row["component_status"] != "FAIL" and any(
            row["axis_id"] in p["axes"] for p in added
        ):
            row["component_status"] = "UNRESOLVED"
    result["axis_status_counts"] = dict(
        Counter(r["component_status"] for r in result["axes"])
    )
    result["pair_census_counts"] = {
        "same_host_pairs": len(neighbors),
        "existing_connection_group_pairs": len(neighbors) - len(added),
        "additional_pairs_with_unresolved_applicability": len(added),
    }
    return result


def review(out):
    previous.require(
        not out.exists() and out.resolve().is_relative_to(ROOT / "fea/generated"),
        "fresh ignored review directory required",
    )
    pins = {
        ref(p)["path"]: sha(p)
        for p in (OWN, Path(census.__file__), Path(previous.__file__))
    }
    issued = read(previous.PUBLIC, pins)
    full = read(issued["full_review"]["path"], pins, issued["full_review"]["sha256"])
    for path, digest in full["source_sha256"].items():
        previous.require(sha(path) == digest, "issued source changed: " + path)
        pins[path] = digest
    geometry, fields, active_pins = previous.basis.load()
    pins.update(active_pins)
    previous.require(
        issued["analysis_geometry"] == ref(previous.analysis.GEOMETRY)
        and len(geometry["axes"]) == 96,
        "own v6 analytical geometry required",
    )
    by_case = {case: (binding, field) for _, case, binding, field in fields}
    previous.require(
        set(by_case) == {c["case_id"] for c in full["cases"]},
        "six own issued cases required",
    )
    result = copy.deepcopy(full)
    result["cases"] = []
    for case in full["cases"]:
        binding, field = by_case[case["case_id"]]
        previous.require(case["field"] == binding, "issued case field changed")
        shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
        result["cases"].append(upgrade_case(case, shafts))
    result.update(
        schema="eoere_current96_bolt_geometry_review/v2",
        preceding_geometry_review=ref(previous.PUBLIC),
        same_host_pair_census_complete=True,
        neighbor_pair_scope="all unordered shaft pairs sharing each analytical wood receiver; no distance cutoff",
        source_sha256={**full["source_sha256"], **pins},
    )
    result["qualification_limits"] += [
        "The preceding occurrence report omitted same-host pairs with different complete receiver sets. This version enumerates them independently of receiver order and shaft direction; their connection-row applicability remains unresolved.",
        "Affine endpoint pressures are reconstructed from each admitted host force and midpoint couple, rather than sampled raw pressures.",
        "Affected-pair measurements retain the first case's explicitly labeled load classification; geometry alone is not a load-direction verdict.",
    ]
    for path, digest in result["source_sha256"].items():
        previous.require(sha(path) == digest, "source changed during review: " + path)
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    (out / "census-snapshot.py").write_bytes(Path(census.__file__).read_bytes())
    previous.write_new(out / "full-review.json", result)
    summary = previous.public_summary(result, out / "full-review.json")
    summary.update(
        producer=ref(OWN),
        occurrence_producer=ref(previous.OWN),
        census_producer=ref(Path(census.__file__)),
    )
    for row, case in zip(summary["case_summaries"], result["cases"], strict=True):
        row["pair_census_counts"] = case["pair_census_counts"]
    # Pair geometry is identical in all six frozen fields; complete intervals
    # and case-specific component rules stay in the ignored full report.
    summary["additional_same_host_pairs"] = [
        {
            k: p[k]
            for k in (
                "host",
                "axes",
                "parallel_bore_axes",
                "actual_spacing_mm",
                "component_status",
                "complete_Cdelta",
                "complete_joint_qualified",
            )
        }
        for p in result["cases"][0]["same_host_pairs"]
        if not p["existing_connection_group_pair"]
    ]
    return result, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    previous.require(
        not args.publish or not PUBLIC.exists(), "fresh public v2 review required"
    )
    result, summary = review(args.out.resolve())
    if args.publish:
        previous.write_new(PUBLIC, summary)
    print(
        json.dumps(
            {
                "full_review": summary["full_review"],
                "case_pair_counts": [c["pair_census_counts"] for c in result["cases"]],
                "complete_Cdelta": None,
                "complete_joint_qualified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
