"""Independent source/architecture/retention review; no geometry or force run.

Hash frozen files, inspect saved JSON and private correction seams, and reproduce
one output-ownership defect with temporary files and a deliberately inert intake.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
HERE = OWN.parents[2]
EXPECTED = {
    "descriptor.py": "691f46fd47b2e952e3b8911d61ddf855d9806c20190f77a1d6e0f57ad022a9ac",
    "review-fix-v2/descriptor.py": "8ab67c15c544ba1cf1f0209020fb87614072c665a8eaa39dc667a23db5b2823a",
    "review-fix-v3/descriptor.py": "b9540ab1612033194c8ae7ac230ab21082813cd63cf824cc77b58cba9bfa6b1b",
    "review-fix-v4/descriptor.py": "a7b27b82eb3bafc698d371ce2f4b2e71c89cc4306459cd795ed1ca1c983ae106",
    "review-fix-v4/inputs.json": "a359cb1c7c3c30954d6e36204bd523cd0d565c10a9b78f9af09e6ddcbb66b6be",
    "runs-v1/attempt03/descriptor.json": "e7a1a56f7c61119445c85f554d534abc5c43f77fede27a7fab42ad252bb275f0",
    "result.json": "3b8c2b7849573104a10ca1b0cf827bd9b0055c6edf3ee2ac91feaab88e3357d4",
}
HOSTS = {"base_post_outer_left", "base_post_outer_right", "eoere_cleat_left", "eoere_cleat_right"}
AXES = {"cleat_post_bolt_" + side + "_" + str(i) for side in ("left", "right") for i in (1, 2)}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def indexed(rows, key="id"):
    result = {row[key]: row for row in rows}
    assert len(result) == len(rows)
    return result


def union(pins, additions):
    for name, digest in additions.items():
        assert name not in pins or pins[name] == digest
        pins[name] = digest


def output_ownership_reproduction(function):
    """No source intake or descriptor arithmetic runs; only fake FAILED writes."""
    with tempfile.TemporaryDirectory(prefix="z180-output-owner-review-") as temporary:
        base = Path(temporary).resolve()
        packet, outside, alias = base / "packet", base / "outside", base / "alias"
        runs = packet / "runs-v1"
        runs.mkdir(parents=True)
        outside.mkdir()
        alias.symlink_to(runs, target_is_directory=True)
        mkdir, calls = Path.mkdir, []

        def retarget_mkdir(path, *args, **kwargs):
            if path == alias:
                alias.unlink()
                alias.symlink_to(outside, target_is_directory=True)
            return mkdir(path, *args, **kwargs)

        def inert_intake(*args, **kwargs):
            calls.append("fake intake only")
            raise RuntimeError("inert review stop")

        with patch.dict(function.__globals__, {"OWN": packet / "descriptor.py", "ROOT": base, "load_inputs": inert_intake}), \
                patch.object(Path, "mkdir", retarget_mkdir):
            try:
                function(base / "unused.json", "unused", alias / "descriptor.json")
            except RuntimeError as error:
                assert str(error) == "inert review stop"
            else:
                raise AssertionError("inert callback must stop the write")
        saved = read(outside / "descriptor.json")
        assert saved["status"] == "FAILED" and not any(saved["release"].values())
        assert not (runs / "descriptor.json").exists() and calls == ["fake intake only"]
        return {"outside_owned_runs_output_created": True, "owned_runs_output_created": False,
                "outside_status": saved["status"], "callbacks": calls,
                "genuine_descriptor_build_or_source_intake": False}


def main():
    assert all(sha(HERE / name) == digest for name, digest in EXPECTED.items())
    frozen = {relative(path): sha(path) for path in HERE.rglob("*") if path.is_file()
              and not any(part.startswith("independent-review") or part == "__pycache__" for part in path.relative_to(HERE).parts)}
    inp, result, compact = (read(HERE / name) for name in ("review-fix-v4/inputs.json", "runs-v1/attempt03/descriptor.json", "result.json"))
    records = {key: read(ROOT / ref["path"]) for key, ref in inp["sources"].items() if Path(ref["path"]).suffix == ".json"}
    current, native = records["current"], records["native"]
    pins = {relative(HERE / "review-fix-v4/inputs.json"): EXPECTED["review-fix-v4/inputs.json"], inp["helper"]["path"]: inp["helper"]["sha256"]}
    union(pins, {ref["path"]: ref["sha256"] for ref in inp["sources"].values()})
    for key in ("current", "native", "receiver_inventory"):
        union(pins, records[key]["source_sha256"])
    for row in current["finished_body_observations"]:
        union(pins, {row["source"]["path"]: row["source"]["sha256"]})
    for scenario in native["scenarios"]:
        if scenario["scenario"] in {"current_Z200_modeled", "proposed_Z180_modeled"}:
            union(pins, {ref["path"]: ref["sha256"] for ref in scenario["finished_bodies"].values()})
    assert pins == result["source_sha256"] and len(pins) == compact["consumed_source_pins"] == 1116

    def unchanged():
        assert all(sha(HERE / name) == digest for name, digest in EXPECTED.items())
        assert all(sha(ROOT / path) == digest for path, digest in frozen.items())
        assert all(sha(Path(path) if Path(path).is_absolute() else ROOT / path) == digest for path, digest in pins.items())

    unchanged()
    assert compact["descriptor"] == {"path": relative(HERE / "runs-v1/attempt03/descriptor.json"), "sha256": EXPECTED["runs-v1/attempt03/descriptor.json"]}
    assert compact["descriptor_bytes"] == (HERE / "runs-v1/attempt03/descriptor.json").stat().st_size == 6092178
    assert compact["source_closure_canonical_sha256"] == canonical(pins)
    assert compact["inputs"] == {"path": relative(HERE / "review-fix-v4/inputs.json"), "sha256": EXPECTED["review-fix-v4/inputs.json"]}
    assert compact["helper"] == inp["sources"]["mixed_contact_contract_adapter"]
    for name in ("method", "tests", "source_contract_audit"):
        ref = compact[name]
        assert sha(ROOT / ref["path"]) == ref["sha256"]
    assert compact["source_corrections"] == result["descriptor_source_corrections"]
    assert compact["source_only_parent_manifest"] == result["manifest"] == inp["sources"]["manifest"]
    assert result["geometry"] == compact["frozen_geometry"] == inp["sources"]["layout"]
    assert result["parent_descriptors"] == compact["parent_descriptors"] == inp["sources"]["current"]
    assert result["parent_geometry"] == compact["parent_geometry"] == inp["sources"]["current_geometry"]
    assert all(not any(record["release"].values()) for record in (inp, result, compact, current, records["layout"], records["manifest"]))
    assert result["complete_joint_resistance"] is compact["complete_joint_resistance"] is None
    for name in ("force_execution_readiness_claimed", "historical_q_forces_operators_or_acceptance_transferred",
                 "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed"):
        assert result[name] is compact[name] is False
    assert result["unresolved_joins"] == compact["unresolved_joins"]
    assert records["manifest"]["readiness"] == {"candidate_operator_assembly_or_solve": False,
        "independent_field_admission": False, "source_only_analytic_descriptor_preparation": True}
    assert inp["scope"]["original_4in_hardware"] is True and inp["scope"]["spacer_proposal_included"] is False
    for ref in compact["preserved_failures"]:
        assert sha(ROOT / ref["path"]) == ref["sha256"]
        failure = read(ROOT / ref["path"])
        output_ref = failure["failed_output"]
        assert sha(ROOT / output_ref["path"]) == output_ref["sha256"]
        assert read(ROOT / output_ref["path"])["status"] == "FAILED"

    proof = result["geometry_delta_proof"]
    assert compact["counts"] == proof["counts"]
    assert compact["byte_identical_descriptor_fields"] == proof["byte_identical_descriptor_fields"]
    assert all(current[key] == result[key] for key in proof["byte_identical_descriptor_fields"])
    old_shafts, shafts = indexed(current["shafts"], "axis_id"), indexed(result["shafts"], "axis_id")
    assert len(shafts) == 100 and set(shafts) == set(old_shafts)
    assert {key for key in shafts if shafts[key] != old_shafts[key]} == AXES
    for axis_id in AXES:
        expected_axis = copy.deepcopy(old_shafts[axis_id]["source_axis"])
        expected_axis["point_xyz_mm"][2] -= 20.
        assert shafts[axis_id]["source_axis"] == expected_axis and expected_axis["nominal_under_head_length_mm"] == 101.6
        assert len(shafts[axis_id]["metal_roles"]) == 5
        for before, after in zip(old_shafts[axis_id]["metal_roles"], shafts[axis_id]["metal_roles"], strict=True):
            assert after["center_of_mass_xyz_mm"] == [before["center_of_mass_xyz_mm"][0], before["center_of_mass_xyz_mm"][1], before["center_of_mass_xyz_mm"][2] - 20.]
    assert len(result["hillman_rows"]) == 66 and result["hillman_rows"] == current["hillman_rows"]
    assert len(result["physical_owner_gravity_rows"]) == 150
    old_bodies, bodies = indexed(current["finished_body_observations"]), indexed(result["finished_body_observations"])
    assert len(bodies) == 28 and {key for key in bodies if bodies[key] != old_bodies[key]} == HOSTS
    assert set(proof["COM"]) == set(compact["COM"]) == HOSTS
    for host in HOSTS:
        assert bodies[host]["source_only_analytic_centroid"] is True
        assert proof["COM"][host]["new_native_COM_query_performed"] is False
        assert compact["COM"][host]["native_COM_query_performed"] is False
        assert bodies[host]["center_xyz_mm"] == compact["COM"][host]["new_center_xyz_mm"] == proof["COM"][host]["new_center_xyz_mm"]
        assert compact["COM"][host]["old_COM_source"] == proof["COM"][host]["old_COM_observation_source"]
    patches, old_patches = indexed(result["timber_and_panel_shared_face_patches"]), indexed(current["timber_and_panel_shared_face_patches"])
    rebuilt = {row["id"] for row in proof["rebuilt_patches"]}
    inherited = {row["id"] for row in proof["changed_host_inherited_regions"]}
    assert len(rebuilt) == 2 and len(inherited) == 12
    retired_patch_keys = {"source_first_face", "source_second_face", "trimmed_region_signature_sha256", "coplanar_offset_mm", "opposed_normal_dot", "occupancy_refinement_levels"}
    retired_cell_keys = {"both_inward_material_probes_occupied", "reference_centroid_on_trimmed_patch", "reference_centroid_patch_distance_mm"}
    for identity in rebuilt | inherited:
        row = patches[identity]
        assert not (set(row) & retired_patch_keys)
        assert row["inherited_native_observation"] == {"source_export": inp["sources"]["current"], "patch_id": identity,
            "patch_canonical_sha256": canonical(old_patches[identity]), "observed_geometry_is_parent_Z200": True}
        assert canonical(row["source_region_identity"]) == row["analytic_source_region_sha256"]
        assert all(not (set(cell) & retired_cell_keys) and cell["analytic_material_at_reference"]["native_probe_performed"] is False for cell in row["cells"])
    assert all(patches[key] == old_patches[key] for key in patches.keys() - rebuilt - inherited)
    changed_floors = [row for row in result["floor_observations"] if row["host"] in HOSTS]
    assert len(changed_floors) == 2
    assert all(row["source_only_unchanged_floor_region_proved"] is True and "own_floor_face_confirmed_from_current_cached_solid" not in row for row in changed_floors)
    for row in result["finished_receiver_wall_queries"]:
        if row["receiver"] in HOSTS:
            assert row["observation_provenance"]["query_performed_now"] is False
            assert row["observation_provenance"]["saved_native_result"] == inp["sources"]["native"]
    for key, compact_key in (("flange_domains", "flange_domains_canonical_sha256_before_and_after"),
                             ("flange_shared_face_patches", "flange_patches_canonical_sha256_before_and_after")):
        assert current[key] == result[key] and canonical(result[key]) == compact[compact_key]
    assert compact["contact_reuse"] == result["mixed_contact_source_contract"]

    imports = {}
    for name in ("descriptor.py", "review-fix-v2/descriptor.py", "review-fix-v3/descriptor.py", "review-fix-v4/descriptor.py"):
        tree = ast.parse((HERE / name).read_bytes())
        names = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        names.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
        assert names <= sys.stdlib_module_names
        imports[name] = sorted(names)
    v4 = runpy.run_path(str(HERE / "review-fix-v4/descriptor.py"))
    private = v4["corrected_v3"]()
    second = v4["corrected_v3"]()
    assert private is not second and private.source_correction_record is not second.source_correction_record
    v2 = private.verified_v2()
    base = private.corrected_frozen_module(v2)
    assert base is not sys.modules.get(base.__name__)
    previous_verify = base.verify
    try:
        with v2.source_context(base):
            assert base.verify is not previous_verify
            raise RuntimeError("inert restoration check")
    except RuntimeError:
        pass
    assert base.verify is previous_verify
    absolute = {path: digest for path, digest in pins.items() if Path(path).is_absolute()}
    assert absolute == v2.INHERITED_ABSOLUTE_PINS and len(absolute) == 2
    assert private.PROPOSAL_RELEASE == result["descriptor_source_corrections"]["authentic_proposal_release_keys"]
    assert not any(private.PROPOSAL_RELEASE.values()) and set(private.PROPOSAL_RELEASE) != set(result["release"])
    assert v4["verify_output_reuse"](current, result) == result["mixed_contact_source_contract"]
    reproduction = output_ownership_reproduction(base.write_descriptor)
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    finding = {
        "id": "canonical_output_parent_not_bound", "priority": "P2",
        "path": relative(HERE / "descriptor.py"), "line": 556, "end_line": 558,
        "description": "The guard validates out.parent.resolve(), then mkdir and exclusive open reuse the unresolved parent alias. Retargeting that alias between validation and reservation can create the retained STARTED/FAILED output outside this packet's runs-v1.",
        "impact": "Future reproductions can violate output ownership and lose the owned retained failure record. Issued attempt03 uses the canonical in-packet path; this finding does not invalidate its saved geometry arithmetic or source bytes.",
        "concrete_fix": "Resolve and validate the parent once, then bind out = canonical_parent / out.name before mkdir and exclusive reservation; preserve the current reserved-inode check and STARTED/FAILED retention.",
        "inert_reproduction": reproduction,
    }
    receipt = {
        "schema": "eoere_z180_geometry_descriptors_independent_review/v1",
        "status": "independent_z180_descriptor_source_checks_fail", "success": False,
        "findings": [finding], "descriptor": compact["descriptor"], "release": result["release"],
        "all_release_false": True,
        "target_sha256": {relative(HERE / name): digest for name, digest in EXPECTED.items()},
        "sourcepins": {"verified_before_after": len(pins), "exact_reconstructed_union": True,
                       "canonical_sha256": canonical(pins), "inherited_absolute_pins_unchanged": absolute},
        "saved_result_checks": {"compact_result_binds_exact_issued_descriptor": True,
            "protected_100_shafts_66_screws_150_owners_28_finished_bodies": True,
            "four_axes_twenty_role_centers_original4in_no_spacer": True,
            "four_analytic_COMs_two_rebuilt_patches_twelve_inherited_regions_two_floor_regions": True,
            "old_native_observations_retired_or_exactly_inherited_with_provenance": True,
            "flange_and_unaffected_contacts_preserved": True,
            "private_correction_modules_and_verifier_restoration": True,
            "stdlib_imports": imports},
        "architecture": {
            "ownership": "The frozen base owns metadata intake, cylinder/moment deltas and reservation. Private v2 adds only two exact inherited absolute pin spellings; v3 changes one authenticated release comparison; v4 changes one authenticated mixed-contact iterable after exact source joins. Private module instances contain overrides, and v2 restores the verifier in finally.",
            "claims": "Saved receiver walls/volumes remain tied to their native result and exact saved BREP hashes. Four new COMs and changed contact/floor descriptors are marked analytic or inherited; old face/probe qualification flags are retired. Distinct proposal release keys remain authentic all-false. No source-only descriptor is an operator, RHS, response, field admission, native geometry revalidation or force/capacity acceptance.",
            "deferred": "Unchanged panel/material/support primitives are retained for parent validation, with fresh own-case maps, RHS, operators, method/producer/admission and serialized execution still explicit unresolved joins. No extra physical or sign-off prerequisite is added.",
            "retention": "The compact33259-byte result links the ignored6092178-byte issued descriptor and frozen methods, corrections, inputs, audit and two failed trials. Frozen original paths and bytes remain active. No raw copy, archive, pruning, model or documentation change occurs.",
        },
        "retention_checks": {"existing_frozen_files_unchanged": len(frozen), "frozen_map_canonical_sha256": canonical(frozen),
                             "two_failure_records_and_failed_outputs_preserved": True},
        "limits": ["Read-only saved JSON/source checks, source hashing and one temporary inert output-owner reproduction only.",
                   "No genuine descriptor CLI or geometry arithmetic rerun; no mechanics input, panel preparation, K/q/force, CAD/BREP query, native solve or physical work.",
                   "Substantial finding concerns future output reservation. Exact issued attempt03 remains eligible for separate arithmetic review within its source-only unadopted scope."],
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN), "receipt": relative(OWN.with_name("receipt.json"))},
        "target_shared_docs_Git_index_staging_commit_or_cleanup_action": False,
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "findings": len(receipt["findings"]), "pins": len(pins),
                      "helper_sha256": sha(OWN), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
