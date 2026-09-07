"""Portable selected-input replay; no solver outcome or moving qualification."""
import gzip
import json
from pathlib import Path

import pytest

from fea import hardware_mass_cache as mass
from fea import moving_hardware_control as control
from fea.publish_moving_fixture import checked_members
from fea.results.stitch_joint_mesh.publisher import sha

ARCHIVE = Path(__file__).resolve().parents[1] / "fea/results/coarse_moving_control/preparation.tar.gz"
ARCHIVE_SHA = "053d6c06995cb76c666ec8eae85178be299747db96cadd220cabc8355bb5c9d1"
QUIET_SHA = "0149053d26aa67e1c5f2d22de7e9b1e058d24f7188ef02324fe3cc6508bb86ea"


@pytest.fixture(scope="module")
def files():
    return checked_members(ARCHIVE, ARCHIVE_SHA)


def hashes(files, prefix, inventory):
    assert all(sha(files[prefix + name]) == expected for name, expected in inventory.items())


def test_selected_preparation_and_frozen_launch_are_exact(files):
    refs = json.loads(files["references.json"])
    assert refs["selected_commit"] == "bd17eac78586d51b8d74945b12f7395671930198"
    assert refs["prepared_directory"] == "fea/generated/moving-hardware-events/moving-event-tnev6k3a"
    assert refs["mass_directory"] == "fea/generated/hardware-mass-caches/mass-cache-c4qwd4l5"
    assert refs["solve_directory"] == "fea/generated/moving-hardware-solves/moving-9gsvcbgg"
    assert refs["posed_quiet_archive"] == "fea/results/posed_hardware_control/posed-quiet.tar.gz"
    assert refs["posed_quiet_archive_sha256"] == QUIET_SHA
    assert sha(files["prepared/frozen/posed-quiet.tar.gz"]) == QUIET_SHA
    assert {n.split("/")[0] for n in files} == {"prepared", "mass", "solve", "members.json", "references.json"}
    assert not any(n.startswith("solve/result/") or n == "solve/launch.json" for n in files)
    prepared = json.loads(files["prepared/freeze.json"])["files_sha256"]
    assert set(prepared) == {n.removeprefix("prepared/") for n in files if n.startswith("prepared/")} - {"freeze.json"}
    hashes(files, "prepared/", prepared)
    context = json.loads(files["prepared/context.json"])
    for group in ("input_sha256", "source_sha256"):
        hashes(files, "prepared/frozen/", context[group])
        assert all(prepared["frozen/" + n] == h for n, h in context[group].items())
    assert context["cases"] == {"moving": {"initial_dt_s": 1e-7, "total_time_s": 2e-5,
        "maximum_increment_count": 200, "alpha": 0., "direct_moving": True,
        "initial_velocity_mm_s": {"BOLT_NUT": [0., 0., 0.], "WASHER": [-100., 100., 0.]}}}
    assert context["angular_reference_mm_local"] == [1.001, .7356, 0.]
    assert context["passed_quiet_evidence"]["archive_sha256"] == QUIET_SHA
    assert context["integration_intent"]["expected_fixed_increment_count"] == 200
    assert context["moving_protocol"]["solver_timeout_seconds"] == 1800
    assert context["moving_protocol"]["outer_timeout_seconds"] == 1820
    assert files["prepared/moving.inp"] == control.deck(context, "moving").encode()
    assert sha(files["prepared/moving.inp"]) == context["deck_sha256"]["moving"]
    assert "prepared/quiescent.inp" not in files
    freeze = json.loads(files["solve/freeze.json"])
    assert freeze["case"] == "moving" and freeze["solver_timeout_seconds"] == 1800
    assert freeze["image"] == "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
    assert set(freeze["inputs_sha256"]) == {n.removeprefix("solve/frozen/") for n in files if n.startswith("solve/frozen/")}
    hashes(files, "solve/frozen/", freeze["inputs_sha256"])
    assert files["solve/frozen/context.json"] == files["prepared/context.json"]
    assert files["solve/frozen/control.inp"] == files["prepared/moving.inp"]
    assert files["solve/frozen/prepared-freeze.json"] == files["prepared/freeze.json"]
    approval = json.loads(files["solve/frozen/moving-preflight.json"])
    assert approval["inputs_sha256"] == {n: h for n, h in freeze["inputs_sha256"].items() if n != "moving-preflight.json"}
    assert approval["case"] == "moving" and approval["passed_quiet_archive_sha256"] == QUIET_SHA
    for key, name in (("context_sha256", "context.json"), ("deck_sha256", "control.inp"),
                      ("prepared_freeze_sha256", "prepared-freeze.json"),
                      ("mass_report_sha256", "mass/report.json"), ("mass_blocks_sha256", "mass/blocks.json.gz")):
        assert approval[key] == sha(files["solve/frozen/" + name])
    assert approval["evaluator_sha256"] == {"evaluators/" + n + ".snapshot": h for n, h in context["source_sha256"].items()}
    hashes(files, "solve/frozen/", approval["evaluator_sha256"])
    assert all(context["audit_source_sha256"][n] == context["source_sha256"][n] for n in context["audit_source_sha256"])
    for name in context["source_sha256"]:
        assert files["solve/frozen/evaluators/" + name + ".snapshot"] == files["prepared/frozen/" + name]
    assert files["solve/frozen/moving_hardware_solve.py"] == files["prepared/frozen/moving_hardware_solve.py"]
    assert b'"--memory=4g", "--memory-swap=4g", "--cpus=2"' in files["solve/frozen/moving_hardware_solve.py"]


def test_full_selected_mass_operators_and_reference_scales(files):
    data = files["prepared/context.json"]
    context = json.loads(data)
    names = {n.removeprefix("mass/") for n in files if n.startswith("mass/")}
    assert names == {"context.json", "moving.inp", "prepared-freeze.json", "report.json", "blocks.json.gz",
                     "hardware_mass_cache.py.snapshot", "dynamic_momentum.py.snapshot"}
    assert all(files["mass/" + n] == files["solve/frozen/mass/" + n] for n in names)
    assert files["mass/context.json"] == data
    assert files["mass/moving.inp"] == files["prepared/moving.inp"]
    assert files["mass/prepared-freeze.json"] == files["prepared/freeze.json"]
    report = json.loads(files["mass/report.json"])
    assert report["case"] == "moving" and report["context_sha256"] == sha(data)
    assert report["deck_sha256"] == sha(files["prepared/moving.inp"])
    assert report["prepared_freeze_sha256"] == sha(files["prepared/freeze.json"])
    assert report["blocks_sha256"] == sha(files["mass/blocks.json.gz"])
    assert set(report["source_sha256"]) == {"hardware_mass_cache.py", "dynamic_momentum.py"}
    hashes(files, "mass/", {n + ".snapshot": h for n, h in report["source_sha256"].items()})
    assert all(files["mass/" + n + ".snapshot"] == files["prepared/frozen/" + n] for n in report["source_sha256"])
    cache = json.loads(gzip.decompress(files["mass/blocks.json.gz"]))
    mass.deck_mesh(files["mass/moving.inp"].decode(), context)
    totals = mass.validate_cache(cache, data)
    assert totals == report["body_mass_tonne"] and cache["gmsh_version"] == report["gmsh_version"]
    assert set(totals) == {"native_four_point", "physical_Gauss8"}
    reference = context["diagnostic_reference_scales"]
    washer = totals["native_four_point"]["WASHER"]
    for key, expected in (("reference_mass_tonne", washer), ("P_star_tonne_mm_s", washer*20000**.5),
                          ("E_star_N_mm", washer*10000), ("H_star_tonne_mm2_s", 57.15*washer*20000**.5)):
        assert reference[key] == pytest.approx(expected, rel=1e-12, abs=0)
