"""Own seat datums and authenticated portable containment orchestration."""

import copy
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import eoere_current_washer_lands as washer


def seat():
    profile = {"OD_mm": 26., "ID_mm": 11., "source_support_opening_diameter_mm": 10.}
    corner = {"OD_mm": 24., "ID_mm": 12.3, "source_support_opening_diameter_mm": 13.}
    row = {"receiver_kind": "wood", "grain_axis_abs_cos_to_pressure_normal": 0., "host": "wood",
           "capture_id": "bolt/nut", "axis_id": "bolt", "own_support_point_xyz_mm": [10., 20., 30.],
           "nominal_own_hardware_geometry": profile, "USS_catalog_corners_min_thickness": [corner]}
    end = {"id": "bolt/nut", "second": "wood", "axis_id": "bolt", "host_support_point_xyz_mm": [10., 20., 30.],
           "point_xyz_mm": [10., 20., 32.], "end": {"direction_on_shaft_xyz": [0., 0., 1.]}}
    return row, end


@pytest.mark.parametrize("catalog_wider", [False, True])
def test_bounding_annulus_covers_each_profile_without_transferring_contact(catalog_wider):
    row, end = seat()
    if catalog_wider:
        row["USS_catalog_corners_min_thickness"][0].update({"OD_mm": 28., "ID_mm": 20.})
    before = copy.deepcopy((row, end))
    result = washer.seat_geometry(row, end)
    assert result == {"capture_id": "bolt/nut", "axis_id": "bolt", "host": "wood", "point_xyz_mm": [10., 20., 30.],
                      "inward_xyz": [0., 0., -1.], "bounding_OD_mm": 28. if catalog_wider else 26.,
                      "bounding_inner_diameter_mm": 11.,
                      "least_profile_ring_area_mm2": pytest.approx(math.pi/4*(28.**2-20.**2 if catalog_wider else 24.**2-13.**2))}
    assert (row, end) == before


@pytest.mark.parametrize("mutation", ["owner", "axis", "capture", "grain", "outward", "offset", "datum", "bad_annulus"])
def test_seat_rejects_foreign_invalid_or_misaligned_geometry(mutation):
    row, end = seat()
    if mutation == "owner": end["second"] = "other"
    elif mutation == "axis": end["axis_id"] = "other"
    elif mutation == "capture": end["id"] = "other"
    elif mutation == "grain": row["grain_axis_abs_cos_to_pressure_normal"] = .1
    elif mutation == "outward": end["end"]["direction_on_shaft_xyz"] = [0., 0., -1.]
    elif mutation == "offset": end["point_xyz_mm"][0] += 1.
    elif mutation == "datum": row["own_support_point_xyz_mm"][0] += 1.
    else: row["USS_catalog_corners_min_thickness"][0]["ID_mm"] = 30.
    with pytest.raises(ValueError):
        washer.seat_geometry(row, end)


@pytest.mark.parametrize("mutation", [None, "five_cases", "duplicate_state", "field_case", "raw_canonical", "source_drift"])
def test_intake_authenticates_six_own_states_and_all_dependency_bytes(monkeypatch, tmp_path, mutation):
    current = washer.current
    monkeypatch.setattr(current, "ROOT", tmp_path)

    def put(name, value):
        p = tmp_path/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
        return {"path": name, "sha256": current.sha(p)}

    producer = put("producer.py", b"washer producer")
    monkeypatch.setattr(washer, "OWN", tmp_path/producer["path"])
    probe, parent = put("probe.py", b"probe"), put("parent.py", b"parent")
    monkeypatch.setattr(washer, "PROBE", probe)
    monkeypatch.setattr(washer, "PARENT", parent)
    dependency = put("dependency.py", b"dependency")
    bindings, components, raw_refs = [], [], []
    for case in washer.SEQUENCE:
        field = {"case_id": case, "state_id": case+"/own"}
        if mutation == "field_case" and case == washer.SEQUENCE[0]: field["case_id"] = "foreign"
        fref = put(case+"/field.json", field)
        aref = put(case+"/admission.json", {"admitted": True})
        binding = {"case_id": case, "state_id": case+"/own", "field": fref, "admission": aref}
        bindings.append(binding)
        data = {**binding, "raw_field_canonical_sha256": washer.canonical_sha(field)}
        if mutation == "raw_canonical" and case == washer.SEQUENCE[0]: data["raw_field_canonical_sha256"] = "0"*64
        raw_refs.append(put(case+"/components.json", data))
        components.append(copy.deepcopy(binding))
    if mutation == "five_cases":
        bindings.pop(); components.pop(); raw_refs.pop()
    if mutation == "duplicate_state": bindings[1]["state_id"] = bindings[0]["state_id"]
    common = {"case_sequence": washer.SEQUENCE, "geometry_revision": "eoere-raised-kicker-screws-v1",
              "hardware_revision": "eoere-selected-purchase-hardware-v1", "extra_grid": False,
              "geometry": {"id": "current geometry"}, "hardware_model": {"id": "current hardware"}, "release": {"fabrication": False}}
    source_map = {dependency["path"]: dependency["sha256"]}
    union = put("union.json", source_map)
    common["source_union"] = {"record": union, "count": 1, "canonical_sha256": washer.canonical_sha(source_map)}
    force = put("force.json", {**common, "cases": bindings, "all_six_saved_field_admissions_pass": True})
    component = put("component.json", {**common, "cases": components, "current_response": force})
    inputs = put("inputs.json", {"current_response": force, "current_components": component, "case_components": raw_refs})
    monkeypatch.setattr(washer, "INPUTS", inputs)
    monkeypatch.setattr(current, "manifest", lambda: common)
    if mutation == "source_drift": (tmp_path/dependency["path"]).write_bytes(b"changed")
    if mutation:
        with pytest.raises(ValueError): washer.intake()
        return
    result, pins = washer.intake()
    assert [binding["case_id"] for binding, _, _ in result] == washer.SEQUENCE
    assert [field["state_id"] for _, field, _ in result] == [case+"/own" for case in washer.SEQUENCE]
    expected = {dependency["path"]: dependency["sha256"], **{r["path"]: r["sha256"] for r in
                [producer, probe, parent, inputs, force, component, union, *raw_refs]}}
    assert pins == expected


@pytest.mark.parametrize("failure", [None, "partial_land", "post_drift", "wrong_force", "changed_seat"])
def test_run_queries_each_current_seat_once_and_keeps_six_own_forces(monkeypatch, tmp_path, failure):
    current = washer.current
    monkeypatch.setattr(current, "ROOT", tmp_path)
    source = tmp_path/"producer.py"
    source.write_bytes(b"producer")
    monkeypatch.setattr(washer, "OWN", source)
    monkeypatch.setattr(washer, "LOADED_SHA", current.sha(source))
    observations = [{"id": "wood"+str(i), "source": {"path": "wood"+str(i)+".brep", "sha256": f"{i:064x}"},
                     "volume_mm3": 20.+i} for i in range(22)]
    expected_probes = []
    expected_areas = []
    cases = []
    for i, case in enumerate(washer.SEQUENCE):
        ends, rows = [], []
        for j in range(112):
            row, end = seat()
            key, axis = "seat"+str(j), "axis"+str(j)
            host = observations[j % 22]["id"]
            point = [10.+j, 20.+j % 22, 30.]
            row.update({"capture_id": key, "axis_id": axis, "host": host,
                        "own_support_point_xyz_mm": point, "N_n": 1.+10*i+j})
            if j % 3 == 1:
                row["USS_catalog_corners_min_thickness"][0].update({"OD_mm": 28., "ID_mm": 20.})
                outer, inner, area = 28., 11., math.pi/4*(28.**2-20.**2)
            elif j % 3 == 2:
                row["USS_catalog_corners_min_thickness"][0].update({"ID_mm": 8., "source_support_opening_diameter_mm": 9.})
                outer, inner, area = 26., 9., math.pi/4*(24.**2-9.**2)
            else:
                outer, inner, area = 26., 11., math.pi/4*(24.**2-13.**2)
            end.update({"id": key, "axis_id": axis, "second": host, "host_support_point_xyz_mm": point,
                        "point_xyz_mm": [*point[:2], 32.], "compression_n": row["N_n"]})
            if i == 0:
                expected_probes.append((host, point, [0., 0., -1.], outer, inner))
                expected_areas.append(area)
            if failure == "wrong_force" and i == 1 and j == 0: row["N_n"] += 1.
            if failure == "changed_seat" and i == 1 and j == 0: row["nominal_own_hardware_geometry"]["OD_mm"] += 1.
            rows.append(row); ends.append(end)
        ends.extend({"id": "steel"+str(j)} for j in range(88))
        field = {"source_inputs": {"finished_body_observations": observations,
                                   "timber_rows": [{"name": r["id"]} for r in observations],
                                   "shafts": [{"axis_id": "fixed"+str(j)} for j in range(100)]}, "shaft_end_capture_actions": ends}
        rows.extend({"receiver_kind": "steel"} for j in range(88))
        data = {"findings": {"washers": {"all200_own_end_diagnostics": rows}}}
        cases.append(({"case_id": case, "state_id": case+"/own"}, field, data))
    monkeypatch.setattr(washer, "intake", lambda: (cases, {"dependency": "d"*64}))
    verified = []
    def verify(pins):
        verified.append(copy.deepcopy(pins))
        if failure == "post_drift" and len(verified) == 2: raise ValueError("source drift")
    monkeypatch.setattr(current, "verify", verify)
    probes, imports = [], []
    class Shape:
        def __init__(self, host): self.host = host
        def isValid(self): return True
        def Solids(self): return [self]
        def Volume(self): return 20.+int(self.host.removeprefix("wood"))
    def import_brep(path):
        imports.append(path)
        return Shape(Path(path).stem)
    monkeypatch.setitem(sys.modules, "cadquery", SimpleNamespace(Shape=SimpleNamespace(importBrep=import_brep)))
    def probe(shape, point, inward, outer, inner):
        actual = (shape.host, point, inward, outer, inner)
        assert actual == expected_probes[len(probes)]
        probes.append(actual)
        return {"full_modeled_support": failure != "partial_land" or len(probes) != 4}
    method = SimpleNamespace(known_answers=lambda: {"full_gap_clipped_probe_fractions": [1., 0., .5]}, annular_probe=probe)
    monkeypatch.setattr(washer.component, "load", lambda ref, name: method)
    monkeypatch.setattr(current, "manifest", lambda: {"release": {"fabrication": False}})
    if failure in ["post_drift", "wrong_force", "changed_seat"]:
        with pytest.raises(ValueError): washer.run()
        return
    result = washer.run()
    assert [Path(path).stem for path in imports] == [r["id"] for r in observations]
    assert len(probes) == len(result["wood_seats"]) == 112
    assert probes == expected_probes
    assert result["all112_bounding_thin_annuli_inside_modeled_finished_wood"] is (failure != "partial_land")
    assert result["known_answer_checks"]["full_gap_clipped_probe_fractions"] == [1., 0., .5]
    assert verified == [result["source_sha256"], result["source_sha256"]]
    for i, case in enumerate(result["cases"]):
        assert (case["case_id"], case["state_id"]) == (washer.SEQUENCE[i], washer.SEQUENCE[i]+"/own")
        for j, row in enumerate(case["wood_seat_comparisons"]):
            assert row["capture_id"] == "seat"+str(j)
            assert row["own_model_axial_n"] == 1.+10*i+j
            assert row["least_profile_area_uniform_mean_mpa"] == pytest.approx((1.+10*i+j)/expected_areas[j])
            assert row["physical_pressure_couple_or_combined_resistance"] is None
    assert result["complete_hardware_or_wood_resistance"] is None
    assert result["actual_fit_or_contact_observed"] is result["structural_acceptance"] is False
