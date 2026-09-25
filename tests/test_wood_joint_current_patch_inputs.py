from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import wood_joint_current_patch_inputs as patch


class _Box:
    def __init__(self, bounds=(0, 1, 0, 1, 0, 1)):
        self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax = bounds


class _Point:
    def __init__(self, xyz):
        self.xyz = tuple(float(value) for value in xyz)

    def toTuple(self):
        return self.xyz


class _Vertex:
    def __init__(self, xyz):
        self.xyz = tuple(float(value) for value in xyz)

    def Center(self):
        return _Point(self.xyz)


class _Face:
    def __init__(
        self,
        name,
        normal,
        centroid,
        bounds,
        *,
        area=8000.0,
        inner_wires=0,
        mate=None,
        overlap_area=6000.0,
    ):
        self.name = name
        self.normal = normal
        self.centroid = centroid
        self.bounds = bounds
        self.area = area
        self.inner_wires = inner_wires
        self.mate = mate
        self.overlap_area = overlap_area

    def geomType(self):
        return "PLANE"

    def Area(self):
        return self.area

    def normalAt(self):
        return self.normal

    def Center(self):
        return _Point(self.centroid)

    def BoundingBox(self):
        return _Box(self.bounds)

    def Wires(self):
        return [object() for _ in range(1 + self.inner_wires)]

    def intersect(self, other):
        if self.mate != other.mate or self.mate is None:
            return _Common([])
        return _Common(
            [
                _OverlapFace(
                    self.overlap_area,
                    tuple((a + b) / 2 for a, b in zip(self.centroid, other.centroid, strict=True)),
                )
            ]
        )


class _OverlapFace:
    def __init__(self, area, centroid):
        self.area = area
        self.centroid = centroid

    def geomType(self):
        return "PLANE"

    def Area(self):
        return self.area

    def Center(self):
        return _Point(self.centroid)


class _Common:
    def __init__(self, faces):
        self._faces = faces

    def Faces(self):
        return self._faces


class _FakeShape:
    def __init__(self, name, vertices, *, volume=1.0, faces=(), bounds=None, center=None):
        self.name = name
        self._vertices = [_Vertex(vertex) for vertex in vertices]
        self._volume = float(volume)
        self._center = center
        self._faces = list(faces)
        self._bounds = bounds or (
            min(vertex[0] for vertex in vertices),
            max(vertex[0] for vertex in vertices),
            min(vertex[1] for vertex in vertices),
            max(vertex[1] for vertex in vertices),
            min(vertex[2] for vertex in vertices),
            max(vertex[2] for vertex in vertices),
        )
        self.overlaps = {}
        self.cut_volumes = {}

    def isNull(self):
        return False

    def isValid(self):
        return True

    def Solids(self):
        return [self]

    def Volume(self):
        return self._volume

    def Center(self):
        if self._center is not None:
            return _Point(self._center)
        return _Point(
            tuple((self._bounds[2 * i] + self._bounds[2 * i + 1]) / 2 for i in range(3))
        )

    def BoundingBox(self):
        return _Box(self._bounds)

    def Vertices(self):
        return self._vertices

    def Faces(self):
        return self._faces

    def intersect(self, other):
        if isinstance(other, _FakeShape):
            return _FakeVolume(self.overlaps.get(other.name, 0.0))
        raise TypeError("unexpected fake intersection")

    def clean(self):
        return self

    def cut(self, other):
        return _FakeVolume(self.cut_volumes.get(other.name, 0.0))


class _FakeVolume:
    def __init__(self, volume):
        self._volume = float(volume)

    def Volume(self):
        return self._volume

    def cut(self, _other):
        return _FakeVolume(0.0)


def _body_shapes():
    rail_faces = [
        _Face(
            "cleat_rail_contact",
            (0, -1, 0),
            (44.45, 11.1, 59.85),
            (0, 88.9, 11.1, 11.1, 0, 119.7),
            inner_wires=2,
            mate="rail",
        )
    ]
    principal_faces = [
        _Face(
            "cleat_principal_contact",
            (-1, 0, 0),
            (0, 55.55, 59.85),
            (0, 0, 11.1, 100, 0, 119.7),
            inner_wires=1,
            mate="principal",
        )
    ]
    rail_receiver_face = [
        _Face(
            "rail_cleat_contact",
            (0, 1, 0),
            (44.45, 11.1, 59.85),
            (0, 88.9, 11.1, 11.1, 0, 139.7),
            mate="rail",
        )
    ]
    rail_receiver_face.append(
        _Face(
            "rail_principal_contact",
            (1, 0, 0),
            (0, 55.55, 59.85),
            (0, 0, 0, 100, 0, 119.7),
            mate="rail_principal",
            overlap_area=5322.57,
        )
    )
    principal_receiver_face = [
        _Face(
            "principal_cleat_contact",
            (1, 0, 0),
            (0, 55.55, 59.85),
            (0, 0, 0, 100, 0, 139.7),
            mate="principal",
        )
    ]
    principal_receiver_face.append(
        _Face(
            "principal_rail_contact",
            (-1, 0, 0),
            (0, 55.55, 59.85),
            (0, 0, 0, 100, 0, 119.7),
            mate="rail_principal",
            overlap_area=5322.57,
        )
    )
    cleat = _FakeShape(
        patch.CLEAT_ID,
        [(x, y, z) for x in (0, 88.9) for y in (11.1, 100) for z in (0, 119.7)],
        volume=500000.0,
        faces=rail_faces + principal_faces,
    )
    rail = _FakeShape(
        "base_rail_bottom_right",
        [(x, y, z) for x in (0, 1000) for y in (-27, 11.1) for z in (0, 139.7)],
        volume=500000.0,
        faces=rail_receiver_face,
    )
    principal = _FakeShape(
        "base_principal_center_right",
        [(x, y, z) for x in (-38.1, 0) for y in (0, 100) for z in (0, 2500)],
        volume=500000.0,
        faces=principal_receiver_face,
    )
    return cleat, rail, principal


def _geometry(monkeypatch):
    inventory = json.loads(patch.INVENTORY_PATH.read_text())
    inventory_bytes = patch.INVENTORY_PATH.read_bytes()
    cleat, rail, principal = _body_shapes()
    axis_ids = tuple(patch.AXIS_RECEIVERS)
    grip_inputs = patch._read_current_grip_inputs()
    grip_rows = grip_inputs["axes"]
    bores = {}
    hardware = {}
    stack_rows = {}
    role_shapes = {}
    for index, axis_id in enumerate(axis_ids):
        receivers = patch.AXIS_RECEIVERS[axis_id]
        row = grip_rows[axis_id]
        origin = tuple(row["frozen_shaft_center_xyz_mm"])
        direction = tuple(row["axis_head_to_nut_global_unit"])
        station_id = "clip_horizontal_bottom_right_1"
        stack_rows[axis_id] = {
            "axis_id": axis_id,
            "station_id": station_id,
            "receiver_ids": list(receivers),
            "head_seat_global_xyz_mm": [999.0, 999.0, 999.0],
            "direction_global_xyz": list(direction),
            "layers_head_to_nut": [
                {"body_id": receivers[1], "thickness_mm": 88.9},
                {"body_id": receivers[0], "thickness_mm": 38.1},
            ],
        }
        bore_shape = _FakeShape(f"{axis_id}/bore", [(0, 0, 0), (1, 1, 1)])
        bores[axis_id] = SimpleNamespace(
            axis_id=axis_id,
            receiver_ids=tuple(reversed(receivers)),
            family="bottom_center",
            shape=bore_shape,
        )
        roles = {}
        for role_index, role in enumerate(patch.HARDWARE_ROLES):
            intervals = row["hardware_roles"][role]["union_intervals_from_underhead_mm"]
            datum_axis = row["underhead_datum"]["head_underface_contact_check"][
                "head_toward_nut_face_global_axis_mm"
            ]
            center_station = datum_axis + sum(intervals[0]) / 2
            center_axis = sum(origin[i] * direction[i] for i in range(3))
            role_center = tuple(
                origin[i] + (center_station - center_axis) * direction[i]
                for i in range(3)
            )
            role_shape = _FakeShape(
                f"{axis_id}/{role}", [(0, 0, 0), (1 + role_index / 10, 1, 1)],
                volume=100 + index + role_index,
                center=role_center,
            )
            roles[role] = role_shape
            role_shapes[f"{axis_id}/{role}"] = role_shape
        hardware[axis_id] = roles

    # Synthetic union behavior lets the manifest test verify the physical-body
    # contract without asking CadQuery/OCC to operate on these fakes.
    for axis_id in axis_ids:
        head, shaft = hardware[axis_id]["head"], hardware[axis_id]["shaft"]
        head.overlaps[shaft.name] = 0.0
        shaft.overlaps[head.name] = 0.0
        union = _FakeShape(
            f"{axis_id}/physical_bolt",
            [(0, 0, 0), (2, 2, 2)],
            volume=head.Volume() + shaft.Volume(),
        )
        union.cut_volumes[head.name] = 0.0
        union.cut_volumes[shaft.name] = 0.0
        head.cut_volumes[union.name] = 0.0
        shaft.cut_volumes[union.name] = 0.0
        head.fuse_result = union

        def _fuse(other, _head=head, _shaft=shaft):
            assert other is _shaft
            return _head.fuse_result

        head.fuse = _fuse

    geometry = SimpleNamespace(
        layout_id=patch.CURRENT_REVISION_ID,
        trial_id=patch.CURRENT_REVISION_ID,
        status="unaccepted_viewer_geometry_revision",
        source_inventory_sha256=hashlib.sha256(inventory_bytes).hexdigest(),
        source_inputs_sha256={
            "docs/wood-joints-mvp/source-inventory.json": hashlib.sha256(
                inventory_bytes
            ).hexdigest()
        },
        source_inventory=inventory,
        finished_hosts={
            "base_rail_bottom_right": rail,
            "base_principal_center_right": principal,
        },
        finished_candidate_parts={patch.CLEAT_ID: cleat},
        candidate_bores=bores,
        candidate_installed_hardware=hardware,
        local_delta_diagnostics={"bottom_center": {"stack_rows": stack_rows}},
        _current_grip_inputs=grip_inputs,
    )
    monkeypatch.setattr(patch, "_source_shape_fingerprint", lambda shape: f"sha:{shape.name}")

    def _project(shape, _direction, *, axis_id, label):
        row = grip_rows[axis_id]
        datum_axis = row["underhead_datum"]["head_underface_contact_check"][
            "head_toward_nut_face_global_axis_mm"
        ]
        intervals = row["hardware_roles"][label]["union_intervals_from_underhead_mm"]
        return [[datum_axis + float(low), datum_axis + float(high)] for low, high in intervals]

    def _receiver(_geometry, receiver_id, _shaft, _direction, _datum, _diameter, axis_id):
        return next(
            dict(receiver)
            for receiver in grip_rows[axis_id]["wood_receiver_intervals"]
            if receiver["receiver_id"] == receiver_id
        )

    monkeypatch.setattr(patch.current_grip, "projected_solid_intervals", _project)
    monkeypatch.setattr(patch.current_grip, "_shaft_diameter_mm", lambda *_args: 6.35)
    monkeypatch.setattr(patch.current_grip, "_receiver_axis_record", _receiver)
    return geometry


def test_current_pin_archive_records_baseline_and_distinct_current_revision():
    pins = patch._read_current_pins()

    assert pins["revision_id"] == patch.CURRENT_REVISION_ID
    assert pins["implementation_revision"] == "b1e8707d"
    assert pins["source_files_sha256"] == patch.VERIFIED_CURRENT_SOURCE_HASHES
    assert len(pins["input_adapter_source_sha256"]) == 64
    inventory = json.loads(patch.INVENTORY_PATH.read_text())
    assert inventory["source_commit"] == patch.SOURCE_BASELINE_COMMIT
    assert inventory["source_commit"] != pins["implementation_revision"]


def test_manifest_extracts_three_wood_bodies_four_physical_bolts_and_sixteen_metal_bodies(
    monkeypatch,
):
    geometry = _geometry(monkeypatch)
    manifest, shapes = patch._build_manifest(
        geometry, {"test_pin": "mock"}, geometry._current_grip_inputs
    )

    assert [row["part_id"] for row in manifest["wood_bodies"]] == list(patch.WOOD_PARTS)
    assert len(manifest["physical_bolts"]) == 4
    assert len(manifest["physical_metal_bodies"]) == 16
    assert sum(row["cad_role_count"] for row in manifest["physical_bolts"]) == 20
    assert manifest["scope"]["physical_metal_bodies"] == 16
    assert manifest["scope"]["step_artifacts"] == 27
    assert manifest["geometry_binding"]["layout_id"] == patch.CURRENT_REVISION_ID
    assert manifest["migration_blockers"] == []
    assert len([key for key in shapes if key.startswith("physical_metal/")]) == 4
    for bolt in manifest["physical_bolts"]:
        assert bolt["physical_bolt_count"] == 1
        assert bolt["physical_bolt_roles"] == ["head", "shaft"]
        assert bolt["head_and_shaft_are_one_physical_bolt"]
        assert len(bolt["raw_receiver_projected_intervals"]) == 2
        assert bolt["raw_receiver_projected_intervals"][0]["member_id"] == patch.CLEAT_ID
        assert bolt["raw_receiver_projected_intervals"][0][
            "projected_intervals_from_underhead_datum_mm"
        ][0] == pytest.approx([2.032, 90.932])
        assert bolt["raw_receiver_projected_intervals"][1][
            "projected_intervals_from_underhead_datum_mm"
        ][0] == pytest.approx([90.932, 129.032])
        assert bolt["receivers_head_to_nut"] == geometry._current_grip_inputs["axes"][
            bolt["physical_bolt_id"]
        ]["ordered_receiver_ids_head_to_nut"]
        assert bolt["axis_origin_global_xyz_mm"] != [999.0, 999.0, 999.0]
    cleat_grain = next(row for row in manifest["wood_bodies"] if row["part_id"] == patch.CLEAT_ID)["grain"]
    assert cleat_grain["grain_axis_local_name"] == "N"
    assert cleat_grain["grain_axis_global_xyz"] == [0.0, -0.766044443, 0.64278761]


def test_contact_inventory_uses_finite_opposed_face_intersection_area_with_holes_retained(
    monkeypatch,
):
    geometry = _geometry(monkeypatch)
    manifest, _ = patch._build_manifest(
        geometry, {"test_pin": "mock"}, geometry._current_grip_inputs
    )

    assert len(manifest["wood_interfaces"]) == 3
    for interface in manifest["wood_interfaces"]:
        assert interface["status"] == "finite_opposed_coplanar_patch_extracted"
        expected_area = (
            5322.57
            if interface["members"]
            == ["base_rail_bottom_right", "base_principal_center_right"]
            else 6000.0
        )
        assert interface["finite_overlap_area_mm2"] == expected_area
        if interface["members"] == ["base_rail_bottom_right", "base_principal_center_right"]:
            assert interface["bolt_axis_ids"] == []
        assert interface["finite_overlap_area_centroid_global_xyz_mm"] is not None
        assert len(interface["actual_face_pairs"]) == 1
        first_face = interface["actual_face_pairs"][0]["first_face"]
        if interface["members"][0] == patch.CLEAT_ID:
            assert first_face["inner_wire_count"] > 0
        assert interface["actual_face_pairs"][0]["plane_normal_first_member_global_xyz"]


def test_stale_stack_row_order_and_datum_are_ignored_in_favor_of_live_intervals(monkeypatch):
    geometry = _geometry(monkeypatch)
    first_axis = next(iter(patch.AXIS_RECEIVERS))
    geometry.local_delta_diagnostics["bottom_center"]["stack_rows"][first_axis][
        "receiver_ids"
    ].reverse()

    manifest, _ = patch._build_manifest(
        geometry, {"test_pin": "mock"}, geometry._current_grip_inputs
    )
    axis = next(
        row for row in manifest["physical_bolts"] if row["physical_bolt_id"] == first_axis
    )
    current = geometry._current_grip_inputs["axes"][first_axis]
    assert axis["receivers_head_to_nut"] == current["ordered_receiver_ids_head_to_nut"]
    assert axis["axis_origin_global_xyz_mm"] != [999.0, 999.0, 999.0]
    assert axis["axis_source"].startswith("current grip-screen attempt02")


def test_noncurrent_geometry_is_rejected_before_any_export(tmp_path, monkeypatch):
    geometry = _geometry(monkeypatch)
    geometry.layout_id = "historical-wj16"
    called = False

    def _unexpected_export(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("export must not run for a historical geometry")

    monkeypatch.setattr(patch.cq.exporters, "export", _unexpected_export)
    with pytest.raises(ValueError, match="not the selected current revision"):
        patch.export_current_patch_inputs(geometry, tmp_path / "new-bundle")
    assert not called
    assert not (tmp_path / "new-bundle").exists()


def test_existing_output_path_is_never_overwritten(tmp_path, monkeypatch):
    output = tmp_path / "already-published"
    output.mkdir()
    (output / "keep.txt").write_text("untouched")
    called = False

    def _pins():
        nonlocal called
        called = True
        raise AssertionError("pins must not be loaded after the destination preflight")

    monkeypatch.setattr(patch, "_read_current_pins", _pins)
    with pytest.raises(FileExistsError):
        patch.export_current_patch_inputs(object(), output)
    assert not called
    assert (output / "keep.txt").read_text() == "untouched"


def test_callable_writes_27_role_preserving_step_inputs_only_with_mocked_cad_io(
    tmp_path, monkeypatch
):
    geometry = _geometry(monkeypatch)
    shape_by_path = {}
    export_calls = []

    def _export(shape, path):
        export_calls.append(path)
        shape_by_path[path] = shape
        Path(path).write_bytes(b"synthetic STEP payload")

    def _import_step(path):
        return SimpleNamespace(val=lambda: shape_by_path[path])

    monkeypatch.setattr(patch.cq.exporters, "export", _export)
    monkeypatch.setattr(patch.cq.importers, "importStep", _import_step)
    output = tmp_path / "current_patch"

    result = patch.export_current_patch_inputs(geometry, output)
    inventory = json.loads((output / "inventory.json").read_text())
    hashes = json.loads((output / "sha256.json").read_text())

    assert result["status"] == "current_geometry_patch_inputs_only"
    assert len(export_calls) == 27
    assert len(inventory["step_artifacts"]) == 27
    assert len([key for key in inventory["step_artifacts"] if key.startswith("wood/")]) == 3
    assert len([key for key in inventory["step_artifacts"] if key.startswith("hardware/")]) == 20
    assert len(
        [key for key in inventory["step_artifacts"] if key.startswith("physical_metal/")]
    ) == 4
    assert len(inventory["physical_metal_bodies"]) == 16
    assert len(hashes) == 28
    assert hashes["inventory.json"] == result["inventory_sha256"]
    for artifact_key, artifact in inventory["step_artifacts"].items():
        relative_path = f"{artifact_key}.step"
        step_path = output / relative_path
        assert step_path.is_file()
        assert not step_path.stat().st_mode & 0o222
        assert hashlib.sha256(step_path.read_bytes()).hexdigest() == artifact[
            "file_sha256"
        ]
        assert artifact["identity_checks"]["symmetric_difference"]["passed"]


def test_frozen_live_attempt01_bundle_has_current_axis_and_three_contact_schema():
    bundle = (
        patch.ROOT
        / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-patch-inputs-attempt01"
    )
    inventory_bytes = (bundle / "inventory.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    hashes = json.loads((bundle / "sha256.json").read_text())

    assert hashlib.sha256(inventory_bytes).hexdigest() == (
        "70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3"
    )
    assert inventory["schema"] == patch.SCHEMA
    assert inventory["status"] == "current_geometry_patch_inputs_only"
    assert inventory["candidate"]["revision_id"] == patch.CURRENT_REVISION_ID
    assert inventory["candidate"]["implementation_revision"] == "b1e8707d"
    assert inventory["scope"]["wood_interfaces"] == 3
    assert inventory["scope"]["physical_metal_bodies"] == 16
    assert inventory["scope"]["step_artifacts"] == 27
    assert inventory["migration_blockers"] == []
    assert len(inventory["physical_bolts"]) == 4
    assert all(
        "current grip-screen attempt02" in row["axis_source"]
        for row in inventory["physical_bolts"]
    )
    assert all(
        row["union_identity"]["valid"]
        and row["union_identity"]["symmetric_difference_passed"]
        for row in inventory["physical_metal_bodies"]
        if row["physical_kind"] == "bolt_head_plus_shaft_union"
    )
    assert [row["interface_id"] for row in inventory["wood_interfaces"]] == [
        "bottom_center_right_cleat_to_base_rail_bottom_right",
        "bottom_center_right_cleat_to_base_principal_center_right",
        "base_rail_bottom_right_to_base_principal_center_right",
    ]
    assert inventory["wood_interfaces"][2]["bolt_axis_ids"] == []
    assert set(hashes) == {"inventory.json", *[f"{key}.step" for key in inventory["step_artifacts"]]}
    for relative_path, expected_hash in hashes.items():
        assert hashlib.sha256((bundle / relative_path).read_bytes()).hexdigest() == expected_hash
