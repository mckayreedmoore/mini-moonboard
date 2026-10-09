"""Independent bounded testing review; all output controls live in /tmp."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OWN = Path(__file__).resolve()
TARGET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "inputs.json": "e3fda210640db0bc395d808c90625d65e8049da315c0872da12077731e6f0e41",
    "calculate.py": "5f6d088a836f1ac198c2cc7c8355b3a6ca8a20034a863ab813e4e33fa4a3fa03",
    "result.json": "a21c25d6693a86f2617655cec1e82aa51c182b153e19baf8f5d1431afa381443",
    "verify.py": "1ab517d0e2b874fc43c9c4f78fce1cda80dd6dbda2a70f9e37ebdce2edffc51c",
    "verification-v1.json": "ae0c5dd215fd2bddaa6c2b0fcf46fa51038ac672d8611722ee34b4b4d6afded6",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejected(callback):
    try:
        callback()
    except ValueError as error:
        return str(error)
    raise AssertionError("corruption accepted")


def inventory_controls(m, inp, data, datum):
    observed = {}
    for label in ("missing_axis", "missing_proposal", "foreign_proposal_translation", "source_axis_join",
                  "source_screw_join", "non_X_bore", "partial_wall", "missing_wall", "recorded_service_cut",
                  "wrong_finished_source", "inconsistent_void_volume", "non_extrusion_profile"):
        altered, options = copy.deepcopy(data), copy.deepcopy(inp)
        name = options["receivers"][0]
        if label == "missing_axis":
            altered["geometry"]["axes"].pop()
        elif label == "missing_proposal":
            altered["placement"]["proposed_axes"].pop()
        elif label == "foreign_proposal_translation":
            altered["placement"]["proposed_axes"][0]["point_xyz_mm"][0] += 1.
        elif label == "source_axis_join":
            altered["cache"]["shafts"][0]["source_axis"]["grip_mm"] += 1.
        elif label == "source_screw_join":
            altered["cache"]["hillman_rows"][0]["source_screw_descriptor"]["receiver"] = "foreign"
        elif label == "non_X_bore":
            axes = altered["geometry"]["axes"]
            next(a for a in axes if name in a["receivers"])["direction_xyz"] = [0., 1., 0.]
            altered["base"]["axes"] = copy.deepcopy(axes)
            by_id = {a["id"]: a for a in axes}
            for shaft in altered["cache"]["shafts"]:
                shaft["source_axis"] = copy.deepcopy(by_id[shaft["axis_id"]])
            altered["placement"]["current_100_axes_canonical_sha256"] = m.canonical(axes)
            for proposed in altered["placement"]["proposed_axes"]:
                axis = copy.deepcopy(by_id[proposed["id"]])
                axis["point_xyz_mm"][2] = options["proposed_Z_mm"]
                proposed.clear()
                proposed.update(axis)
        elif label in {"partial_wall", "missing_wall"}:
            walls = altered["cache"]["finished_receiver_wall_queries"]
            index = next(i for i, w in enumerate(walls) if w["receiver"] == name)
            if label == "partial_wall":
                walls[index]["partial_wall_present"] = True
            else:
                walls.pop(index)
        elif label == "recorded_service_cut":
            altered["base"]["service_cuts"].append({"receiver": name})
        elif label == "wrong_finished_source":
            next(o for o in altered["cache"]["finished_body_observations"] if o["id"] == name)["source"]["sha256"] = "0" * 64
        elif label == "inconsistent_void_volume":
            altered["profiles"][name]["finished"]["volume_mm3"] -= 1.
            next(o for o in altered["cache"]["finished_body_observations"] if o["id"] == name)["volume_mm3"] -= 1.
        else:
            altered["profiles"][name]["vertices_luv_mm"].pop()
        observed[label] = rejected(lambda options=options, altered=altered: m.existing_inventory(options, altered, datum))
    return observed


def scope_and_skin(result, inp):
    assert result["limits"][:len(inp["limits"])] == inp["limits"]
    assert result["complete_joint_resistance"] is None and not any(result["release"].values())
    for case in result["scenarios"]:
        for seat in case["nominal_annular_seats"]:
            stock = result["affected_members"][seat["receiver"]]
            assert seat["inward_skin_mm"] == inp["annular_inward_skin_mm"] > 0
            x = seat["support_point_xyz_mm"][0]
            inner = x + seat["inward_X_sign"] * seat["inward_skin_mm"]
            low, high = stock["X_interval_mm"]
            assert low - 2e-8 <= min(x, inner) <= max(x, inner) <= high + 2e-8
            assert seat["physical_contact_or_strength_qualified"] is False


def scenario_controls(m, inp, proposed, members, cuts, capsule):
    observed = {}
    for label in ("bore_exceeds_inner_opening", "annulus_crosses_stock_edge", "nonzero_external_plate", "intersecting_other_cut"):
        axes, current = copy.deepcopy(proposed), copy.deepcopy(cuts)
        for axis in axes.values():
            if label == "bore_exceeds_inner_opening":
                axis["hardware_scenario"]["washer_id_mm"] = 1.
            elif label == "annulus_crosses_stock_edge":
                axis["hardware_scenario"]["washer_od_mm"] = 1000.
            elif label == "nonzero_external_plate":
                axis["before_plate_mm"] = 1.
        if label == "intersecting_other_cut":
            axis = next(iter(axes.values()))
            cut = copy.deepcopy(axis)
            cut["id"] = "synthetic-intersecting-other-cut"
            for receiver in axis["receivers"]:
                current[receiver].append(cut)
        observed[label] = rejected(lambda axes=axes, current=current: m.scenarios(inp, axes, members, current, capsule))
    return observed


def hand_arithmetic(capsule, verifier):
    # Integer-coordinate triangles give expected distances without invoking
    # either production or verification distance implementation to derive them.
    cases = (([6., 3., 0.], [1., 0., 0.], 2., 1., 1., 5., 3.),
             ([10., 3., 0.], [-1., 0., 0.], 8., 1., 1., 3., 1.),
             ([0., 2., 0.], [1., 0., 0.], 2., 1., 1., 2., 0.),
             ([0., 3., 4.], [1., 0., 0.], 2., .5, 1.5, 5., 3.))
    error = 0.
    for second, direction, length, r1, r2, distance, separation in cases:
        for translation in ([0., 0., 0.], [117., -23., 44.]):
            point = [second[i] + translation[i] for i in range(3)]
            first = capsule.primitive("first", "test", translation, [1., 0., 0.], 0., 2., r1)
            other = capsule.primitive("second", "test", point, direction, 0., length, r2)
            result = capsule.pair(first, other)
            error = max(error, abs(result["finite_axis_distance_mm"] - distance),
                        abs(result["capsule_separation_lower_bound_mm"] - separation))
    assert error < 1e-12
    square, diamond = [(0., 0.), (10., 0.), (10., 10.), (0., 10.)], [(0., -5.), (5., 0.), (0., 5.), (-5., 0.)]
    assert verifier.circle_margin([3., 4.], square) == 3.
    assert abs(verifier.circle_margin([0., 0.], diamond) - 5. / math.sqrt(2.)) < 1e-14
    rejected(lambda: verifier.circle_margin([-1., 4.], square))
    return {"finite_segment_known_answers_including_translation_reverse_direction_and_tangency": 8,
            "maximum_distance_or_separation_error_mm": error, "finite_edge_known_answers_and_exterior_rejection": 3}


def mirror_cli(directory, inp, result, verification):
    """Replay byte-identical CLIs in a disposable source-linked root."""
    mirror = directory / "mirror"
    mirror.mkdir()
    (mirror / "AGENTS.md").write_text("Disposable source-only testing root.\n")
    packet = mirror / TARGET.relative_to(ROOT)
    packet.mkdir(parents=True)
    for source in ("calculate.py", "verify.py", "inputs.json"):
        shutil.copyfile(TARGET / source, packet / source)
        assert sha(packet / source) == EXPECTED[source]
    pins = {**result["source_sha256"], **verification["source_sha256"]}
    for relative, expected in pins.items():
        target = mirror / relative
        if target.exists():
            assert sha(target) == expected
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(ROOT / relative)
    output = packet / "producer-replay.json"
    command = [sys.executable, "-B", str(packet / "calculate.py"), "--out"]
    success = subprocess.run([*command, str(output)], cwd=directory, capture_output=True, text=True, check=False, timeout=30)
    assert success.returncode == 0, success.stderr
    replay = read(output)
    assert replay["scenarios"] == result["scenarios"] and replay["affected_members"] == result["affected_members"]
    assert replay["source_sha256"] == result["source_sha256"]
    verifier_output = packet / "verifier-replay.json"
    verifier = subprocess.run([sys.executable, "-B", str(packet / "verify.py"), "--out", str(verifier_output)],
                              cwd=directory, capture_output=True, text=True, check=False, timeout=30)
    assert verifier.returncode == 0, verifier.stderr
    assert read(verifier_output)["checked_bore_and_seat_rows"] == 64
    target = packet / "protected-target.json"
    target.write_text("preserved")
    dangling, existing_link = packet / "dangling.json", packet / "existing-link.json"
    dangling.symlink_to(packet / "absent-target.json")
    existing_link.symlink_to(target)
    cases = {"occupied_output": output, "input_alias": packet / "inputs.json", "existing_target_symlink": existing_link,
             "dangling_symlink": dangling, "outside_packet": mirror / "outside.json"}
    negatives = {}
    before = {p: sha(p) for p in (output, target, packet / "inputs.json")}
    for label, path in cases.items():
        run = subprocess.run([*command, str(path)], cwd=directory, text=True, capture_output=True, check=False, timeout=30)
        assert run.returncode != 0
        assert all(sha(p) == h for p, h in before.items())
        assert not (packet / "absent-target.json").exists() and dangling.is_symlink() and existing_link.is_symlink()
        assert not (mirror / "outside.json").exists()
        negatives[label] = {"returncode": run.returncode, "protected_bytes_preserved": True}
    race = packet / "race.json"
    processes = [subprocess.Popen([*command, str(race)], cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    for process in processes:
        process.communicate(timeout=30)
    assert sorted(p.returncode for p in processes) == [0, 1]
    assert read(race)["scenarios"] == result["scenarios"]
    return {"byte_identical_program_and_input_copies": True, "source_assets_linked_to_exact_original_bytes": True,
            "all_outputs_in_private_temporary_root": True, "producer_scenarios_and_source_pins_exact_match": True,
            "verifier_checked_rows": 64, "negative_CLI_controls": negatives,
            "same_output_competition": {"returncodes": [0, 1], "complete_successful_output_preserved": True},
            "dangling_symlink_limit": "Exclusive final open preserves the link and target; this producer does not promise reservation before source-only arithmetic."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    packet_path = TARGET / "controls01/frozen-packet.json"
    frozen_sha = sha(packet_path)
    frozen = read(packet_path)
    frozen_files = frozen["final_files"] + frozen["retained_development_files"]
    verification = read(TARGET / "verification-v1.json")

    def unchanged():
        assert sha(packet_path) == frozen_sha
        for record in frozen_files:
            path = ROOT / record["path"]
            assert sha(path) == record["sha256"] and path.stat().st_size == record["bytes"]
        assert all(sha(TARGET / name) == value for name, value in EXPECTED.items())
        assert all(sha(ROOT / path) == value for path, value in verification["source_sha256"].items())

    unchanged()
    m, v = load(TARGET / "calculate.py", "testing_receiver_producer"), load(TARGET / "verify.py", "testing_receiver_verifier")
    inp, result = read(TARGET / "inputs.json"), read(TARGET / "result.json")
    data = {key: read(ROOT / ref["path"]) for key, ref in inp["sources"].items() if ref["path"].endswith(".json")}
    datum = m.pure(inp["sources"]["datum_helper"], "testing_receiver_datum")
    capsule = m.pure(inp["sources"]["capsule_helper"], "testing_receiver_capsule")
    assert v.check(result, inp, data["geometry"], data["profiles"], data["placement"]) == 64
    scope_and_skin(result, inp)
    axes, proposed, members, cuts = m.existing_inventory(inp, data, datum)
    assert m.scenarios(inp, proposed, members, cuts, capsule) == result["scenarios"]
    assert all(axes[key]["point_xyz_mm"][2] == 200 for key in inp["axis_ids"])
    inventory = inventory_controls(m, inp, data, datum)
    scenario = scenario_controls(m, inp, proposed, members, cuts, capsule)
    arithmetic = hand_arithmetic(capsule, v)
    corruptions = {}
    for label, mutate in (("wrong_inward_sign", lambda r: r["scenarios"][0]["nominal_annular_seats"][0].update(inward_X_sign=0)),
                          ("wrong_receiver_owner", lambda r: r["scenarios"][0]["nominal_annular_seats"][0].update(receiver="eoere_cleat_right")),
                          ("changed_separation", lambda r: r["scenarios"][0]["bore_occurrences"][0]["minimum_other_cut_separation"].update(capsule_separation_lower_bound_mm=0)),
                          ("invented_capacity", lambda r: r.update(complete_joint_resistance=1.))):
        altered = copy.deepcopy(result)
        mutate(altered)
        corruptions[label] = rejected(lambda altered=altered: v.check(altered, inp, data["geometry"], data["profiles"], data["placement"]))
    with tempfile.TemporaryDirectory(prefix="receiver-seat-testing-") as scratch:
        cli = mirror_cli(Path(scratch), inp, result, verification)
    unchanged()
    assert not any(n in sys.modules for n in ("cadquery", "OCP", "numpy", "scipy"))
    report = {"schema": "eoere_current_Z180_receiver_seats_independent_testing_review/v1",
        "status": "PASS_SOURCE_RECIPE_TESTING_ONLY_CURRENT_AXES_REMAIN_Z200", "confirmed_substantial_findings": [],
        "source_sha256": {str((TARGET / name).relative_to(ROOT)): value for name, value in EXPECTED.items()},
        "frozen_packet_manifest": {"path": str(packet_path.relative_to(ROOT)), "sha256": frozen_sha},
        "frozen_final_and_development_files_unchanged": len(frozen_files), "verification_source_pins_unchanged": len(verification["source_sha256"]),
        "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
        "independent_finite_edge_parallel_axis_verifier_checked_rows": 64,
        "producer_source_functions_reproduce_frozen_scenarios": True,
        "independent_annular_skin_within_source_thickness_and_limits_checked": True,
        "source_inventory_corruptions_rejected": inventory, "scenario_boundary_corruptions_rejected": scenario,
        "additional_independent_hand_arithmetic": arithmetic,
        "additional_verifier_corruptions_rejected": corruptions, "temporary_mirror_actual_CLI_checks": cli,
        "scope": "Four unadopted Z180 axes, eight receiver occurrences/eight external nominal annuli, nominal and maximum-hole cases, retained-old versus replaced-old void inventories. All current source axes stay Z200.",
        "limits": result["limits"], "required_next_inputs_or_queries": result["required_next_inputs_or_queries"],
        "execution": {"stdlib_source_metadata_and_analytic_helpers_only": True, "CAD_native_global_component_tool_or_model_action": False,
                      "actual_BREP_bytes_only_authenticated": True, "shared_source_index_staging_or_commit_changes": False},
        "complete_joint_resistance": None, "release": result["release"],
        "retention": "Keep this compact testing helper/receipt active. Disposable source-linked CLI mirror and corruptions used /tmp and in-memory copies; no frozen evidence was removed or changed."}
    path = OWN.with_name("receipt.json")
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
