"""Independent saved current-input joins and fresh-load review; no preparation."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
INPUT = OWN.parent.parent / "attempt01/inputs.json"
INPUT_SHA = "f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa"
DESCRIPTOR = MECH / "current-source-observations-v1/attempt01.json"
DESCRIPTOR_SHA = "0f7e95f0dabfb5f0b5d63f8ef7d78e3c52c07672b4f482a89a89496eec703de7"
DESCRIPTOR_REVIEW = MECH / "current-source-observations-v1/independent-review-v1/correctness/receipt.json"
DESCRIPTOR_REVIEW_SHA = "14db73198c6705d866e42f43f41184e2235cfe66450418f6ba892aabbd98ee34"
BRIDGE = MECH / "current-force-bridge-v1/review-fix-v2/bridge.py"
BRIDGE_SHA = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
CASE_IDS = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear", "gravity-only")
LIVE = (("A12", (0.,300.)), ("A12", (0.,-300.)), ("A12", (-300.,0.)),
        ("K12", (300.,0.)), ("K12", (0.,300.)), ("A1", (0.,300.)))
GRAVITY = 9.80665


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load(path, expected, name):
    assert sha(path) == expected
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def indexed(rows, key="id"):
    result = {row[key]: row for row in rows}
    assert len(result) == len(rows), key
    return result


def add(a, b):
    return [x+y for x,y in zip(a,b,strict=True)]


def scale(a, value):
    return [x*value for x in a]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def close(a, b, tolerance=1e-8):
    assert len(a) == len(b) and max(abs(x-y) for x,y in zip(a,b,strict=True)) < tolerance, (a,b)


def main():
    assert INPUT.stat().st_size == 13705709 and sha(INPUT) == INPUT_SHA and sha(DESCRIPTOR) == DESCRIPTOR_SHA
    assert sha(DESCRIPTOR_REVIEW) == DESCRIPTOR_REVIEW_SHA
    raw = json.loads(INPUT.read_bytes())
    exported = json.loads(DESCRIPTOR.read_bytes())
    prior_review = json.loads(DESCRIPTOR_REVIEW.read_bytes())
    assert prior_review["status"] == "PASS_NO_SUBSTANTIAL_FINDINGS" and not prior_review["findings"]
    assert prior_review["sources"][str(DESCRIPTOR.relative_to(ROOT))] == DESCRIPTOR_SHA
    process_path = INPUT.with_name("process.json")
    process_sha = sha(process_path)
    process = json.loads(process_path.read_bytes())
    assert process["exit_code"] == 0 and process["output_sha256"] == INPUT_SHA and process["wrapper_sha256"] == BRIDGE_SHA
    assert "build-inputs" in process["command"] and "--run" not in process["command"]
    assert "--slot" not in process["command"]
    for key, name in (("stdout_sha256", "stdout.log"),("stderr_sha256", "stderr.log")):
        assert sha(INPUT.with_name(name)) == process[key]
    assert len(raw["source_sha256"]) == 1086 and exported["source_sha256"].items() <= raw["source_sha256"].items()
    source_pins = dict(raw["source_sha256"])
    evidence = {str(INPUT.relative_to(ROOT)): INPUT_SHA, str(DESCRIPTOR_REVIEW.relative_to(ROOT)): DESCRIPTOR_REVIEW_SHA,
                str(process_path.relative_to(ROOT)): process_sha, str(OWN.relative_to(ROOT)): sha(OWN),
                str(INPUT.with_name("stdout.log").relative_to(ROOT)): process["stdout_sha256"],
                str(INPUT.with_name("stderr.log").relative_to(ROOT)): process["stderr_sha256"]}
    for path, digest in evidence.items():
        assert path not in source_pins or source_pins[path] == digest
        source_pins[path] = digest
    for path,digest in source_pins.items():
        assert sha(ROOT/path) == digest, path
    assert raw["schema"] == "eoere_extended_cleat_first_order_mechanics_inputs/v1" and raw["optional_2026_extra"] is False
    assert raw["status"] == "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW"
    assert raw["historical_q"] is None and raw["old_field"] is None
    assert raw["readiness"] == {"source_joins_independently_reviewed": False, "complete_reference_contact_inventory": False}
    assert raw["source_pins_before_after_unchanged"] is True
    assert raw["geometry"]["cached_source_export"] == {"path": str(DESCRIPTOR.relative_to(ROOT)), "sha256": DESCRIPTOR_SHA}
    assert raw["geometry"]["report"] == exported["geometry"] and raw["geometry"]["source_manifest"] == exported["manifest"]

    joined = (("timber_rows","raw_gross_timber_rows"), ("physical_owner_gravity_rows","physical_owner_gravity_rows"),
        ("fitting_poses","fitting_poses"), ("fitting_port_bindings","fitting_ports"), ("all_factory_holes","all_factory_holes"),
        ("shafts","shafts"), ("finished_receiver_wall_queries","finished_receiver_wall_queries"),
        ("finished_body_observations","finished_body_observations"), ("direct_contacts","direct_contacts"),
        ("hillman_rows","hillman_rows"), ("current_panel_machining_descriptors","current_panel_machining_descriptors"),
        ("flange_domains","flange_domains"), ("flange_shared_face_patches","flange_shared_face_patches"),
        ("timber_and_panel_shared_face_patches","timber_and_panel_shared_face_patches"), ("shared_pair_query_census","shared_pair_query_census"))
    for key, source_key in joined:
        assert raw[key] == exported[source_key], key
    assert raw["parameters"] == exported["parameters"] and raw["scenario"] == exported["material_scenario"]
    owners = indexed(raw["physical_owner_gravity_rows"])
    assert len(owners) == 150 and Counter(r["kind"] for r in owners.values()) == {"timber":22,"fitting":22,"panel":6,"shaft":100}
    bases = [row for row in owners.values() if row["kind"] != "shaft"]
    assert raw["base_bodies"] == bases and len(bases) == 50
    assert raw["panel_ids"] == sorted(row["id"] for row in owners.values() if row["kind"] == "panel")
    assert raw["floor_footprints"] == {r["host"]:r["observed_normal_reference_points_xyz_mm"] for r in exported["floor_observations"]}
    assert len(raw["floor_footprints"]) == 8 and sum(map(len,raw["floor_footprints"].values())) == 32
    assert exported["support"]["enabled_centroid_xy_hosts"] == ["lumber_leg_left","lumber_leg_right"]
    assert exported["support"]["no_slip_assumed_not_verified"] is True
    holes = [{**hole,"angle_id":angle["angle_id"],"used":hole["installed_bolt_axis_id"] is not None}
        for angle in raw["all_factory_holes"] for hole in angle["holes"]]
    assert raw["factory_holes"] == holes and len(holes) == 176 and sum(r["used"] for r in holes) == 88
    assert len(raw["fitting_port_bindings"]) == 88 and len(raw["hillman_rows"]) == 66
    assert len(indexed(raw["shafts"],"axis_id")) == 100 and len(raw["finished_receiver_wall_queries"]) == 120
    assert sum(len(r["ends"]) for r in raw["shafts"]) == 200

    # Transitive source authentication plus actual equality preserves the complete reviewed graph.
    contacts = indexed(raw["direct_contacts"])
    common = indexed(raw["timber_and_panel_shared_face_patches"])
    flanges = indexed(raw["flange_shared_face_patches"])
    assert len(contacts) == 1606 and len(common) == 96 and len(flanges) == 88
    assert Counter(r["kind"] for r in contacts.values()) == {"timber_face_contact":332,"panel_contact":922,"flange_contact":352}
    all_cells = sum(len(r["cells"]) for r in [*common.values(),*flanges.values()])
    assert all_cells == 1606 and len(raw["shared_pair_query_census"]) == 72
    assert all(r["first"] in owners and r["second"] in owners and r["first"] != r["second"]
        and r["stiffness"] > 0 and r["reference_area_mm2"] > 0 for r in contacts.values())

    panel_contract = raw["panel_operator_source_inputs"]
    assert panel_contract["geometry"] == raw["geometry"]["report"] and panel_contract["optional_2026_extra"] is False
    assert panel_contract["panel_machining_canonical_sha256"] == canonical(raw["current_panel_machining_descriptors"])
    screws = [r["source_screw_descriptor"] for r in raw["hillman_rows"]]
    assert panel_contract["screw_axes_canonical_sha256"] == canonical(screws)
    assert panel_contract["screw_axis_ids"] == [r["axis_id"] for r in screws]
    observations = indexed(raw["finished_body_observations"])
    slim = lambda row:{k:row[k] for k in ("id","path","sha256","volume_mm3")}
    assert indexed(panel_contract["finished_panel_solids"]) == {name:slim(observations[name]["source"]) for name in raw["panel_ids"]}
    assert panel_contract["aperture_updated_K_panels"] == ["kicker_right","main_lower_right","main_upper_right"]
    assert set(panel_contract["unchanged_K_panels"]) == set(raw["panel_ids"])-set(panel_contract["aperture_updated_K_panels"])
    assert panel_contract["old_contact_domains_reused"] is False and panel_contract["old_response_or_acceptance_used"] is False
    assert len(panel_contract["changed_feature_ids"]) == 10

    # Independently construct all current permanent rows, without the generator's implementation.
    permanent = {}
    for row in bases:
        permanent["self-weight/"+row["id"]] = {"body":row["id"],"point_xyz_mm":row["center_xyz_mm"],"force_xyz_n":[0.,0.,-row["mass_kg"]*GRAVITY]}
    roles = []
    for shaft in raw["shafts"]:
        for role in shaft["metal_roles"]:
            roles.append({"id":role["id"],"owner":shaft["body"],"mass_kg":role["mass_kg"],
                "center_xyz_mm":role["center_of_mass_xyz_mm"],"basis":role["basis"]})
            permanent["physical-bolt-metal/"+role["id"]] = {"body":shaft["body"],"point_xyz_mm":role["center_of_mass_xyz_mm"],"force_xyz_n":[0.,0.,-role["mass_kg"]*GRAVITY]}
    aux = exported["auxiliary_metal_gravity_descriptors"]
    for row in aux:
        permanent["bolt-weight/"+row["id"]] = {"body":row["owner"],"point_xyz_mm":row["center_xyz_mm"],"force_xyz_n":[0.,0.,-row["mass_kg"]*GRAVITY]}
    features = indexed(raw["current_panel_machining_descriptors"]["features"],"identity")
    top = features["hold_tnut_main_A12"]
    accessory_point = add(add(top["start_xyz_mm"],[1019.2,0.,0.]),scale(top["direction_xyz"],18.25625))
    for name in ("main_upper_left","main_upper_right"):
        permanent["accessory/"+name] = {"body":name,"point_xyz_mm":accessory_point,"force_xyz_n":[0.,0.,-12.5*GRAVITY]}
    assert len(permanent) == 826 and len(roles) == 500 and len(aux) == 274
    physical_mass = math.fsum(r["mass_kg"] for r in owners.values())
    aux_mass = math.fsum(r["mass_kg"] for r in aux)
    total_mass = physical_mass+aux_mass+25.
    assert abs(physical_mass-191.908938620187) < 1e-10 and abs(aux_mass-2.207001080119) < 1e-10
    assert abs(total_mass-219.115939700306) < 1e-10
    assert abs(raw["gravity"]["known_modeled_mass_kg"]-(physical_mass+aux_mass)) < 1e-10
    assert raw["gravity"]["additional_accessory_kg"] == 25. and raw["gravity"]["primary_accessory_point_xyz_mm"] == accessory_point
    assert [r["case_id"] for r in raw["cases"]] == list(CASE_IDS) and raw["case"] == raw["cases"][0]
    case_results = []
    for i,case in enumerate(raw["cases"]):
        loads = indexed(case["loads"])
        assert case["primary_load_basis"] is True and case["accessory_placement"] == "retained-original-top-hold"
        assert all(r["body"] in owners and len(r["point_xyz_mm"]) == len(r["force_xyz_n"]) == 3 for r in loads.values())
        assert all(r.get("moment_xyz_nmm",[0.,0.,0.]) == [0.,0.,0.] for r in loads.values())
        expected = copy.deepcopy(permanent)
        if i < 6:
            label,horizontal = LIVE[i]
            feature = features["hold_tnut_main_"+label]
            direction = feature["direction_xyz"]
            inward = scale(direction,1./math.sqrt(sum(v*v for v in direction)))
            front = feature["start_xyz_mm"]
            point = add(front,scale(inward,-100.))
            mid = add(front,scale(inward,18.25625/2))
            force = [*horizontal,-2.*250.*.45359237*GRAVITY]
            expected["climber/"+label] = {"body":feature["panel"],"point_xyz_mm":point,"force_xyz_n":force}
            hold = case["hold"]
            assert hold["label"] == label and hold["panel"] == feature["panel"] and hold["front_xyz_mm"] == front
            close(hold["load_point_xyz_mm"],point)
            close(hold["panel_midplane_xyz_mm"],mid)
            close(hold["force_xyz_n"],force)
            close(hold["moment_about_panel_midplane_xyz_nmm"],cross(add(point,scale(mid,-1)),force))
        else:
            assert case["hold"] is None
        assert loads.keys() == expected.keys() and len(loads) == (827 if i<6 else 826)
        by_owner = defaultdict(list)
        for name,row in loads.items():
            own = expected[name]
            assert row["body"] == own["body"]
            close(row["point_xyz_mm"],own["point_xyz_mm"])
            close(row["force_xyz_n"],own["force_xyz_n"],1e-10)
            by_owner[row["body"]].append(row)
        assert set(by_owner) == set(owners)
        force = [math.fsum(r["force_xyz_n"][j] for r in loads.values()) for j in range(3)]
        moments = [cross(r["point_xyz_mm"],r["force_xyz_n"]) for r in loads.values()]
        moment = [math.fsum(r[j] for r in moments) for j in range(3)]
        close(case["applied_force_xyz_n"],force)
        close(case["applied_moment_about_global_origin_xyz_nmm"],moment,1e-6)
        assert abs(force[2]+total_mass*GRAVITY+(2.*250.*.45359237*GRAVITY if i<6 else 0.)) < 1e-8
        case_results.append({"case_id":case["case_id"],"load_count":len(loads),"load_owner_count":len(by_owner),
            "applied_force_xyz_n":force,"applied_moment_about_global_origin_xyz_nmm":moment,
            "max_saved_force_error_n":max(abs(a-b) for a,b in zip(force,case["applied_force_xyz_n"],strict=True)),
            "max_saved_moment_error_nmm":max(abs(a-b) for a,b in zip(moment,case["applied_moment_about_global_origin_xyz_nmm"],strict=True))})

    # Use genuine metadata APIs for the consumer contract and the original fresh load recipe only.
    fixed = load(BRIDGE,BRIDGE_SHA,"independent_current_input_bridge")
    b = fixed.frozen()
    assert raw["release"] == b.core.RELEASE and not any(raw["release"].values())
    case_source = b.PACKET/"raised-rail-cases-v1/cases.py"
    case_provider = load(case_source,b.REUSED["raised-rail-cases-v1/cases.py"],"independent_genuine_current_case_recipe")
    regenerated,gravity = case_provider.derive_fresh_cases({"panel_machining":exported["current_panel_machining_descriptors"]},
        {"bodies":bases,"bolt_gravity_components":roles+aux},expected_owner_ids=list(owners),source_sha256=raw["source_sha256"])
    assert regenerated == raw["cases"] and gravity == raw["gravity"]
    with fixed.corrected_context(b), patch.object(b,"methods",side_effect=AssertionError("bank callback prohibited in this review")), \
            patch.object(b.factory,"_prepare",side_effect=AssertionError("candidate preparation prohibited in this review")):
        with b.factory_boundary():
            for case in raw["cases"]:
                selected = {**raw,"case":case}
                assert b.factory.validate_rows(selected) == {"timber":22,"fitting":22,"shaft":100,"panel":6,"physical_bodies":150}
        b.require_current_sources(raw)
        for path,digest in source_pins.items():
            assert sha(ROOT/path) == digest, path
        receipt = {"schema":"eoere_extended_cleat_mechanics_inputs_independent_review/v1",
            "success":"independent_extended_cleat_source_input_checks_pass","complete_reference_contact_inventory":True,
            "input":{"path":str(INPUT.relative_to(ROOT)),"sha256":INPUT_SHA},"geometry":copy.deepcopy(raw["geometry"]["report"]),
            "release":copy.deepcopy(raw["release"]),"source_sha256":source_pins,"findings":[],
            "inputs_canonical_sha256":canonical(raw),"selected_case_canonical_sha256":{r["case_id"]:canonical(r) for r in raw["cases"]},
            "saved_descriptor_review":{"path":str(DESCRIPTOR_REVIEW.relative_to(ROOT)),"sha256":DESCRIPTOR_REVIEW_SHA},
            "checks":{"input_source_pins":1086,"all_used_source_bytes_before_after_unchanged":True,
                "all_descriptor_rows_and_complete_contact_graph_match_independently_reviewed_current_export":True,
                "finished_observations":28,"physical_owners":150,"base_owners":50,"shaft_roles":500,"auxiliary_metal_shares":274,
                "shafts":100,"walls":120,"external_seats":200,"ports":88,"factory_holes":176,"Hillman_screws":66,
                "floor_hosts":8,"floor_normals":32,"direct_contacts":1606,"fresh_case_recipe_reproduces_exact_saved_cases":True,
                "independent_all_load_identity_owner_point_force_and_wrench_checks":True,"cases":case_results},
            "mass_reconciliation_kg":{"physical_owners":physical_mass,"auxiliary_source_metal_shares":aux_mass,"accessory_allowance":25.,"total":total_mass},
            "scope":"Saved current source inputs and seven fresh load recipes; no current operator, force field or mechanics admission",
            "frozen_import_dependencies_load_native_geometry_packages":"cadquery" in sys.modules or "OCP" in sys.modules,
            "review_rebuild_BREP_query_bank_K_preparation_frame_K_q_native_solve_or_browser_performed":False,
            "limits":["All release flags remain false. Parent owns method readiness and serialized mechanics slots.",
                "Current panel and frame operators, six current force fields and independent raw-field admission remain unperformed.",
                "Reviewed nominal contact masks, gross-stock sections, uninspected grain and assumed no-slip support retain their recorded limits.",
                "Contact inventory completion means authenticated source rows, not pressure convergence, physical contact or complete joint resistance."]}
        receipt_path = OWN.with_name("receipt.json")
        if receipt_path.exists():
            assert json.loads(receipt_path.read_bytes()) == receipt, "preserve a different existing review receipt"
        else:
            with receipt_path.open("x") as stream:
                json.dump(receipt,stream,indent=2,sort_keys=True,allow_nan=False)
                stream.write("\n")
        record = {"path":str(receipt_path.relative_to(ROOT)),"sha256":sha(receipt_path)}
        pins = b.source_pins({**raw["source_sha256"],str(INPUT.relative_to(ROOT)):INPUT_SHA})
        _, checked = b.authenticate_review(record,raw,pins)
        assert checked["inputs_canonical_sha256"] == canonical(raw)
        for case_id in CASE_IDS[:6]:
            selected,selection = b.driver.select_case(raw,case_id)
            _, checked = b.authenticate_review(record,selected,pins,raw_data=raw,selection=selection)
            assert checked["source_case_selection"] == selection
    assert sha(INPUT) == INPUT_SHA and sha(DESCRIPTOR) == DESCRIPTOR_SHA and sha(OWN) == source_pins[str(OWN.relative_to(ROOT))]
    print(json.dumps({"success":receipt["success"],"source_pins":1086,"seven_cases_checked":True,
        "consumer_raw_and_six_selected_cases_authenticated":True,"review_receipt_sha256":sha(receipt_path)}))


if __name__ == "__main__":
    main()
