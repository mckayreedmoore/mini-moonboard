"""Parent-only nominal grain-section comparison for the proposed knee bridge.

Loads remain the frozen mechanical actions and original physical gravity.
Only comparison sections include the two additional hypothetical v bores.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import sys
from functools import cache
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE / "rawlocal/remaining-block-transverse/attempt01"
RAW = HERE / "rawlocal/knee-bridge-grain"
SOURCE_HASH = "f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19"
CUT_HASH = "86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc"
PRODUCER_HASH = "b7636729f666633feed74eb274968dc92b5d06620b4806ae697c79160869c9c8"
BLOCKS = ("knee_outer_left_spine", "knee_outer_right_spine")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def imported(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def authenticate(pins):
    for name, digest in pins.items():
        require(sha(ROOT / name) == digest, f"source changed: {name}")


def build(output, proposal_path, expected_proposal_hash):
    output, proposal_path = Path(output).resolve(), Path(proposal_path).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate output child required")
    require(sha(proposal_path) == expected_proposal_hash, "proposal differs from parent frozen hash")
    require(sha(SOURCE / "checks.json") == SOURCE_HASH, "twenty-cleat source changed")
    require(sha(SOURCE / "cuts.jsonl.gz") == CUT_HASH, "saved cuts changed")
    require(sha(SOURCE / "producer.py.snapshot") == PRODUCER_HASH, "saved producer changed")
    proposal, source = read(proposal_path), read(SOURCE / "checks.json")
    require(proposal["status"] == "FINITE_PROPOSAL_STATIC_ARITHMETIC_COMPLETE"
            and not proposal["proposal_adopted"], "require completed unadopted proposal")
    pins = dict(source["source_sha256"])
    for path in (proposal_path, proposal_path.with_name("receipt.json"),
                 SOURCE / "checks.json", SOURCE / "cuts.jsonl.gz", SOURCE / "producer.py.snapshot",
                 Path(__file__).resolve()):
        pins[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in proposal["source_sha256"].items():
        require(name not in pins or pins[name] == digest, f"conflicting source pin: {name}")
        pins[name] = digest
    receipt = read(proposal_path.with_name("receipt.json"))
    require(receipt["output_sha256"]["checks.json"] == expected_proposal_hash,
            "proposal receipt differs")
    authenticate(pins)
    old = imported(SOURCE / "producer.py.snapshot", "bridge_grain_original")
    physical = imported(old.PHYSICAL, "bridge_grain_physical")
    long = imported(old.LONG, "bridge_grain_longitudinal")
    sections = imported(HERE / "corner-timber-sections.py", "bridge_grain_geometry")
    net = imported(HERE / "corner-net-section.py", "bridge_grain_nominal")
    net.rectangle_torsion = cache(net.rectangle_torsion)
    geometry = read(HERE / "rawlocal/knee-spine-net-sections/attempt02/checks.json")["geometry"]
    members, results = [read(old.MEMBERS / name) for name in ("geometry.json", "member-results.json")]
    adapter, masses, current, contacts = [read(path) for path in (old.ADAPTER, old.MASS, old.CURRENT, old.CONTACTS)]
    factor = source["source_gravity_multiplier"]
    saved = {}
    with gzip.open(SOURCE / "cuts.jsonl.gz", "rt") as stream:
        for line in stream:
            record = json.loads(line)
            if record["block"] in BLOCKS and record["axis"] == 0:
                saved[(record["block"], record["case_id"], record["station_mm"], record["limit"])] = record
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "inputs-before.json", {"source_sha256": pins, "proposal_sha256": expected_proposal_hash})
    peaks, count, added_count, replay_error, area_fraction = {}, 0, 0, 0.0, {}
    coupon = None
    with (np.load(old.MEMBERS / "action-section-arrays.npz", allow_pickle=False) as arrays,
          gzip.open(output / "cuts.jsonl.gz", "wt") as stream):
        for body in BLOCKS:
            member = members["members"][body]
            original = geometry[body]
            modified = proposal["geometry_proposals"][body]["hypothetical_geometry"]
            require(modified["bores"][:4] == original["bores"] and len(modified["bores"]) == 6,
                    "proposal must preserve four old bores and add two")
            own = old.prepare_body(body, original, member, adapter, masses, current, contacts,
                                   physical, long, factor)
            points = arrays[body + "__point_xyz_mm"]
            point_rows = arrays[body + "__point_rows"]
            mechanical_mask = point_rows != -1
            extras = {b["station_mm"] + offset for b in modified["bores"][4:]
                      for offset in (-b["radius_mm"], 0.0, b["radius_mm"])}
            stations = sorted({key[2] for key in saved if key[0] == body} | extras)
            for case in old.CASES:
                refs = next(m["conditional_material"]["CF_only_reference_mpa"]
                            for c in results["cases"] if c["case_id"] == case
                            for m in c["members"] if m["member"] == body)
                if coupon is None:
                    coupon = net.rectangular_known_answer(refs)
                values = arrays[f"{case}__{body}__point_force_free_couple_xyz"]
                mechanical = old.action_prepared(physical, points[mechanical_mask], values[mechanical_mask],
                                                  own["frame"], own["start"])
                for station in stations:
                    volume, first = physical.volume_first(original, 0, station)
                    timber = np.r_[volume * own["body_force"],
                                   np.cross(np.asarray(first) - [station * volume, 0, 0], own["body_force"])]
                    section = sections.section(modified, station)
                    old_section = sections.section(original, station)
                    area_fraction[f"{body}:{station}"] = section["net_area_mm2"] / old_section["net_area_mm2"]
                    for limit in ("before", "after"):
                        q = -physical.point_gravity(mechanical, 0, station, limit) - timber \
                            - physical.point_gravity(own["hardware"], 0, station, limit)
                        identity = (body, case, station, limit)
                        if identity in saved:
                            error = float(np.max(abs(q - saved[identity]["signed_internal_n_nmm"])))
                            replay_error = max(replay_error, error)
                            require(error < 1e-6, "original full grain wrench replay differs")
                        else:
                            added_count += 1
                        nominal = net.nominal_section(q, section["regions"], refs)
                        corners = [c for r in nominal["regions"] for c in r["longitudinal_corners"]]
                        metrics = {name: max(c["comparisons"][field] for c in corners) for name, field in (
                            ("tension_over_Ft", "total_tension_over_Ft"),
                            ("compression_over_Fc", "total_compression_over_Fc"),
                            ("bending_over_Fb", "absolute_bending_over_Fb"),
                            ("normal_reference_sum", "axial_plus_bending_reference_sum"))}
                        metrics["regional_shear_torsion_over_Fv"] = max(
                            r["same_state_shear_bound_over_Fv"] for r in nominal["regions"])
                        record = {"block": body, "case_id": case, "station_mm": station, "limit": limit,
                                  "source_signed_grain_cut_n_nmm": q.tolist(), "metrics": metrics,
                                  "section": section, "nominal": nominal}
                        stream.write(json.dumps(record, allow_nan=False, separators=(",", ":")) + "\n")
                        for name, value in metrics.items():
                            if name not in peaks or value > peaks[name]["value"]:
                                peaks[name] = {"value": value, "block": body, "case_id": case,
                                               "station_mm": station, "limit": limit}
                        count += 1
    authenticate(pins)
    report = {"status": "FINITE_MODIFIED_GRAIN_COMPARISON_COMPLETE", "source_sha256": pins,
              "proposal_sha256": expected_proposal_hash, "cut_count": count,
              "added_center_tangency_limit_count": added_count,
              "original_cut_replay_max_error_n_nmm": replay_error,
              "area_fraction_by_station": area_fraction, "peak_witnesses": peaks,
              "all_named_nominal_comparisons_below_one": all(p["value"] < 1 for p in peaks.values()),
              "rectangular_known_answer": coupon, "regional_hypotheses": net.ASSUMPTIONS,
              "scope": "Actual modified grain-section rectangles with frozen full six-component actions and original physical gravity; equal symmetric bridge end pairs cancel on grain cuts. No global gravity adoption, elastic compatibility, local concentration or splitting resistance.",
              "proposal_adopted": False, "current_geometry_changed": False,
              "physical_release": False, "complete_joint_acceptance": False}
    dump(output / "checks.json", report)
    dump(output / "receipt.json", {"source_sha256": pins, "sources_authenticated_before_and_after": True,
                                   "output_sha256": {name: sha(output / name) for name in (
                                       ".gitignore", "inputs-before.json", "producer.py.snapshot", "cuts.jsonl.gz", "checks.json")},
                                   "proposal_adopted": False, "physical_release": False})
    return {"status": report["status"], "cut_count": count, "added_cut_count": added_count,
            "all_named_nominal_comparisons_below_one": report["all_named_nominal_comparisons_below_one"],
            "peak_witnesses": peaks, "checks_sha256": sha(output / "checks.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--proposal-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.proposal, args.proposal_sha256), allow_nan=False))
