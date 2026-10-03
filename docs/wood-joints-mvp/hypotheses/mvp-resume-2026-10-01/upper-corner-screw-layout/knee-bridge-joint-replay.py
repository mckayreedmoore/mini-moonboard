"""Parent-run, six-case static replay of the two proposed knee spines.

Consume the completed fresh member actions. Replace their mapped gravity once
with retained six-bore timber gravity and the declared hardware point actions.
This supplies finite static allocations and reference comparisons only.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import platform
import sys
from functools import cache
from itertools import pairwise
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-joint-replay"
FRESH = HERE.parent / "member-screen-attempt02/knee-bridge-gravity01"
SOURCE = HERE / "rawlocal/remaining-block-transverse/attempt01"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02"
PROPOSAL = HERE / "rawlocal/knee-spine-reinforcement/attempt01"
GEOMETRY = HERE / "rawlocal/knee-spine-net-sections/attempt02/checks.json"
BLOCKS = ("knee_outer_left_spine", "knee_outer_right_spine")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
TOL = 1e-6
FORCE_GATE, MOMENT_GATE = 0.1, 2.0  # Original member-screen whole-body gates.
PINS = {
    FRESH / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    FRESH / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    FRESH / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    FRESH / "inputs.json": "34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    GRAVITY / "receipt.json": "315c16d2a592b12dcd0160af47f9d4bababb6afaf54c6c74ddcbd41e01d45b6c",
    FRAME / "response/comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response/response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    FRAME / "receipt.json": "6acb01eb1b07dc9f9175cb3a0e916fe74a9a32a7b90941cf3b18e84a24d9c599",
    INTEGRATION / "manifest.json": "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    INTEGRATION / "receipt.json": "8a2813419289bee46e2e0985ab702a602a8ff3a0d3aacdd43d1aad841c92c8df",
    SOURCE / "checks.json": "f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19",
    SOURCE / "receipt.json": "dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519",
    SOURCE / "cuts.jsonl.gz": "86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc",
    SOURCE / "producer.py.snapshot": "b7636729f666633feed74eb274968dc92b5d06620b4806ae697c79160869c9c8",
    PROPOSAL / "checks.json": "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778",
    PROPOSAL / "receipt.json": "991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819",
    HERE / "knee-spine-reinforcement.py": "2ecd3e799dc9929b2524b3fd17efd853ea2a0c0e57dcd3da5d7506267d7c0741",
    GEOMETRY: "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
    HERE / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
}
FLAGS = {
    "proposal_adopted": False,
    "authority_changed": False,
    "original_sources_changed": False,
    "historical_force_acceptance_transferred": False,
    "fresh_member_elementary_acceptance_transferred": False,
    "global_compatibility_acceptance_transferred": False,
    "local_elastic_compatibility_solved": False,
    "actual_changed_hole_stiffness_qualified": False,
    "hardware_capacity_qualified": False,
    "installation_preload_credited": False,
    "new_lateral_capacity_established": False,
    "new_receiver_interface_added": False,
    "floor_restraint_added": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "frame_native_or_CAD_run": False,
    "helper_pipelines_coupons_tests_or_reviews_run": False,
    "gravity_delta_in_consumed_global_frame": True,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    path = Path(path)
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def line(stream, value):
    stream.write(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path)
    require(path not in pins or pins[path] == digest, f"conflicting source pin: {key(path)}")
    pins[path] = digest


def inherit(pins, document):
    for name, digest in document["source_sha256"].items():
        bind(pins, ROOT / name, digest)


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen source: {key(path)}")


def imported(path, name):
    """Load inert definitions; none of the imported build/run/coupon APIs run."""
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    require(spec is not None, f"helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def close(actual, expected, label, tolerance=TOL):
    error = np.asarray(actual) - np.asarray(expected)
    require(np.isfinite(error).all() and np.max(abs(error)) < tolerance, label)
    return float(np.max(abs(error)))


def whole_gate(wrench, label):
    require(np.isfinite(wrench).all(), f"nonfinite {label}")
    require(np.max(abs(wrench[:3])) <= FORCE_GATE and np.max(abs(wrench[3:])) <= MOMENT_GATE,
            f"whole-body closure failed: {label}: {wrench.tolist()}")


def about_start(work, center, start, frame):
    """W uses N and N*m about the physical node mean; cuts use local N,N*mm."""
    return np.r_[frame @ work[:3], frame @ (1000 * work[3:] + np.cross(center - start, work[:3]))]


def global_wrench(local, frame, start):
    force, moment = frame.T @ local[:3], frame.T @ local[3:]
    return np.r_[force, moment + np.cross(start, force)]


def node_mean_wrench(local, own, center):
    value = global_wrench(local, own["frame"], own["start"])
    value[3:] -= np.cross(center, value[:3])
    return value


def cut(physical, mechanical, own, axis, station, limit, volume_function):
    volume, first = volume_function(own["clip_geometry"], axis, station)
    offset = np.eye(3)[axis] * station
    timber = np.r_[volume * own["body_force"],
                   np.cross(np.asarray(first) - offset * volume, own["body_force"])]
    hardware = physical.point_gravity(own["hardware"], axis, station, limit)
    mechanics = physical.point_gravity(mechanical, axis, station, limit)
    internal = -mechanics - timber - hardware
    perm = [axis, (axis + 1) % 3, (axis + 2) % 3]
    return {
        "axis": axis, "station_mm": float(station), "limit": limit,
        "signed_internal_n_nmm": np.r_[internal[:3][perm], internal[3:][perm]].tolist(),
        "mechanical_negative_half_n_nmm": np.r_[mechanics[:3][perm], mechanics[3:][perm]].tolist(),
        "physical_gravity_negative_half_n_nmm": np.r_[(timber + hardware)[:3][perm],
                                                     (timber + hardware)[3:][perm]].tolist(),
    }


def unit_actions(body, member, points, point_rows, rows, D, names, center):
    """Use the original extraction recipe, including every rigid free couple.

    Row ownership fixes the force sign. The full -D row supplies the moment
    about the physical node mean; subtracting the point lever arm gives its
    free couple. No old scalar force is divided, including at zero force.
    """
    require(len(points) == len(point_rows) == len(member["point_action_ids"]), "action census differs")
    incident = {r["row"] for r in rows if body in (r["ownership"]["first_body"], r["ownership"]["second_body"])}
    require(set(map(int, point_rows[point_rows >= 0])) == incident, f"lost owned mechanical row: {body}")
    require(len(point_rows[point_rows >= 0]) == len(incident), "duplicated mechanical row")
    projection = D[:, 6 * names.index(body):6 * names.index(body) + 6]
    units, identities = [], []
    for i, (point, row_number, identity, role, other) in enumerate(zip(
        points, point_rows, member["point_action_ids"], member["point_action_roles"],
        member["point_action_other_bodies"], strict=True
    )):
        if row_number == -1:
            require(role == "discrete_body_load", "nonmechanical row is not a mapped load")
            continue
        require(row_number >= 0 and role != "discrete_body_load", "invalid mechanical action row")
        row = rows[int(row_number)]
        own = row["ownership"]
        require(row["row"] == int(row_number) and row["row_id"] == identity and own["role"] == role,
                "row/action identity differs")
        side = 0 if own["first_body"] == body else 1
        require((own["first_body"], own["second_body"])[side] == body
                and (own["second_body"], own["first_body"])[side] == other, "row receiver differs")
        close(point, own["point_mm"], "recorded source application point differs")
        unit = -projection[int(row_number)].copy()
        unit[3:] *= 1000
        sign = 1.0 if side == 0 else -1.0
        close(unit[:3], sign * np.asarray(own["direction_global_xyz"]), "row ownership force sign differs")
        free = unit[3:] - np.cross(point - center, unit[:3])
        if "outer_seat_points_mm" in row:
            close(unit[3:], np.cross(np.asarray(row["outer_seat_points_mm"][side]) - center, unit[:3]),
                  "outer-seat rigid moment differs")
        units.append(np.r_[unit[:3], free])
        identities.append({"point_index": i, "row": int(row_number), "source_id": identity,
                           "role": role, "other_body": other, "ownership_force_sign": sign,
                           "source_application_point_xyz_mm": point.tolist(),
                           "force_free_couple_per_unit_row_force": np.r_[unit[:3], free].tolist()})
    return np.asarray(units), identities


def stations(old, geom, member, local_points, own, saved, body, axis):
    """Retain original events and add cylinder/hardware events and midpoints."""
    lo, hi = old.bounds3(geom)[axis]
    values = set(old.cut_events(geom, local_points, own["hardware"], own["vertices"], axis))
    values.update(k[3] for k in saved if k[0] == body and k[2] == axis)
    if axis == 0:
        values.update(member["stations_mm"])
    for cylinder in old.cylinders(geom):
        values.add(float(cylinder["center"][axis]))
        if cylinder["shaft"] != axis:
            values.update(cylinder["center"][axis] + s * cylinder["radius"] for s in (-1, 1))
    values.update(float(p[axis]) for p in own["hardware"][0])
    values = sorted(v for v in values if lo + TOL < v < hi - TOL)
    values = sorted(set(values) | {(a + b) / 2 for a, b in pairwise(values)})
    require(0 < len(values) <= 2048, "finite station census unsupported")
    return values


def modified_gravity(body, geom, original, physical, long, assessment, factor, old_factor):
    require(geom["bores"][:4] == original["geom"]["bores"] and len(geom["bores"]) == 6,
            "six-bore proposal must preserve the four original bores")
    shape = {k: geom[k] for k in ("block", "grain_length_mm", "width_depth_mm",
                                 "grain_frame_rows_xyz", "start_xyz_mm")}
    # Source bore metadata is retained in the report, not passed as shape fields
    # to the existing strict cylinder clipper.
    shape["bores"] = [{k: b[k] for k in ("axis_id", "radius_mm", "removed_interval_axis",
                                        "station_mm", "transverse_center_mm")} for b in geom["bores"]]
    long.validate_geometry(shape)
    components = [c for c in assessment["planning_gravity"]["components"] if c["body"] == body]
    positive = [c for c in components if c["signed_mass_delta_kg"] > 0]
    removed = [c for c in components if c["signed_mass_delta_kg"] < 0]
    require(len(positive) == 10 and len(removed) == 2
            and all(c["role"] == "removed_wood_cylinder" for c in removed), "hardware/removal census differs")
    frame, start = original["frame"], original["start"]
    ratio = factor / old_factor
    added = physical.prepare_points([
        {"point_xyz_mm": c["center_xyz_mm"], "force_xyz_n": c["force_xyz_n"],
         "free_couple_xyz_nmm": [0.0, 0.0, 0.0]} for c in positive
    ], frame, start, factor)
    hardware = (np.concatenate((original["hardware"][0], added[0])),
                np.concatenate((original["hardware"][1] * ratio, added[1])))
    volume, first = long.volume_first(shape, 0, geom["grain_length_mm"])
    body_force = original["body_force"] * ratio
    full = np.r_[volume * body_force, np.cross(first, body_force)] + hardware[1].sum(axis=0)
    delta_global = np.asarray(assessment["planning_gravity"]["body_gravity_delta_n_nmm"][body])
    delta_local = np.r_[frame @ delta_global[:3],
                        frame @ (delta_global[3:] - np.cross(start, delta_global[:3]))]
    delta_error = close(full - original["full_gravity"] * ratio, factor * delta_local,
                        "physical six-bore gravity differs from authenticated full F/M delta")
    removed_mass = (original["retained_volume_mm3"] - volume) * original["source_density_kg_m3"] / 1e9
    close([removed_mass], [-sum(c["signed_mass_delta_kg"] for c in removed)], "removed timber mass differs", 1e-12)
    return {**original, "geom": geom, "clip_geometry": shape, "body_force": body_force,
            "hardware": hardware, "full_gravity": full,
            "retained_volume_mm3": volume, "retained_centroid_xyz_mm": (start + frame.T @ (np.asarray(first) / volume)).tolist(),
            "positive_components": positive, "delta_recovery_error_n_nmm": delta_error,
            "negative_removal_components_applied_as_point_loads": False}


def matched_axes(body, geom, integration):
    result = []
    frame, start = np.asarray(geom["grain_frame_rows_xyz"]), np.asarray(geom["start_xyz_mm"])
    for bore in geom["bores"][4:]:
        center = [bore["station_mm"], bore["transverse_center_mm"], 0.0]
        matches = [a for a in integration["proposed_internal_bolt_axes"] if a["body"] == body
                   and np.max(abs(np.asarray(a["center_local_guv_mm"]) - center)) < TOL]
        require(len(matches) == 1, "body/local-center bridge join is not unique")
        axis = matches[0]
        require(bore["axis_id"] == axis["canonical_axis_id"] and axis["same_body_end_pair"]
                and axis["global_operator_row"] is None and not axis["receiver_interfaces"], "canonical bridge identity differs")
        close(axis["center_global_xyz_mm"], start + frame.T @ center, "global bridge center differs")
        close(axis["axis_unit_global_xyz"], frame[2], "bridge direction differs")
        require(bore["removed_interval_axis"] == 1, "bridge bore direction differs")
        for end in axis["end_seats"]:
            seat = [center[0], center[1], end["end_v_sign"] * geom["width_depth_mm"][1] / 2]
            close(end["center_local_guv_mm"], seat, "bridge local seat differs")
            close(end["center_xyz_mm"], start + frame.T @ seat, "bridge global seat differs")
            close(end["outward_unit_xyz"], end["end_v_sign"] * frame[2], "bridge end direction differs")
        require(sorted(e["end_v_sign"] for e in axis["end_seats"]) == [-1, 1], "bridge seat pair differs")
        result.append(axis)
    require(len(result) == 2, "two internal bolts per spine required")
    return result


def bridge_points(own, ties, physical):
    """Tension applies inward wood-seat forces; no lateral end action is added."""
    return physical.prepare_points([
        {"point_xyz_mm": end["center_xyz_mm"],
         "force_xyz_n": (-np.asarray(end["outward_unit_xyz"]) * tension).tolist()}
        for axis, tension in zip(own["axes"], ties, strict=True)
        for end in axis["end_seats"]
    ], own["frame"], own["start"])


def finish(output, pins, report):
    after, changed = {}, []
    for path, digest in pins.items():
        actual = sha(path) if path.is_file() else None
        after[key(path)] = actual
        if actual != digest:
            changed.append({"path": key(path), "expected_sha256": digest, "actual_sha256": actual})
    dump(output / "inputs-after.json", {"source_sha256": after, "changed_sources": changed})
    if changed:
        report.update(status="STOP_CHANGED_SOURCE", changed_sources=changed)
    report.update(source_sha256={key(p): h for p, h in pins.items()},
                  sources_authenticated_before_and_after=not changed and report.get("inputs_authenticated", False),
                  producer_sha256=pins[Path(__file__).resolve()], runtime={"python": platform.python_version(), "numpy": np.__version__},
                  **FLAGS)
    report["original_sources_changed"] = bool(changed)
    if report["status"].startswith("STOP"):
        dump(output / "stop.json", report)
    report["output_sha256"] = {p.name: sha(p) for p in sorted(output.iterdir())
                               if p.is_file() and p.name not in ("checks.json", "receipt.json")}
    dump(output / "checks.json", report)
    dump(output / "receipt.json", {"schema": "knee-bridge-joint-replay-receipt/v1",
        "status": report["status"], "source_sha256": report["source_sha256"],
        "producer_sha256": report["producer_sha256"],
        "sources_authenticated_before_and_after": report["sources_authenticated_before_and_after"],
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name != "receipt.json"},
        **FLAGS, "original_sources_changed": bool(changed)})
    return report


def build(output):
    """Execute only in the parent; create one fresh immediate owned output child."""
    require(Path.cwd().resolve() == ROOT, "run from repository root")
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    producer = Path(__file__).resolve()
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    pins = {**PINS, producer: sha(producer)}
    report = {"schema": "knee-bridge-joint-replay/v1", "status": "STOP_INCOMPLETE",
              "stage": "authenticate inputs", "case_ids": list(CASES), "blocks": list(BLOCKS), "states": []}
    dump(output / "inputs-before.json", {"source_sha256": {key(p): h for p, h in pins.items()}})
    try:
        authenticate(pins)
        fresh, inputs, gravity, comparison, source, proposal, integration = [read(p) for p in (
            FRESH / "member-results.json", FRESH / "inputs.json", GRAVITY / "operator-assessment.json",
            FRAME / "response/comparison.json", SOURCE / "checks.json", PROPOSAL / "checks.json", INTEGRATION / "manifest.json")]
        # The parent's complete 134-pin fresh extraction is authenticated, not
        # re-executed. Older unused producer dependencies remain in frozen records.
        require(len(fresh["source_sha256"]) == 134 and inputs["source_sha256"] == fresh["source_sha256"], "fresh 134-pin extraction differs")
        inherit(pins, fresh)
        for name, digest in gravity["output_sha256"].items():
            bind(pins, GRAVITY / name, digest)
        old = imported(SOURCE / "producer.py.snapshot", "knee_replay_remaining")
        consumed = (old.MEMBERS / "geometry.json", old.MEMBERS / "member-results.json",
                    old.MEMBERS / "action-section-arrays.npz", old.PHYSICAL, old.NORMAL, old.LONG,
                    old.ADAPTER, old.MASS, old.CURRENT, old.CONTACTS, old.ROWS,
                    HERE / "frame-250-attempt02/comparison.json", HERE / "frame-250-attempt02/response.npz",
                    HERE.parent / "member_stability.py")
        for path in consumed:
            require(key(path) in source["source_sha256"], f"consumed old source lacks binding: {key(path)}")
            bind(pins, path, source["source_sha256"][key(path)])
        for directory, receipt_name, names in (
            (SOURCE, "receipt.json", ("checks.json", "cuts.jsonl.gz", "producer.py.snapshot")),
            (PROPOSAL, "receipt.json", ("checks.json",)),
            (INTEGRATION, "receipt.json", ("manifest.json",)),
            (GRAVITY, "receipt.json", ("operator-assessment.json",)),
            (FRAME, "receipt.json", ("response/comparison.json", "response/response.npz")),
        ):
            receipt = read(directory / receipt_name)
            for name in names:
                require(receipt["output_sha256"][name] == pins[directory / name], "source receipt output differs")
        for name in ("inputs.json", "geometry.json", "action-section-arrays.npz"):
            require(fresh["output_sha256"][name] == pins[FRESH / name], "fresh action output binding differs")
        authenticate(pins)
        report["inputs_authenticated"] = True
        dump(output / "inputs-before.json", {"source_sha256": {key(p): h for p, h in pins.items()},
             "selected_force_keys": [c + "_gap_raw_force_n" for c in CASES], "fresh_extraction_pin_count": 134})
        require(tuple(c["case_id"] for c in fresh["cases"]) == CASES
                and inputs["selected_force_keys"] == [c + "_gap_raw_force_n" for c in CASES], "six nominal member cases required")
        require(fresh["counts"]["timber_members"] == 44 and fresh["counts"]["whole_member_balances"] == 264, "fresh member extraction incomplete")
        require(ROOT / fresh["frame_operator_directory"] == GRAVITY
                and ROOT / fresh["clearance_input_directory"] == FRAME / "response"
                and ROOT / comparison["frame_operator_directory"] == GRAVITY, "fresh frame/operator binding differs")
        require(comparison["response_sha256"] == pins[FRAME / "response/response.npz"], "fresh response binding differs")
        nominal = [s for s in comparison["states"] if s["gap_scale"] == 1.0]
        require(tuple(s["case_id"] for s in nominal) == CASES and all(
            s["status"] in ("PASS_CONDITIONAL_COUPLED_FRAME_LAWS", "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING")
            for s in nominal), "fresh nominal conditional frame laws incomplete")
        require(comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1.0
                and comparison["comparison_climber_weight_lb"] == 250.0
                and comparison["comparison_horizontal_force_n"] == 300.0, "fixed load identity differs")
        require(gravity["operator_ready"] and not gravity["planning_gravity"]["actual_new_hole_stiffness_qualified"], "filled-bore operator scope differs")
        factor, old_factor = gravity["dead_load_factor"], source["source_gravity_multiplier"]
        require(fresh["same_state_dead_load_factor"] == comparison["dead_load_factor"] == factor
                and gravity["modeled_mass_kg"] == comparison["modeled_mass_kg"], "true mass/deadfactor differs")
        require(not proposal["proposal_adopted"] and not integration["proposal_adopted"]
                and len(integration["proposed_internal_bolt_axes"]) == 4, "unadopted four-bolt proposal required")
        physical, normal, long, reinforcement, sections, net = [imported(p, n) for p, n in (
            (old.PHYSICAL, "knee_replay_physical"), (old.NORMAL, "knee_replay_normal"),
            (old.LONG, "knee_replay_long"), (HERE / "knee-spine-reinforcement.py", "knee_replay_ties"),
            (HERE / "corner-timber-sections.py", "knee_replay_sections"),
            (HERE / "corner-net-section.py", "knee_replay_nominal"))]
        net.rectangle_torsion = cache(net.rectangle_torsion)
        members = read(FRESH / "geometry.json")["members"]
        original_geometry = read(GEOMETRY)["geometry"]
        adapter, masses, current, contacts, model, rows = [read(p) for p in (
            old.ADAPTER, old.MASS, old.CURRENT, old.CONTACTS, GRAVITY / "model.json", GRAVITY / "row-identities.json")]
        saved = {}
        with gzip.open(SOURCE / "cuts.jsonl.gz", "rt") as stream:
            for text in stream:
                record = json.loads(text)
                if record["block"] in BLOCKS and record["axis"] in (0, 2):
                    identity = tuple(record[k] for k in ("block", "case_id", "axis", "station_mm", "limit"))
                    require(identity not in saved, "duplicate original cut")
                    saved[identity] = record
        old_result = read(old.MEMBERS / "member-results.json")
        require(old_result["same_state_dead_load_factor"] == old_factor, "old replay deadfactor differs")
        fc = source["existing_Fc_perpendicular_reference_mpa"]
        require(abs(fc - 4.309223308230226) < 1e-12 and reinforcement.MARGIN == 1.25, "frozen normal reference or margin differs")
        report.update(modeled_mass_kg=gravity["modeled_mass_kg"], dead_load_factor=factor,
                      original_dead_load_factor=old_factor, planning_accessory_mass_kg=25,
                      fixed_loads="250 lb x 2; 300 N horizontal; preserved 100 mm lever",
                      stiffness_idealization=gravity["planning_gravity"]["stiffness_idealization"],
                      planning_mass_convention=gravity["planning_gravity"]["mass_convention"],
                      planning_order_counts=integration["planning_order"]["counts"],
                      existing_Fc_perpendicular_reference_mpa=fc,
                      grain_sharing_hypotheses=net.ASSUMPTIONS,
                      axial_reference_basis={k: reinforcement.HARDWARE[k] for k in (
                          "thread_tensile_stress_area_in2", "conditional_bolt_yield_ksi", "conditional_nut_proof_ksi")},
                      geometry_overrides=integration["geometry"]["STEP_overrides"],
                      axis_aliases=integration["axis_aliases"],
                      event_scope="Finite original and new point/cylinder events and interval midpoints; no continuous maximum claim.",
                      original_whole_body_gates={"force_n": FORCE_GATE, "moment_nmm": MOMENT_GATE},
                      exact_replay_and_gravity_wrench_tolerance_n_nmm=TOL)
        with (np.load(old.MEMBERS / "action-section-arrays.npz", allow_pickle=False) as archived,
              np.load(FRESH / "action-section-arrays.npz", allow_pickle=False) as arrays,
              np.load(HERE / "operators-attempt02/operators.npz", allow_pickle=False) as old_operators,
              np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators,
              np.load(HERE / "frame-250-attempt02/response.npz", allow_pickle=False) as old_response,
              np.load(FRAME / "response/response.npz", allow_pickle=False) as response):
            D, W = operators["D"], operators["W"]
            require(D.tobytes() == old_operators["D"].tobytes(), "rigid action operator D changed")
            require(W[:, 1::2].tobytes() == old_operators["W"][:, 1::2].tobytes(), "live wrench columns changed")
            require(model["body_names"] == current["body_names"] and rows == read(old.ROWS), "body/row ownership changed")
            own_old, own_new, mapping, replay = {}, {}, {}, {"cut_count": 0, "mechanical_max_error_n_nmm": 0.0, "cut_max_error_n_nmm": 0.0}
            report["stage"] = "prove original mechanical actions and signed cuts"
            # Finish all old replay proofs before deriving any fresh cut demand.
            for body in BLOCKS:
                member = members[body]
                points, point_rows = arrays[body + "__point_xyz_mm"], arrays[body + "__point_rows"]
                close(points, archived[body + "__point_xyz_mm"], "fresh mechanical source points changed")
                require(np.array_equal(point_rows, archived[body + "__point_rows"]), "fresh point-row mapping changed")
                own = old.prepare_body(body, original_geometry[body], member, adapter, masses, current,
                                       contacts, physical, long, old_factor)
                own["clip_geometry"] = own["geom"]
                own_old[body] = own
                ids = sorted(set(model["body_nodes"][body]))
                center = np.mean([model["physical_node_coordinates_mm"][str(n)] for n in ids], axis=0)
                close(center, np.mean([adapter["nodes"][str(n)] for n in ids], axis=0), "original physical node-mean datum differs")
                units, identities = unit_actions(body, member, points, point_rows, rows, D, model["body_names"], center)
                mapping[body] = (units, identities, center)
                mask = point_rows >= 0
                for case in CASES:
                    values = archived[f"{case}__{body}__point_force_free_couple_xyz"]
                    scalar = old_response[case + "_gap_raw_force_n"][point_rows[mask]]
                    error = close(units * scalar[:, None], values[mask], "original full force/free-couple replay differs")
                    replay["mechanical_max_error_n_nmm"] = max(replay["mechanical_max_error_n_nmm"], error)
                    mechanical = old.action_prepared(physical, points[mask], values[mask], own["frame"], own["start"])
                    mapped = old.action_prepared(physical, points[~mask], values[~mask], own["frame"], own["start"])
                    close(mapped[1].sum(axis=0), own["full_gravity"], "original physical/mapped gravity differs")
                    whole_gate(node_mean_wrench(mechanical[1].sum(axis=0) + own["full_gravity"], own, center),
                               "original " + body + "/" + case)
                    records = [r for identity, r in saved.items() if identity[:2] == (body, case)]
                    require(records and {r["axis"] for r in records} == {0, 2}, "original knee cut scope incomplete")
                    for record in records:
                        q = cut(physical, mechanical, own, record["axis"], record["station_mm"], record["limit"], own["volume_function"])
                        error = close(q["signed_internal_n_nmm"], record["signed_internal_n_nmm"], "original full signed cut replay differs")
                        replay["cut_max_error_n_nmm"] = max(replay["cut_max_error_n_nmm"], error)
                        replay["cut_count"] += 1
            require(replay["cut_count"] == len(saved), "original replay coverage differs")
            dump(output / "original-replay.json", {**replay, "historical_acceptance_transferred": False})
            report["original_replay"] = replay
            gravity_records = {}
            for body in BLOCKS:
                geom = proposal["geometry_proposals"][body]["hypothetical_geometry"]
                own_new[body] = modified_gravity(body, geom, own_old[body], physical, long, gravity, factor, old_factor)
                axes = matched_axes(body, geom, integration)
                require(tuple(tuple(a["center_local_guv_mm"][:2]) for a in axes) == reinforcement.CENTERS, "two-variable LP centers differ")
                own_new[body]["axes"] = axes
                for axis in axes:
                    components = [c for c in own_new[body]["positive_components"] if c["canonical_axis_id"] == axis["canonical_axis_id"]]
                    require(len(components) == 5 and {c["role"] for c in components} == {"shaft", "head", "head_washer", "nut_washer", "nut"}
                            and all(c["fit_axis_id"] == axis["fit_axis_id"] for c in components), "five-component hardware/alias join differs")
                gravity_records[body] = {k: own_new[body][k] for k in (
                    "retained_volume_mm3", "retained_centroid_xyz_mm", "source_density_kg_m3",
                    "delta_recovery_error_n_nmm", "negative_removal_components_applied_as_point_loads")}
                gravity_records[body].update(full_factored_local_gravity_n_nmm=own_new[body]["full_gravity"].tolist(),
                    original_allocated_hardware_count=12, original_hardware_factor_ratio=factor / old_factor,
                    positive_components=own_new[body]["positive_components"], positive_hardware_point_count=10,
                    hardware_points_local_guv_mm=own_new[body]["hardware"][0].tolist(),
                    hardware_wrenches_about_local_start_n_nmm=own_new[body]["hardware"][1].tolist())
            dump(output / "physical-gravity.json", gravity_records)
            report["stage"] = "fresh physical cuts and prescribed static allocation"
            normal_count = grain_count = allocation_count = event_count = 0
            with (gzip.open(output / "normal-cuts.jsonl.gz", "wt") as normal_stream,
                  gzip.open(output / "grain-cuts.jsonl.gz", "wt") as grain_stream,
                  (output / "allocations.jsonl").open("w") as allocation_stream,
                  (output / "mechanical-actions.jsonl").open("w") as action_stream,
                  (output / "hardware-events.jsonl").open("w") as event_stream):
                for body in BLOCKS:
                    own, member = own_new[body], members[body]
                    points, point_rows = arrays[body + "__point_xyz_mm"], arrays[body + "__point_rows"]
                    mask = point_rows >= 0
                    units, identities, center = mapping[body]
                    local_points = (points - own["start"]) @ own["frame"].T
                    event_axes = {axis: stations(old, own["geom"], member, local_points, own, saved, body, axis) for axis in (0, 2)}
                    body_id = model["body_names"].index(body)
                    for case_index, case in enumerate(CASES):
                        report["active_state"] = {"block": body, "case_id": case}
                        values = arrays[f"{case}__{body}__point_force_free_couple_xyz"]
                        raw = response[case + "_gap_raw_force_n"]
                        require(raw.shape == (len(rows),) and np.isfinite(raw).all(), "fresh raw connector force shape differs")
                        action_error = close(units * raw[point_rows[mask], None], values[mask], "fresh full force/free-couple action audit differs")
                        mechanical = old.action_prepared(physical, points[mask], values[mask], own["frame"], own["start"])
                        mapped = old.action_prepared(physical, points[~mask], values[~mask], own["frame"], own["start"])
                        require(np.max(abs(values[~mask, 3:])) < TOL, "mapped nodal load has an unexplained free couple")
                        work = W[6 * body_id:6 * body_id + 6, 2 * case_index] * factor + W[6 * body_id:6 * body_id + 6, 2 * case_index + 1]
                        expected = about_start(work, center, own["start"], own["frame"])
                        require(np.max(abs(W[6 * body_id:6 * body_id + 6, 2 * case_index + 1])) < TOL,
                                "unexpected direct live load on knee spine")
                        gravity_error = close(own["full_gravity"], mapped[1].sum(axis=0), "fresh physical/mapped whole gravity differs")
                        operator_error = close(own["full_gravity"], expected, "fresh physical gravity differs from true frame W")
                        residual = mechanical[1].sum(axis=0) + own["full_gravity"]
                        residual_at_center = node_mean_wrench(residual, own, center)
                        whole_gate(residual_at_center, "fresh " + body + "/" + case)
                        line(action_stream, {"block": body, "case_id": case, "raw_force_key": case + "_gap_raw_force_n",
                            "actions": [{**identity, "force_free_couple_xyz": value.tolist()} for identity, value in zip(identities, values[mask], strict=True)]})
                        state = {"block": body, "case_id": case, "fresh_action_audit_max_error_n_nmm": action_error,
                            "physical_minus_mapped_gravity_max_error_n_nmm": gravity_error,
                            "physical_minus_frame_W_max_error_n_nmm": operator_error,
                            "whole_body_residual_local_n_nmm": residual.tolist(),
                            "whole_body_residual_global_about_node_mean_n_nmm": residual_at_center.tolist(),
                            "whole_body_residual_global_origin_n_nmm": global_wrench(residual, own["frame"], own["start"]).tolist(),
                            "normal_cut_count": 0, "grain_cut_count": 0, "grain_indices": {},
                            "finite_pressure_status_counts": {}, "missing_pressure_witnesses": [], "reference_exceedances": []}
                        inventory = [{"block": body, "case_id": case, **cut(physical, mechanical, own, 2, station, limit, long.volume_first)}
                                     for station in event_axes[2] for limit in ("before", "after")]
                        constraints = reinforcement.constraints(inventory, own["geom"]["grain_length_mm"],
                                                                 own["geom"]["width_depth_mm"][0], reinforcement.CENTERS)
                        optimum = reinforcement.lp(constraints)
                        ties = [1.25 * t for t in optimum["axial_ties_n"]]
                        state.update(LP_constraints=constraints, necessary_hull_LP=optimum,
                                     uniform_case_force_margin=1.25, constant_axial_ties_n=ties, axial_stack_reference_comparisons=[])
                        bridge = bridge_points(own, ties, physical)
                        for record in inventory:
                            pressure = reinforcement.pressure_record(record, ties, own["geom"], normal, old)
                            wood_delta = -physical.point_gravity(bridge, 2, record["station_mm"], record["limit"])
                            perm = [2, 0, 1]
                            canonical_wood = np.asarray(record["signed_internal_n_nmm"]) + np.r_[wood_delta[:3][perm], wood_delta[3:][perm]]
                            close(canonical_wood, pressure["wood_full_cut_n_nmm"],
                                  "canonical inward end seats do not recover wood allocation", 1e-7)
                            result = pressure["finite_wood_compression"]
                            status = result["status"]
                            state["finite_pressure_status_counts"][status] = state["finite_pressure_status_counts"].get(status, 0) + 1
                            if "pressure_peak_mpa" not in result:
                                state["missing_pressure_witnesses"].append({k: pressure[k] for k in ("station_mm", "limit", "wood_full_cut_n_nmm")})
                            else:
                                result["pressure_over_existing_Fc_perp_reference"] = result["pressure_peak_mpa"] / fc
                                if result["pressure_peak_mpa"] > fc:
                                    state["reference_exceedances"].append({"kind": "finite_pressure", "station_mm": record["station_mm"], "limit": record["limit"], "index": result["pressure_peak_mpa"] / fc})
                                if "peak_pressure" not in state or result["pressure_peak_mpa"] > state["peak_pressure"]["finite_wood_compression"]["pressure_peak_mpa"]:
                                    state["peak_pressure"] = pressure
                            line(normal_stream, {**record, "uniform_case_force_margin": 1.25, "normal_allocation": pressure})
                            state["normal_cut_count"] += 1
                            normal_count += 1
                        area = math.pi / 4 * (25.4**2 - 8.3058**2)
                        steel_area = reinforcement.HARDWARE["thread_tensile_stress_area_in2"] * 25.4**2
                        bridge_pairs = []
                        for axis, tension in zip(own["axes"], ties, strict=True):
                            stack = {"canonical_axis_id": axis["canonical_axis_id"], "fit_axis_id": axis["fit_axis_id"],
                                "axial_tension_n": tension, "both_end_supported_annulus_area_mm2": area,
                                "each_end_mean_pressure_mpa": tension / area, "mean_over_Fc_perp_reference": tension / area / fc,
                                "thread_nominal_axial_stress_mpa": tension / steel_area,
                                "bolt_axial_over_conditional_yield_reference": tension / steel_area / (92 * 6.894757293168361),
                                "nut_axial_over_conditional_proof_reference": tension / steel_area / (120 * 6.894757293168361),
                                "washer_metal_or_actual_thread_capacity_qualified": False}
                            state["axial_stack_reference_comparisons"].append(stack)
                            if any(stack[k] > 1 for k in ("mean_over_Fc_perp_reference", "bolt_axial_over_conditional_yield_reference", "nut_axial_over_conditional_proof_reference")):
                                state["reference_exceedances"].append({"kind": "axial_stack", **stack})
                            ends = [{**end, "force_on_wood_xyz_n": (-np.asarray(end["outward_unit_xyz"]) * tension).tolist()} for end in axis["end_seats"]]
                            bridge_pairs.append(physical.prepare_points([
                                {"point_xyz_mm": e["center_xyz_mm"], "force_xyz_n": e["force_on_wood_xyz_n"]}
                                for e in ends
                            ], own["frame"], own["start"]))
                            wrench = sum((np.r_[e["force_on_wood_xyz_n"], np.cross(e["center_xyz_mm"], e["force_on_wood_xyz_n"])] for e in ends), np.zeros(6))
                            close(wrench, np.zeros(6), "canonical equal axial end pair has nonzero rigid wrench", 1e-7)
                            line(allocation_stream, {"block": body, "case_id": case, **stack, "end_seats": ends,
                                "global_origin_rigid_wrench_n_nmm": wrench.tolist(), "global_receiver_force_record": False,
                                "constant_over_relevant_v_cuts": True, "static_allocation_only": True})
                            allocation_count += 1
                        refs = next(m["conditional_material"]["CF_only_reference_mpa"] for c in fresh["cases"] if c["case_id"] == case for m in c["members"] if m["member"] == body)
                        old_refs = next(m["conditional_material"]["CF_only_reference_mpa"] for c in old_result["cases"] if c["case_id"] == case for m in c["members"] if m["member"] == body)
                        require(refs == old_refs, "conditional timber references changed")
                        state["conditional_CF_only_reference_mpa"] = refs
                        for station in event_axes[0]:
                            section = sections.section(own["geom"], station)
                            for limit in ("before", "after"):
                                record = {"block": body, "case_id": case, **cut(physical, mechanical, own, 0, station, limit, long.volume_first)}
                                grain = old.grain_nominal(record["signed_internal_n_nmm"], own["geom"], station, sections, net, None, refs)
                                # Both ends of each bridge share exactly one grain
                                # station. Their signed half-wrench cancels at both limits.
                                for pair in bridge_pairs:
                                    close(physical.point_gravity(pair, 0, station, limit), np.zeros(6),
                                          "canonical end pair changed grain-cut wrench", 1e-7)
                                for name, value in grain["metrics"].items():
                                    witness = {"value": value, "station_mm": station, "limit": limit}
                                    if name not in state["grain_indices"] or value > state["grain_indices"][name]["value"]:
                                        state["grain_indices"][name] = witness
                                    if value > 1:
                                        state["reference_exceedances"].append({"kind": "grain_nominal", "metric": name, **witness})
                                line(grain_stream, {**record, "actual_net_section": section, "grain_nominal": grain,
                                                    "canonical_bridge_pair_grain_wrench_zero": True})
                                state["grain_cut_count"] += 1
                                grain_count += 1
                        # All positive component centers are recorded at both
                        # limits, including external head/nut/washer v stations.
                        # No timber pressure is assigned outside the stock.
                        for axis in (0, 2):
                            lo, hi = old.bounds3(own["geom"])[axis]
                            for component in own["positive_components"]:
                                local = (np.asarray(component["center_xyz_mm"]) - own["start"]) @ own["frame"].T
                                for limit in ("before", "after"):
                                    line(event_stream, {"block": body, "case_id": case, "axis": axis,
                                        "canonical_axis_id": component["canonical_axis_id"], "fit_axis_id": component["fit_axis_id"],
                                        "role": component["role"], "station_mm": float(local[axis]), "limit": limit,
                                        "within_timber_cut_domain": bool(lo + TOL < local[axis] < hi - TOL),
                                        "pressure_assigned_outside_timber": False,
                                        "hardware_negative_half_local_n_nmm": physical.point_gravity(own["hardware"], axis, float(local[axis]), limit).tolist()})
                                    event_count += 1
                        state["named_reference_screen_satisfied"] = not state["missing_pressure_witnesses"] and not state["reference_exceedances"]
                        report["states"].append(state)
            require(len(report["states"]) == 12 and allocation_count == 24 and event_count == 480, "fresh finite output census differs")
            report.update(normal_cut_count=normal_count, grain_cut_count=grain_count,
                          internal_allocation_count=allocation_count, internal_end_count=2 * allocation_count,
                          positive_hardware_component_count=20, hardware_before_after_event_record_count=event_count,
                          negative_removal_point_load_count=0, all_old_replays_proved_first=True,
                          physical_gravity_updated_on_modified_geometry=True,
                          all_named_reference_screens_satisfied=all(s["named_reference_screen_satisfied"] for s in report["states"]))
        report["status"] = ("FINITE_FRESH_KNEE_STATIC_REPLAY_COMPLETE" if report["all_named_reference_screens_satisfied"] else "STOP_NAMED_REFERENCE_SCREEN")
        report["stage"] = "complete finite static arithmetic"
    except (ValueError, OSError, RuntimeError, np.linalg.LinAlgError) as exc:
        report.update(status="STOP_SOURCE_OR_REPLAY", reason=str(exc), exception_type=type(exc).__name__)
    return finish(output, pins, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "checks_sha256": sha(args.output / "checks.json"),
                      "receipt_sha256": sha(args.output / "receipt.json"),
                      "reason": result.get("reason")}, allow_nan=False))
    raise SystemExit(2 if result["status"].startswith("STOP") else 0)
