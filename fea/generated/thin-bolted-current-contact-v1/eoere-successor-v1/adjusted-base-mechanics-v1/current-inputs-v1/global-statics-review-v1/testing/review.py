"""Independent current source statics testing; no frame, CAD or browser work."""
from __future__ import annotations

import copy
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGET = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-inputs-v1/global-statics-v1"
EXPECTED = {
    "check_current.py": "c2c32d1fdadae374b5d7f7d192d979e52954011bc041171980cc6e63a0aeceaa",
    "verify.py": "68e27a587cadc08b64923cbe76fdf5db36c35ca0cca6d8789ac3f3b44be7862d",
    "result.json": "f05f81d17a80b1fc1e2a0df106a60ac34f6253a1bb0b664a7241e63cc3702c24",
    "verification.json": "2278f49ebd516bb3cc10fc1fffa53bdda989008c66429eeb4e55c2952404b203",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def require_close(a, b, tolerance=1e-8):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tolerance, (a, b)
    return abs(a-b)


def hull(points):
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    ordered = sorted(set(tuple(p[:2]) for p in points))
    sides = []
    for vertices in (ordered, list(reversed(ordered))):
        chain = []
        for vertex in vertices:
            while len(chain) > 1 and cross(chain[-2], chain[-1], vertex) <= 0:
                chain.pop()
            chain.append(vertex)
        sides.append(chain[:-1])
    return sides[0]+sides[1]


def rejects(fn):
    try:
        fn()
    except (ValueError, FileExistsError, KeyError):
        return
    raise AssertionError("controlled invalid input was accepted")


def main():
    assert not (OWN/"receipt.json").exists(), "do not overwrite a review receipt"
    assert {n: sha(TARGET/n) for n in EXPECTED} == EXPECTED
    record, verification = read(TARGET/"result.json"), read(TARGET/"verification.json")
    pins = record["source_bindings"]
    assert len(pins) == 8
    for path, expected in pins.items():
        assert sha(ROOT/path) == expected, path
    assert len(verification["source_bindings"]) == 10
    for path, expected in verification["source_bindings"].items():
        assert sha(ROOT/path) == expected, path
    current, producer_verify = module(TARGET/"check_current.py", "testing_current_statics"), module(TARGET/"verify.py", "testing_statics_verifier")
    data, old = read(ROOT/current.CURRENT), read(ROOT/current.OLD_INPUT)
    cache = read(ROOT/data["geometry"]["cached_source_export"]["path"])
    assert record["input_recursive_pin_count_declared_not_independently_rehashed_here"] == len(data["source_sha256"]) == 1086
    assert record["input_readiness_preserved"] == data["readiness"] == {"complete_reference_contact_inventory": False, "source_joins_independently_reviewed": False}
    assert record["input_status_preserved"] == data["status"] == "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW"
    points, changes, mass = current.validate(data, old, cache)
    assert points == record["support_point_order"] and len(points) == 32
    assert len(changes) == 4 and changes == record["legacy_footprint_comparison"]["changed_points"]
    assert record["legacy_footprint_comparison"]["identical_point_count"] == 28
    assert all(c["host"] == "base_post_center_right" for c in changes)
    for change in changes:
        for actual, expected in zip(change["delta_xyz_mm"], [-39.2, 0, 0], strict=True):
            require_close(actual, expected, 1e-12)
    xy = [p["point_xyz_mm"] for p in points]
    polygon = hull(xy)
    assert len(polygon) == 6
    assert polygon == hull([p for host in sorted(old["floor_footprints"]) for p in old["floor_footprints"][host]])
    independent = []
    max_force = max_moment = max_witness = 0.0
    for source, result in zip(data["cases"], record["cases"], strict=True):
        assert source["case_id"] == result["case_id"]
        with localcontext() as context:
            context.prec = 55
            force, moment = [Decimal(0)]*3, [Decimal(0)]*3
            for row in source["loads"]:
                p = list(map(lambda v: Decimal(str(v)), row["point_xyz_mm"]))
                f = list(map(lambda v: Decimal(str(v)), row["force_xyz_n"]))
                for i in range(3):
                    force[i] += f[i]
                    j, k = (i+1)%3, (i+2)%3
                    moment[i] += p[j]*f[k]-p[k]*f[j]
        force, moment = list(map(float, force)), list(map(float, moment))
        for a, b in zip(force, result["applied_force_xyz_n"], strict=True):
            max_force = max(max_force, require_close(a, b))
        for a, b in zip(moment, result["applied_moment_xyz_nmm"], strict=True):
            max_moment = max(max_moment, require_close(a, b, 1e-6))
        weight = -force[2]
        assert weight > 0
        cop = [moment[1]/weight, -moment[0]/weight]
        for a, b in zip(cop, result["required_center_of_pressure_xy_mm"], strict=True):
            require_close(a, b)
        distances = []
        for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
            dx, dy = b[0]-a[0], b[1]-a[1]
            distances.append((dx*(cop[1]-a[1])-dy*(cop[0]-a[0]))/math.hypot(dx, dy))
        margin = min(distances)
        require_close(margin, result["minimum_support_polygon_edge_margin_mm"], 1e-9)
        assert margin > 0 and result["compression_equilibrium_possible"] is True
        witness = result["normal_reaction_witness_n"]
        assert len(witness) == 32 and all(math.isfinite(n) and n >= 0 for n in witness)
        residual = [math.fsum(witness)-weight, math.fsum(p[1]*n for p, n in zip(xy, witness, strict=True))+moment[0], -math.fsum(p[0]*n for p, n in zip(xy, witness, strict=True))+moment[1]]
        for r in residual:
            max_witness = max(max_witness, require_close(r, 0, 1e-4))
        assert result["elastic_joint_demands_or_floor_capacity_established"] is False
        independent.append({"case_id": source["case_id"], "edge_margin_mm": margin, "load_count": len(source["loads"])})
    require_close(mass["total_kg"], 219.11593970030577, 1e-10)
    require_close(min(r["edge_margin_mm"] for r in independent), 330.28499147990897, 1e-9)
    assert all(v is False for v in record["release"].values())
    assert record["no_frame_or_native_solve_or_CAD"] is True

    # Exercise semantic rejection branches beyond the frozen byte gates.
    core = {k: data[k] for k in ("schema", "optional_2026_extra", "historical_q", "old_field", "release", "floor_footprints", "cases", "parameters", "gravity")}
    mutations = {
        "wrong_schema": lambda d, c: d.update(schema="old/v1"),
        "extra_grid": lambda d, c: d.update(optional_2026_extra=True),
        "historical_q": lambda d, c: d.update(historical_q=[]),
        "old_field": lambda d, c: d.update(old_field={}),
        "release": lambda d, c: d["release"].update(climbing_released=True),
        "missing_footprint": lambda d, c: d["floor_footprints"].pop("base_floor_left"),
        "observation_mismatch": lambda d, c: c["floor_observations"][0]["observed_normal_reference_points_xyz_mm"][0].__setitem__(0, 999),
        "unconfirmed_floor_face": lambda d, c: c["floor_observations"][0].update(own_floor_face_confirmed_from_current_cached_solid=False),
        "case_order": lambda d, c: d["cases"].reverse(),
        "gravity_hold": lambda d, c: d["cases"][-1].update(hold={}),
        "gravity_load_census": lambda d, c: d["cases"][-1]["loads"].pop(),
        "duplicate_load_id": lambda d, c: d["cases"][0]["loads"][0].update(id=d["cases"][0]["loads"][1]["id"]),
        "nonfinite_load_point": lambda d, c: d["cases"][0]["loads"][0]["point_xyz_mm"].__setitem__(0, float("nan")),
        "boolean_force": lambda d, c: d["cases"][0]["loads"][0]["force_xyz_n"].__setitem__(0, True),
        "mismatched_climber": lambda d, c: d["cases"][0]["hold"]["force_xyz_n"].__setitem__(1, 301),
        "wrong_gravity": lambda d, c: d["parameters"].update(gravity_m_s2=10),
        "wrong_mass": lambda d, c: d["gravity"].update(known_modeled_mass_kg=0),
    }
    semantic_controls = []
    for name, mutate in mutations.items():
        d, c = copy.deepcopy(core), copy.deepcopy({"floor_observations": cache["floor_observations"]})
        mutate(d, c)
        rejects(lambda: current.validate(d, old, c))
        semantic_controls.append(name)
    for bad in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'):
        rejects(lambda: current.strict_json(bad))

    corruptions = {
        "force": lambda r: r["cases"][0]["applied_force_xyz_n"].__setitem__(2, 0),
        "moment": lambda r: r["cases"][0]["applied_moment_xyz_nmm"].__setitem__(0, 0),
        "cop": lambda r: r["cases"][0]["required_center_of_pressure_xy_mm"].__setitem__(0, 0),
        "margin": lambda r: r["cases"][0].update(minimum_support_polygon_edge_margin_mm=0),
        "feasibility": lambda r: r["cases"][0].update(compression_equilibrium_possible=False),
        "hull": lambda r: r["cases"][0]["support_polygon_xy_mm"][0].__setitem__(0, 0),
        "negative_witness": lambda r: r["cases"][0]["normal_reaction_witness_n"].__setitem__(0, -1),
        "nonclosing_witness": lambda r: r["cases"][0]["normal_reaction_witness_n"].__setitem__(0, 1),
        "friction": lambda r: r["cases"][0].update(minimum_aggregate_friction_ratio_ignoring_yaw_and_distribution=1),
        "yaw": lambda r: r["cases"][0].update(required_reaction_yaw_moment_nmm=0),
        "elastic_claim": lambda r: r["cases"][0].update(elastic_joint_demands_or_floor_capacity_established=True),
        "summary": lambda r: r["summary"].update(compression_feasible_case_count=6),
        "governing_case": lambda r: r["summary"].update(minimum_edge_margin_case="gravity-only"),
        "readiness": lambda r: r["input_readiness_preserved"].update(source_joins_independently_reviewed=True),
        "release": lambda r: r["release"].update(climbing_released=True),
        "mass": lambda r: r["mass"].update(total_kg=0),
    }
    for mutate in corruptions.values():
        damaged = copy.deepcopy(record)
        mutate(damaged)
        rejects(lambda: producer_verify.numerical(damaged))

    method = module(ROOT/current.METHOD, "testing_frozen_support_method")
    assert method.fixtures() == {"passed": True, "known_answer_fixture_count": 7}
    corners = [[-1000, -1000, 0], [-1000, 1000, 0], [1000, -1000, 0], [1000, 1000, 0]]
    def assess(point, force, supports=corners):
        return method.assess(supports, [{"point_xyz_mm": point, "force_xyz_n": force}])
    additional_fixtures = []
    for name, point, force, expected_cop, feasible in [
        ("vertex", [1000, 1000, 0], [0, 0, -100], [1000, 1000], True),
        ("outside_corner", [1001, 1001, 0], [0, 0, -100], [1001, 1001], False),
        ("inside_edge", [999.999, 0, 0], [0, 0, -100], [999.999, 0], True),
        ("outside_edge", [1000.001, 0, 0], [0, 0, -100], [1000.001, 0], False),
        ("opposite_horizontal_signs", [0, 0, 1000], [10, -20, -100], [100, -200], True),
    ]:
        answer = assess(point, force)
        assert answer["compression_equilibrium_possible"] is feasible
        for a, b in zip(answer["required_center_of_pressure_xy_mm"], expected_cop, strict=True):
            require_close(a, b)
        additional_fixtures.append(name)
    duplicate = assess([0, 0, 0], [0, 0, -100], corners+[corners[0], [0, 0, 0]])
    assert duplicate["compression_equilibrium_possible"] and duplicate["minimum_support_polygon_edge_margin_mm"] == 1000
    additional_fixtures.append("duplicate_and_interior_supports")
    assert assess([0, 0, 0], [0, 0, 0])["compression_equilibrium_possible"] is False
    additional_fixtures.append("zero_downward_resultant")
    rejects(lambda: assess([0, 0, 0], [0, float("nan"), -100]))
    rejects(lambda: assess([0, 0, 0], [0, 0, -100], [[-1000, -1000, .001], *corners[1:]]))
    rejects(lambda: assess([0, 0, 0], [0, 0, -100], [[float("nan"), -1000, 0], *corners[1:]]))
    additional_fixtures.extend(["nonfinite_force_rejected", "off_plane_rejected", "nonfinite_support_rejected"])

    with tempfile.TemporaryDirectory(prefix="source-only-", dir=OWN) as temp:
        temp = Path(temp)
        # Reuse the frozen verifier to execute its seven exact CLI/drift/race controls.
        process = subprocess.run([sys.executable, "-B", str(TARGET/"verify.py"), "--out", str(temp/"verification")], cwd=ROOT, capture_output=True, text=True, timeout=120, check=False)
        assert process.returncode == 0, process.stderr
        fresh = read(temp/"verification/receipt.json")
        assert fresh == verification
        producer_controls = [r["name"] for r in fresh["controls"]]
        # Early rejection must occur before any source parsing or method execution.
        existing = temp/"occupied.json"
        existing.write_bytes(b"keep\n")
        original_validate = current.validate
        current.validate = lambda *args: (_ for _ in ()).throw(AssertionError("validation reached after occupied-output rejection"))
        rejects(lambda: current.run(temp/"missing-input", existing))
        assert existing.read_bytes() == b"keep\n"
        current.validate = original_validate
        # Exact malformed source byte rejection occurs before semantic validation/work.
        bad = temp/"bad.json"
        bad.write_bytes(b"{}\n")
        rejects(lambda: current.run(bad, temp/"absent.json"))
        assert not (temp/"absent.json").exists()
        ruff = subprocess.run([str(ROOT/".venv/bin/ruff"), "check", "--no-cache", str(TARGET/"check_current.py"), str(TARGET/"verify.py")], cwd=ROOT, capture_output=True, text=True, check=False)
        assert ruff.returncode == 0, ruff.stdout+ruff.stderr
    assert {n: sha(TARGET/n) for n in EXPECTED} == EXPECTED
    for path, expected in verification["source_bindings"].items():
        assert sha(ROOT/path) == expected, path
    receipt = {
        "schema": "eoere_current_global_statics_testing_review/v1", "passed": True, "substantial_findings": [],
        "target": {"path": str(TARGET.relative_to(ROOT)), "sha256": EXPECTED}, "reviewer_sha256": sha(__file__),
        "direct_sources": {"count": 8, "before_and_after": True, "bindings": pins},
        "independent_scalar_checks": {"cases": independent, "support_points": 32, "hull_vertices": 6, "old_points_unchanged": 28, "four_right_center_post_x_shifts_mm": -39.2, "mass_kg": mass["total_kg"], "max_force_error_n": max_force, "max_moment_error_nmm": max_moment, "max_witness_residual_n_or_nmm": max_witness},
        "semantic_rejection_controls": semantic_controls, "nonfinite_json_controls": 3,
        "tampered_report_numerical_rejections": list(corruptions), "preserved_method_fixtures_rerun": 7,
        "additional_small_method_fixtures": additional_fixtures, "producer_verification_rerun": {"exact_receipt_replay": True, "controls": producer_controls},
        "early_occupied_output_rejection_and_bad_source_no_output": True, "ruff_two_frozen_helpers_no_cache": True,
        "unchanged": {"target_four_files": True, "ten_verifier_bound_files": True},
        "limits": ["Eight direct source pins are authenticated; the declared1086 recursive input pins are not readmitted by this statics review.", "Current source inputs and frame-method admission remain pending; both readiness flags stay false.", "Nonnegative normal reactions prove only equilibrium possibility; no compatible elastic distribution, joint demands/capacity, friction/floor capacity, or actual weight is established.", "No historical response was used, and no frame/native/CAD/BREP/browser execution, model edit, shared write, staging or commit was performed."],
        "release": record["release"],
    }
    with (OWN/"receipt.json").open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"passed": True, "findings": 0, "receipt_sha256": sha(OWN/"receipt.json")}))


if __name__ == "__main__":
    main()
