"""Focused bundle and geometry-descriptor contracts for the current patch mesher."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
from pathlib import Path

import pytest

from fea import wood_joint_current_patch_mesh as current_mesh


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _shape(volume, label, *, extra=None):
    result = {
        "solid_count": 1,
        "volume_mm3": float(volume),
        "centroid_global_xyz_mm": [float(volume) / 10, 2.0, 3.0],
        "bounds_xyz_mm": [0.0, 5.0, 0.0, 5.0, 0.0, 5.0],
        "cad_shape_sha256": _sha(label.encode()),
    }
    if extra:
        result.update(extra)
    return result


def _review_pins():
    verification_bytes = (
        current_mesh.ROOT / current_mesh.VERIFICATION_REPORT_PATH
    ).read_bytes()
    return {
        "revision_report": current_mesh.REVISION_REPORT_PATH,
        "revision_report_sha256": current_mesh.REVISION_REPORT_SHA256,
        "verification_report": current_mesh.VERIFICATION_REPORT_PATH,
        "verification_report_sha256": _sha(verification_bytes),
        "scene_snapshot": current_mesh.SCENE_SNAPSHOT_PATH,
        "scene_sha256": current_mesh.SCENE_SHA256,
        "source_files_sha256": current_mesh.VERIFIED_CURRENT_SOURCE_HASHES,
        "input_adapter_source_sha256": current_mesh.sha256_file(
            current_mesh.ROOT / current_mesh.EXPORTER_SOURCE_PATH
        ),
        "report_claim_boundary": (
            "current viewer geometry review only; no joint evaluation or acceptance"
        ),
    }


def _synthetic_inventory_and_artifacts():
    pins = _review_pins()
    wood_rows = []
    for part_id in current_mesh.WOOD_BODY_IDS:
        wood_rows.append(
            {
                "part_id": part_id,
                "geometry_role": current_mesh.WOOD_BODY_ROLES[part_id],
                "finished_geometry": _shape(100.0, part_id),
                "step_artifact_key": f"wood/{part_id}.step",
                "full_finished_member_exported": True,
                "arbitrary_patch_cut_applied": False,
            }
        )

    axes = []
    role_shapes = {}
    metal_rows = []
    for axis_index, (axis_id, receivers) in enumerate(current_mesh.AXIS_RECEIVERS.items()):
        roles = []
        for role in current_mesh.HARDWARE_ROLES:
            metadata = _shape(4.0 + len(role), f"{axis_id}/{role}")
            role_shapes[(axis_id, role)] = metadata
            roles.append(
                {
                    "role": role,
                    "cad_shape": metadata,
                    "step_artifact_key": f"hardware/{axis_id}/{role}.step",
                }
            )
        bolt_union = {
            "source_role_ids": [f"{axis_id}/head", f"{axis_id}/shaft"],
            "source_role_shape_sha256": {
                role: role_shapes[(axis_id, role)]["cad_shape_sha256"]
                for role in ("head", "shaft")
            },
            "valid": True,
            "solid_count": 1,
            "head_shaft_overlap_volume_mm3": 1.0,
            "expected_volume_by_inclusion_exclusion_mm3": 9.0,
            "observed_fused_volume_mm3": 9.0,
            "inclusion_exclusion_volume_difference_mm3": 0.0,
            "symmetric_difference_volume_mm3": 0.0,
            "allowed_volume_difference_mm3": (
                current_mesh.UNION_VOLUME_ABSOLUTE_TOLERANCE_MM3
                + current_mesh.UNION_VOLUME_RELATIVE_TOLERANCE * 9.0
            ),
            "symmetric_difference_passed": True,
        }
        bolt_shape = _shape(
            9.0,
            f"{axis_id}/physical-bolt",
            extra={"physical_bolt_union": bolt_union},
        )
        metal_rows.append(
            {
                "physical_body_id": f"physical_metal/{axis_id}/bolt",
                "physical_kind": "bolt_head_plus_shaft_union",
                "axis_id": axis_id,
                "source_cad_role_ids": [f"{axis_id}/head", f"{axis_id}/shaft"],
                "step_artifact_key": f"physical_metal/{axis_id}/bolt.step",
                "solid": bolt_shape,
                "union_identity": copy.deepcopy(bolt_union),
            }
        )
        for role in ("head_washer", "nut_washer", "nut"):
            metal_rows.append(
                {
                    "physical_body_id": f"physical_metal/{axis_id}/{role}",
                    "physical_kind": role,
                    "axis_id": axis_id,
                    "source_cad_role_ids": [f"{axis_id}/{role}"],
                    "step_artifact_key": f"hardware/{axis_id}/{role}.step",
                    "solid": role_shapes[(axis_id, role)],
                }
            )
        axes.append(
            {
                "physical_bolt_id": axis_id,
                "physical_bolt_count": 1,
                "physical_bolt_roles": ["head", "shaft"],
                "head_and_shaft_are_one_physical_bolt": True,
                "axis_origin_global_xyz_mm": [float(axis_index), 0.0, 0.0],
                "axis_direction_head_to_nut_global_xyz": [0.0, 0.0, 1.0],
                "receivers_head_to_nut": list(receivers),
                "raw_receiver_projected_intervals": [
                    {
                        "member_id": receivers[0],
                        "receiver_order_head_to_nut": 1,
                        "projected_intervals_from_underhead_datum_mm": [[2.032, 90.932]],
                        "projected_material_length_mm": 88.9,
                        "projection_gaps_mm": [],
                        "current_shaft_covers_raw_receiver": True,
                        "long_probe_minus_current_shaft_volume_mm3": 0.0,
                    },
                    {
                        "member_id": receivers[1],
                        "receiver_order_head_to_nut": 2,
                        "projected_intervals_from_underhead_datum_mm": [[90.932, 129.032]],
                        "projected_material_length_mm": 38.1,
                        "projection_gaps_mm": [],
                        "current_shaft_covers_raw_receiver": True,
                        "long_probe_minus_current_shaft_volume_mm3": 0.0,
                    },
                ],
                "physical_hardware_roles": roles,
                "cad_role_count": 5,
                "physical_metal_body_ids": [
                    f"physical_metal/{axis_id}/bolt",
                    f"physical_metal/{axis_id}/head_washer",
                    f"physical_metal/{axis_id}/nut_washer",
                    f"physical_metal/{axis_id}/nut",
                ],
            }
        )

    interface_rows = []
    for interface_id, members in current_mesh.EXPECTED_INTERFACE_MEMBERS.items():
        pair = {
            "first_member": members[0],
            "second_member": members[1],
            "common_area_mm2": 100.0,
            "common_area_centroid_global_xyz_mm": [1.0, 2.0, 3.0],
            "measured_plane_gap_mm": 0.0,
            "plane_normal_first_member_global_xyz": [0.0, 0.0, 1.0],
            "plane_normal_second_member_global_xyz": [0.0, 0.0, -1.0],
            "first_face": {
                "area_mm2": 100.0,
                "centroid_global_xyz_mm": [1.0, 2.0, 3.0],
                "normal_global_xyz": [0.0, 0.0, 1.0],
                "bounds_xyz_mm": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
                "cad_face_sha256": _sha(f"{interface_id}:first".encode()),
            },
            "second_face": {
                "area_mm2": 100.0,
                "centroid_global_xyz_mm": [1.0, 2.0, 3.0],
                "normal_global_xyz": [0.0, 0.0, -1.0],
                "bounds_xyz_mm": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
                "cad_face_sha256": _sha(f"{interface_id}:second".encode()),
            },
        }
        interface_rows.append(
            {
                "interface_id": interface_id,
                "members": list(members),
                "bolt_axis_ids": current_mesh.EXPECTED_INTERFACE_AXIS_IDS[interface_id],
                "status": "finite_opposed_coplanar_patch_extracted",
                "finite_opposed_face_pair_count": 1,
                "finite_overlap_area_mm2": 100.0,
                "finite_overlap_area_centroid_global_xyz_mm": [1.0, 2.0, 3.0],
                "actual_face_pairs": [pair],
                "contact_law_assigned": False,
                "active_pressure_patch_established": False,
            }
        )
    inventory = {
        "schema": current_mesh.BUNDLE_SCHEMA,
        "status": current_mesh.BUNDLE_STATUS,
        "geometry_binding": {
            "layout_id": current_mesh.CURRENT_REVISION_ID,
            "trial_id": current_mesh.CURRENT_REVISION_ID,
            "status": "unaccepted_viewer_geometry_revision",
            "source_inventory_sha256": current_mesh.SOURCE_INVENTORY_SHA256,
            "source_inputs_sha256": current_mesh.VERIFIED_CURRENT_SOURCE_HASHES,
        },
        "candidate": {
            "revision_id": current_mesh.CURRENT_REVISION_ID,
            "implementation_revision": current_mesh.CURRENT_IMPLEMENTATION_REVISION,
            "source_inventory_baseline_commit": current_mesh.SOURCE_BASELINE_COMMIT,
            "source_inventory_sha256": current_mesh.SOURCE_INVENTORY_SHA256,
            "current_review_pins": pins,
        },
        "scope": {
            "finished_wood_bodies": 3,
            "physical_bolts": 4,
            "modeled_hardware_cad_roles": 20,
            "wood_interfaces": 3,
            "step_artifacts": 27,
            "derived_physical_bolt_unions": 4,
            "physical_metal_bodies": 16,
            "full_finished_members_exported": True,
            "arbitrary_member_cuts": False,
            "meshed": False,
            "native_solve_run": False,
            "contact_law_assigned": False,
            "boundary_method": "pending",
            "strength_or_joint_acceptance_claim": False,
        },
        "migration_blockers": [],
        "wood_bodies": wood_rows,
        "physical_bolts": axes,
        "physical_metal_bodies": metal_rows,
        "wood_interfaces": interface_rows,
        "step_artifacts": {},
    }

    artifact_shapes = {
        f"wood/{row['part_id']}": row["finished_geometry"] for row in wood_rows
    }
    for axis in axes:
        for role in axis["physical_hardware_roles"]:
            artifact_shapes[role["step_artifact_key"][:-5]] = role["cad_shape"]
    for row in metal_rows:
        artifact_shapes[row["step_artifact_key"][:-5]] = row["solid"]
    assert len(artifact_shapes) == 27
    return inventory, artifact_shapes


def _write_synthetic_bundle(path: Path):
    path.mkdir()
    inventory, artifact_shapes = _synthetic_inventory_and_artifacts()
    hashes = {}
    for artifact_key, source_shape in artifact_shapes.items():
        relative = f"{artifact_key}.step"
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = f"synthetic STEP bytes: {relative}\n".encode()
        target.write_bytes(payload)
        digest = _sha(payload)
        hashes[relative] = digest
        readback = {
            key: value
            for key, value in source_shape.items()
            if key != "physical_bolt_union"
        }
        readback["cad_shape_sha256"] = _sha(f"readback:{relative}".encode())
        inventory["step_artifacts"][artifact_key] = {
            "file": Path(relative).name,
            "file_sha256": digest,
            "source_solid": source_shape,
            "step_readback_solid": readback,
            "identity_checks": {
                "solid_count": True,
                "volume": True,
                "centroid": True,
                "bounds": True,
                "symmetric_difference": {
                    "source_only_volume_mm3": 0.0,
                    "step_only_volume_mm3": 0.0,
                    "symmetric_difference_volume_mm3": 0.0,
                    "allowed_volume_difference_mm3": 0.001,
                    "passed": True,
                },
            },
        }
    inventory_bytes = _json_bytes(inventory)
    (path / "inventory.json").write_bytes(inventory_bytes)
    hashes["inventory.json"] = _sha(inventory_bytes)
    index_bytes = _json_bytes(hashes)
    (path / "sha256.json").write_bytes(index_bytes)
    return {
        "path": path,
        "inventory_sha256": _sha(inventory_bytes),
        "hash_index_sha256": _sha(index_bytes),
    }


@pytest.fixture
def bundle(tmp_path):
    return _write_synthetic_bundle(tmp_path / "bundle")


def _rewrite_bundle(bundle_path, inventory):
    bundle_path = Path(bundle_path)
    inventory_bytes = _json_bytes(inventory)
    (bundle_path / "inventory.json").write_bytes(inventory_bytes)
    hashes = json.loads((bundle_path / "sha256.json").read_text())
    hashes["inventory.json"] = _sha(inventory_bytes)
    index_bytes = _json_bytes(hashes)
    (bundle_path / "sha256.json").write_bytes(index_bytes)
    return _sha(inventory_bytes), _sha(index_bytes)


def test_current_patch_loader_binds_exact_three_wood_sixteen_metal_and_27_artifacts(bundle):
    loaded = current_mesh.load_current_patch_bundle(
        bundle["path"],
        expected_inventory_sha256=bundle["inventory_sha256"],
        expected_hash_index_sha256=bundle["hash_index_sha256"],
    )

    assert tuple(row["part_id"] for row in loaded["inventory"]["wood_bodies"]) == (
        current_mesh.WOOD_BODY_IDS
    )
    assert len(loaded["inventory"]["physical_bolts"]) == 4
    assert len(loaded["inventory"]["physical_metal_bodies"]) == 16
    assert len(loaded["step_artifacts"]) == 27
    assert len(loaded["input_file_sha256"]) == 29
    assert tuple(
        row["interface_id"] for row in loaded["inventory"]["wood_interfaces"]
    ) == current_mesh.EXPECTED_INTERFACE_IDS


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda inventory: inventory.__setitem__(
                "schema", "wood_joint_wj24_patch_reconciliation/v1"
            ),
            "schema or geometry-only status",
        ),
        (
            lambda inventory: inventory["physical_metal_bodies"][0][
                "union_identity"
            ]["source_role_ids"].reverse(),
            "bolt union identity is not the solid",
        ),
        (
            lambda inventory: inventory["physical_bolts"][0][
                "raw_receiver_projected_intervals"
            ].reverse(),
            "projected receiver evidence changed",
        ),
        (
            lambda inventory: inventory["wood_interfaces"].pop(),
            "exact three wood interface records",
        ),
    ],
)
def test_loader_fails_closed_on_historical_or_mutated_physical_contract(
    bundle, tmp_path, mutate, message
):
    target = tmp_path / "mutated"
    shutil.copytree(bundle["path"], target)
    inventory = json.loads((target / "inventory.json").read_text())
    mutate(inventory)
    expected_inventory, expected_index = _rewrite_bundle(target, inventory)

    with pytest.raises((TypeError, ValueError), match=message):
        current_mesh.load_current_patch_bundle(
            target,
            expected_inventory_sha256=expected_inventory,
            expected_hash_index_sha256=expected_index,
        )


def test_mesh_configuration_requires_explicit_valid_independent_sizes():
    assert current_mesh.validate_mesh_configuration(40, 3, 12) == {
        "global_max_size_mm": 40.0,
        "axis_local_min_size_mm": 3.0,
        "axis_refinement_band_mm": 12.0,
    }
    assert current_mesh.validate_mesh_configuration(4, 1.5, 3) == {
        "global_max_size_mm": 4.0,
        "axis_local_min_size_mm": 1.5,
        "axis_refinement_band_mm": 3.0,
    }
    with pytest.raises((TypeError, ValueError)):
        current_mesh.validate_mesh_configuration(3, 4, 2)


def test_cylinder_probe_fit_recovers_axis_and_radius_without_claiming_face_orientation():
    probes = []
    for station in (0.0, 5.0, 10.0):
        for angle in (0.0, math.pi / 2, math.pi):
            normal = (math.cos(angle), math.sin(angle), 0.0)
            probes.append(
                {
                    "xyz_mm": [
                        20.0 + 3.0 * normal[0],
                        -5.0 + 3.0 * normal[1],
                        station,
                    ],
                    "parametric_normal_global": normal,
                }
            )

    fit = current_mesh._fit_cylinder_from_probes(probes)

    assert fit["status"] == "least-squares analytic-cylinder fit from CAD parametric probes"
    assert fit["radius_mm"] == pytest.approx(3.0)
    assert fit["axis_point_global_xyz_mm"] == pytest.approx([20.0, -5.0, 5.0])
    assert abs(fit["axis_direction_global_xyz_unoriented"][2]) == pytest.approx(1.0)
    assert fit["probe_fit_max_residual_mm"] < 1e-10
    assert "orientation are not physical" in fit["basis"]
