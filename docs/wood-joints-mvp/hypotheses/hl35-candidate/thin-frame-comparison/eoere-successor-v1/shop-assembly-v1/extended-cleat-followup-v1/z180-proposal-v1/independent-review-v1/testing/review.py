"""Independent source/metadata and inert-only review of the Z180 shop adapter.

No genuine build_outputs call, candidate CSV/SVG write, CAD, native or mechanics.
The issued receipt is immutable; reruns print evidence without replacing it.
"""
from __future__ import annotations

import ast
import builtins
import copy
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
SHOP = OWN.parents[2]
EXPECTED = {
    "adapter.py": "805dd6afe0921cb14f7e24fea4974714de6ee4c94cc50e74daca3b5595c951c2",
    "test_adapter.py": "e243ed889154b21f4f380ee20c6a012cda87f80bc5ffdb1d42240cf11767eddb",
    "inputs.json": "24168aba426c8a3e65035e877b03fc58347a3c00f450980cba9319f4d6e19918",
    "preflight.json": "cd7e28c42e59f41d9fae96378a5cc1cf005a5b04cbc7613db23088fef1a08854",
}
CLOSURE = "9359334ec1453dcd3dc1306a3477d9af2da64a651a258d3e32f12b33d41a20f6"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def ref(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}


def authenticate_targets():
    for name, expected in EXPECTED.items():
        require(sha((SHOP / name).read_bytes()) == expected, "review target changed: " + name)


def verify(pins):
    for path, expected in pins.items():
        with (ROOT / path).open("rb") as handle:
            require(hashlib.file_digest(handle, "sha256").hexdigest() == expected, "source closure changed: " + path)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_error(call, message):
    try:
        call()
    except ValueError as error:
        require(message in str(error), "unexpected refusal: " + str(error))
    else:
        raise AssertionError("missing refusal: " + message)


def check_vector(actual, expected, label, tolerance=2e-6):
    require(len(actual) == len(expected) == 3, "vector dimension: " + label)
    require(all(math.isfinite(x) and math.isclose(x, y, rel_tol=0., abs_tol=tolerance)
                for x, y in zip(actual, expected, strict=True)), "coordinate mismatch: " + label)


def vector(row, prefix, axes="xyz", unit="mm"):
    return [float(row[f"{prefix}_{c}_{unit}"]) for c in axes]


def local(point, profile):
    delta = [x-y for x, y in zip(point, profile["datum_xyz_mm"], strict=True)]
    return [math.fsum(d*c for d, c in zip(delta, basis, strict=True)) for basis in profile["basis_grain_u_v_xyz"]]


def authenticate_closure(bundle):
    """Reconstruct independently rather than trusting adapter.join/verify."""
    inp, data = bundle["inputs"], bundle["data"]
    pins = {str((SHOP / "inputs.json").relative_to(ROOT)): EXPECTED["inputs.json"]}
    refs = [inp["helper"], *inp["sources"].values(), *inp["saved_files"].values(),
            *(p["finished"] for p in data["profiles"].values())]
    entries = [(r["path"], r["sha256"]) for r in refs] + list(data["descriptor"]["source_sha256"].items())
    for path, expected in entries:
        require(path not in pins or pins[path] == expected, "independent conflicting source pin: " + path)
        pins[path] = expected
    require(pins == bundle["pins"] and len(pins) == 1141 and canonical(pins) == CLOSURE, "1141-pin independent closure differs")
    verify(pins)
    return pins


def authentic_metadata(bundle, a):
    """Saved-table/source joins only: no candidate rows or renderings created."""
    data, profiles, axes = bundle["data"], bundle["data"]["profiles"], bundle["old_axes"]
    tables = {name: data[name][1] for name in ("members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv",
              "panel-screw-datums.csv", "panel-machining.csv")}
    for name, rows in tables.items():
        columns = data[name][0]
        require(columns[-2:] == ["Actual", "Disposition"], "saved observation suffix: " + name)
        require(all(set(row) == set(columns) for row in rows), "saved CSV row/column alignment: " + name)
        require(all(v == "" for row in rows for k, v in row.items() if k.startswith("Actual") or k == "Disposition"), "filled observation cell")
    require(len(profiles) == 28 and sum(p["kind"] == "timber" for p in profiles.values()) == 22
            and sum(p["kind"] == "panel" for p in profiles.values()) == 6, "protected profile census")
    used = [name for stick in data["stock"]["sticks"] for name in stick["members"]]
    require(len(data["stock"]["sticks"]) == 13 and data["stock"]["nominal_board_feet"] == 150.
            and len(used) == len(set(used)) == 22 and set(used) == {name for name, p in profiles.items() if p["kind"] == "timber"}, "13-stick/150bf unique timber nesting")
    members = {r["member"]: r for r in tables["members.csv"]}
    require(len(members) == 28 and set(members) == set(profiles), "member identities")
    for name, profile in profiles.items():
        row = members[name]
        check_vector(vector(row, "datum"), profile["datum_xyz_mm"], name)
        for i, label in enumerate("luv"):
            check_vector(vector(row, "basis_"+label, unit="unitless"), profile["basis_grain_u_v_xyz"][i], name)
        require(row["profile_source"] == "current_profiles.json#/"+name, "own profile pointer")
        require(row["current_finished_source_path"] == profile["finished"]["path"]
                and row["current_finished_source_sha256"] == profile["finished"]["sha256"], "saved member/profile binding")
    holes = {(r["axis_id"], r["receiver"]): r for r in tables["receiver-holes.csv"]}
    require(len(holes) == len(tables["receiver-holes.csv"]) == 120, "receiver identities")
    require(set(holes) == {(axis["id"], host) for axis in axes.values() for host in axis["receivers"]}, "complete axis/receiver incidence")
    for (axis_id, host), row in holes.items():
        axis, profile = axes[axis_id], profiles[host]
        check_vector(vector(row, "axis_point"), axis["point_xyz_mm"], axis_id)
        check_vector(vector(row, "axis_direction", unit="unitless"), axis["direction_xyz"], axis_id)
        check_vector(vector(row, "axis_point_in_receiver", "luv"), local(axis["point_xyz_mm"], profile), axis_id)
        for side in ("entry", "exit"):
            distance = float(row[side+"_from_axis_point_mm"])
            point = [p+distance*d for p, d in zip(axis["point_xyz_mm"], axis["direction_xyz"], strict=True)]
            check_vector(vector(row, side+"_in_receiver", "luv"), local(point, profile), axis_id+" "+side)
    stacks = {r["axis_id"]: r for r in tables["bolt-stacks.csv"]}
    access = {(r["axis_id"], r["side"]): r for r in tables["access-sides.csv"]}
    require(len(stacks) == 100 and set(stacks) == set(axes), "100 stack identities")
    require(len(access) == 200 and set(access) == {(axis, side) for axis in axes for side in ("head", "nut")}, "200 access identities")
    for axis_id, axis in axes.items():
        require(stacks[axis_id]["receiver_member_ids"].split(";") == axis["receivers"], "stack receiver order")
        for side in ("head", "nut"):
            row = access[axis_id, side]
            check_vector(list(map(float, row["axis_origin_xyz_mm"].split(";"))), axis["point_xyz_mm"], axis_id)
            check_vector(list(map(float, row["axis_positive_xyz"].split(";"))), axis["direction_xyz"], axis_id)
            require(row["scene_role_id"] == axis_id+"_"+side, "installed access role identity")
        if axis_id in a.AXES:
            require(float(stacks[axis_id]["nominal_underhead_length_mm"]) == 101.6
                    and stacks[axis_id]["head_side_plate_mm"] == stacks[axis_id]["nut_side_plate_mm"] == "0", "four 4in/no-spacer recipes")
    native_pairs = {(w["axis_id"], w["receiver"]): w for w in bundle["scenario"]["wall_queries"]}
    require(len(native_pairs) == 16 and set(native_pairs) == {key for key in holes if key[1] in a.HOSTS}, "16 authentic own-wall joins")
    for key, wall in native_pairs.items():
        row, axis = holes[key], bundle["new_axes"][key[0]]
        require(len(wall["full_wall_intervals_mm"]) == 1 and wall["partial_wall_present"] is False, "saved full wall")
        interval = wall["full_wall_intervals_mm"][0]
        require(all(abs(float(row[side+"_from_axis_point_mm"])-interval[i]) <= 1e-6 for i, side in enumerate(("entry", "exit"))), "saved interval join")
        check_vector(wall["query_point_xyz_mm"], axis["point_xyz_mm"], "own wall origin")
        check_vector(wall["query_direction_xyz"], axis["direction_xyz"], "own wall direction")
    seats = bundle["scenario"]["annular_queries"]
    require(len(seats) == 16 and {(s["axis_id"], s["receiver"]) for s in seats} == set(native_pairs)
            and all(s["physical_contact_or_strength_qualified"] is False for s in seats), "16 saved seat metadata joins")
    require(len(tables["panel-screw-datums.csv"]) == len({r["axis_id"] for r in tables["panel-screw-datums.csv"]}) == 66, "66 screw identities")
    require(len(tables["panel-machining.csv"]) == len({r["identity"] for r in tables["panel-machining.csv"]}) == 340, "340 machining identities")
    for row in tables["panel-machining.csv"]:
        check_vector(vector(row, "origin_in_panel", "luv"), local(vector(row, "origin"), profiles[row["panel"]]), "panel machining")
    for row in tables["panel-screw-datums.csv"]:
        require(row["moved_by_rail_revision"] in ("True", "False"), "saved screw boolean")
        point = vector(row, "front_axis_origin")
        check_vector(vector(row, "origin_in_panel", "luv"), local(point, profiles[row["panel"]]), "panel screw")
        check_vector(vector(row, "origin_in_receiver", "luv"), local(point, profiles[row["receiver"]]), "screw receiver")


def independent_controls(a, t, methods, monkeypatch):
    controls = []
    shop, datum, _ = methods
    row, axis, profile, wall = t.fixture_hole()
    axis.update(point_xyz_mm=[10., -14., 38.], direction_xyz=[-1., 0., 0.])
    profile.update(datum_xyz_mm=[10., -20., 30.], basis_grain_u_v_xyz=[[0., .6, .8], [-1., 0., 0.], [0., -.8, .6]])
    row.update(entry_from_axis_point_mm="-2", exit_from_axis_point_mm="36.1", axis_direction_x_unitless="-1")
    wall.update(query_point_xyz_mm=axis["point_xyz_mm"], query_direction_xyz=axis["direction_xyz"], full_wall_intervals_mm=[[-2., 36.1]])
    a.update_hole(row, axis, profile, wall, moved=True, shop=shop, datum=datum, tolerance=1e-6)
    check_vector(shop.vector(row, "axis_point_in_receiver", "luv"), [10., 0., 0.], "oblique origin", 1e-12)
    check_vector(shop.vector(row, "entry_in_receiver", "luv"), [10., -2., 0.], "oblique entry", 1e-12)
    check_vector(shop.vector(row, "exit_in_receiver", "luv"), [10., 36.1, 0.], "oblique exit", 1e-12)
    controls.append("oblique orthonormal datum and negative installed direction known answer")
    old = {"point_xyz_mm": [1., 2., 200.], "direction_xyz": [-1., 0., 0.], "receivers": ["a", "b"]}
    new = {**copy.deepcopy(old), "point_xyz_mm": [1., 2., 180.], "nominal_under_head_length_mm": 101.6}
    for mutation in ("length", "receivers", "direction", "delta", "origin"):
        changed = copy.deepcopy(new)
        access = {"axis_origin_xyz_mm": "1;2;200"}
        if mutation == "length":
            changed["nominal_under_head_length_mm"] = 114.3
        elif mutation == "receivers":
            changed["receivers"] = ["b", "a"]
        elif mutation == "direction":
            changed["direction_xyz"] = [1., 0., 0.]
        elif mutation == "delta":
            changed["point_xyz_mm"][0] += 1.
        else:
            access["axis_origin_xyz_mm"] = "0;2;200"
        expect_error(lambda access=access, changed=changed: a.shift_access(access, old, changed, datum),
                     "4in access recipe" if mutation in ("length", "receivers", "direction") else "Z180 translation" if mutation == "delta" else "old access origin")
        controls.append("access rejection: " + mutation)
    selected = a.selected_functions(b"raise RuntimeError('excluded top level')\nimport nonexistent_review_module\ndef safe():\n    return 17\n", ("safe",))
    require(selected.safe() == 17, "AST selection executed excluded top level")
    expect_error(lambda: a.selected_functions(b"def safe(): pass\ndef safe(): pass\n", ("safe",)), "exact pure function/class")
    controls.append("AST selection excludes top-level imports/side effects and rejects duplicates")
    expect_error(lambda: a.join({"inert": "a"*64}, {"inert": "b"*64}), "source pin conflict")
    controls.append("conflicting closure pin cannot replace authenticated source")
    for path in ("/absolute/source", "../foreign-source"):
        expect_error(lambda path=path: a.read_ref({"path": path, "sha256": "0"*64}), "relative reference" if path.startswith("/") else "foreign source")
    controls.append("source references reject absolute and parent traversal")
    fixture = t.inert_bundle.__wrapped__(methods)
    before = canonical({key: fixture[key] for key in ("data", "encoded", "pins")} | {"encoded": {k: v.hex() for k, v in fixture["encoded"].items()}})
    with monkeypatch.context() as patch:
        patch.setattr(a, "validate_join", lambda b: a.require(b["data"].get("inert_only"), "inert fixture required"))
        outputs, result = a.build_outputs(fixture)
    after = canonical({key: fixture[key] for key in ("data", "encoded", "pins")} | {"encoded": {k: v.hex() for k, v in fixture["encoded"].items()}})
    require(before == after, "inert composition mutated source tables/profile metadata")
    bindings = json.loads(outputs["source-bindings.json"])
    holes = list(csv.DictReader(io.StringIO(outputs["receiver-holes.csv"].decode())))
    for row in holes:
        if row["receiver"] in a.HOSTS:
            key = row["axis_id"]+"|"+row["receiver"]
            require(row["source"] == "source-bindings.json#/receiver_holes/"+key and key in bindings["receiver_holes"], "output receiver pointer")
            binding = bindings["receiver_holes"][key]
            source = fixture["scenario"]["wall_queries"][binding["saved_native_wall_query_index"]]
            require((source["axis_id"], source["receiver"]) == (row["axis_id"], row["receiver"]), "wall source index")
    for role in json.loads(outputs["hardware-role-locations.json"])["roles"]:
        _, _, shaft, _, index = role["source_pointer"].split("/")
        source = fixture["data"]["descriptor"]["shafts"][int(shaft)]["metal_roles"][int(index)]
        require(all(role[k] == v for k, v in source.items()) and role["source_descriptor"] == fixture["inputs"]["sources"]["descriptor"], "role source pointer")
    require(all(result["files"][name] == {"sha256": sha(raw), "bytes": len(raw)} for name, raw in outputs.items()), "deferred output byte manifest")
    require(result["release"] == a.RELEASE and not any(result["release"].values()), "false release flags")
    controls.append("inert composition preserves inputs and resolves all16 wall/all20 role pointers and byte manifest")
    with monkeypatch.context() as patch:
        patch.setattr(a, "validate_join", lambda b: a.require(b["data"].get("inert_only"), "inert fixture required"))
        patch.setattr(a, "verify", lambda _: a.require(False, "inert post-composition source changed"))
        expect_error(lambda: a.build_outputs(fixture), "inert post-composition source changed")
    controls.append("deferred source-check failure refuses result after inert composition")
    return controls


def main():
    authenticate_targets()
    import pytest
    t = load(SHOP / "test_adapter.py", "independent_shop_test_fixtures")
    a = t.a
    inp = json.loads((SHOP / "inputs.json").read_bytes())
    preflight = json.loads((SHOP / "preflight.json").read_bytes())
    original_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        require(name.split(".")[0] not in {"cadquery", "OCP", "OCC", "build123d", "numpy", "scipy"}, "prohibited import: " + name)
        return original_import(name, *args, **kwargs)

    before_files = {p.name for p in SHOP.iterdir() if p.suffix in (".csv", ".svg")}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(builtins, "__import__", guarded)
        patch.setattr(a, "build_outputs", lambda *_: require(False, "genuine output trial prohibited"))
        bundle = a.prepare(SHOP / "inputs.json", EXPECTED["inputs.json"])
    pins = authenticate_closure(bundle)
    authentic_metadata(bundle, a)
    require(preflight["source_pin_count"] == len(pins) and preflight["source_map_canonical_sha256"] == canonical(pins), "preflight closure claim")
    require(preflight["validation"]["genuine_build_outputs_calls"] == 0 and not any(preflight["release"].values())
            and preflight["readiness"]["genuine_nominal_output_trial"] is False, "preflight held-output/release claims")
    methods = a.reusable_methods(inp["sources"])
    controls = independent_controls(a, t, methods, pytest.MonkeyPatch)
    tree = ast.parse((SHOP / "adapter.py").read_bytes())
    require(not any(isinstance(n, ast.Attribute) and n.attr in {"write_bytes", "write_text", "mkdir", "unlink", "rename"}
                    for n in ast.walk(tree)), "adapter disk writer found")
    require(all(n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "rb"
                for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "open"), "adapter writable open found")
    require("main" not in {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}, "adapter unexpectedly has CLI")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    commands = [[sys.executable, "-m", "pytest", "-q", str(SHOP / "test_adapter.py")],
                [sys.executable, "-m", "ruff", "check", str(SHOP / "adapter.py"), str(SHOP / "test_adapter.py"), str(OWN)]]
    checks = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        require(result.returncode == 0, "assigned check failed: " + result.stdout + result.stderr)
        checks.append({"command": command, "returncode": result.returncode, "output": result.stdout.strip()})
    verify(pins)
    authenticate_targets()
    require(before_files == {p.name for p in SHOP.iterdir() if p.suffix in (".csv", ".svg")} == set(), "candidate CSV/SVG appeared")
    receipt = {"schema": "eoere_z180_proposal_shop_independent_testing_review/v1",
        "status": "independent_z180_proposal_shop_source_and_inert_checks_pass",
        "helper": ref(OWN), "targets": {name: ref(SHOP / name) for name in EXPECTED},
        "source_pin_count": len(pins), "source_map_canonical_sha256": canonical(pins),
        "all_consumed_sources_verified_before_after": True,
        "authentic_metadata_checks": ["28 unique profiles/members and their datum/basis/source pointers",
            "100 unique stacks, 120 axis/receiver incidences, 200 side/role incidences",
            "all120 saved world/local hole origins and interval endpoints",
            "16 own saved wall and16 seat occurrences; native query performed now false",
            "all66 screw and340 machining world/local datums, blank actual/disposition cells",
            "four original4in no-spacer recipes; exact1141-pin closure and preflight claims"],
        "independent_inert_control_count": len(controls), "independent_inert_controls": controls, "checks": checks,
        "findings": [], "release": copy.deepcopy(inp["release"]),
        "execution": {"genuine_metadata_prepare": True, "genuine_build_outputs_calls": 0,
            "candidate_CSV_or_SVG_files_created": 0, "CAD_BREP_native_or_mechanics_queries": 0,
            "genuine_output_trial_authorized": False, "adapter_writer_or_CLI": False},
        "limits": ["Genuine candidate composition and SVG replay remain held; inert composition cannot establish their success.",
            "No output writer/reservation exists in this adapter; a future writer requires its own ownership/reservation review.",
            "Source metadata and saved evidence only; no geometry adoption, physical operation, tool access, force/resistance or readiness inference."]}
    output = OWN.with_name("receipt.json")
    if "--issue" in sys.argv:
        with output.open("xb") as handle:
            handle.write((json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n").encode())
    print(json.dumps({"status": receipt["status"], "source_pins": len(pins), "independent_controls": len(controls),
        "checks": checks, "helper_sha256": sha(OWN.read_bytes()), "receipt": ref(output) if output.exists() else None}, indent=2))


if __name__ == "__main__":
    main()
