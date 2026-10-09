"""One parent-authorized nominal SHOP trial. No automatic retry.

This saved driver is a reproduction record. Another genuine invocation requires
separate parent authorization and a different exclusively reserved directory.
The already-reserved original output01 is never overwritten by this driver.
"""
import builtins
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import stat
import sys
import time
import traceback
from types import ModuleType
import xml.etree.ElementTree as ET

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
SHOP = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/z180-proposal-v1"
OWN = Path(__file__).resolve()
TARGETS = {
    "adapter.py": "805dd6afe0921cb14f7e24fea4974714de6ee4c94cc50e74daca3b5595c951c2",
    "inputs.json": "24168aba426c8a3e65035e877b03fc58347a3c00f450980cba9319f4d6e19918",
    "test_adapter.py": "e243ed889154b21f4f380ee20c6a012cda87f80bc5ffdb1d42240cf11767eddb",
    "preflight.json": "cd7e28c42e59f41d9fae96378a5cc1cf005a5b04cbc7613db23088fef1a08854",
    "independent-review-v1/correctness/receipt.json": "01c30762dc419ac1bca4fd247e757ff59ebdde005f23b2fb1a4517df4be70bf2",
    "independent-review-v1/testing/receipt.json": "f9013e25a0787b33b0f46e87d545026386282e153d350b0ea9965f85ac151922",
    "independent-review-v1/structure/receipt.json": "04d55159998df2d067ae4ad5ad1918043bd1101a3d8a6bb8fec8ada921442841",
}
CANDIDATES = {"members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv", "current_profiles.json",
    "source-bindings.json", "hardware-role-locations.json", "member-projections-1.svg", "member-projections-3.svg", "extended-cleats.svg"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()


def ref(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def check_targets():
    for name, expected in TARGETS.items():
        require(sha((SHOP/name).read_bytes()) == expected, "frozen execution source/review differs: "+name)


def saved_validation(a, bundle, out, result):
    """Read persisted outputs only; never call build or renderer here."""
    raw = {name: (out/name).read_bytes() for name in CANDIDATES}
    require(set(result["files"]) == CANDIDATES, "exact ten candidate byte outputs required")
    require(all({"sha256": sha(data), "bytes": len(data)} == result["files"][name] for name, data in raw.items()), "saved candidate bytes differ")
    parsed = {name: json.loads(data) for name, data in raw.items() if name.endswith(".json")}
    tables, actual_cells, blank_actual = {}, 0, 0
    for name, data in raw.items():
        if name.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(data.decode()))
            rows = list(reader)
            require(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames), "unique CSV fields required")
            require(all(None not in row and None not in row.values() for row in rows), "CSV width mismatch")
            a.blank_observations(rows)
            tables[name] = (reader.fieldnames, rows)
            for row in rows:
                for key, value in row.items():
                    if key.startswith("Actual") or key == "Disposition":
                        actual_cells += 1
                        blank_actual += value == ""
        elif name.endswith(".svg"):
            require(ET.fromstring(data).tag == "{http://www.w3.org/2000/svg}svg", "own SVG root differs")
            require(b"Unadopted Z180 proposal" in data, "own SVG proposal identity absent")
    data, inp = bundle["data"], bundle["inputs"]
    profiles, bindings, role_data = (parsed[n] for n in ("current_profiles.json", "source-bindings.json", "hardware-role-locations.json"))
    require([len(tables[n][1]) for n in ("members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv")] == [28, 120, 100, 200], "saved shop census differs")
    a.verify_table_reuse(data, tables, profiles)
    require(not any(result["release"].values()) and not any(bindings["release"].values()) and not any(role_data["release"].values()), "proposal release changed")
    require(len(bindings["receiver_holes"]) == 16 and len(bindings["finished_members"]) == 4, "source binding census differs")
    holes = a.index(tables["receiver-holes.csv"][1], ("axis_id", "receiver"))
    max_axis, max_local, max_interval = 0., 0., 0.
    pointer_count = 0
    for key, row in holes.items():
        if row["receiver"] not in a.HOSTS:
            continue
        joined = bindings["receiver_holes"]["|".join(key)]
        require(row["source"] == "source-bindings.json#/receiver_holes/"+"|".join(key), "own wall pointer differs")
        require(joined["saved_native_result"] == inp["sources"]["native"] and joined["scenario"] == "proposed_Z180_modeled"
                and joined["native_query_performed_now"] is False and joined["complete_joint_bearing_or_pressure_qualified"] is False, "saved wall meaning changed")
        wall = bundle["scenario"]["wall_queries"][joined["saved_native_wall_query_index"]]
        require((wall["axis_id"], wall["receiver"]) == key, "native wall query pointer differs")
        axis = bundle["new_axes"][row["axis_id"]]
        point = [float(row["axis_point_"+c+"_mm"]) for c in "xyz"]
        max_axis = max(max_axis, *(abs(x-y) for x, y in zip(point, axis["point_xyz_mm"], strict=True)))
        interval = [float(row[s+"_from_axis_point_mm"]) for s in ("entry", "exit")]
        max_interval = max(max_interval, *(abs(x-y) for x, y in zip(interval, wall["full_wall_intervals_mm"][0], strict=True)))
        for label, scalar in (("axis_point", 0.), ("entry", interval[0]), ("exit", interval[1])):
            world = [p+scalar*v for p, v in zip(axis["point_xyz_mm"], axis["direction_xyz"], strict=True)]
            profile = profiles[row["receiver"]]
            expected = [sum((p-o)*v for p, o, v in zip(world, profile["datum_xyz_mm"], direction, strict=True)) for direction in profile["basis_grain_u_v_xyz"]]
            actual = [float(row[label+"_in_receiver_"+c+"_mm"]) for c in "luv"]
            max_local = max(max_local, *(abs(x-y) for x, y in zip(actual, expected, strict=True)))
        pointer_count += 1
    coordinate_tolerance = data["native_inputs"]["tolerances"]["coordinate_mm"]
    require(max(max_axis, max_local, max_interval) <= coordinate_tolerance, "saved own coordinate/interval check failed")
    own_centers = {}
    for host in a.HOSTS:
        new, observation, native = profiles[host]["finished"], bundle["observations"][host], bundle["scenario"]["finished_bodies"][host]
        require(new == bindings["finished_members"][host], "finished source pointer differs")
        require(new["analytic_center_xyz_mm"] == observation["center_xyz_mm"]
                and new["analytic_center_source"]["descriptor"] == inp["sources"]["descriptor"]
                and new["analytic_center_source"]["native_COM_query_performed"] is False, "analytic COM meaning changed")
        require(all(new[k] == native[k] for k in ("path", "sha256", "bytes", "volume_mm3", "bounds_xyz_mm")), "saved native facts differ")
        require("center_xyz_mm" not in new, "native COM falsely asserted")
        own_centers[host] = {"center_xyz_mm": new["analytic_center_xyz_mm"], "volume_mm3": new["volume_mm3"],
            "native_COM_query_performed": False, "native_geometry_source": {k: new[k] for k in ("path", "sha256")}}
    proposal = data["layout"]["proposed_axes"]
    stacks = a.index(tables["bolt-stacks.csv"][1], ("axis_id",))
    for name in a.AXES:
        row = stacks[(name,)]
        prefix, number = row["geometry_axis_pointer"].rsplit("/", 1)
        require(prefix == "proposal#/proposed_axes" and proposal[int(number)]["id"] == name, "proposal stack pointer differs")
        require(float(row["nominal_underhead_length_mm"]) == 101.6 and row["model_each_washer_thickness_mm"] == "2.6416", "original4in recipe changed")
    old_access = a.index(data["access-sides.csv"][1], ("axis_id", "side"))
    max_access = 0.
    for row in tables["access-sides.csv"][1]:
        if row["axis_id"] not in a.AXES:
            continue
        old = old_access[(row["axis_id"], row["side"])]
        for key in ("axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm"):
            expected = [float(x)+shift for x, shift in zip(old[key].split(";"), [0., 0., -20.], strict=True)]
            max_access = max(max_access, *(abs(float(x)-y) for x, y in zip(row[key].split(";"), expected, strict=True)))
    require(max_access <= coordinate_tolerance, "saved access translation differs")
    roles = role_data["roles"]
    require(len(roles) == len({r["id"] for r in roles}) == 20, "own20 roles differ")
    for row in roles:
        parts = row["source_pointer"].split("/")
        require(parts[1] == "shafts" and parts[3] == "metal_roles", "role pointer schema differs")
        shaft = data["descriptor"]["shafts"][int(parts[2])]
        expected = shaft["metal_roles"][int(parts[4])]
        require(row["axis_id"] == shaft["axis_id"] in a.AXES and row["source_descriptor"] == inp["sources"]["descriptor"], "role identity/source differs")
        require({k: v for k, v in row.items() if k not in {"axis_id", "source_descriptor", "source_pointer", "Actual", "Disposition"}} == expected, "own saved hardware role changed")
        require(row["Actual"] == row["Disposition"] == "", "hardware role observation filled")
    inherited = result["inherited_files_via_links"]
    require(set(inherited) == a.REUSED_DRAWINGS | a.UNCHANGED_FILES, "eleven inherited source links required")
    for name, value in inherited.items():
        require(value == inp["saved_files"][name] and not (out/name).exists(), "inherited bytes copied or rebound")
        require(a.read_ref(value) == bundle["encoded"][name], "inherited source bytes changed")
        if name.endswith(".svg"):
            require(ET.fromstring(bundle["encoded"][name]).tag == "{http://www.w3.org/2000/svg}svg", "inherited SVG parse failed")
    require(actual_cells == blank_actual, "Actual/Disposition blank census differs")
    return {"saved_CSV_counts": {name: len(value[1]) for name, value in tables.items()}, "candidate_actual_disposition_cells": actual_cells,
        "candidate_actual_disposition_cells_blank": blank_actual, "own_role_actual_disposition_cells_blank": 40,
        "receiver_source_pointers_resolved": pointer_count, "proposal_stack_pointers_resolved": 4, "role_pointers_resolved": 20,
        "maximum_world_axis_error_mm": max_axis, "maximum_local_entry_exit_error_mm": max_local,
        "maximum_saved_wall_interval_error_mm": max_interval, "maximum_access_translation_error_mm": max_access,
        "recorded_coordinate_tolerance_mm": coordinate_tolerance, "four_finished_geometry_and_analytic_centers": own_centers,
        "protected_fields_compared_to_authenticated_old_tables": True, "raw28_profiles_exact_except4_finished_records": True,
        "eight_retained_holes_only_source_changed": True, "original_four4in_recipes_and_washer_stack_unchanged": True,
        "inherited_drawing_links": 6, "inherited_data_links": 5, "six_actual_inherited_drawings_replayed_equal_in_single_build": True,
        "candidate_XML_SVG_parses": 3, "inherited_XML_SVG_parses": 6, "candidate_JSON_parses": 3,
        "protected_inherited_stock": {"sticks": len(data["stock"]["sticks"]), "nominal_board_feet": data["stock"]["nominal_board_feet"]},
        "protected_inherited_screw_datums": len(data["panel-screw-datums.csv"][1]), "protected_inherited_machining_features": len(data["panel-machining.csv"][1])}


def main():
    check_targets()
    require(len(sys.argv) == 1, "original authorized trial has no mutable command-line bindings")
    out = OWN.parent
    canonical_parent = (SHOP.resolve(strict=True)/"runs-v1").resolve(strict=True)
    require(out == canonical_parent/"output01" and not out.is_symlink(), "canonical owned output01 required")
    directory_fd = os.open(out, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    directory_stat = os.fstat(directory_fd)
    handles, written = {}, set()
    started = time.monotonic()
    process = {"schema": "eoere_z180_proposal_shop_trial_process/v1", "status": "STARTED", "helper": ref(SHOP/"adapter.py"),
        "inputs": ref(SHOP/"inputs.json"), "reproduction_driver": ref(OWN),
        "review_receipts": {key: ref(SHOP/("independent-review-v1/"+key+"/receipt.json")) for key in ("correctness", "testing", "structure")},
        "python": platform.python_version(), "command": "uv run python "+str(OWN.relative_to(ROOT)),
        "canonical_output_directory": str(out.relative_to(ROOT)), "output_directory_inode": directory_stat.st_ino,
        "build_outputs_call_count": 0, "CAD_BREP_native_panel_K_forces_or_solve": False,
        "spacer_or_4p5in_recipe_adopted": False, "old_Z200_HOLD_authority_changed": False,
        "release": {key: False for key in ("geometry_adopted", "drilling", "fabrication", "climbing", "physical_observations", "complete_joint_acceptance")}}

    def guard(name):
        opened = os.fstat(handles[name].fileno())
        live = os.stat(out/name, follow_symlinks=False)
        current_dir = os.stat(out, follow_symlinks=False)
        require(stat.S_ISREG(live.st_mode) and (live.st_dev, live.st_ino) == (opened.st_dev, opened.st_ino), "reserved output leaf changed: "+name)
        require((current_dir.st_dev, current_dir.st_ino) == (directory_stat.st_dev, directory_stat.st_ino), "reserved output directory changed")

    def write(name, raw):
        guard(name)
        handle = handles[name]
        handle.seek(0)
        handle.write(raw)
        handle.truncate()
        handle.flush()
        os.fsync(handle.fileno())

    imported = builtins.__import__
    bundle = None
    try:
        # Exclusively reserve every leaf before importing the adapter or callbacks.
        for name in ["process.json", "result.json", *sorted(CANDIDATES)]:
            handles[name] = (out/name).open("xb+")
            write(name, encoded({"status": "STARTED", "output_name": name, "release": process["release"]}))
        process["exclusive_reserved_outputs"] = {name: {"device": os.fstat(h.fileno()).st_dev, "inode": os.fstat(h.fileno()).st_ino} for name, h in handles.items()}
        write("process.json", encoded(process))

        def no_heavy_import(name, *args, **kwargs):
            require(name.split(".")[0] not in {"cadquery", "OCP", "OCC", "build123d", "numpy", "scipy"}, "forbidden CAD/operator import: "+name)
            return imported(name, *args, **kwargs)
        builtins.__import__ = no_heavy_import
        raw = (SHOP/"adapter.py").read_bytes()
        require(sha(raw) == TARGETS["adapter.py"], "immediate exact adapter bytes differ")
        a = ModuleType("authenticated_z180_shop_adapter")
        a.__file__ = str(SHOP/"adapter.py")
        exec(compile(raw, a.__file__, "exec"), a.__dict__)
        bundle = a.prepare(SHOP/"inputs.json", TARGETS["inputs.json"])
        require(len(bundle["pins"]) == 1141, "exact1141 source closure required")
        a.verify(bundle["pins"])
        process["source_closure_before"] = {"pin_count": len(bundle["pins"]), "canonical_sha256": a.canonical(bundle["pins"]), "all_exact": True}
        process["build_outputs_call_count"] = 1
        write("process.json", encoded(process))
        outputs, result = a.build_outputs(bundle)  # The single genuine call.
        require(set(outputs) == CANDIDATES, "exact ten candidate outputs required")
        for name, data in outputs.items():
            write(name, data)
            written.add(name)
        write("result.json", encoded(result))
        written.add("result.json")
        process["validation"] = saved_validation(a, bundle, out, result)
        a.verify(bundle["pins"])
        check_targets()
        process["source_closure_after"] = {"pin_count": len(bundle["pins"]), "canonical_sha256": a.canonical(bundle["pins"]), "all_exact": True}
        require(process["source_closure_before"] == process["source_closure_after"], "source closure changed")
        require(ref(OWN) == process["reproduction_driver"], "reproduction driver changed")
        process["outputs"] = {name: ref(out/name) for name in sorted(CANDIDATES | {"result.json"})}
        process["candidate_byte_volume"] = sum(value["bytes"] for name, value in process["outputs"].items() if name in CANDIDATES)
        process["candidate_plus_result_byte_volume"] = sum(value["bytes"] for value in process["outputs"].values())
        process["status"] = "PASS_SAVED_NOMINAL_SHOP_OUTPUT_TRIAL_UNADOPTED"
        process["elapsed_seconds"] = time.monotonic()-started
        write("process.json", encoded(process))
        print(json.dumps({"status": process["status"], "process": ref(out/"process.json"), "result": ref(out/"result.json"),
            "candidate_bytes": process["candidate_byte_volume"], "candidate_plus_result_bytes": process["candidate_plus_result_byte_volume"],
            "elapsed_seconds": process["elapsed_seconds"]}, sort_keys=True))
    except Exception as error:
        process.update(status="FAILED_RETAINED_NO_RETRY", error={"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}, elapsed_seconds=time.monotonic()-started)
        process["completed_candidate_files"] = sorted(written)
        for name in handles:
            if name != "process.json" and name not in written:
                write(name, encoded({"status": "FAILED_RETAINED", "output_name": name, "error": process["error"], "release": process["release"]}))
        if "process.json" in handles:
            write("process.json", encoded(process))
        print(json.dumps({"status": process["status"], "error": process["error"]["message"], "process": ref(out/"process.json")}, sort_keys=True))
        raise
    finally:
        builtins.__import__ = imported
        for handle in handles.values():
            handle.close()
        os.close(directory_fd)


if __name__ == "__main__":
    main()
