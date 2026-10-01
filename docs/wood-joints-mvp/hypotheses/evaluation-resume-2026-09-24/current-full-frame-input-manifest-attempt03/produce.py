"""Refresh source-only current-frame input readiness without making a solver deck."""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
OUTPUT_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt03"
)
OUTPUT = OUTPUT_DIR / "current-full-frame-input-manifest.json"
README = OUTPUT_DIR / "README.md"
PRODUCER = OUTPUT.as_posix().replace("current-full-frame-input-manifest.json", "produce.py")

BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
PREVIOUS = BASE / "current-full-frame-input-manifest-attempt02"
SOLIDS = BASE / "current-full-frame-member-solids-attempt01"
TIMBER_MAP = BASE / "current-frame-timber-material-frame-map-attempt01"
BLOCK_MAP = BASE / "current-block-material-frame-map-attempt02"
DEAD_LOAD = BASE / "current-frame-dead-load-scenarios-attempt01"
MASS_CENTROIDS = BASE / "current-mass-centroids-attempt01/mass-centroids.json"
MASS_TOPOLOGY = BASE / "current-mass-topology-map-attempt03/source-topology-map.json"
LOAD_CASES = BASE / "current-load-cases.json"
SOLVER_PROFILE = Path("fea/calculix_223/solver-profile.json")

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
SELECTED = "compact-floor-flush-development"
REVIEWED_COMMIT = "b1e8707d"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _pin(path: Path, *, digest_key: str | None = None) -> dict[str, Any]:
    absolute = ROOT / path
    record: dict[str, Any] = {
        "path": path.as_posix(),
        "file_sha256": _sha256(absolute),
        "size_bytes": absolute.stat().st_size,
    }
    if digest_key is not None:
        data = _read_json(path)
        record["content_digest_field"] = digest_key
        record["content_digest"] = data[digest_key]
    return record


def _artifact_binding(
    path: Path,
    *,
    digest_key: str | None = None,
    counts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    binding = _pin(path, digest_key=digest_key)
    if counts:
        binding["reconciled_facts"] = counts
    return binding


def build_manifest() -> dict[str, Any]:
    previous_path = PREVIOUS / "current-full-frame-input-manifest.json"
    previous = _read_json(previous_path)
    previous_payload = dict(previous)
    previous_digest = previous_payload.pop("manifest_sha256", None)
    if previous_digest != hashlib.sha256(_canonical_json(previous_payload)).hexdigest():
        raise ValueError("attempt02 manifest content digest does not verify")
    if (previous["candidate"], previous["geometry_revision_id"],
            previous["selected_candidate_authority_preserved"]) != (
            CANDIDATE, REVISION, SELECTED):
        raise ValueError("attempt02 candidate/revision/selected authority changed")
    if previous["reviewed_repository_commit"] != REVIEWED_COMMIT:
        raise ValueError("attempt02 reviewed candidate checkpoint changed")

    bundle_path = SOLIDS / "bundle/current-full-frame-member-solids.json"
    bundle = _read_json(bundle_path)
    if (
        bundle["candidate"] != CANDIDATE
        or bundle["geometry_revision_id"] != REVISION
        or bundle["reviewed_source_commit"] != REVIEWED_COMMIT
        or bundle["selected_candidate_preserved"] != SELECTED
        or bundle["readiness"]["all_50_finished_member_solids_exported"] is not True
        or bundle["readiness"]["step_roundtrip_checked"] is not True
        or bundle["readiness"]["native_solve_executed"] is not False
    ):
        raise ValueError("50-member bundle identity/readiness does not match")

    bundle_dir = SOLIDS
    step_records: list[dict[str, Any]] = []
    for row in bundle["members"]:
        step_path = bundle_dir / row["step_file"]
        if not (ROOT / step_path).is_file():
            raise ValueError(f"missing STEP file: {step_path.as_posix()}")
        if _sha256(ROOT / step_path) != row["step_sha256"]:
            raise ValueError(f"STEP hash differs: {step_path.as_posix()}")
        if (ROOT / step_path).stat().st_size != row["step_size_bytes"]:
            raise ValueError(f"STEP size differs: {step_path.as_posix()}")
        if row["shape_summary"]["solid_count"] != 1:
            raise ValueError(f"STEP source is not one solid: {row['member_id']}")
        if row["step_roundtrip_summary"]["valid"] is not True:
            raise ValueError(f"STEP round-trip is not valid: {row['member_id']}")
        step_records.append(
            {
                "member_id": row["member_id"],
                "member_kind": row["member_kind"],
                "path": step_path.as_posix(),
                "file_sha256": row["step_sha256"],
                "size_bytes": row["step_size_bytes"],
                "source_shape_fingerprint_sha256": row[
                    "source_shape_fingerprint_sha256"
                ],
                "shape_summary_sha256": row["shape_summary_sha256"],
                "source_bounds_and_volume_match": row[
                    "bounds_and_volume_match_current_manifest"
                ],
                "one_solid_valid_roundtrip": True,
            }
        )
    member_ids = [row["member_id"] for row in step_records]
    step_files = sorted((ROOT / SOLIDS / "bundle/members").glob("*.step"))
    if len(step_records) != 50 or len(set(member_ids)) != 50 or len(step_files) != 50:
        raise ValueError("the current exact STEP bundle must contain 50 unique members")
    expected_member_ids = {row["member_id"] for row in previous["physical_members"]}
    if set(member_ids) != expected_member_ids:
        raise ValueError("STEP member identities differ from the 50-member inventory")
    kind_counts: dict[str, int] = {}
    for row in step_records:
        kind_counts[row["member_kind"]] = kind_counts.get(row["member_kind"], 0) + 1
    if kind_counts != {"timber": 20, "plywood_panel": 6, "candidate_block": 24}:
        raise ValueError(f"unexpected member kind counts: {kind_counts}")

    timber_path = TIMBER_MAP / "current-frame-timber-material-frame-map.json"
    timber_map = _read_json(timber_path)
    timber_ids = {row["member_id"] for row in timber_map["members"]}
    if len(timber_ids) != 20 or timber_ids != {
        row["member_id"] for row in step_records if row["member_kind"] == "timber"
    }:
        raise ValueError("frame timber orientation map does not cover 20 current timbers")

    block_path = BLOCK_MAP / "material-frame-map.json"
    block_map = _read_json(block_path)
    block_ids = {row["part_id"] for row in block_map["members"]}
    if len(block_ids) != 24 or block_ids != {
        row["member_id"] for row in step_records if row["member_kind"] == "candidate_block"
    }:
        raise ValueError("block orientation map does not cover 24 current blocks")

    dead_path = DEAD_LOAD / "dead-load-scenarios.json"
    dead = _read_json(dead_path)
    topology = _read_json(MASS_TOPOLOGY)
    if (
        dead["candidate"] != CANDIDATE
        or dead["revision_id"] != REVISION
        or dead["readiness"]["inputs_ready"] is not False
        or dead["readiness"]["native_solve_run"] is not False
        or dead["modeled_body_gravity"]["row_count"] != 778
        or topology["mass_inventory_row_count"] != 778
        or topology["mechanical_acceptance"] is not False
        or topology["native_solve_run"] is not False
    ):
        raise ValueError("dead-load/mass topology readiness or row count changed")

    loads = _read_json(LOAD_CASES)
    if (
        loads["candidate"] != CANDIDATE
        or loads["geometry_revision_id"] != REVISION
        or len(loads["cases"]) != 6
        or not any("no frame reactions or connection demands" in item
                   for item in loads["limits"])
    ):
        raise ValueError("current applied load contract changed identity or scope")

    profile = _read_json(SOLVER_PROFILE)
    if (
        profile["version"] != "2.23"
        or profile["candidate_joint_contact_validated"] is not False
        or profile["mechanical_acceptance"] is not False
    ):
        raise ValueError("2.23 profile no longer carries its development-only scope")

    previous_step_evidence = previous["existing_step_export_evidence"]
    member_by_id = {row["member_id"]: row for row in step_records}
    refreshed = previous
    refreshed["schema"] = "wood_joint_current_full_frame_input_manifest/v2"
    refreshed["manifest_id"] = OUTPUT_DIR.name
    refreshed["status"] = "source_prepared_geometry_inventory_and_load_inputs_not_ready"
    refreshed["existing_step_export_evidence"] = {
        "status": "source_replayed_50_member_finished_step_bundle",
        "path": (SOLIDS / "bundle/current-full-frame-member-solids.json").as_posix(),
        "artifact_sha256": bundle["artifact_sha256"],
        "member_bundle_sha256": bundle["member_bundle_sha256"],
        "member_count": len(step_records),
        "member_kind_counts": kind_counts,
        "all_50_step_files_hashed_and_size_checked": True,
        "all_50_source_summaries_one_solid_and_roundtrip_valid": True,
        "scope_limit": (
            "Exact finished member geometry only; the STEP bundle has no solver mesh, "
            "hardware solids, material properties, load carriers, contact law, or "
            "mechanical attachment model."
        ),
    }
    refreshed["historical_d6_step_export_evidence"] = previous_step_evidence
    for artifact in refreshed["source_artifacts"]:
        artifact["pin_scope"] = "historical_attempt02_inventory_snapshot"
        if artifact["role"] == "execution_plan":
            artifact["note"] = (
                "Historical attempt02 plan pin; it is not a pin of the current "
                "execution plan."
            )
    refreshed["source_artifacts_scope"] = (
        "The inherited source_artifacts list preserves attempt02's historical "
        "input pins. Current Step 4 source records are pinned under evidence_bindings."
    )
    refreshed["finished_member_step_bindings"] = step_records
    refreshed["evidence_bindings"] = {
        "previous_attempt02_snapshot": {
            **_pin(previous_path, digest_key="manifest_sha256"),
            "attempt02_manifest_sha256": previous_digest,
            "role": "Preserved source inventory and candidate identity baseline.",
        },
        "finished_member_geometry": {
            **_artifact_binding(
                bundle_path,
                digest_key="artifact_sha256",
                counts={"members": 50, **kind_counts},
            ),
            "member_bundle_sha256": bundle["member_bundle_sha256"],
            "step_files": step_records,
        },
        "conditional_frame_timber_orientation": {
            **_artifact_binding(
                timber_path,
                digest_key="record_sha256",
                counts={"members": 20},
            ),
            "status": "orientation_consistency_screen_only_not_received_grain",
        },
        "conditional_connector_block_orientation": {
            **_artifact_binding(
                block_path,
                digest_key="record_sha256",
                counts={"members": 24, "conditional_transverse_cases": 48},
            ),
            "status": "orientation_scenarios_only_not_received_grain",
        },
        "modeled_body_gravity_and_accessory_scenarios": {
            **_artifact_binding(
                dead_path,
                digest_key="contract_sha256",
                counts={
                    "mass_rows": dead["modeled_body_gravity"]["row_count"],
                    "modeled_mass_kg": dead["modeled_body_gravity"]["modeled_mass_kg"],
                    "accessory_allowance_kg": dead["accessory_allowance"]["budget_kg"],
                },
            ),
            "status": dead["status"],
        },
        "source_to_mass_topology": {
            **_pin(MASS_TOPOLOGY),
            "reconciled_facts": {
                "mass_inventory_rows": topology["mass_inventory_row_count"],
                "unique_source_mass_entities": topology[
                    "unique_source_mass_entity_count"
                ],
                "global_solver_mass_dof_mapping": False,
            },
        },
        "source_mass_centroids": _pin(MASS_CENTROIDS),
        "six_current_applied_load_cases": {
            **_artifact_binding(
                LOAD_CASES,
                digest_key="contract_sha256",
                counts={
                    "cases": len(loads["cases"]),
                    "case_ids": [case["case_id"] for case in loads["cases"]],
                    "applied_wrenches_only": True,
                    "reactions_or_joint_demands": False,
                },
            ),
        },
        "development_solver_profile": {
            **_pin(SOLVER_PROFILE),
            "version": profile["version"],
            "image_id": profile["image_id"],
            "binary_path": profile["binary_path"],
            "binary_sha256": profile["binary_sha256"],
            "candidate_joint_contact_validated": False,
            "mechanical_acceptance": False,
        },
    }

    step_by_id = {row["member_id"]: row for row in step_records}
    for member in refreshed["physical_members"]:
        row = step_by_id[member["member_id"]]
        member["exact_current_finished_brep_or_step_available_in_manifest_sources"] = True
        member["current_finished_step_binding"] = {
            "path": row["path"],
            "file_sha256": row["file_sha256"],
            "source_shape_fingerprint_sha256": row[
                "source_shape_fingerprint_sha256"
            ],
            "step_roundtrip_checked": True,
        }
    for block in refreshed["candidate_blocks"]:
        row = step_by_id[block["part_id"]]
        block["prior_attempt02_export_status"] = block["exact_export_status"]
        block["exact_export_status"] = "source_replayed_finished_step_roundtrip_checked"
        block["current_finished_step_binding"] = {
            "path": row["path"],
            "file_sha256": row["file_sha256"],
            "source_shape_fingerprint_sha256": row[
                "source_shape_fingerprint_sha256"
            ],
            "step_roundtrip_checked": True,
        }

    readiness = refreshed["readiness"]
    readiness["exact_full_frame_finished_geometry_ready"] = True
    readiness["frame_timber_orientation_screens_cover_20_of_20"] = True
    readiness["connector_block_orientation_screens_cover_24_of_24"] = True
    readiness["body_level_gravity_input_contract_available"] = True
    readiness["six_current_applied_case_contract_available"] = True
    readiness["development_solver_profile_pinned"] = True
    readiness["inputs_ready"] = False
    readiness["per_member_material_mapping_ready"] = False
    readiness["selected_structural_hardware_ready"] = False
    readiness["complete_mechanical_contact_attachment_model_ready"] = False
    readiness["current_full_frame_demands_available"] = False
    readiness["criterion_resolved"] = False
    readiness["native_solve_executed"] = False
    readiness["source_preparation_only"] = True
    readiness["unresolved_inputs"] = [
        (
            "The 50 finished STEP solids are source-replayed and round-trip checked, but no "
            "solver mesh, element/node map, or current-frame finite-element model is supplied."
        ),
        (
            "The 20 timber and 24 connector-block maps supply conditional orientation scenarios "
            "only; delivered species group, grade, moisture, treatment, connection-zone condition, "
            "and design properties are unobserved. Six plywood panels lack a complete layup, axis, "
            "and property map."
        ),
        (
            "No physical bolt, nut, washer, or T-nut product is selected and fit-qualified for "
            "the 92 candidate or 12 retained stacks. The catalog screen fit-qualifies 0 of 92 "
            "candidate axes; thread start/runout, matched engagement, delivery tolerances, and "
            "receiving are unresolved."
        ),
        (
            "The 66 Hillman screw axes remain geometric/mass proxies; actual product conformance, "
            "embedment, panel/frame transfer, and resistance are not established."
        ),
        (
            "The 50-member contact graph and operation registers are geometry-only. Bolt/bore "
            "transfer, wood bearing/slip/opening, axial engagement, screw attachment, panel "
            "transfer, and all 24 replacement duties lack a demonstrated mechanical model."
        ),
        (
            "The 778-row body-gravity inventory and separate 25 kg accessory allowance are "
            "source-bound scenarios; no mass-to-mesh/carrier DOF map or solver load mapping exists."
        ),
        (
            "No full-frame boundary-condition/contact model is defined. The no-slip floor support "
            "remains an unverified analytical assumption with no qualified floor or anchorage."
        ),
        (
            "The six current cases are applied force/wrench inputs only. They provide no frame "
            "reactions, connection demands, load sharing, or stability results."
        ),
        (
            "Source-bound simultaneous six-component local rail/principal-port histories and a "
            "time basis for a physical ordinary-joint transient remain absent. "
            "The analyst-selected 1 N pulse cannot be transferred to a physical history."
        ),
    ]
    refreshed["source_preparation_checks"] = {
        "candidate_and_revision_reconciled": True,
        "selected_candidate_authority_preserved": True,
        "all_current_finished_member_steps_present_and_hash_checked": True,
        "step_member_count": 50,
        "step_member_kind_counts": kind_counts,
        "conditional_wood_orientation_maps_reconciled": True,
        "body_gravity_and_accessory_contracts_pinned": True,
        "six_applied_cases_pinned": True,
        "2_23_profile_pinned_for_future_development_diagnostics": True,
        "solver_model_inputs_complete": False,
        "native_solve_executed": False,
    }
    refreshed["claim_limits"] = list(refreshed["claim_limits"])
    refreshed["claim_limits"].append(
        "Attempt03 advances exact geometry and source input preparation only; it is not a "
        "finite-element model or solver-ready load manifest."
    )
    refreshed["producer"] = {
        "path": PRODUCER,
        "sha256": _sha256(Path(__file__).resolve()),
    }
    refreshed.pop("base_manifest_producer", None)
    refreshed["attempt02_base_producer"] = previous.get("base_manifest_producer")
    refreshed.pop("manifest_sha256", None)
    refreshed["manifest_sha256"] = hashlib.sha256(
        _canonical_json(refreshed)
    ).hexdigest()
    return refreshed


def render_readme(manifest: dict[str, Any]) -> str:
    binding = manifest["evidence_bindings"]
    step_rows = manifest["finished_member_step_bindings"]
    counts = manifest["source_preparation_checks"]["step_member_kind_counts"]
    unresolved = manifest["readiness"]["unresolved_inputs"]
    unresolved_lines = "\n".join(
        textwrap.fill(
            item,
            width=98,
            initial_indent="- ",
            subsequent_indent="  ",
        )
        for item in unresolved
    )
    bound_inputs = [
        ("attempt02 snapshot", binding["previous_attempt02_snapshot"]),
        ("50-member STEP bundle", binding["finished_member_geometry"]),
        ("frame timber orientation map", binding["conditional_frame_timber_orientation"]),
        ("candidate block orientation map", binding["conditional_connector_block_orientation"]),
        ("dead-load scenario contract", binding["modeled_body_gravity_and_accessory_scenarios"]),
        ("six-case current load contract", binding["six_current_applied_load_cases"]),
        ("CalculiX development profile", binding["development_solver_profile"]),
        ("source mass-centroid table", binding["source_mass_centroids"]),
        ("source-to-mass topology", binding["source_to_mass_topology"]),
    ]
    bound_input_lines = "\n".join(
        f"- {label}\n  Digest: "
        f"`{record.get('content_digest', record['file_sha256'])}`"
        for label, record in bound_inputs
    )
    return f"""# Current full-frame input manifest — attempt03

## Decision and result

This source-only refresh preserves attempt02 and binds the later exact 50-member
STEP bundle, current conditional wood-orientation screens, body-gravity and
accessory scenarios, six applied load cases, and the explicit CalculiX 2.23
development profile. It supersedes attempt02's geometry-availability status
only. Candidate identity remains `{manifest['candidate']}`, revision
`{manifest['geometry_revision_id']}`, reviewed checkpoint
`{manifest['reviewed_repository_commit']}`; selected authority remains
`{manifest['selected_candidate_authority_preserved']}`.

Attempt03 verifies {len(step_rows)} individual one-solid STEP files: {counts['timber']}
timbers, {counts['plywood_panel']} panels, and {counts['candidate_block']} candidate
blocks. Each file's hash and byte size match the source bundle; the source
export records a valid round-trip for every member. The bundle SHA-256 is
`{binding['finished_member_geometry']['content_digest']}` and its STEP-set
SHA-256 is `{binding['finished_member_geometry']['member_bundle_sha256']}`.

The frame map covers 20 timber orientation proposals, the block map covers 24
conditional transverse cases, the gravity contract covers 778 modeled mass
rows plus a separate 25 kg accessory allowance, and the current load contract
contains six applied wrench cases. These are geometry, orientation, mass/load
inputs only. `inputs_ready=false`; no current-frame finite-element model,
mechanical transfer model, reactions, demands, or criteria results are supplied.
All acceptance and release flags remain false.

## Bound input records

The JSON carries relative paths and file hashes for all source records and 50
individual STEP files. Core artifact content digests are:

{bound_input_lines}

The inherited `source_artifacts` list preserves attempt02's source snapshot.
Its execution-plan row is historical and does not pin the current plan; the
current Step 4 input records are the `evidence_bindings` listed above.

## Remaining solver inputs

{unresolved_lines}

## Reproduction

Run from this attempt directory:

```sh
python3 produce.py --verify
```

The producer checks attempt02's frozen content digest, current candidate and
revision identity, all 50 STEP hashes/sizes and member IDs, the two orientation
map coverages, 778 mass rows, six current cases, and the pinned 2.23 profile.
It does not rebuild CAD or run a solver.

Manifest SHA-256: `{manifest['manifest_sha256']}`.
"""


def verify() -> dict[str, Any]:
    expected = build_manifest()
    saved = _read_json(OUTPUT)
    if saved != expected:
        raise ValueError("saved manifest does not match its source-pinned inputs")
    readme = (ROOT / README).read_text(encoding="utf-8")
    if readme != render_readme(saved):
        raise ValueError("README does not match the current verified manifest")
    if saved["readiness"]["inputs_ready"] is not False:
        raise ValueError("attempt03 must keep full-frame inputs not ready")
    if saved["readiness"]["native_solve_executed"] is not False:
        raise ValueError("attempt03 must not claim a native solve")
    if any(saved["release"].values()):
        raise ValueError("attempt03 must keep every release flag false")
    return {
        "status": "verified",
        "manifest_path": OUTPUT.as_posix(),
        "manifest_sha256": saved["manifest_sha256"],
        "step_member_count": len(saved["finished_member_step_bindings"]),
        "step_member_kind_counts": saved["source_preparation_checks"][
            "step_member_kind_counts"
        ],
        "mass_row_count": saved["evidence_bindings"][
            "modeled_body_gravity_and_accessory_scenarios"
        ]["reconciled_facts"]["mass_rows"],
        "applied_load_case_count": saved["evidence_bindings"][
            "six_current_applied_load_cases"
        ]["reconciled_facts"]["cases"],
        "inputs_ready": False,
        "native_solve_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    manifest_path = ROOT / OUTPUT
    readme_path = ROOT / README
    if args.verify:
        result = verify()
    else:
        if manifest_path.exists() or readme_path.exists():
            raise FileExistsError("attempt03 outputs already exist; preserve the snapshot")
        manifest = build_manifest()
        (ROOT / OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        readme_path.write_text(render_readme(manifest), encoding="utf-8")
        result = {
            "status": "written",
            "manifest_path": OUTPUT.as_posix(),
            "manifest_sha256": manifest["manifest_sha256"],
            "step_member_count": len(manifest["finished_member_step_bindings"]),
            "inputs_ready": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
