from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_patch_geometry as patch_export
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts.wood_joint_wj16_compositor import LAYOUT_ID, TRIAL_ID


def _manifest_and_geometry():
    source_inventory = json.loads(
        Path("docs/wood-joints-mvp/source-inventory.json").read_text()
    )
    source_ids = (g7_probe.LOWER_RAIL, g7_probe.UPPER_RAIL, g7_probe.PRINCIPAL)
    role_names = ("shaft", "head", "head_washer", "nut_washer", "nut")

    def box(index: int):
        return cq.Solid.makeBox(
            10.0 + index,
            8.0,
            6.0,
            cq.Vector(index * 25.0, (index % 3) * 17.0, (index % 2) * 11.0),
        )

    finished_hosts = {part_id: box(index) for index, part_id in enumerate(source_ids)}
    finished_candidates = {
        g7_probe.LOWER_CLEAT: box(3),
        g7_probe.UPPER_CLEAT: box(4),
    }
    bores = {}
    installed = {}
    physical_bolts = []
    interface_groups = {}
    for index, spec in enumerate(g7_probe.STACK_SPECS):
        axis_id = patch_export._axis_id(spec.stack_id)
        receiver_ids = tuple(member_id for member_id, _ in spec.layers)
        bores[axis_id] = SimpleNamespace(
            axis_id=axis_id,
            family=patch_export.mechanics.FAMILY,
            trial_id=g7_probe.TRIAL_ID,
            station_id=None,
            receiver_ids=receiver_ids,
            shape=box(5 + index),
        )
        installed[axis_id] = {
            role: box(13 + 5 * index + role_index)
            for role_index, role in enumerate(role_names)
        }
        physical_bolts.append(
            {
                "physical_bolt_id": axis_id,
                "stack_spec_id": spec.stack_id,
                "station_id": spec.station_id,
                "interface_id": spec.interface_id,
                "world_axis_origin_xyz_mm": [float(index), 0.0, 0.0],
                "world_axis_origin_datum": "synthetic wood-side datum",
                "world_axis_direction_head_to_nut": [1.0, 0.0, 0.0],
                "receivers_head_to_nut": [
                    {"member_id": part_id, "wood_thickness_mm": float(thickness)}
                    for part_id, thickness in spec.layers
                ],
                "wood_grip_mm": sum(
                    float(thickness) for _part, thickness in spec.layers
                ),
                "single_wood_shear_plane_global_xyz_mm": [float(index), 0.0, 0.0],
                "hardware": {
                    "selection_status": "synthetic test candidate only",
                },
            }
        )
        interface_id = f"{spec.station_id}__{spec.interface_id}"
        interface_groups.setdefault(interface_id, []).append(spec)

    physical_interfaces = []
    for interface_id, specs in interface_groups.items():
        first = specs[0]
        physical_interfaces.append(
            {
                "interface_id": interface_id,
                "family_stack_ids": [spec.stack_id for spec in specs],
                "members_head_to_nut": [member_id for member_id, _ in first.layers],
                "source_host_face": {"part_id": first.layers[-1][0]},
                "candidate_cleat_face": {"part_id": first.layers[0][0]},
                "shear_plane_datum": {"origin_global_xyz_mm": [0.0, 0.0, 0.0]},
            }
        )

    manifest = {
        "schema": patch_export.mechanics.SCHEMA,
        "status": "bounded_mechanics_inputs_only",
        "composition": {
            "trial_id": TRIAL_ID,
            "source_inventory_sha256": WJ04_TRIAL.source_inventory_sha256,
            "right_rail_family_trial_id": g7_probe.TRIAL_ID,
            "right_rail_source_fingerprints_sha256": {},
        },
        "physical_inventory": {
            "ordinary_physical_bolts": 8,
            "modeled_component_shapes_for_these_bolts": 40,
            "physical_interfaces": 4,
            "scope_does_not_cover": "synthetic test fixture",
        },
        "physical_bolts": physical_bolts,
        "physical_interfaces": physical_interfaces,
    }
    source_reconstruction = {
        part_id: {"matches_source_finished_member": True} for part_id in source_ids
    }
    geometry = SimpleNamespace(
        layout_id=LAYOUT_ID,
        trial_id=TRIAL_ID,
        status="unaccepted_integrated_hypothesis",
        source_inventory_sha256=WJ04_TRIAL.source_inventory_sha256,
        source_inventory=source_inventory,
        family_trial_ids={patch_export.mechanics.FAMILY: g7_probe.TRIAL_ID},
        finished_hosts=finished_hosts,
        finished_candidate_parts=finished_candidates,
        candidate_bores=bores,
        candidate_installed_hardware=installed,
        source_reconstruction=source_reconstruction,
        source_cutters_by_host={part_id: {} for part_id in source_ids},
        applied_source_cutters_by_host={part_id: {} for part_id in source_ids},
        purchased_panel_cutters_by_host={part_id: {} for part_id in source_ids},
        purchased_panel_cutters_by_candidate_part={
            g7_probe.LOWER_CLEAT: {},
            g7_probe.UPPER_CLEAT: {},
        },
    )
    return manifest, geometry


def _patch_frozen_calls(monkeypatch, manifest, composition_report):
    frozen = patch_export.FrozenInputs(
        mechanics_manifest=manifest,
        mechanics_manifest_sha256=hashlib.sha256(b"manifest").hexdigest(),
        composition_report=composition_report,
        composition_sha256=hashlib.sha256(b"composition").hexdigest(),
        execution={},
    )
    monkeypatch.setattr(patch_export, "_load_frozen_inputs", lambda: frozen)
    monkeypatch.setattr(
        patch_export.mechanics,
        "build_mechanics_contract",
        lambda _geometry: manifest,
    )
    monkeypatch.setattr(
        patch_export.wj16_compositor,
        "composition_report",
        lambda _geometry: composition_report,
    )


def test_exports_five_finished_bodies_and_retains_eight_physical_bolts(
    tmp_path, monkeypatch
):
    manifest, geometry = _manifest_and_geometry()
    composition_report = {"trial_id": TRIAL_ID, "source": "synthetic test"}
    _patch_frozen_calls(monkeypatch, manifest, composition_report)

    result = patch_export.export_wj04_patch(geometry, tmp_path / "patch")
    directory = Path(result["output_dir"])
    inventory = json.loads((directory / "inventory.json").read_text())

    assert {row["part_id"] for row in inventory["wood_bodies"]} == set(
        patch_export.WOOD_BODY_IDS
    )
    assert len(inventory["physical_bolts"]) == 8
    assert {row["role_count"] for row in inventory["physical_bolts"]} == {5}
    assert all(not row["role_shapes_are_fused"] for row in inventory["physical_bolts"])
    assert len(inventory["wood_interfaces"]) == 4
    assert all(
        row["finite_paired_overlap_surface"]["status"] == "unresolved_not_extracted"
        for row in inventory["wood_interfaces"]
    )
    assert len(inventory["step_artifacts"]) == 5
    for part_id, artifact in inventory["step_artifacts"].items():
        step_path = directory / "wood" / f"{part_id}.step"
        assert step_path.is_file()
        assert (
            hashlib.sha256(step_path.read_bytes()).hexdigest()
            == artifact["file_sha256"]
        )
        checks = artifact["identity_checks"]
        assert all(
            checks[key] for key in ("solid_count", "volume", "centroid", "bounds")
        )
        assert not checks["face_ordinal_used"]
        assert checks["symmetric_difference"]["passed"]
    hash_rows = json.loads((directory / "sha256.json").read_text())
    assert hash_rows["inventory.json"] == result["inventory_sha256"]
    assert len(hash_rows) == 6


def test_manifest_receiver_order_mismatch_fails_closed(tmp_path, monkeypatch):
    manifest, geometry = _manifest_and_geometry()
    row = manifest["physical_bolts"][0]
    row["receivers_head_to_nut"] = list(reversed(row["receivers_head_to_nut"]))
    composition_report = {"trial_id": TRIAL_ID}
    _patch_frozen_calls(monkeypatch, manifest, composition_report)

    with pytest.raises(ValueError, match="ordered receiver pair changed"):
        patch_export.export_wj04_patch(geometry, tmp_path / "patch")
    assert not (tmp_path / "patch").exists()


def test_live_mechanics_manifest_must_match_frozen_manifest(tmp_path, monkeypatch):
    manifest, geometry = _manifest_and_geometry()
    composition_report = {"trial_id": TRIAL_ID}
    _patch_frozen_calls(monkeypatch, manifest, composition_report)
    changed = dict(manifest)
    changed["status"] = "changed after archive"
    monkeypatch.setattr(
        patch_export.mechanics,
        "build_mechanics_contract",
        lambda _geometry: changed,
    )

    with pytest.raises(ValueError, match="differs from the frozen mechanics manifest"):
        patch_export.export_wj04_patch(geometry, tmp_path / "patch")
    assert not (tmp_path / "patch").exists()


def test_wrong_source_inventory_hash_fails_closed(tmp_path, monkeypatch):
    manifest, geometry = _manifest_and_geometry()
    composition_report = {"trial_id": TRIAL_ID}
    _patch_frozen_calls(monkeypatch, manifest, composition_report)
    geometry.source_inventory_sha256 = "0" * 64

    with pytest.raises(ValueError, match="inventory hash differs"):
        patch_export.export_wj04_patch(geometry, tmp_path / "patch")
    assert not (tmp_path / "patch").exists()


def test_missing_hardware_role_fails_closed(tmp_path, monkeypatch):
    manifest, geometry = _manifest_and_geometry()
    first_axis = manifest["physical_bolts"][0]["physical_bolt_id"]
    del geometry.candidate_installed_hardware[first_axis]["nut_washer"]
    composition_report = {"trial_id": TRIAL_ID}
    _patch_frozen_calls(monkeypatch, manifest, composition_report)

    with pytest.raises(ValueError, match="exactly five distinct CAD component roles"):
        patch_export.export_wj04_patch(geometry, tmp_path / "patch")
    assert not (tmp_path / "patch").exists()


def test_export_refuses_existing_destination(tmp_path, monkeypatch):
    manifest, geometry = _manifest_and_geometry()
    composition_report = {"trial_id": TRIAL_ID}
    _patch_frozen_calls(monkeypatch, manifest, composition_report)
    target = tmp_path / "patch"
    target.mkdir()
    (target / "review.txt").write_text("keep")

    with pytest.raises(FileExistsError, match="already exists"):
        patch_export.export_wj04_patch(geometry, target)
    assert (target / "review.txt").read_text() == "keep"


def test_pinned_archive_file_rejects_hash_mismatch(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("{}")

    with pytest.raises(ValueError, match="pinned file hash changed"):
        patch_export._read_pinned_file(path, "0" * 64, "test manifest")


def test_symmetric_difference_catches_compensating_cut_changes():
    stock = cq.Solid.makeBox(20.0, 10.0, 10.0)
    source = stock.cut(cq.Solid.makeBox(2.0, 2.0, 10.0, cq.Vector(4.0, 4.0, 0.0))).cut(
        cq.Solid.makeBox(2.0, 2.0, 10.0, cq.Vector(14.0, 4.0, 0.0))
    )
    shifted_cuts = stock.cut(
        cq.Solid.makeBox(2.0, 2.0, 10.0, cq.Vector(6.0, 4.0, 0.0))
    ).cut(cq.Solid.makeBox(2.0, 2.0, 10.0, cq.Vector(12.0, 4.0, 0.0)))
    source_signature = patch_export._shape_metadata(source, "source test body")
    shifted_signature = patch_export._shape_metadata(shifted_cuts, "shifted test body")

    patch_export._assert_step_identity(
        source_signature, shifted_signature, "synthetic body"
    )
    with pytest.raises(ValueError, match="symmetric difference"):
        patch_export._symmetric_difference_evidence(
            source, shifted_cuts, "synthetic body"
        )
