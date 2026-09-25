"""Pure contract tests for the WJ04 five-body mesh preparation adapter."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fea import wood_joint_patch_mesh as patch_mesh
from fea.stitch_joint_mesh import (
    append_body,
    external_faces,
    surface_faces,
    validate_ownership,
)

BUNDLE = (
    patch_mesh.ROOT
    / "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
)


def _actual_inventory() -> dict:
    return json.loads((BUNDLE / "inventory.json").read_text())


def _one_c3d10():
    nodes = {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (0.0, 1.0, 0.0),
        4: (0.0, 0.0, 1.0),
        5: (0.5, 0.0, 0.0),
        6: (0.5, 0.5, 0.0),
        7: (0.0, 0.5, 0.0),
        8: (0.0, 0.0, 0.5),
        9: (0.5, 0.0, 0.5),
        10: (0.0, 0.5, 0.5),
    }
    elements = {1: tuple(nodes)}
    return nodes, elements


def test_frozen_bundle_contract_and_all_step_hashes_pass():
    bundle = patch_mesh.load_geometry_bundle(BUNDLE)

    assert bundle["inventory_sha256"] == patch_mesh.FROZEN_PATCH_INVENTORY_SHA256
    assert set(bundle["step_sha256"]) == set(patch_mesh.WOOD_BODY_IDS)
    assert len(bundle["input_file_sha256"]) == 7
    assert tuple(row["part_id"] for row in bundle["inventory"]["wood_bodies"]) == (
        patch_mesh.LOWER_RAIL,
        patch_mesh.UPPER_RAIL,
        patch_mesh.PRINCIPAL,
        patch_mesh.LOWER_CLEAT,
        patch_mesh.UPPER_CLEAT,
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda inventory: inventory["physical_bolts"][0]["receivers_head_to_nut"].reverse(),
            "ordered receiver pair changed",
        ),
        (
            lambda inventory: inventory["physical_bolts"][0].__setitem__(
                "physical_hardware_roles", None
            ),
            "physical hardware role list is missing",
        ),
        (
            lambda inventory: inventory["wood_bodies"][0].__setitem__(
                "bound_interface_ids", []
            ),
            "interface binding metadata changed",
        ),
    ],
)
def test_inventory_rejects_identity_and_role_contract_changes(mutate, message):
    inventory = copy.deepcopy(_actual_inventory())
    mutate(inventory)

    with pytest.raises((TypeError, ValueError), match=message):
        patch_mesh._validate_inventory_contract(inventory)


def test_bundle_rejects_changed_step_bytes(tmp_path):
    copied = tmp_path / "bundle"
    shutil.copytree(BUNDLE, copied)
    step = copied / "wood" / f"{patch_mesh.LOWER_RAIL}.step"
    step.write_bytes(step.read_bytes() + b"tamper")

    with pytest.raises(ValueError, match="frozen STEP file is missing or changed"):
        patch_mesh.load_geometry_bundle(copied)


@pytest.mark.parametrize(
    ("size", "local", "band"),
    [
        (0, 0.5, 10),
        (10, 11, 10),
        (10, 1, float("inf")),
        (True, 1, 10),
    ],
)
def test_mesh_configuration_requires_explicit_finite_positive_sizes(size, local, band):
    with pytest.raises((TypeError, ValueError)):
        patch_mesh.validate_mesh_configuration(size, local, band)


def test_gmsh_bounds_are_normalized_to_explicit_xyz_axis_pair_order():
    normalized = patch_mesh.normalize_gmsh_bounds_xyz(
        [1, 3, 5, 2, 4, 9], "synthetic unequal-axis bounds"
    )

    assert normalized == (1, 2, 3, 4, 5, 9)


def test_c3d10_mapping_uses_calculix_quadratic_node_order():
    elements = patch_mesh.c3d10_elements([7], list(range(1, 11)))

    assert elements == {7: (1, 2, 3, 4, 5, 6, 7, 8, 10, 9)}


def test_c3d10_mapping_uses_ten_node_stride_for_disjoint_elements():
    elements = patch_mesh.c3d10_elements([31, 47], list(range(1, 21)))

    assert elements[31] == (1, 2, 3, 4, 5, 6, 7, 8, 10, 9)
    assert elements[47] == (11, 12, 13, 14, 15, 16, 17, 18, 20, 19)


def test_c3d10_shared_curved_face_uses_second_elements_own_connectivity_block():
    first = list(range(1, 11))
    second = [1, 3, 2, 11, 7, 6, 5, 12, 13, 14]
    elements = patch_mesh.c3d10_elements([31, 47], first + second)

    assert elements[47] == (1, 3, 2, 11, 7, 6, 5, 12, 14, 13)
    exterior = external_faces(elements)
    assert len(exterior) == 6
    assert tuple(sorted((1, 2, 3))) not in exterior


@pytest.mark.parametrize(
    "tags,connectivity",
    [
        ([1], list(range(1, 10))),
        ([1, 1], list(range(1, 21))),
        ([1], [1] * 10),
        ([0], list(range(1, 11))),
        ([1.5], list(range(1, 11))),
    ],
)
def test_c3d10_mapping_rejects_malformed_connectivity(tags, connectivity):
    with pytest.raises(ValueError):
        patch_mesh.c3d10_elements(tags, connectivity)


def test_integrated_volume_and_positive_jacobians_are_audited():
    audit = patch_mesh.audit_mesh_volume(
        2.0,
        determinants=[1.0, 1.0, 1.0, 1.0],
        quadrature_weights=[0.5, 0.5],
        sampled_jacobians=[0.8, 0.9],
        element_count=2,
    )

    assert audit["integrated_mesh_volume_mm3"] == 2.0
    assert audit["relative_volume_error"] == 0.0
    assert audit["minimum_sampled_jacobian"] == 0.8


@pytest.mark.parametrize(
    ("cad_volume", "determinants", "weights", "samples"),
    [
        (2.0, [1.0, 1.01], [1.0], [1.0]),
        (2.0, [1.0, -1.0], [1.0], [1.0]),
        (2.0, [1.0], [1.0, 1.0], [1.0]),
        (2.0, [1.0, 1.0], [1.0], [-0.1]),
        (2.0, [1.0, 1.0, 1.0], [1.0], [1.0]),
    ],
)
def test_integrated_volume_rejects_bad_jacobian_or_volume_evidence(
    cad_volume, determinants, weights, samples
):
    with pytest.raises(ValueError):
        patch_mesh.audit_mesh_volume(
            cad_volume, determinants, weights, samples, element_count=2
        )


def test_surface_tri6_coverage_matches_exact_exterior_and_rejects_gaps():
    _nodes, elements = _one_c3d10()
    exterior = external_faces(elements)
    triangles = [row[2] for row in exterior.values()]
    surface = surface_faces(triangles, exterior)
    references = {"surface-entity": surface["faces"]}

    patch_mesh.validate_surface_coverage(exterior, references)
    with pytest.raises(ValueError, match="more than one CAD surface"):
        patch_mesh.validate_surface_coverage(
            exterior,
            {"surface-a": surface["faces"], "surface-b": surface["faces"][:1]},
        )
    with pytest.raises(ValueError, match="complete exterior TRI6 set"):
        patch_mesh.validate_surface_coverage(
            exterior, {"surface-entity": surface["faces"][:-1]}
        )


def test_surface_coverage_validates_local_ids_before_global_element_remap():
    exterior_local = {(1, 2, 3): (37, 2, (1, 2, 3, 4, 5, 6))}
    local_references = {"surface": [[37, 2]]}

    global_references = patch_mesh.validate_and_remap_surface_coverage(
        exterior_local, local_references, {37: 9001}
    )

    assert global_references == {"surface": [[9001, 2]]}
    with pytest.raises(ValueError, match="complete exterior TRI6 set"):
        patch_mesh.validate_surface_coverage(exterior_local, global_references)
    with pytest.raises(ValueError, match="unmapped local element"):
        patch_mesh.validate_and_remap_surface_coverage(
            exterior_local, local_references, {}
        )


def test_independent_body_renumbering_keeps_coincident_nodes_separate():
    one_nodes, one_elements = _one_c3d10()
    all_nodes, all_elements, bodies = {}, {}, {}

    for body_id in ("body-a", "body-b"):
        node_map, element_map = append_body(
            all_nodes, all_elements, one_nodes, one_elements
        )
        bodies[body_id] = {
            "nodes": sorted(node_map.values()),
            "elements": sorted(element_map.values()),
        }

    assert len(all_nodes) == 20
    assert all_nodes[1] == all_nodes[11]
    assert set(bodies["body-a"]["nodes"]).isdisjoint(bodies["body-b"]["nodes"])
    validate_ownership(all_nodes, all_elements, bodies)

    bodies["body-b"]["nodes"].append(bodies["body-a"]["nodes"][0])
    with pytest.raises(ValueError, match="overlaps or is incomplete"):
        validate_ownership(all_nodes, all_elements, bodies)


def test_output_directory_is_non_overwriting_and_inputs_are_not_gmsh_loaded(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()

    with pytest.raises(FileExistsError, match="already exists"):
        patch_mesh.prepare_geometry_patch(
            BUNDLE,
            output,
            size_mm=40,
            axis_local_size_mm=5,
            axis_refinement_band_mm=40,
        )


def test_output_directory_cannot_overlap_the_frozen_input_bundle():
    with pytest.raises(ValueError, match="must be separate"):
        patch_mesh.prepare_geometry_patch(
            BUNDLE,
            BUNDLE / "mesh-output",
            size_mm=40,
            axis_local_size_mm=5,
            axis_refinement_band_mm=40,
        )


def test_bundle_preflight_failure_is_preserved_without_gmsh(tmp_path):
    copied = tmp_path / "bundle"
    shutil.copytree(BUNDLE, copied)
    (copied / "sha256.json").write_text('{"unexpected": "entry"}\n')
    output = tmp_path / "mesh-attempt"

    with pytest.raises(ValueError, match="hash index differs"):
        patch_mesh.prepare_geometry_patch(
            copied,
            output,
            size_mm=40,
            axis_local_size_mm=5,
            axis_refinement_band_mm=40,
        )

    record = json.loads((output / "mesh.json").read_text())
    assert record["status"] == "FAILED_MESH_PREPARATION_NO_SOLVER"
    assert "hash index differs" in record["error"]
    assert not (output / "mesh.inp").exists()


class _FakeGmshModel:
    def __init__(self):
        self.current = ""
        self.names = []

    def add(self, model_name):
        self.current = model_name
        self.names.append(model_name)

    def list(self):
        return list(self.names)

    def getCurrent(self):
        return self.current

    def remove(self):
        self.names.remove(self.current)
        self.current = ""


def _fake_gmsh(write):
    fake = SimpleNamespace()
    fake.__version__ = "synthetic-test"
    fake.model = _FakeGmshModel()
    fake.option = SimpleNamespace(setNumber=lambda *_args: None)
    fake._initialized = False
    fake.isInitialized = lambda: fake._initialized
    fake.initialize = lambda: setattr(fake, "_initialized", True)
    fake.finalize = lambda: setattr(fake, "_initialized", False)
    fake.write = write
    return fake


def test_active_failed_gmsh_model_is_saved_and_capture_failure_keeps_original_error(
    tmp_path, monkeypatch
):
    output = tmp_path / "mesh-attempt"
    original_mesh_error = "synthetic C3D10 validation failure"

    def fail_inside_active_model(gmsh, _bundle, body_row, *_args):
        gmsh.model.add(body_row["part_id"])
        raise RuntimeError(original_mesh_error)

    def partial_write(path):
        Path(path).write_bytes(b"partial gmsh model bytes")
        raise OSError("synthetic artifact write fault")

    fake_gmsh = _fake_gmsh(partial_write)
    monkeypatch.setitem(sys.modules, "gmsh", fake_gmsh)
    monkeypatch.setattr(patch_mesh, "_mesh_body", fail_inside_active_model)

    with pytest.raises(RuntimeError, match=original_mesh_error):
        patch_mesh.prepare_geometry_patch(
            BUNDLE,
            output,
            size_mm=40,
            axis_local_size_mm=3,
            axis_refinement_band_mm=12,
        )

    record = json.loads((output / "mesh.json").read_text())
    artifact = record["failed_gmsh_model"]
    artifact_path = output / artifact["file"]
    assert record["error"] == f"RuntimeError: {original_mesh_error}"
    assert artifact["body_id"] == patch_mesh.LOWER_RAIL
    assert artifact["status"] == "capture_failed"
    assert artifact["capture_error"] == "OSError: synthetic artifact write fault"
    assert artifact["sha256"] == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    assert artifact["partial_file"] is True
    assert fake_gmsh._initialized is False
