"""Focused source-binding tests for current-patch elastic material fragments."""

from __future__ import annotations

import hashlib
import json
import math
import re
import tarfile
from pathlib import Path, PurePosixPath

import pytest

from fea.wood_joint_current_patch_materials import (
    build_current_patch_materials,
)

ROOT = Path(__file__).resolve().parents[1]
RESUME = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
INVENTORY = RESUME / "ordinary-patch-inputs-attempt01/inventory.json"
MESH_REPORT = RESUME / "ordinary-patch-mesh-attempt02/mesh/mesh.json"
MESH_INPUT = RESUME / "ordinary-patch-mesh-attempt02/mesh/mesh.inp"
MESH_BUNDLE = RESUME / "ordinary-patch-mesh-attempt02/bundle-contents.json"
MESH_ARCHIVE = RESUME / "ordinary-patch-mesh-attempt02/complete-mesh-evidence.tar.gz"
REQUIRED_MESH_MEMBERS = {"mesh/mesh.json", "mesh/mesh.inp"}


def _archive_mesh_report_path(tmp_path_factory):
    bundle = json.loads(MESH_BUNDLE.read_text(encoding="utf-8"))
    assert bundle["archive"] == MESH_ARCHIVE.name
    archive_bytes = MESH_ARCHIVE.read_bytes()
    assert hashlib.sha256(archive_bytes).hexdigest() == bundle["archive_sha256"]

    expected_files = {row["path"]: row for row in bundle["files"]}
    assert len(expected_files) == len(bundle["files"])
    assert REQUIRED_MESH_MEMBERS <= set(expected_files)

    extracted = {}
    with tarfile.open(MESH_ARCHIVE, mode="r:gz") as archive:
        members = archive.getmembers()
        assert len(members) == len(expected_files)
        assert {member.name for member in members} == set(expected_files)
        for member in members:
            path = PurePosixPath(member.name)
            assert not path.is_absolute() and ".." not in path.parts
            assert member.isfile()
            expected = expected_files[member.name]
            assert member.size == expected["bytes"]
            source = archive.extractfile(member)
            assert source is not None
            payload = source.read()
            assert len(payload) == expected["bytes"]
            assert hashlib.sha256(payload).hexdigest() == expected["sha256"]
            if member.name in REQUIRED_MESH_MEMBERS:
                extracted[member.name] = payload

    assert set(extracted) == REQUIRED_MESH_MEMBERS
    destination = tmp_path_factory.mktemp("current-patch-mesh-archive")
    mesh_dir = destination / "mesh"
    mesh_dir.mkdir()
    for relative_path in sorted(REQUIRED_MESH_MEMBERS):
        (destination / relative_path).write_bytes(extracted[relative_path])
    return mesh_dir / "mesh.json"


def _mesh_report_path(tmp_path_factory, *, force_archive=False):
    if not force_archive and MESH_REPORT.is_file() and MESH_INPUT.is_file():
        return MESH_REPORT
    return _archive_mesh_report_path(tmp_path_factory)


@pytest.fixture(scope="module")
def mesh_report_path(tmp_path_factory):
    return _mesh_report_path(tmp_path_factory)


@pytest.fixture(scope="module")
def material_map(mesh_report_path):
    return build_current_patch_materials(INVENTORY, mesh_report_path)


def _dot(left, right):
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _section_elsets(fragment):
    return re.findall(r"(?im)^\*SOLID SECTION,ELSET=([A-Z0-9_]+),", fragment)


def test_current_patch_material_binding_maps_actual_nineteen_mesh_body_elsets(
    material_map,
):
    assert material_map["schema"] == "wood_joint_current_patch_material_binding/v1"
    assert material_map["status"] == "proposal_only_current_patch_material_map"
    assert (
        material_map["candidate"]["revision_id"]
        == "led-clearance-2x6-runner-seated-blocks-v1"
    )
    assert material_map["candidate"]["mesh_accepted"] is False
    assert material_map["scope"]["native_solve_run"] is False
    assert material_map["scope"]["material_mapping_only"] is True
    assert material_map["scope"]["delivered_wood_properties_verified"] is False
    assert material_map["scope"]["delivered_metal_properties_verified"] is False
    assert material_map["scope"]["strength_or_capacity_claim"] is False

    elset_map = material_map["elset_body_map"]
    assert len(elset_map) == 19
    assert len({row["mesh_body_id"] for row in elset_map}) == 19
    assert len({row["elset_name"] for row in elset_map}) == 19
    assert sum(row["owner_kind"] == "wood_member" for row in elset_map) == 3
    assert sum(row["owner_kind"] == "physical_metal" for row in elset_map) == 16
    assert all(row["elset_name"] == row["mesh_body_id"] for row in elset_map)

    bindings = material_map["input_bindings"]
    for binding in ("inventory", "mesh_report", "mesh_input"):
        path = ROOT / bindings[binding]["path"]
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest() == bindings[binding]["sha256"]
        )
    source_inventory = bindings["source_inventory"]
    assert (
        source_inventory["sha256"]
        == source_inventory["pinned_by_input_candidate_sha256"]
    )
    assert (
        source_inventory["sha256"]
        == source_inventory["pinned_by_geometry_binding_sha256"]
    )

    actual_wood = {
        row["part_id"]: row
        for row in material_map["wood_orientation_alternatives"][0]["body_orientations"]
    }
    assert set(actual_wood) == {
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
        "base_principal_center_right",
    }
    assert {
        part_id: row["grain_axis_local_name"] for part_id, row in actual_wood.items()
    } == {
        "bottom_center_right_cleat": "N",
        "base_rail_bottom_right": "X",
        "base_principal_center_right": "T",
    }
    assert actual_wood["bottom_center_right_cleat"]["source_frame_owner"] == (
        "base_rail_bottom_right"
    )
    assert all(row["delivered_stock_observed"] is False for row in actual_wood.values())

    alternatives = material_map["wood_orientation_alternatives"]
    assert [row["case_id"] for row in alternatives] == [
        "source_transverse_a",
        "source_transverse_b",
    ]
    expected_radial = {
        "source_transverse_a": {
            "bottom_center_right_cleat": "X",
            "base_rail_bottom_right": "T",
            "base_principal_center_right": "X",
        },
        "source_transverse_b": {
            "bottom_center_right_cleat": "T",
            "base_rail_bottom_right": "N",
            "base_principal_center_right": "N",
        },
    }
    for alternative in alternatives:
        for body in alternative["body_orientations"]:
            axes = body["orientation"]["material_axes_global_xyz"]
            longitudinal, radial, tangential = axes["L"], axes["R"], axes["T"]
            assert body["orientation"]["right_handed"] is True
            assert (
                body["orientation"]["radial_axis_local_name"]
                == expected_radial[alternative["case_id"]][body["part_id"]]
            )
            assert _dot(longitudinal, radial) == pytest.approx(0.0, abs=1e-8)
            assert _dot(longitudinal, tangential) == pytest.approx(0.0, abs=1e-8)
            assert _dot(radial, tangential) == pytest.approx(0.0, abs=1e-8)
            assert _cross(longitudinal, radial) == pytest.approx(tangential, abs=1e-8)

    wood_scenario = material_map["material_scenarios"]["wood"]
    assert wood_scenario["status"] == "proposal_only_unmeasured_unaccepted"
    assert wood_scenario["stock_properties_measured"] is False
    assert wood_scenario["grade_specific_measured_properties_claim"] is False
    steel_scenario = material_map["material_scenarios"]["steel"]
    assert steel_scenario["youngs_modulus_mpa"] == 200000.0
    assert steel_scenario["poisson_ratio"] == 0.30
    assert steel_scenario["delivered_material_properties_verified"] is False
    assert len(material_map["metal_assignment"]["candidate_metal_bodies"]) == 16
    assert all(
        row["material_name"] == "STEEL_ELASTIC_DIAGNOSTIC"
        for row in material_map["metal_assignment"]["candidate_metal_bodies"]
    )
    assert len(material_map["metal_assignment"]["nut_elsets"]) == 4
    assert (
        "without internal"
        in material_map["metal_assignment"]["nut_representation_limit"]
    )
    nut_rows = [
        row
        for row in material_map["metal_assignment"]["candidate_metal_bodies"]
        if row["component_role"] == "nut"
    ]
    assert len(nut_rows) == 4
    assert all(
        row["generic_assignment_is_physical_nut_compliance"] is False
        and row["physical_nut_response_ready"] is False
        and "without internal" in row["representation_limit"]
        for row in nut_rows
    )

    for variant in material_map["inp_fragments"].values():
        fragment = variant["inp_fragment"]
        assert (
            hashlib.sha256(fragment.encode("utf-8")).hexdigest()
            == variant["fragment_sha256"]
        )
        assert fragment.count("*MATERIAL,") == 2
        assert fragment.count("*ORIENTATION,") == 3
        assert "*CONTACT" not in fragment.upper()
        assert "*BOUNDARY" not in fragment.upper()
        assert "*CLOAD" not in fragment.upper()
        assert "*RIGID BODY" not in fragment.upper()
        assert "*STEP" not in fragment.upper()
        assert "not physical nut compliance" in fragment

    record = dict(material_map)
    record_sha = record.pop("record_sha256")
    canonical = json.dumps(
        record, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == record_sha


def test_fragments_make_elastic_and_rigid_nut_branches_mutually_exclusive(material_map):
    body_elsets = {row["elset_name"] for row in material_map["elset_body_map"]}
    nut_elsets = set(material_map["metal_assignment"]["nut_elsets"])
    assert len(body_elsets) == 19
    assert len(nut_elsets) == 4

    for case_id in ("source_transverse_a", "source_transverse_b"):
        all_elastic = material_map["inp_fragments"][
            f"{case_id}__elastic_reference_all_16_metal_bodies"
        ]
        rigid_reserved = material_map["inp_fragments"][
            f"{case_id}__nuts_reserved_for_downstream_rigid_body"
        ]
        assert all_elastic["unassigned_nut_elsets"] == []
        assert all_elastic["rigid_body_cards_emitted"] is False
        assert set(_section_elsets(all_elastic["inp_fragment"])) == body_elsets
        assert (
            "solid cylindrical viewer envelopes without internal bores"
            in all_elastic["inp_fragment"]
        )

        assert rigid_reserved["nut_rigid_body_candidate_elsets"] == sorted(nut_elsets)
        assert rigid_reserved["unassigned_nut_elsets"] == sorted(nut_elsets)
        assert rigid_reserved["rigid_body_cards_emitted"] is False
        rigid_sections = set(_section_elsets(rigid_reserved["inp_fragment"]))
        assert rigid_sections == body_elsets - nut_elsets
        assert not (rigid_sections & nut_elsets)
        assert len(rigid_sections) == 15
        assert "without internal" in rigid_reserved["inp_fragment"]


def test_material_binding_works_from_verified_archive_members(tmp_path_factory):
    mesh_report_path = _mesh_report_path(tmp_path_factory, force_archive=True)
    assert mesh_report_path.is_absolute()
    assert mesh_report_path != MESH_REPORT
    assert mesh_report_path.with_name("mesh.inp").is_file()

    material_map = build_current_patch_materials(INVENTORY, mesh_report_path)
    assert len(material_map["elset_body_map"]) == 19
    assert material_map["input_bindings"]["mesh_report"]["path"] == str(
        mesh_report_path
    )


def test_current_material_builder_rejects_inventory_not_hash_bound_to_mesh(
    tmp_path, mesh_report_path
):
    altered = json.loads(INVENTORY.read_text(encoding="utf-8"))
    altered["status"] = "changed_after_mesh"
    altered_path = tmp_path / "altered-inventory.json"
    altered_path.write_text(json.dumps(altered), encoding="utf-8")

    with pytest.raises(ValueError, match="schema/status|inventory hash"):
        build_current_patch_materials(altered_path, mesh_report_path)
