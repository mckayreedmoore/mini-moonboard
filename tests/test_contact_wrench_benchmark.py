import json
import math

import pytest

import fea.contact_wrench_benchmark as benchmark
from fea.contact_wrench_benchmark import (
    ARTIFACT_DIR,
    SCENARIOS,
    _cross,
    _dot_deck,
    audit_data,
    audit_run,
    expected_wrench,
    load_manifest,
    parse_contact_reports,
    prepared_record,
)


def _deck(scenario):
    name = "upper-slave.inp" if scenario == "upper_slave" else "lower-slave.inp"
    return (ARTIFACT_DIR / name).read_text()


def _section(deck, keyword):
    lines = deck.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().upper() == keyword)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("*")),
        len(lines),
    )
    return [line.strip() for line in lines[start + 1 : end] if line.strip() and not line.lstrip().startswith("**")]


def _top_load_wrench(deck):
    coordinates = {}
    for row in _section(deck, "*NODE"):
        fields = [part.strip() for part in row.split(",")]
        coordinates[int(fields[0])] = tuple(float(v) for v in fields[1:4])
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    for row in _section(deck, "*CLOAD"):
        node, dof, value = (float(part.strip()) for part in row.split(","))
        assert int(dof) == 3
        x, y, _ = coordinates[int(node)]
        force[2] += value
        moment[0] += y * value
        moment[1] -= x * value
    return tuple(force), tuple(moment)


def _report(scenario, *, time="0.1000000E+01", overrides=None, override_quantity="CF"):
    contract = expected_wrench(scenario)
    blocks = []
    for quantity in ("CF", "CFN", "CFS"):
        if quantity == "CF":
            force = contract["expected_cf_force_n"]
            origin_moment = contract["expected_cf_moment_global_origin_nmm"]
            centroid_moment = contract["expected_cf_moment_at_contact_centroid_nmm"]
            normal_force, shear = -100.0, 0.0
        elif quantity == "CFN":
            force = contract["expected_cfn_force_n"]
            origin_moment = contract["expected_cfn_moment_global_origin_nmm"]
            centroid_moment = contract["expected_cf_moment_at_contact_centroid_nmm"]
            normal_force, shear = -100.0, 0.0
        else:
            force = contract["expected_cfs_force_n"]
            origin_moment = contract["expected_cfs_moment_global_origin_nmm"]
            centroid_moment = [0.0, 0.0, 0.0]
            normal_force, shear = 0.0, 0.0
        values = {
            "force": force,
            "origin_moment": origin_moment,
            "centroid": [10.0, 10.0, -0.002525938],
            "normal": [0.0, 0.0, -1.0 if scenario == "upper_slave" else 1.0],
            "centroid_moment": centroid_moment,
            "area": 400.0,
            "normal_force": normal_force,
            "shear": shear,
        }
        if quantity == override_quantity:
            values.update(overrides or {})
        blocks.append(f"""
 statistics for slave set {contract['slave_surface']}, master set {contract['master_surface']} and time {time}

   total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)

   {' '.join(str(v) for v in values['force'] + values['origin_moment'])}

   center of gravity and mean normal

   {' '.join(str(v) for v in values['centroid'] + values['normal'])}

   moment about the center of gravity(mx,my,mz)

   {' '.join(str(v) for v in values['centroid_moment'])}

   area,  normal force (+ = tension) and shear force (size)

   {values['area']} {values['normal_force']} {values['shear']}
""")
    return "\n".join(blocks)


def _nodal_output(*, bottom_z=(25.0, 25.0, 25.0, 25.0)):
    lines = [
        " displacements (vx,vy,vz) for set TOP and time 0.1000000E+01",
        "",
        " 15 0 0 -0.005026876",
        " 16 0 0 -0.005026876",
        " 17 0 0 -0.005026876",
        " 18 0 0 -0.005026876",
        "",
        " forces (fx,fy,fz) for set TOP and time 0.1000000E+01",
        "",
        " 15 0 0 -25",
        " 16 0 0 -25",
        " 17 0 0 -25",
        " 18 0 0 -25",
        "",
        " forces (fx,fy,fz) for set BOTTOM and time 0.1000000E+01",
        "",
    ]
    for node, z_force in zip((1, 2, 3, 4), bottom_z, strict=True):
        lines.append(f" {node} 0 0 {z_force}")
    return "\n".join(lines) + "\n"


def _data(scenario, *, overrides=None, override_quantity="CF", bottom_z=(25.0, 25.0, 25.0, 25.0)):
    return _nodal_output(bottom_z=bottom_z) + _report(
        scenario, overrides=overrides, override_quantity=override_quantity
    )


def test_source_inventory_manual_and_component_order_are_pinned():
    manifest = load_manifest()
    assert manifest["manual"] == {
        "title": "CalculiX 2.21 User's Manual",
        "url": "https://www.dhondt.de/ccx_2.21.pdf",
        "contact_print_pages": [430, 431],
    }
    assert set(manifest["source_files_sha256"]) == {
        "fea/contact_wrench_benchmark.py",
        "fea/results/ccx_contact_wrench_benchmark/upper-slave.inp",
        "fea/results/ccx_contact_wrench_benchmark/lower-slave.inp",
    }
    assert manifest["solver"] == {"product": "CalculiX CrunchiX", "version": "2.21"}
    assert manifest["solver_completion_contract"]["contact_report_quantity_order"] == ["CF", "CFN", "CFS"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_generated_deck_matches_frozen_source_and_side_contract(scenario):
    contract = expected_wrench(scenario)
    deck = _deck(scenario)
    assert deck == _dot_deck(scenario)
    assert contract["expected_contact_area_mm2"] == 400.0
    assert contract["expected_cf_force_n"][2] == (100.0 if scenario == "upper_slave" else -100.0)
    assert contract["expected_cfn_force_n"] == contract["expected_cf_force_n"]
    assert contract["expected_cfs_force_n"] == [0.0, 0.0, 0.0]
    assert contract["expected_cfn_compression_magnitude_n"] == 100.0
    assert contract["expected_cfs_shear_magnitude_n"] == 0.0
    assert contract["cf_owner_body"] == ("UPPER" if scenario == "upper_slave" else "LOWER")
    assert _top_load_wrench(deck) == ((0.0, 0.0, -100.0), (-1000.0, 1000.0, 0.0))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_analytic_moment_shift_to_contact_centroid(scenario):
    contract = expected_wrench(scenario)
    force = tuple(contract["expected_cf_force_n"])
    moment = tuple(contract["expected_cf_moment_global_origin_nmm"])
    centroid = tuple(contract["expected_contact_centroid_xyz_mm"])
    delta = tuple(-value for value in centroid)
    shifted = tuple(a + b for a, b in zip(moment, _cross(delta, force), strict=True))
    assert shifted == pytest.approx(contract["expected_cf_moment_at_contact_centroid_nmm"], abs=1e-12)
    assert centroid == (10.0, 10.0, 0.0)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_deck_reports_named_slave_and_master_on_face_to_face_pair(scenario):
    deck = _deck(scenario)
    contract = expected_wrench(scenario)
    pair = f"{contract['slave_surface']},{contract['master_surface']}"
    assert "*CONTACT PAIR,INTERACTION=FRICTIONLESS,TYPE=SURFACE TO SURFACE" in deck
    assert pair in deck
    assert (
        f"*CONTACT PRINT,SLAVE={contract['slave_surface']},"
        f"MASTER={contract['master_surface']},FREQUENCY=1\nCF,CFN,CFS"
    ) in deck
    assert "*FRICTION" not in deck
    assert "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR" in deck
    assert "not joint stiffness or resistance" in load_manifest()["fixture"]["contact_penalty_notice"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_same_time_report_group_is_retained_and_audited_by_request_order(scenario):
    reports = parse_contact_reports(_report(scenario))
    assert [report["quantity"] for report in reports] == ["CF", "CFN", "CFS"]
    assert len({report["time"] for report in reports}) == 1
    result = audit_data(_data(scenario), scenario)
    assert result["status"] == "DAT_CONTACT_AND_FIXTURE_BALANCE_PASS_ONLY_NOT_JOINT_CAPACITY"
    assert result["dat_output_audited"] is True
    assert result["contact_report_count"] == 3
    assert result["contact_components"]["CF"]["force_n"][2] == (100.0 if scenario == "upper_slave" else -100.0)
    assert result["contact_components"]["CFN"]["force_n"] == result["contact_components"]["CF"]["force_n"]
    assert result["contact_components"]["CFS"]["force_n"] == [0.0, 0.0, 0.0]
    assert result["contact_centroid_xyz_mm"][:2] == [10.0, 10.0]
    assert -0.003 <= result["contact_centroid_xyz_mm"][2] <= 0.0001
    assert result["fixture_global_balance"]["global_force_residual_n"] == pytest.approx([0.0, 0.0, 0.0], abs=1e-12)
    assert result["fixture_global_balance"]["global_moment_residual_nmm"] == pytest.approx([0.0, 0.0, 0.0], abs=1e-12)


@pytest.mark.parametrize(
    "overrides,quantity",
    [
        ({"force": [0.0, 0.0, -100.0]}, "CF"),
        ({"origin_moment": [0.0, 0.0, 0.0]}, "CF"),
        ({"centroid": [11.0, 10.0, 0.0]}, "CF"),
        ({"centroid": [10.0, 10.0, -0.01]}, "CF"),
        ({"centroid_moment": [1.0, 0.0, 0.0]}, "CF"),
        ({"area": 399.0}, "CF"),
        ({"normal_force": 100.0}, "CF"),
        ({"shear": 0.1}, "CF"),
        ({"force": [0.0, 0.0, 1.0]}, "CFS"),
    ],
)
def test_audit_rejects_wrong_contact_component_or_location(overrides, quantity):
    with pytest.raises(ValueError):
        audit_data(_data("upper_slave", overrides=overrides, override_quantity=quantity), "upper_slave")


def test_audit_rejects_missing_or_reordered_contact_component_blocks():
    report_blocks = _report("upper_slave").split("\n statistics for slave set")
    with pytest.raises(ValueError, match="complete CF/CFN/CFS"):
        parse_contact_reports("\n statistics for slave set" + report_blocks[1])
    reordered = "\n statistics for slave set".join(
        [report_blocks[0], report_blocks[3], report_blocks[2], report_blocks[1]]
    )
    with pytest.raises(ValueError):
        audit_data(_nodal_output() + reordered, "upper_slave")


def test_audit_rejects_fixture_support_imbalance():
    with pytest.raises(ValueError, match="support force equilibrium"):
        audit_data(_data("upper_slave", bottom_z=(26.0, 25.0, 25.0, 25.0)), "upper_slave")


def test_audit_rejects_missing_report_fields():
    with pytest.raises(ValueError, match="Expected one"):
        parse_contact_reports("statistics for slave set UPPER_INTERFACE, master set LOWER_INTERFACE and time 1\n")


def _status():
    return """SUMMARY OF JOB INFORMATION
  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME
     1          1     1     2  0.100000E+01  0.100000E+01  0.100000E+01
"""


def test_run_audit_requires_solver_completion_and_native_output_balance():
    result = audit_run(_data("upper_slave"), _status(), "Job finished\n", "upper_slave", 0, _dot_deck("upper_slave"))
    assert result["status"] == "SOLVER_AND_DAT_ACCOUNTING_PASS_ONLY_NOT_JOINT_CAPACITY"
    assert result["solver_completion"]["accepted_increment_count"] == 1
    assert result["solver_completion"]["final_iterations"] == 2
    assert result["solver_completion"]["exit_code"] == 0
    with pytest.raises(ValueError, match="exit code"):
        audit_run(_data("upper_slave"), _status(), "Job finished\n", "upper_slave", 1, _dot_deck("upper_slave"))
    with pytest.raises(ValueError, match="unconverged"):
        audit_run(
            _data("upper_slave"), _status().replace("     1     1     2", "     1     1U    2"),
            "Job finished\n", "upper_slave", 0, _dot_deck("upper_slave"),
        )
    with pytest.raises(ValueError, match="input deck"):
        audit_run(_data("upper_slave"), _status(), "Job finished\n", "upper_slave", 0, _dot_deck("lower_slave"))


@pytest.mark.parametrize("field,value", [("contact_patch", None), ("solver_completion_contract", None), ("fixture", None), ("load", None)])
def test_acceptance_defining_manifest_fields_are_producer_bound(tmp_path, monkeypatch, field, value):
    manifest = json.loads(benchmark.MANIFEST_PATH.read_text())
    if field == "contact_patch":
        manifest[field]["reported_centroid_z_bounds_mm"] = [-99.0, 0.0]
    elif field == "solver_completion_contract":
        manifest[field]["step_end_time"] = 0.5
    elif field == "fixture":
        manifest[field]["elastic_modulus_n_per_mm2"] = 2.0
    else:
        manifest[field]["resultant_force_n"] = [0.0, 0.0, -99.0]
    altered = tmp_path / "altered-manifest.json"
    altered.write_text(json.dumps(manifest))
    monkeypatch.setattr(benchmark, "MANIFEST_PATH", altered)
    with pytest.raises(ValueError, match=f"contract changed: {field}"):
        benchmark.load_manifest(verify_hashes=False)


def test_prepared_run_is_explicitly_unsolved_and_uses_bounded_comparisons():
    record = prepared_record()
    assert record["status"] == "PREPARED_NOT_SOLVED"
    assert record["native_run_performed"] is False
    assert record["not_a_joint_acceptance"] is True
    tolerance = record["result_tolerances"]
    assert tolerance["force_component_abs_n"] == 0.01
    assert tolerance["force_component_relative"] == 1e-4
    assert tolerance["moment_component_abs_nmm"] == 0.1
    assert tolerance["moment_component_relative"] == 1e-4
    assert record["solver_completion_contract"]["maximum_increments"] == 100
    assert record["contact_patch"]["reported_centroid_z_bounds_mm"] == [-0.003, 0.0001]
    assert math.isfinite(record["contact_patch"]["area_mm2"])
    assert json.loads(json.dumps(record, allow_nan=False))["scenarios"].keys() == set(SCENARIOS)
