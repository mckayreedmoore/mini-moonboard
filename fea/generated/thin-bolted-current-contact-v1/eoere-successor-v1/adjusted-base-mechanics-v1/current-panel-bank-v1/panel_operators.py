"""Current OFF panel source contract and deferred three-panel refresh.

The CLI reads metadata only. The production API requires six current own
observations before loading the frozen raised-rail bank; it never supplies
contacts, loads, response, capacities or acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

OWN = Path(__file__).resolve()
ROOT = OWN.parents[6]
BASE = OWN.parents[2].relative_to(ROOT).as_posix()
DOC = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
GEOMETRY = {"path": DOC+"/occupied-extended-cleats-v1.json",
            "sha256": "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"}
BASE_GEOMETRY = {"path": DOC+"/occupied-adjusted-base-v3.json",
                 "sha256": "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7"}
RAISED = {"path": BASE+"/raised-rail-panel-operators-v1/panel_operators.py",
          "sha256": "dd99c14bbedb56d267aaa9990aa153d0794cb13cbcb9d32a205206f72bc65f20"}
ADAPTER = {"path": BASE+"/adjusted-base-mechanics-v1/adapter.py",
           "sha256": "3eddbab497ae328608b4e5ff93fc2f8e7262ad0bba908afe2f474c1c6fbcca3d"}
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
CHANGED = {"main_lower_right", "main_upper_right", "kicker_right"}
SCHEMA = "eoere_current_off_panel_operator_source_inputs/v1"


def frozen_module(ref, label):
    if hashlib.sha256((ROOT/ref["path"]).read_bytes()).hexdigest() != ref["sha256"]:
        raise ValueError("frozen panel method source differs: "+ref["path"])
    spec = importlib.util.spec_from_file_location(label, ROOT/ref["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


raised = frozen_module(RAISED, "frozen_raised_panel_primitives_for_current_off")
a = frozen_module(ADAPTER, "frozen_adjusted_metadata_for_current_off_panels")
plate, mass = raised.plate, raised.mass
require, canonical, array_sha = raised.require, raised.canonical, raised.array_sha


def source_binding(row):
    return {key: copy.deepcopy(row[key]) for key in ("id", "path", "sha256", "volume_mm3")}


def compose_panel_metadata(prior, base, extension, old_inputs):
    """Reuse the frozen ten-screw census; change only own clearance datums."""
    require(extension["parent_geometry"]["base"] == BASE_GEOMETRY
            and extension["only_two_cleat_bodies_changed"] is True
            and {r["id"] for r in extension["changed_finished_solids"]}
            == {"eoere_cleat_left", "eoere_cleat_right"}, "extension must change only two timber cleats")
    require(extension["screw_axes"] == base["screw_axes"]
            and extension["axes"] == base["axes"], "extension changed protected current axes")
    screws, moved = a.screw_delta(old_inputs, base)
    machining = copy.deepcopy(prior["panel_machining"])
    features = a.indexed(machining["features"], "identity")
    for identity in moved:
        feature, screw = features[identity], screws[identity]
        require(feature["kind"] == "conditional_screw_clearance" and feature["diameter_mm"] == 5.
                and feature["panel"] == screw["panel"], "own5mm clearance required")
        feature["start_xyz_mm"] = copy.deepcopy(screw["origin_xyz_mm"])
    panels = a.indexed([source_binding(r) for r in prior["finished_panel_solids"]], "id")
    changed = [r for r in base["changed_finished_solids"] if r["kind"] == "panel"]
    require(len(changed) == 3 and {r["id"] for r in changed} == CHANGED,
            "three current changed panel sources required")
    panels.update({r["id"]: source_binding(r) for r in changed})
    current = {"panel_machining": machining, "screw_axes": copy.deepcopy(base["screw_axes"]),
               "finished_panel_solids": [panels[n] for n in plate.PANELS]}
    audit_panel_metadata(prior, current, moved)
    return current, moved


def audit_panel_metadata(prior, current, moved):
    keys = ("panel", "identity", "kind", "diameter_mm", "start_xyz_mm", "direction_xyz")
    features = lambda d: a.indexed([{k: r[k] for k in keys}
        for r in d["panel_machining"]["features"]], "identity")
    before, after = features(prior), features(current)
    require(len(before) == len(after) == 340 and before.keys() == after.keys(), "unique340 current apertures required")
    require(len(moved) == len(set(moved)) == 10
            and {n for n in before if before[n] != after[n]} == set(moved), "exact ten aperture moves required")
    require({after[n]["panel"] for n in moved} == CHANGED, "three changed aperture owners required")
    screws = a.indexed(current["screw_axes"], "axis_id")
    require(len(screws) == 66, "unique66 own screw ports required")
    for identity, screw in screws.items():
        feature = after[identity]
        require(feature["panel"] == screw["panel"] and feature["direction_xyz"] == screw["direction_xyz"]
                and np.max(abs(np.asarray(feature["start_xyz_mm"])-screw["origin_xyz_mm"])) < 1e-7,
                "own screw aperture datum/direction differs")
    for identity in moved:
        require(all(before[identity][k] == after[identity][k] for k in keys if k != "start_xyz_mm"),
                "only clearance datum may change")
    require(current["panel_machining"]["outlines"] == prior["panel_machining"]["outlines"], "preserved outlines differ")
    old_panels = a.indexed(prior["finished_panel_solids"], "id")
    new_panels = a.indexed(current["finished_panel_solids"], "id")
    require(set(old_panels) == set(new_panels) == set(plate.PANELS), "six panel sources required")
    require({n for n in new_panels if new_panels[n]["sha256"] != old_panels[n]["sha256"]} == CHANGED,
            "three changed/three unchanged finished source hashes required")
    for name in set(plate.PANELS)-CHANGED:
        require(source_binding(new_panels[name]) == source_binding(old_panels[name]), "unchanged panel source binding differs")


def read_sources():
    plan, prior, _, pins = raised.read_sources()  # Metadata only; no saved operators or q loaded.
    pins = raised.join_pins(pins, {RAISED["path"]: RAISED["sha256"], ADAPTER["path"]: ADAPTER["sha256"],
        a.OLD_INPUT: a.OLD_INPUT_SHA, str(OWN.relative_to(ROOT)): LOADED_SHA,
        str(OWN.with_name("test_panel_operators.py").relative_to(ROOT)):
            plate.sha(OWN.with_name("test_panel_operators.py"))})
    base, extension = a.read_ref(BASE_GEOMETRY, pins), a.read_ref(GEOMETRY, pins)
    require(base["unofficial_2026_grid_included"] is False and base["candidate"] == extension["candidate"]
            == "compact-floor-flush-eoere-bolted-development"
            and not any(base["release"].values()) and not any(extension["release"].values()), "current OFF identity/release differs")
    old = a.read_ref({"path": a.OLD_INPUT, "sha256": a.OLD_INPUT_SHA}, pins)
    current, moved = compose_panel_metadata(prior, base, extension, old)
    pins = raised.join_pins(pins, base["source_sha256"], extension["source_sha256"],
        {r["path"]: r["sha256"] for r in current["finished_panel_solids"]})
    raised.verify(pins)
    return plan, prior, current, moved, pins


def input_record(plan, current, moved):
    return {"schema": SCHEMA, "geometry": copy.deepcopy(GEOMETRY), "base_geometry": copy.deepcopy(BASE_GEOMETRY),
        "optional_2026_extra": False, "scenario": copy.deepcopy(plan["scenario"]),
        "panel_machining_canonical_sha256": canonical(current["panel_machining"]),
        "screw_axes_canonical_sha256": canonical(current["screw_axes"]),
        "finished_panel_solids": copy.deepcopy(current["finished_panel_solids"]),
        "screw_axis_ids": [r["axis_id"] for r in current["screw_axes"]], "changed_feature_ids": moved,
        "aperture_updated_K_panels": sorted(CHANGED), "unchanged_K_panels": sorted(set(plate.PANELS)-CHANGED),
        "reuse_basis": "frozen raised-rail panel bank; own finished-source identity for unchanged three",
        "old_contact_domains_reused": False, "old_response_or_acceptance_used": False}


def source_inputs():
    plan, _, current, moved, _ = read_sources()
    return input_record(plan, current, moved)


def verify_panel_source_inputs(data, proof=None):
    """Source admission only. Never loads a panel K, CAD solid or coefficient q."""
    plan, _, current, moved, pins = read_sources()
    expected = input_record(plan, current, moved)
    require(data["panel_operator_source_inputs"] == expected, "current panel operator inputs differ")
    geometry = data.get("geometry", {})
    require(geometry.get("report", geometry) == GEOMETRY, "current OFF geometry reference differs")
    if "panel_ids" in data:
        require(len(data["panel_ids"]) == 6 and set(data["panel_ids"]) == set(plate.PANELS), "six physical panel owners required")
    require(data["current_panel_machining_descriptors"] == current["panel_machining"], "current own aperture descriptors differ")
    require([r["source_screw_descriptor"] for r in data["hillman_rows"]] == current["screw_axes"], "current own66 screw descriptors differ")
    require(all(data.get("source_sha256", {}).get(p, h) == h for p, h in pins.items()), "current panel source pin conflict")
    if proof is not None:
        require(proof["source_inputs"] == expected and proof["source_sha256"] == pins
                and proof["old_contact_domains_reused"] is False, "current panel proof/source differs")
        require(proof["current_own_projection_canonical_sha256"] == canonical(load_projection_inputs(data)),
                "current own panel projection proof differs")
    raised.verify(pins)
    return {"passed": True, "source_sha256": pins, "source_inputs": expected,
            "metadata_only_no_K_q_or_contact_construction": True}


def load_projection_inputs(data):
    """Current own volume/COM observations feed the unchanged panel load method."""
    verified = verify_panel_source_inputs(data)
    expected = a.indexed(verified["source_inputs"]["finished_panel_solids"], "id")
    rows = a.indexed([r for r in data["finished_body_observations"] if r["id"] in expected], "id")
    require(set(rows) == set(expected), "six current own panel observations required before bank loading")
    stock = []
    for name in plate.PANELS:
        row, source = rows[name], expected[name]
        require(source_binding(row["source"]) == source, "current own panel observation source differs")
        require(math.isfinite(row["volume_mm3"]) and row["volume_mm3"] > 0.
                and abs(row["volume_mm3"]-source["volume_mm3"]) < max(.01, source["volume_mm3"]*1e-9), "current own panel observed volume differs")
        require(len(row["center_xyz_mm"]) == 3 and all(math.isfinite(x) for x in row["center_xyz_mm"]), "finite current own panel COM required")
        stock.append({"name": name, "volume_mm3": row["volume_mm3"],
                      "center_of_mass_xyz_mm": copy.deepcopy(row["center_xyz_mm"])})
    return {"panel_machining": copy.deepcopy(data["current_panel_machining_descriptors"]),
            "screw_axes": [copy.deepcopy(r["source_screw_descriptor"]) for r in data["hillman_rows"]],
            "finished_stock": stock, "panel_operator_source_inputs": verified["source_inputs"]}


def refresh_bank(panels, current, moved):
    """Apply only the frozen aperture/port/mass primitives, in each own chart."""
    require(set(panels) == set(plate.PANELS), "six frozen panel charts required")
    rows = []
    for name, panel in panels.items():
        old_K = array_sha(panel["K"])
        old_holes = a.indexed(panel["holes"], "identity")
        holes = [{**r, "xy_mm": plate.local_xy(r["start_xyz_mm"], panel["geometry"]).tolist()}
            for r in current["panel_machining"]["features"] if r["panel"] == name]
        require(set(old_holes) == {r["identity"] for r in holes}, "frozen/current own hole identities differ")
        changed = [r for r in holes if r["identity"] in moved]
        require(bool(changed) == (name in CHANGED), "three changed panel routes required")
        if changed:
            panel["K"] = raised.aperture_delta(panel, [old_holes[r["identity"]] for r in changed], changed)
        panel["holes"] = holes
        for key in tuple(panel):
            if key.startswith("contact_") or key in {"q", "support_bounds"}:
                del panel[key]
        raised.refresh_screw_ports(panel, [r for r in current["screw_axes"] if r["panel"] == name])
        _, area = mass.mass_only_quadrature(panel)
        require(np.isfinite(panel["K"]).all() and np.isfinite(area).all() and area.sum() > 0., "finite current panel operators/mass required")
        panel["hole_area_mm2"] = float(sum(np.pi*(r["diameter_mm"]/2)**2 for r in holes))
        rows.append({"panel": name, "K_route": "raised_K+old_apertures-new_apertures" if changed else "exact_raised_K",
            "changed_feature_ids": [r["identity"] for r in changed], "screw_count": len(panel["screws"]),
            "hole_count": len(holes), "K_sha256": array_sha(panel["K"]), "old_K_sha256": old_K,
            "screw_ports_sha256": canonical({k: array_sha(panel[k]) for k in ("screw_u", "screw_v", "screw_w")}),
            "mass_measure_sha256": canonical({k: array_sha(panel[k]) for k in ("mass_xy", "mass_weights", "mass_row")}),
            "signed_net_mass_area_mm2": float(area.sum()), "hole_area_mm2": panel["hole_area_mm2"],
            "K_symmetry_error": float(abs(panel["K"]-panel["K"].T).max())})
    require(sum(r["screw_count"] for r in rows) == 66, "refreshed66 own screw ports required")
    return rows


def prepare_panel_operators(data):
    projection = load_projection_inputs(data)  # Reject missing current observations before any real K loading.
    plan, _, current, moved, pins = read_sources()
    panels, old_pins, _ = raised.prepare_panel_operators()
    require(all(pins.get(p) == h for p, h in old_pins.items()), "frozen raised-bank dependency not bound")
    rows = refresh_bank(panels, current, moved)
    raised.verify(pins)
    proof = {"schema": "eoere_current_off_panel_operator_preparation/v1",
        "source_inputs": input_record(plan, current, moved), "source_sha256": pins, "panels": rows,
        "source_pins_before_after_unchanged": True, "old_contact_domains_reused": False,
        "historical_q_or_actions_used_for_new_bank": False,
        "frozen_loader_reference_coefficients_validated_then_discarded": True,
        "current_own_projection_canonical_sha256": canonical(projection),
        "fresh_contact_extractor_required": True, "global_K_or_response_constructed": False,
        "CAD_or_native_executed": False, "limits": plan["limits"]+[
            "This current OFF bank refreshes ten apertures in three panels; optional extra2026 geometry is excluded.",
            "No actual Hillman/panel resistance or complete joint acceptance is supplied."],
        "release": copy.deepcopy(raised.RELEASE)}
    return panels, pins, proof


def load_panel_dependencies(data):
    panels, pins, proof = prepare_panel_operators(data)
    return panels, load_projection_inputs(data), pins, proof


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    require(not args.out.exists(), "preserve prior current panel output")
    plan, _, current, moved, pins = read_sources()
    result = {"schema": "eoere_current_off_panel_source_plan/v1", "source_inputs": input_record(plan, current, moved),
        "source_sha256": pins, "metadata_only_no_K_q_or_contact_construction": True,
        "production_bank_prepared": False, "current_observed_volume_COM_required": True,
        "fresh_contacts_loads_frame_response_and_independent_admission_required": True,
        "release": copy.deepcopy(raised.RELEASE)}
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
