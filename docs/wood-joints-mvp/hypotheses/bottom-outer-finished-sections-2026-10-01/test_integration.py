"""Synthetic end-to-end contract checks for the bottom section producer."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

HERE = Path(__file__).resolve().parent
producer_spec = importlib.util.spec_from_file_location(
    "bottom_finished_sections_integration", HERE / "produce.py"
)
producer = importlib.util.module_from_spec(producer_spec)
producer_spec.loader.exec_module(producer)


def load_host(path: Path):
    spec = importlib.util.spec_from_file_location(
        "bottom_sections_integration_host", path
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


host_source = producer.HOST_METHOD
section_source = producer.SECTION_METHOD
host = load_host(host_source)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def balance_record(actions, datum):
    result = host.wrench(actions, datum)
    return {
        "reference_xyz_mm": datum,
        "force_residual_xyz_n": result["force_xyz_n"],
        "moment_residual_xyz_nmm": result["moment_about_datum_xyz_nmm"],
        "force_rounding_radius_xyz_n": result["force_rounding_radius_xyz_n"],
        "moment_rounding_radius_xyz_nmm": result["moment_rounding_radius_xyz_nmm"],
        "printed_resultants_passed": True,
        "interval_resultants_passed": True,
    }


def model_template(case_id: str, bindings: dict[str, dict[str, object]]) -> dict:
    members = sorted(producer.MEMBERS)
    body_geometry = {}
    for member in members:
        binding = bindings[member]
        body_geometry[member] = {
            "geometry_record": {
                "axis": [1.0, 0.0, 0.0],
                "section_u": [0.0, 1.0, 0.0],
                "section_v": [0.0, 0.0, 1.0],
                "start": [0.0, 0.0, 0.0],
                "end": [100.0, 0.0, 0.0],
                "source_descriptor": {
                    "step_path": binding["path"],
                    "step_sha256": binding["file_sha256"],
                    "transverse_status": "synthetic test frame retained",
                },
            }
        }
    return {
        "candidate": producer.CANDIDATE,
        "geometry_revision_id": producer.REVISION,
        "case_id": case_id,
        "body_geometry": body_geometry,
        "contact_cell_ownership": [],
        "physical_body_loads": {member: {"1": [0.0, 0.0, -2.0]} for member in members},
        "nodes": {"1": [80.0, 5.0, 25.0]},
    }


def physical_rows(factor: float) -> dict[str, dict]:
    edges = (
        ("cleat-rail", producer.CLEAT, producer.RAIL, 10.0, 1.0),
        ("rail-side", producer.RAIL, producer.SIDE, 35.0, 2.0),
        ("side-cleat", producer.SIDE, producer.CLEAT, 48.0, 3.0),
    )
    result = {}
    for name, first, second, station, force_y in edges:
        result[name] = {
            "first": first,
            "second": second,
            "role": "synthetic physical connection",
            "point": [station, 10.0, 20.0],
            "force_on_first_xyz_n": [0.0, factor * force_y, 0.0],
            "force_on_second_xyz_n": [0.0, -factor * force_y, 0.0],
            "force_rounding_radius_xyz_n": [0.01, 0.01, 0.01],
        }
    return result


def build_fixture(tmp_path: Path, monkeypatch) -> dict:
    root = tmp_path / "synthetic-workspace"
    root.mkdir()
    features_path = root / "features.json"
    freeze_path = root / "freeze.json"
    contacts_path = root / "contact-geometry.json"

    copied_host = root / "methods" / "host_actions.py"
    copied_section = root / "methods" / "section_geometry.py"
    copied_host.parent.mkdir(parents=True)
    shutil.copyfile(host_source, copied_host)
    shutil.copyfile(section_source, copied_section)

    bindings = {}
    for member in sorted(producer.MEMBERS):
        relative = f"members/{member}.step"
        step_path = root / relative
        step_path.parent.mkdir(parents=True, exist_ok=True)
        step_path.write_bytes(f"synthetic STEP for {member}\n".encode())
        bindings[member] = {
            "path": relative,
            "file_sha256": digest(step_path),
            "face_count": 1,
        }

    axes = []
    for axis_id in sorted(producer.AXES):
        role = axis_id.removeprefix(producer.PREFIX).split("_")[0]
        ordinal = int(axis_id.rsplit("_", 1)[1])
        memberships = []
        for member in sorted(producer.RECEIVERS[role]):
            if member == producer.CLEAT:
                station = 10.0 * ordinal if role == "rail" else 15.0
            elif member == producer.RAIL:
                station = 30.0
            else:
                station = 30.0 + 10.0 * ordinal
            feature_id = f"{member}/{role}_{ordinal}"
            memberships.append(
                {
                    "receiver_member_id": member,
                    "match_status": "matched_bore_patch",
                    "matched_feature_ids": [feature_id],
                    "cylinder_surface_candidates": [
                        {
                            "feature_id": feature_id,
                            "association_status": "eligible_bore_patch",
                            "patch_interval_projected_from_axis_datum_mm": [
                                station - 1.0,
                                station + 1.0,
                            ],
                            "cylinder_radius_mm": 3.75,
                        }
                    ],
                    "current_finished_step_binding": bindings[member],
                }
            )
        axes.append(
            {
                "axis_id": axis_id,
                "receiver_memberships": memberships,
                "source_axis_fields": {
                    "occupied_diameter_mm": 6.35,
                    "datum_global_xyz_mm": [0.0, 0.0, 0.0],
                    "direction_global_xyz": [1.0, 0.0, 0.0],
                },
            }
        )
    axes.extend({"axis_id": f"unrelated/axis-{index:02d}"} for index in range(88))
    write_json(
        features_path,
        {
            "candidate": producer.CANDIDATE,
            "geometry_revision_id": producer.REVISION,
            "source_axis_groups": {"candidate_bolt_axes": {"axes": axes}},
        },
    )
    write_json(contacts_path, {"contact_patches": []})

    relative_sources = {}
    for case in ("a1-rear", "a12-rear", "k12-rear"):
        case_model = model_template(case, bindings)
        response = {
            "candidate": producer.CANDIDATE,
            "geometry_revision_id": producer.REVISION,
            "case_id": case,
            "increments": [],
        }
        audit = {"increments": []}
        for factor in producer.FACTORS:
            increment = {
                "load_factor": factor,
                "physical_connection_forces": physical_rows(factor),
                "exact_floor_tangent_reactions": [],
                "physical_balance": {"body_equilibrium": {}},
                **{gate: True for gate in producer.GATES},
            }
            audit_increment = {
                "load_factor": factor,
                "passed": True,
                "body_equilibrium": {},
            }
            for member in sorted(producer.MEMBERS):
                frame = {
                    "host": member,
                    "member_start_xyz_mm": [0.0, 0.0, 0.0],
                    "member_end_xyz_mm": [100.0, 0.0, 0.0],
                    "member_grain_length_mm": 100.0,
                    "grain_axis_global_xyz": [1.0, 0.0, 0.0],
                    "section_u_global_xyz": [0.0, 1.0, 0.0],
                    "section_v_global_xyz": [0.0, 0.0, 1.0],
                }
                actions, _, _ = host.host_actions_for_state(
                    case_model, increment, member, frame, {"contact_patches": []}
                )
                datum = [0.0, 0.0, 0.0]
                record = balance_record(actions, datum)
                audit_increment["body_equilibrium"][member] = record
                increment["physical_balance"]["body_equilibrium"][member] = {
                    key: value
                    for key, value in record.items()
                    if key != "reference_xyz_mm"
                }
            response["increments"].append(increment)
            audit["increments"].append(audit_increment)

        case_files = {}
        for name, document in (
            ("model", case_model),
            ("response", response),
            ("all_body_audit", audit),
        ):
            relative = f"cases/{case}/{name}.json"
            path = root / relative
            write_json(path, document)
            case_files[name] = {"path": relative, "sha256": digest(path)}
            relative_sources[f"{case}:{name}"] = path
        relative_sources[f"{case}:documents"] = {
            "model": case_model,
            "response": response,
            "audit": audit,
        }
        relative_sources[f"{case}:files"] = case_files

    freeze = {
        "cases": {
            case: relative_sources[f"{case}:files"]
            for case in ("a1-rear", "a12-rear", "k12-rear")
        }
    }
    write_json(freeze_path, freeze)

    monkeypatch.setattr(producer, "ROOT", root)
    monkeypatch.setattr(producer, "FEATURES", features_path)
    monkeypatch.setattr(producer, "FREEZE", freeze_path)
    monkeypatch.setattr(producer, "CONTACT", contacts_path)
    monkeypatch.setattr(producer, "HOST_METHOD", copied_host)
    monkeypatch.setattr(producer, "SECTION_METHOD", copied_section)
    monkeypatch.setattr(
        producer,
        "PINS",
        {
            "axis_features": (features_path, digest(features_path)),
            "three_case_freeze": (freeze_path, digest(freeze_path)),
            "source_contact_geometry": (contacts_path, digest(contacts_path)),
            "point_action_method": (copied_host, digest(copied_host)),
            "finished_section_method": (copied_section, digest(copied_section)),
        },
    )

    real_module = producer.module

    def load_with_synthetic_section(path, expected_digest, name):
        loaded = real_module(path, expected_digest, name)
        if name == "bottom_finished_section_geometry":
            loaded.section_properties = lambda shape, origin, grain, u, v: {
                "component_count": 2,
                "area_mm2": 500.0,
                "centroid_global_xyz_mm": [origin[0], 20.0, 10.0],
            }
        return loaded

    monkeypatch.setattr(producer, "module", load_with_synthetic_section)

    class SyntheticSolid:
        def isValid(self):
            return True

        def Solids(self):
            return [self]

        def Faces(self):
            return [object()]

    monkeypatch.setattr(
        cq.importers,
        "importStep",
        lambda path: SimpleNamespace(val=lambda: SyntheticSolid()),
    )

    return {"root": root, "sources": relative_sources, "bindings": bindings}


def refresh_freeze_pin(fixture: dict, monkeypatch) -> None:
    root = fixture["root"]
    freeze_path = producer.FREEZE
    freeze = json.loads(freeze_path.read_text())
    for files in freeze["cases"].values():
        for pin in files.values():
            pin_path = root / pin["path"]
            pin["sha256"] = digest(pin_path)
    write_json(freeze_path, freeze)
    pins = dict(producer.PINS)
    pins["three_case_freeze"] = (freeze_path, digest(freeze_path))
    monkeypatch.setattr(producer, "PINS", pins)


def test_synthetic_producer_emits_complete_replayable_geometry_only_artifact(
    tmp_path, monkeypatch
):
    fixture = build_fixture(tmp_path, monkeypatch)
    first = producer.produce()
    second = producer.produce()

    canonical = lambda value: json.dumps(
        value, sort_keys=True, indent=2, allow_nan=False
    )
    assert canonical(first) == canonical(second)
    assert first["candidate"] == producer.CANDIDATE
    assert first["geometry_revision_id"] == producer.REVISION
    assert first["status"] == "PASS_FROZEN_GEOMETRY_AND_POINT_ACTION_DEMAND_JOIN_ONLY"
    assert first["counts"] == {
        "axes": 4,
        "members": 3,
        "receiver_memberships": 8,
        "unique_planes": 6,
        "whole_body_states": 63,
        "two_trace_cut_states": 252,
    }

    expected_bindings = fixture["bindings"]
    assert {
        member: (record["step_path"], record["step_sha256"])
        for member, record in first["member_frames"].items()
    } == {
        member: (binding["path"], binding["file_sha256"])
        for member, binding in expected_bindings.items()
    }
    assert len(first["planes"]) == 6
    assert sum(len(plane["axis_memberships"]) for plane in first["planes"]) == 8
    expected_plane_memberships = {
        (producer.CLEAT, 10.0): {f"{producer.PREFIX}rail_1"},
        (producer.CLEAT, 15.0): {
            f"{producer.PREFIX}side_1",
            f"{producer.PREFIX}side_2",
        },
        (producer.CLEAT, 20.0): {f"{producer.PREFIX}rail_2"},
        (producer.RAIL, 30.0): {
            f"{producer.PREFIX}rail_1",
            f"{producer.PREFIX}rail_2",
        },
        (producer.SIDE, 40.0): {f"{producer.PREFIX}side_1"},
        (producer.SIDE, 50.0): {f"{producer.PREFIX}side_2"},
    }
    actual_plane_memberships = {
        (plane["member_id"], plane["cut_station_mm"]): {
            identity["axis_id"] for identity in plane["axis_memberships"]
        }
        for plane in first["planes"]
    }
    assert actual_plane_memberships == expected_plane_memberships
    expected_bore_identities = {
        (
            axis_id,
            f"{member}/{axis_id.removeprefix(producer.PREFIX)}",
        )
        for axis_id in producer.AXES
        for member in producer.RECEIVERS[
            axis_id.removeprefix(producer.PREFIX).split("_")[0]
        ]
    }
    actual_bore_identities = {
        (identity["axis_id"], identity["bore_feature_id"])
        for plane in first["planes"]
        for identity in plane["axis_memberships"]
    }
    assert actual_bore_identities == expected_bore_identities

    cases = ("a1-rear", "a12-rear", "k12-rear")
    members = producer.MEMBERS
    expected_body_keys = {
        (case, index, factor, member)
        for case in cases
        for index, factor in enumerate(producer.FACTORS)
        for member in members
    }
    body_keys = {
        (
            row["case_id"],
            row["increment_index"],
            row["load_factor"],
            row["member_id"],
        )
        for row in first["whole_body_states"]
    }
    assert body_keys == expected_body_keys
    assert len(body_keys) == len(first["whole_body_states"]) == 63

    expected_plane_ids = {
        (producer.CLEAT, 10.0): f"{producer.CLEAT}/bore-plane-rail_1",
        (producer.CLEAT, 15.0): f"{producer.CLEAT}/bore-plane-side_1",
        (producer.CLEAT, 20.0): f"{producer.CLEAT}/bore-plane-rail_2",
        (producer.RAIL, 30.0): f"{producer.RAIL}/bore-plane-rail_1",
        (producer.SIDE, 40.0): f"{producer.SIDE}/bore-plane-side_1",
        (producer.SIDE, 50.0): f"{producer.SIDE}/bore-plane-side_2",
    }
    expected_cut_keys = {
        (case, index, factor, member, plane_id, trace)
        for case in cases
        for index, factor in enumerate(producer.FACTORS)
        for (member, _station), plane_id in expected_plane_ids.items()
        for trace in (
            "approached_from_negative_station",
            "approached_from_positive_station",
        )
    }
    cut_keys = {
        (
            row["case_id"],
            row["increment_index"],
            row["load_factor"],
            row["member_id"],
            row["plane_id"],
            row["source_point_action_cut"]["trace"],
        )
        for row in first["cut_states"]
    }
    assert cut_keys == expected_cut_keys
    assert len(cut_keys) == len(first["cut_states"]) == 252
    for case in cases:
        assert first["case_sources"][case] == fixture["sources"][f"{case}:files"]

    for row in first["cut_states"]:
        assert row["finite_patch_or_ligament_force_distribution_established"] is False
        assert row["section_resistance_accepted"] is False
    # Independent hand sum at full load on the cleat: forces (0,1,0)
    # at (10,10,20), (0,-3,0) at (48,10,20), and (0,0,-2) at (80,5,25).
    # The first force lies on the 10 mm bore plane, so the emitted two traces
    # must retain its jump. These expectations do not call the host helpers.
    body = next(
        row["whole_body_source_balance"]
        for row in first["whole_body_states"]
        if row["case_id"] == "a1-rear"
        and row["load_factor"] == 1
        and row["member_id"] == producer.CLEAT
    )
    for key, expected in {
        "point_action_external_residual_force_xyz_n": [0, -2, -2],
        "point_action_external_residual_moment_xyz_nmm": [30, 160, -134],
        "propagated_force_rounding_radius_xyz_n": [0.02, 0.02, 0.02],
        "propagated_moment_rounding_radius_xyz_nmm": [0.6, 0.98, 0.78],
    }.items():
        assert body[key] == pytest.approx(expected, abs=1e-10)
    traces = {
        row["source_point_action_cut"]["trace"]: row
        for row in first["cut_states"]
        if row["case_id"] == "a1-rear"
        and row["load_factor"] == 1
        and row["plane_id"] == f"{producer.CLEAT}/bore-plane-rail_1"
    }
    for trace, force, cut_moment, cut_radius, centroid_moment, centroid_radius in (
        (
            "approached_from_negative_station",
            [0, 2, 2],
            [-30, -140, 114],
            [0.6, 0.78, 0.58],
            [-50, -140, 114],
            [1.2, 0.98, 0.98],
        ),
        (
            "approached_from_positive_station",
            [0, 3, 2],
            [-50, -140, 114],
            [0.3, 0.58, 0.48],
            [-60, -140, 114],
            [0.6, 0.68, 0.68],
        ),
    ):
        row = traces[trace]
        cut = row["source_point_action_cut"][
            "internal_cut_wrench_on_positive_side_material"
        ]
        assert cut["force_xyz_n"] == pytest.approx(force, abs=1e-10)
        assert cut["moment_about_datum_xyz_nmm"] == pytest.approx(cut_moment, abs=1e-10)
        assert cut["moment_rounding_radius_xyz_nmm"] == pytest.approx(
            cut_radius, abs=1e-10
        )
        centered = row["positive_internal_wrench_at_finished_area_centroid"]
        assert centered["force_xyz_n"] == pytest.approx(force, abs=1e-10)
        assert centered["moment_about_datum_xyz_nmm"] == pytest.approx(
            centroid_moment, abs=1e-10
        )
        assert centered["moment_rounding_radius_xyz_nmm"] == pytest.approx(
            centroid_radius, abs=1e-10
        )
        local = row["positive_local_wrench_at_finished_area_centroid"]
        assert local["force_N_Vu_Vv_n"] == pytest.approx(
            dict(zip(("N", "Vu", "Vv"), force))
        )
        assert local["moment_T_Mu_Mv_nmm"] == pytest.approx(
            dict(zip(("T", "Mu", "Mv"), centroid_moment))
        )
    negative = traces["approached_from_positive_station"][
        "negative_internal_wrench_at_finished_area_centroid"
    ]
    assert negative["force_xyz_n"] == [0, -1, 0]
    assert negative["moment_about_datum_xyz_nmm"] == [10, 0, 0]
    for plane in first["planes"]:
        section = plane["finished_section"]
        assert section["common_strain_or_component_load_sharing_established"] is False
        assert section["actual_integrated_traction_established"] is False
        assert section["section_resistance_accepted"] is False
    for key in (
        "actual_traction",
        "common_strain",
        "per_ligament_force_sharing",
        "adopted_resistance",
        "criterion_pass",
        "joint_accepted",
        "native_solve",
        "geometry_changed",
    ):
        assert first["claim_limits"][key] is False


@pytest.mark.parametrize("failure", ["source_gate", "frame", "step"])
def test_synthetic_producer_refuses_corrupt_gate_frame_or_step(
    failure, tmp_path, monkeypatch
):
    fixture = build_fixture(tmp_path, monkeypatch)
    root = fixture["root"]
    freeze_path = producer.FREEZE
    freeze = json.loads(freeze_path.read_text())

    if failure == "source_gate":
        case = "a1-rear"
        response_pin = freeze["cases"][case]["response"]
        response_path = root / response_pin["path"]
        response = json.loads(response_path.read_text())
        response["increments"][0][producer.GATES[0]] = False
        write_json(response_path, response)
        refresh_freeze_pin(fixture, monkeypatch)
        expected_message = "source response gate failed"
    elif failure == "frame":
        case = "a1-rear"
        model_pin = freeze["cases"][case]["model"]
        model_path = root / model_pin["path"]
        model = json.loads(model_path.read_text())
        model["body_geometry"][producer.CLEAT]["geometry_record"]["axis"] = [
            2.0,
            0.0,
            0.0,
        ]
        write_json(model_path, model)
        refresh_freeze_pin(fixture, monkeypatch)
        expected_message = "source model frame is not orthonormal"
    else:
        member = producer.CLEAT
        step_path = root / fixture["bindings"][member]["path"]
        step_path.write_bytes(b"changed synthetic STEP\n")
        expected_message = "finished STEP changed"

    with pytest.raises(ValueError, match=expected_message):
        producer.produce()
