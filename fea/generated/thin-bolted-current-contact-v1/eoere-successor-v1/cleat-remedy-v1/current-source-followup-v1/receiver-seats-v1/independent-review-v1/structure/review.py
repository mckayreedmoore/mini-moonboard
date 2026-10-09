"""Architecture/source/retention review of the unadopted source-only Z180 proof.

Replay reads frozen files, calls the separate stdlib verifier's check function,
and runs only early-rejected producer CLIs. It writes this receipt only; no
producer calculation, model edit, CAD query or mechanics is performed.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
EXPECTED = {
    "inputs.json": "e3fda210640db0bc395d808c90625d65e8049da315c0872da12077731e6f0e41",
    "calculate.py": "5f6d088a836f1ac198c2cc7c8355b3a6ca8a20034a863ab813e4e33fa4a3fa03",
    "result.json": "a21c25d6693a86f2617655cec1e82aa51c182b153e19baf8f5d1431afa381443",
    "verify.py": "1ab517d0e2b874fc43c9c4f78fce1cda80dd6dbda2a70f9e37ebdce2edffc51c",
    "verification-v1.json": "ae0c5dd215fd2bddaa6c2b0fcf46fa51038ac672d8611722ee34b4b4d6afded6",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    assert all(sha(PACKET / path) == expected for path, expected in EXPECTED.items())
    frozen_path = PACKET / "controls01/frozen-packet.json"
    frozen_raw_sha = sha(frozen_path)
    frozen = read(frozen_path)
    protected = [*frozen["final_files"], *frozen["retained_development_files"]]
    assert len(frozen["final_files"]) == len(frozen["retained_development_files"]) == 5
    assert {Path(row["path"]).name: row["sha256"] for row in frozen["final_files"]} == EXPECTED
    parent_manifest = PACKET.parent / "controls02/frozen-packet.json"
    parent_manifest_sha = sha(parent_manifest)
    parent_files = read(parent_manifest)["files"]
    assert len(parent_files) == 6
    previous_reviews = {relative(path): sha(path) for path in (PACKET.parent / "independent-review-v1").rglob("*") if path.is_file()}

    def unchanged():
        assert sha(frozen_path) == frozen_raw_sha
        assert all(sha(ROOT / row["path"]) == row["sha256"] and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in protected)
        assert sha(parent_manifest) == parent_manifest_sha
        assert all(sha(ROOT / row["path"]) == row["sha256"] for row in parent_files)
        assert all(sha(ROOT / path) == expected for path, expected in previous_reviews.items())

    unchanged()
    inp, result, verification = (read(PACKET / name) for name in ("inputs.json", "result.json", "verification-v1.json"))
    pins = verification["source_sha256"]
    assert len(pins) == 29 and all(sha(ROOT / path) == expected for path, expected in pins.items())
    assert all(inp["source_sha256"][source["path"]] == source["sha256"] for source in inp["sources"].values())
    data = {key: read(ROOT / inp["sources"][key]["path"]) for key in ("geometry", "profiles", "placement")}
    current_axes = {row["id"]: row for row in data["geometry"]["axes"]}
    assert len(current_axes) == 100 and len(data["geometry"]["screw_axes"]) == 66
    assert all(current_axes[identity]["point_xyz_mm"][2] == 200 for identity in inp["axis_ids"])
    for proposed in result["proposed_axes"]:
        expected = copy.deepcopy(current_axes[proposed["id"]])
        expected["point_xyz_mm"][2] = 180
        assert proposed == expected
    assert result["current_geometry_adopted_or_changed"] is False and result["complete_joint_resistance"] is None
    assert all(value is False for value in result["release"].values())
    assert any("consistency check" in limit for limit in result["limits"])
    assert any("Screw pilots" in limit for limit in result["limits"])
    assert any("No new finished BREP" in limit for limit in result["limits"])
    stdlib_sources = [PACKET / "calculate.py", PACKET / "verify.py", *[ROOT / inp["sources"][key]["path"] for key in ("datum_helper", "capsule_helper")]]
    import_roots = {}
    for path in stdlib_sources:
        tree = ast.parse(path.read_bytes())
        names = {node.module.split(".")[0] for node in tree.body if isinstance(node, ast.ImportFrom)}
        names.update(alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import) for alias in node.names)
        assert names <= sys.stdlib_module_names
        import_roots[relative(path)] = sorted(names)
    spec = importlib.util.spec_from_file_location("independent_receiver_structure_saved_verifier", PACKET / "verify.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    checked_rows = verifier.check(result, inp, data["geometry"], data["profiles"], data["placement"])
    assert checked_rows == 64
    corruption_controls = []
    for label, mutate in (
        ("missing_own_seat", lambda r: r["scenarios"][0]["nominal_annular_seats"].pop()),
        ("wrong_proposed_Z", lambda r: r["proposed_axes"][0]["point_xyz_mm"].__setitem__(2, 200)),
        ("changed_bore_margin", lambda r: r["scenarios"][0]["bore_occurrences"][0].update(bore_to_raw_profile_edge_lower_bound_mm=0)),
        ("invented_physical_support", lambda r: r["scenarios"][0]["nominal_annular_seats"][0].update(physical_contact_or_strength_qualified=True)),
        ("hidden_old_void_provenance", lambda r: r["scenarios"][0]["nominal_annular_seats"][0]["minimum_other_cut_separation"].update(second_cut_geometry_provenance="proposed_Z180")),
    ):
        altered = copy.deepcopy(result)
        mutate(altered)
        try:
            verifier.check(altered, inp, data["geometry"], data["profiles"], data["placement"])
        except ValueError:
            corruption_controls.append(label)
        else:
            raise AssertionError("corruption accepted: " + label)
    cli_controls = []
    outside = OWN.parent / "must-remain-absent.json"
    assert not outside.exists()
    for label, target in (("occupied_output", PACKET / "result.json"), ("input_output_alias", PACKET / "inputs.json"), ("outside_owned_packet", outside)):
        response = subprocess.run([sys.executable, "-B", str(PACKET / "calculate.py"), "--out", str(target)],
                                  cwd=ROOT, capture_output=True, check=False, timeout=10)
        assert response.returncode != 0 and b"fresh direct output in owned packet required" in response.stderr
        cli_controls.append(label)
    assert not outside.exists()
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    assert all(sha(ROOT / path) == expected for path, expected in pins.items())
    receipt = {
        "schema": "eoere_Z180_receiver_seats_independent_structure_review/v1",
        "status": "PASS_NO_SUBSTANTIAL_FINDINGS_SOURCE_ONLY_SCOPE",
        "confirmed_findings": [],
        "scope": "Architecture, source identity, bounded claims and retention for unadopted source-profile bore/nominal-annulus proof only",
        "target_sha256": {relative(PACKET / path): expected for path, expected in EXPECTED.items()},
        "frozen_packet_manifest": {"path": relative(frozen_path), "sha256": frozen_raw_sha},
        "preserved_parent_packet_manifest": {"path": relative(parent_manifest), "sha256": parent_manifest_sha},
        "retention_checks": {"five_final_files_unchanged": True, "five_development_files_unchanged": True,
                             "final_packet_bytes": sum(row["bytes"] for row in frozen["final_files"]),
                             "development_evidence_bytes": sum(row["bytes"] for row in frozen["retained_development_files"]),
                             "source_pins_verified_before_after": len(pins),
                             "six_parent_files_unchanged": True, "previous_parent_review_files_unchanged": len(previous_reviews),
                             "source_pin_map_canonical_sha256": hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                             "archive_move_prune_cleanup_performed": False},
        "independent_review_controls": {"saved_verifier_rows": checked_rows, "corruptions_rejected": corruption_controls,
                                        "early_CLI_rejections": cli_controls, "stdlib_only_module_imports": import_roots,
                                        "current_model_target_axes_still_Z200": True, "proposal_changes_only_four_Z_coordinates": True,
                                        "source_recipe_producer_reexecuted": False},
        "architecture": {
            "ownership": "calculate owns the bounded source-profile/cut inventory and four analytic scenarios; pinned cut-datums.world owns coordinate transformation, pinned finite-envelope helper owns primitive/distance arithmetic. verify uses separate coordinate permutation and finite-edge/parallel-axis arithmetic.",
            "coupling": "Imported helper modules use only standard-library imports; their legacy main/build entrypoints are not called. CAD recipe sources and four BREP files are authenticated source witnesses, with no import, query or current component execution.",
            "source_binding": "Exact current profile/cache/geometry/placement references join 100 current shafts, 66 current screws and four proposed Z-only moves. All source refs are covered by the bounded frozen pin map. Current Z200 geometry remains authority.",
            "claim_boundary": "Bore and annular containment belongs to four explicit diameter/void branches. Retained Z200 voids are read-only comparison; proposed adoption replaces eight old receiver void occurrences. Saved-volume equality is consistency evidence, not reconstructed topology. Omitted timber screw pilots/countersinks, delivered parts, uncertainty, actual contact and tool paths remain explicit limits.",
            "failure_ownership": "Source-only CLIs reject occupied/aliased/outside outputs before intake and exclusively create final files. The first stdout-formatting failure, its exact source snapshot and written result are retained separately; no failed evidence is overwritten or relabeled success.",
            "retention": "Final sources/results, all five development witnesses, upstream placement/shop receipts, exact receiver BREP witnesses and shared helpers remain active. No duplicate installation/manual/mesh or new bulky evidence was created by this review.",
        },
        "remaining": ["Source-only analytic support does not adopt Z180 or release drilling instructions.",
                      "Parent must separately assess readiness for four receiver reconstructions, eight new finished bore/seat observations and affected current intersections.",
                      "Actual fit/tool/removal envelopes and complete-joint mechanics remain open; panel/screw remedies stay stopped; Z200 forces do not transfer."],
        "actual_CAD_native_global_current_component_model_or_physical_execution": False,
        "target_shared_index_staging_commit_or_cleanup_action": False,
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN), "receipt": relative(OWN.with_name("receipt.json"))},
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "rows": checked_rows, "pins": len(pins), "helper_sha256": sha(OWN),
                      "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
