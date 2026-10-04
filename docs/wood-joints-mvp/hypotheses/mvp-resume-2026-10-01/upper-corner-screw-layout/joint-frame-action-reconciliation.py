"""Export physical actions from an accepted saved coupled response, without solving.

prepare authenticates inputs only. build recovers body wrenches and signed cuts;
it never executes a source producer, CAD, native mechanics or a frame solver.
The new response remains a separately identified conditional sensitivity.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RESUME = HERE.parent
RAW = HERE / "rawlocal/joint-frame-action-reconciliation"
OPERATORS = HERE / "operators-attempt02"
BASELINE = RESUME / "member-screen-attempt02/four-screw-layout01"
BASE = RESUME.parent / "mvp-acceleration-2026-09-28"
MODEL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
DOFS = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PERMANENT = "dead-only"
ALL_CASES = (*CASES, PERMANENT)
COMPLETE_RESPONSE = "COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES"
PARTIAL_RESPONSE = "PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS"
ACCEPTED_STATE = "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM"
FLOOR_STOP = "STOP_NO_AUDITED_POSITIVE_BEARING_FLOOR_BRANCH"
NUMERICAL_STOP = "STOP_NUMERICAL_QUALIFICATION_OPEN"
FLOOR_FAILURE_PREFIX = "STOP: no audited coupled floor branch among 256 masks: "
PERMANENT_BASE = HERE / "rawlocal/dead-load-check/parent-attempt06"
PINS = {
    BASELINE / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    BASELINE / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    HERE / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    RESUME / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    RESUME / "top_corner_actions.py": "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    RESUME / "simple_frame.py": "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    HERE / "panel-reference-completion.py": "1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1",
    HERE / "all-joint-splitting/closure.py": "095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d",
    PERMANENT_BASE / "comparison.json": "20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75",
    PERMANENT_BASE / "response.npz": "9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14",
    PERMANENT_BASE / "producer.py.snapshot": "ffdb2ee797000c055cd67c6e46ac80e549b4865a79346e728074625767bf213d",
}
LIMITS = [
    "Separate reviewed104 coupled first-order sensitivity; no proposal ties or historical capacity transfer.",
    "Frozen filled-body timber compliance, original other100 connector laws, no-slip and source loads remain conditional.",
    "Floor cell actions preserve the exact original stiffness-weighted T map; they are not resolved local pressures.",
    "New bore/wood-seat forces use the consumed point terms; metal-only head-seat ports apply no direct timber action.",
    "Existing timber stations and section indices are preserved; separate event cuts include every new point-action station.",
    "Actions and cuts are inputs for resistance comparisons; no resistance, material acceptance or physical release is inferred.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(loaded)
    finally:
        sys.dont_write_bytecode = old
    return loaded


def sources(preparation, reduction, response=None):
    """Reuse inert bindings; no numerical arrays are opened by this function."""
    require(sha(HERE / "all-joint-splitting/closure.py") == PINS[HERE / "all-joint-splitting/closure.py"],
            "authentication helper changed")
    api = module(HERE / "all-joint-splitting/closure.py", "coupled_action_bindings")
    pins = dict(PINS)
    api.bind(pins, Path(__file__).resolve(), sha(__file__))
    preparation, reduction = Path(preparation).resolve(), Path(reduction).resolve()
    for directory in (preparation, reduction):
        api.bind(pins, directory / "receipt.json", sha(directory / "receipt.json"))
        api.receipt_sources(pins, directory / "receipt.json")
    prepared, reduced = read(preparation / "receipt.json"), read(reduction / "receipt.json")
    require(prepared["status"] == "PREPARED_COUPLED_PORTS_NOT_FRAME_RESPONSE"
            and reduced["status"] == "PASS_JOINT_FRAME_PORT_REDUCTION", "prepared/reduction status unsupported")
    require(reduced["request_sha256"] == sha(preparation / "wood-port-request.json"),
            "reduction consumes another joint request")
    request = read(preparation / "wood-port-request.json")
    require(request["reviewed_bolt_axes"] == 104 and request["proposed_internal_ties_included"] is False,
            "reviewed/proposal geometry conflated")
    if response is not None:
        response = Path(response).resolve()
        api.bind(pins, response / "receipt.json", sha(response / "receipt.json"))
        api.receipt_sources(pins, response / "receipt.json")
        receipt = read(response / "receipt.json")
        comparison = read(response / "comparison.json")
        inputs = read(response / "inputs.json")
        require(receipt["status"] == comparison["status"]
                and receipt["status"] in (COMPLETE_RESPONSE, PARTIAL_RESPONSE),
                "completed accepted-state/disposition packet required; raw STOP/diagnostic arrays are not inputs")
        require(inputs["preparation"] == preparation.relative_to(ROOT).as_posix()
                and inputs["wood_reduction"] == reduction.relative_to(ROOT).as_posix(),
                "response prepared-input identity differs")
        require(comparison["reviewed_geometry_changed"] is False and inputs["proposal_ties_included"] is False,
                "response changes reviewed geometry")
    original = read(BASELINE / "member-results.json")
    for path in (MODEL, DOFS, RESUME / "top-corner-contact-geometry.json",
                 BASE / "reduced-static-attempt01/contact-geometry.json"):
        api.bind(pins, path, original["source_sha256"][path.relative_to(ROOT).as_posix()])
    # Every needed operator/load/row source must belong to the consumed request.
    for name in ("operators.npz", "model.json", "row-identities.json"):
        require(OPERATORS / name in pins, "operator input missing from consumed closure")
    api.authenticate(pins)
    return api, pins, request


def state_key(record):
    case, gap = record["case_id"], record["gap_scale"]
    require(case in ALL_CASES and type(gap) in (int,float) and gap in (0.,1.), "unsupported case/gap identity")
    return case, gap


def state_tag(key):
    return key[0]+("_zero" if key[1] == 0 else "_gap")


def response_inventory(api, pins, response, comparison, inputs, loader):
    """Bind accepted records and finite exclusions; never recover a stopped field."""
    path = response / "comparison.json"
    def source_record(pointer):
        return {"path":api.key(path),"sha256":pins[path],"pointer":pointer}
    accepted = {}
    for index, state in enumerate(comparison["states"]):
        key = state_key(state)
        audit = state["audit"]
        require(key not in accepted and audit["all_passed"] is True
                and audit["checks"] and all(value is True for value in audit["checks"].values()),
                "duplicate or unaccepted source state: "+state_tag(key))
        accepted[key] = source_record("/states/"+str(index))
    require(accepted, "at least one actually accepted source state is required")
    records = comparison.get("case_dispositions")
    if records is None:
        require(comparison["status"] == COMPLETE_RESPONSE, "partial response lacks disposition inventory")
        records = [{"case_id":case,"gap_scale":gap,"status":ACCEPTED_STATE,
                    "accepted_force_field_exists":True,"response_tag":state_tag((case,gap)),"physical_release":False}
                   for case,gap in accepted]
    declared = {}
    for index, original in enumerate(records):
        item = copy.deepcopy(original)
        key, status = state_key(item), item["status"]
        require(key not in declared and item.get("physical_release") is False, "invalid repeated/released disposition")
        item.update(state_tag=state_tag(key), source_disposition_record=(
            source_record("/case_dispositions/"+str(index)) if "case_dispositions" in comparison else None))
        if status == ACCEPTED_STATE:
            require(item["accepted_force_field_exists"] is True and key in accepted
                    and item["response_tag"] == state_tag(key), "accepted disposition/field identity differs")
            item.update(source_state_record=accepted[key],finite_disposition_completed=True)
        else:
            require(status in (FLOOR_STOP,NUMERICAL_STOP) and item["accepted_force_field_exists"] is False
                    and key not in accepted and item.get("physical_frame_failure_claim") is False,
                    "unsupported stop disposition or rejected force transferred")
            evidence = item["stop_evidence"]
            packet, trace = (ROOT/evidence["packet"]).resolve(), (ROOT/evidence["trace_path"]).resolve()
            require(packet.is_relative_to(ROOT) and trace.is_relative_to(packet)
                    and evidence["pointer"] == "exception", "stop evidence leaves source packet")
            receipt_path = packet/"receipt.json"
            digest = evidence["receipt_sha256"]
            require(digest is not None or packet == response, "only current-packet receipt may omit self hash")
            if digest is not None:
                api.bind(pins,receipt_path,digest)
            else:
                require(receipt_path in pins, "current source receipt is not bound")
            receipt = read(receipt_path)
            if packet == response:
                require(receipt["status"] == comparison["status"], "current stop receipt status differs")
            elif receipt["status"] == PARTIAL_RESPONSE:
                partial_path = packet/"comparison.json"
                api.bind(pins,partial_path,receipt["output_sha256"]["comparison.json"])
                partial = read(partial_path)
                matches = [entry for entry in partial["case_dispositions"] if state_key(entry) == key]
                require(status == FLOOR_STOP and partial["status"] == PARTIAL_RESPONSE
                        and partial["complete_requested_state_inventory"] is True
                        and partial["reviewed_geometry_changed"] is False and len(matches) == 1
                        and matches[0]["status"] == FLOOR_STOP and matches[0]["accepted_force_field_exists"] is False
                        and all(state_key(state) != key for state in partial["states"]),
                        "external partial source lacks exact excluded floor case/gap")
                original_evidence = matches[0]["stop_evidence"]
                require(all(original_evidence[field] == evidence[field] for field in
                        ("packet","trace_path","trace_sha256","pointer"))
                        and matches[0]["floor_search_summary"] == item["floor_search_summary"],
                        "external partial stopped disposition/trace provenance differs")
            else:
                require(receipt["status"] == "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN",
                        "stop receipt has unsupported source status")
            api.bind(pins,trace,evidence["trace_sha256"])
            require(receipt["output_sha256"].get(trace.relative_to(packet).as_posix()) == evidence["trace_sha256"],
                    "stopped trace is absent from exact source receipt outputs")
            trace_data, stopped_inputs = read(trace), read(packet/"inputs.json")
            api.bind(pins,packet/"inputs.json",receipt["output_sha256"]["inputs.json"])
            require(stopped_inputs["preparation"] == inputs["preparation"]
                    and stopped_inputs["wood_reduction"] == inputs["wood_reduction"]
                    and stopped_inputs["dead_load_factor"] == inputs["dead_load_factor"]
                    and stopped_inputs["proposal_ties_included"] is False, "stopped source physics differs")
            if "case_id" in trace_data:
                require(state_key(trace_data) == key, "stopped trace has another case/gap")
            else:
                require(stopped_inputs["cases"] == [key[0]] and stopped_inputs["gap_scales"] == [key[1]],
                        "unkeyed stop is not an isolated exact case/gap")
            if status == FLOOR_STOP:
                exception = trace_data["exception"]
                pure = loader.definitions(response/"producer.py.snapshot",("floor_failure_summary",),
                    {"json":json,"require":require,"FLOOR_FAILURE_PREFIX":FLOOR_FAILURE_PREFIX})
                require(pure.floor_failure_summary(exception) == item["floor_search_summary"],
                        "finite search census differs from saved complete trace")
                history = json.loads(exception[len(FLOOR_FAILURE_PREFIX):])
                masks = [entry["bearing_footprints"] for entry in history]
                require(all(len(set(mask)) == len(mask) and all(type(i) is int and 0 <= i < 8 for i in mask)
                            for mask in masks)
                        and {sum(1 << i for i in mask) for mask in masks} == set(range(256)),
                        "finite search does not cover exactly the 256 original masks")
                item.update(finite_disposition_completed=True,physical_equilibrium_nonexistence_proven=False)
            else:
                item["finite_disposition_completed"] = False
        declared[key] = item
    require({key for key,item in declared.items() if item["accepted_force_field_exists"]} == set(accepted),
            "accepted state/disposition census differs")
    require((comparison["status"] == PARTIAL_RESPONSE) == any(
            not item["accepted_force_field_exists"] for item in declared.values()),
            "source completed/partial status contradicts accepted-state census")
    selected = {(case,gap) for case in inputs["cases"] for gap in inputs["gap_scales"]}
    if "case_dispositions" in comparison:
        require(set(declared) == selected and comparison["complete_requested_state_inventory"] is True,
                "source selected-state disposition inventory is incomplete")
    inventory = []
    for case in ALL_CASES:
        for gap in (0.,1.):
            key = case,gap
            inventory.append(declared.get(key,{"case_id":case,"gap_scale":gap,"state_tag":state_tag(key),
                "status":"UNASSESSED_REQUIRED_STATE","accepted_force_field_exists":False,
                "finite_disposition_completed":False,"source_disposition_record":None,"physical_release":False}))
    api.authenticate(pins)
    return inventory, accepted


def new_output(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def finish(output, api, pins, report, started):
    api.authenticate(pins)
    report.update(source_sha256={api.key(p): h for p, h in pins.items()},
                  physical_release=False, complete_joint_acceptance=False,
                  numerical_goal_complete=False, limits=LIMITS)
    write(output / "summary.json", report)
    outputs = {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}
    write(output / "receipt.json", {"schema": "joint_frame_action_reconciliation_receipt/v1",
        "status": report["status"], "source_sha256": report["source_sha256"], "output_sha256": outputs,
        "elapsed_seconds": time.monotonic()-started, "physical_release": False,
        **{key:report[key] for key in ("required_state_inventory","counts","finite_state_disposition_inventory_complete",
            "action_state_scope","action_exports_complete_for_accepted_states") if key in report},
        "source_producers_solvers_native_CAD_or_tests_executed": False})
    api.authenticate(pins)
    require(all(sha(output / name) == digest for name, digest in outputs.items()), "published output changed")
    return report


def prepare(output, preparation, reduction):
    started = time.monotonic()
    api, pins, request = sources(preparation, reduction)
    output = new_output(output)
    write(output / "input-plan.json", {"preparation": str(Path(preparation).resolve().relative_to(ROOT)),
        "wood_reduction": str(Path(reduction).resolve().relative_to(ROOT)),
        "reviewed_axes": 104, "Hillman_axes": 66, "cases": list(ALL_CASES),
        "permanent_case_id": PERMANENT, "permanent_load_columns": {"gravity":0,"live":None},
        "permanent_duration_factor_for_downstream_strength": .9,
        "new_ports": request["new_port_count"], "required_body_balances_per_state": 50,
        "response_required": "completed accepted-state packet, or PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS; authenticated receipt and actual audit-passed fields only"})
    return finish(output, api, pins, {"schema": "joint_frame_action_reconciliation_preparation/v1",
        "status": "PREPARED_SOURCE_ONLY_NOT_ACTION_OR_RESISTANCE_RESULTS"}, started)


def build(output, preparation, reduction, response):
    """Parent-run saved-array postprocessing only; no equation solve is called."""
    import numpy as np

    started = time.monotonic()
    api, pins, request = sources(preparation, reduction, response)
    preparation, reduction, response = [Path(p).resolve() for p in (preparation, reduction, response)]
    loader = module(HERE / "panel-reference-completion.py", "coupled_action_pure_definitions")
    namespace = {"np": np, "require": require, "TOL": 1e-5}
    actions_api = loader.definitions(RESUME / "top_corner_actions.py", ("wrench", "physical_actions"), namespace)
    section_api = loader.definitions(RESUME / "member_screen.py",
        ("basis", "cut_vectors", "rectangle_at", "section_stations"), namespace)
    floor_api = loader.definitions(RESUME / "simple_frame.py", ("lump_floor",), namespace)
    revised, model = read(OPERATORS / "model.json"), read(MODEL)
    names = revised["body_names"]
    require(len(names) == 50 and set(names) == set(model["physical_body_nodes"]), "50-body census differs")
    require(model["physical_body_nodes"] == revised["body_nodes"], "physical node ownership changed")
    model["nodes"] = revised["physical_node_coordinates_mm"]
    geometry = read(BASELINE / "geometry.json")
    records = geometry["members"]
    require(len(records) == 44 and len(set(names)-set(records)) == 6, "44-timber/six-panel census differs")
    centers = {b: np.mean([model["nodes"][str(n)] for n in sorted(set(model["physical_body_nodes"][b]))], axis=0)
               for b in names}
    for body in names:
        if body in records:
            model["body_geometry"][body]["geometry_record"] = records[body]["geometry"]
        else:
            # Panel actions use this named chart only for station metadata;
            # timber beam sections are never assigned to these six bodies.
            panel_axis = revised["material_binding"]["panel_axes"][body]["assumed_apa_direction_1_global_xyz"]
            model["body_geometry"][body]["geometry_record"] = {"start": centers[body].tolist(), "axis": panel_axis}
    rows = read(OPERATORS / "row-identities.json")
    require([r["row"] for r in rows] == list(range(len(rows))), "canonical row order changed")
    labels = [tuple(map(int, line.split("."))) for line in DOFS.read_text().splitlines() if line.strip()]
    require(len(set(labels)) == len(labels) and all(d in (1, 2, 3) for _, d in labels), "invalid load DOF labels")
    contact_path = BASE / "reduced-static-attempt01/contact-geometry.json"
    api.bind(pins, contact_path, read(BASELINE / "member-results.json")["source_sha256"][api.key(contact_path)])
    contact = read(contact_path)
    patches = {c["name"]: {"area": c["area_mm2"],
        "vertices": contact["contact_patches"][c["source_patch_index"]]["vertices_xyz_mm"]}
        for c in model["contact_cell_ownership"] if c["kind"] == "timber_or_panel_contact"}
    corrected = read(RESUME / "top-corner-contact-geometry.json")
    for row in rows:
        if "contact_area_mm2" in row:
            own = row["ownership"]
            cleat = next(c for c in corrected["cleats"] if c["block"] == own["second_body"])
            face = next(f for f in cleat["faces"] if f["host"] == own["first_body"])
            patches[row["row_id"]] = {"area": row["contact_area_mm2"], "vertices": face["corners_mm"]}
    api.authenticate(pins)
    port_labels = read(preparation / "port-labels.json")["new_ports"]
    terms = request["new_wood_port_terms"]
    require(len(port_labels) == len(terms) == request["new_port_count"], "new port census differs")
    comparison, inputs = read(response / "comparison.json"), read(response / "inputs.json")
    states = comparison["states"]
    inventory, accepted_sources = response_inventory(api,pins,response,comparison,inputs,loader)
    identities = [state_key(s) for s in states]
    require(inputs["dead_load_factor"] == revised["dead_load_factor"], "reviewed gravity factor changed")
    if any(case == PERMANENT for case, _ in identities):
        permanent = read(PERMANENT_BASE / "comparison.json")
        require(inputs["permanent_only_load_columns"] == {"gravity":0,"live":None}
                and inputs["elastic_duration_factor"] == 1.
                and permanent["status"] == "COMPLETED_CONDITIONAL_DEAD_ONLY_COMPARISON"
                and permanent["load_columns"] == {"gravity":0,"live":None}
                and permanent["dead_load_factor"] == revised["dead_load_factor"]
                and permanent["modeled_mass_kg"] == revised["modeled_mass_kg"]
                and permanent["output_sha256"]["response.npz"] == PINS[PERMANENT_BASE / "response.npz"],
                "permanent source load/starting-response identity changed")
        for name in ("operators.npz", "model.json", "row-identities.json"):
            require(permanent["source_sha256"][api.key(OPERATORS / name)] == pins[OPERATORS / name],
                    "permanent source uses another frame basis")
    output = new_output(output)
    write(output / "inputs.json", {"preparation": api.key(preparation), "wood_reduction": api.key(reduction),
        "response": api.key(response), "states": identities, "source_force_basis": "reviewed104_coupled_knee_sensitivity",
        "source_response_status":comparison["status"],"required_state_inventory":inventory,
        "dead_load_factor": revised["dead_load_factor"], "permanent_case_id":PERMANENT,
        "permanent_load_columns":{"gravity":0,"live":None},
        "permanent_duration_factor_for_downstream_strength":.9,
        "source_sha256": {api.key(p): h for p, h in pins.items()}})
    summaries, branch_arrays, branch_geometry, branch_ids, branch_cases = [], {}, {}, {}, {}
    canonical_response = {}
    with np.load(OPERATORS / "operators.npz", allow_pickle=False) as original, \
            np.load(reduction / "wood-operators.npz", allow_pickle=False) as wood, \
            np.load(preparation / "joint-operators.npz", allow_pickle=False) as joint, \
            np.load(response / "response.npz", allow_pickle=False) as saved, \
            np.load(HERE / "frame-250-attempt02/response.npz", allow_pickle=False) as prior, \
            np.load(PERMANENT_BASE / "response.npz", allow_pickle=False) as prior_permanent, \
            gzip.open(output / "body-actions.jsonl.gz", "wt") as action_stream:
        require(set(saved.files) == {state_tag(key)+suffix for key in accepted_sources for suffix in
                ("_force_n","_relative_motion_mm","_rigid_scaled_mm","_shaft_pose_mm","_bearing")},
                "saved response contains missing, unlisted or rejected state fields")
        D, F, W = [original[k] for k in ("D", "F", "W")]
        require(D.shape == (len(rows), 300) and F.shape == (len(labels), 12) and W.shape == (300, 12),
                "source D/F/W dimensions differ")
        require(all(np.isfinite(v).all() for v in (D, F, W)), "nonfinite source operators")
        *_, T, _footprints = floor_api.lump_floor(original["H"], D, original["e"], W, rows)
        kept = joint["old_kept_lumped_rows"]
        require(kept.tolist() == request["old_kept_lumped_rows"], "kept floor/source row map changed")
        require(np.array_equal(wood["Dwood"][:len(kept)], (T @ D)[kept])
                and np.array_equal(wood["Wwood"], W), "consumed rigid/load maps changed")
        kept_map = T[kept]
        available = np.any(kept_map != 0., axis=0)
        require(np.all(np.count_nonzero(kept_map,axis=0) <= 1), "source row occurs in multiple kept lumped rows")
        positions = np.where(available,np.argmax(kept_map != 0.,axis=0),-1)
        canonical_response["canonical_raw_row_available"] = available
        canonical_response["canonical_raw_row_to_kept_lumped_position"] = positions
        canonical_response["old_kept_lumped_rows"] = kept
        write(output / "source-row-map.json", {"old_kept_lumped_rows":kept.tolist(),
            "unavailable_replaced_canonical_rows":np.flatnonzero(~available).tolist(),
            "kept_map":[{"kept_position":position,"lumped_row":int(i),"raw_rows":np.flatnonzero(T[i]).tolist(),
                         "weights":T[i,np.flatnonzero(T[i])].tolist()} for position,i in enumerate(kept)],
            "unavailable_zero_placeholders_are_not_zero_demand_results":True})
        for state in states:
            case, gap = state["case_id"], state["gap_scale"]
            tag, branch = case + ("_zero" if gap == 0 else "_gap"), ("zero-gap" if gap == 0 else "nominal-gap")
            if case == PERMANENT:
                branch = "permanent-"+branch
            force = saved[tag + "_force_n"]
            require(force.shape == (len(kept)+len(terms),) and np.isfinite(force).all(), "invalid coupled force vector")
            raw = T[kept].T @ force[:len(kept)]
            canonical_response[tag+"_raw_force_n"] = raw
            canonical_response[tag+"_kept_lumped_relative_motion_mm"] = saved[tag+"_relative_motion_mm"][:len(kept)]
            canonical_response[tag+"_coupled_force_n"] = force
            load_column = 0 if case == PERMANENT else 2*CASES.index(case)
            body_load = revised["dead_load_factor"]*W[:,load_column]
            if case != PERMANENT:
                body_load = body_load+W[:,load_column+1]
            coupled_balance = wood["Dwood"].T @ force - body_load
            require(np.max(abs(coupled_balance.reshape(50,6)[:,:3])) <= .1
                    and 1000*np.max(abs(coupled_balance.reshape(50,6)[:,3:])) <= 2., "saved wood equilibrium does not close")
            maps = []
            for column in ((load_column,) if case == PERMANENT else (load_column,load_column+1)):
                mapped = {}
                for (node, dof), value in zip(labels, F[:,column], strict=True):
                    if value != 0:
                        mapped.setdefault(str(node), [0.,0.,0.])[dof-1] = float(value)
                maps.append(mapped)
            case_map = {"gravity_nodal_map": maps[0], "climber_nodal_map": {} if case == PERMANENT else maps[1],
                        "dead_load_factor": revised["dead_load_factor"]}
            arrays = branch_arrays.setdefault(branch, {})
            export_geometry = branch_geometry.setdefault(branch, copy.deepcopy(geometry))
            inventories = branch_ids.setdefault(branch, {})
            balances, timber_results = [], []
            global_load, global_support = np.zeros(6), np.zeros(6)
            for body_index, body in enumerate(names):
                actions, center, chart = actions_api.physical_actions(body, case_map, raw, model, rows, D, names, patches)
                for action in actions:
                    action["source_force_available"] = action["row"] is None or bool(available[action["row"]])
                    action["replaced_source_row_placeholder"] = not action["source_force_available"]
                for port, point_terms in enumerate(terms):
                    for term_index, term in enumerate(point_terms):
                        if term["member_id"] != body:
                            continue
                        point = np.asarray(term["point_mm"])
                        direction = np.asarray(term["direction_global_xyz"])
                        value = -float(force[len(kept)+port])*direction
                        station = float(np.asarray(chart["axis"]) @ (point-chart["start"]))
                        label = port_labels[port]
                        actions.append({"row": None, "coupled_port_row": len(kept)+port,
                            "axis_id":label["axis_id"],"source_force_available":True,"replaced_source_row_placeholder":False,
                            "source_id": f"coupled/{label['axis_id']}/{port}/{term_index}", "role": label["role"],
                            "other_body": None, "other_component": "continuous_knee_shaft_or_washer",
                            "point_mm": point.tolist(), "force_n": value.tolist(), "free_moment_nmm": [0.,0.,0.],
                            "station_mm": station, "footprint_mm": [station,station],
                            "cell_area_mm2": label.get("area_mm2"), "scalar_row_force_n": float(force[len(kept)+port])})
                closure = actions_api.wrench(actions, center)
                loads = [a for a in actions if a["role"] == "discrete_body_load"]
                load_wrench = actions_api.wrench(loads, center)
                expected = body_load[6*body_index:6*body_index+6]*[1,1,1,1000,1000,1000]
                require(np.max(abs(load_wrench-expected)) < 1e-6, "F/W source-load mismatch: "+tag+"/"+body)
                require(np.max(abs(closure[:3])) <= .1 and np.max(abs(closure[3:])) <= 2.,
                        "physical body imbalance: "+tag+"/"+body)
                connector = [a for a in actions if a["role"] != "discrete_body_load"]
                expected_connector = -(wood["Dwood"][:,6*body_index:6*body_index+6].T @ force)*[1,1,1,1000,1000,1000]
                require(np.max(abs(actions_api.wrench(connector, center)-expected_connector)) < 1e-5,
                        "point actions do not reproduce consumed Dwood: "+tag+"/"+body)
                global_load += actions_api.wrench(loads, np.zeros(3))
                global_support += actions_api.wrench([a for a in actions if a["other_body"] == "floor"], np.zeros(3))
                balance = {"body": body, "center_mm": center.tolist(), "closure_n_nmm": closure.tolist(),
                           "source_W_n_nmm": expected.tolist(), "point_action_count": len(actions)}
                balances.append(balance)
                action_stream.write(json.dumps({"state_tag":tag,"case_id":case,"gap_scale":gap,"body":body,
                    "source_state_record":accepted_sources[(case,gap)],
                    "center_mm":center.tolist(),"actions":actions},separators=(",",":"),allow_nan=False)+"\n")
                if body not in records:
                    continue
                record = export_geometry["members"][body]
                stations = np.asarray(records[body]["stations_mm"])
                event_stations = section_api.section_stations(actions, record, [])
                prefix, frame = case+"__"+body, section_api.basis(chart)
                for suffix, cuts in (("", stations), ("__event", event_stations)):
                    negative, positive, *_ = section_api.cut_vectors(actions, chart, cuts)
                    arrays[prefix+suffix+"__internal_negative_grain_u_v"] = np.column_stack((negative[:,:3]@frame.T,negative[:,3:]@frame.T))
                    arrays[prefix+suffix+"__internal_positive_grain_u_v"] = np.column_stack((positive[:,:3]@frame.T,positive[:,3:]@frame.T))
                arrays[prefix+"__point_force_free_couple_xyz"] = np.asarray([a["force_n"]+a["free_moment_nmm"] for a in actions])
                point_inventory = ([a["source_id"] for a in actions], [a["point_mm"] for a in actions], event_stations.tolist())
                if body in inventories:
                    require(inventories[body] == point_inventory, "body action/station identities changed between cases")
                else:
                    inventories[body] = point_inventory
                    record.update(point_action_ids=point_inventory[0], point_action_roles=[a["role"] for a in actions],
                        point_action_other_bodies=[a["other_body"] for a in actions], event_stations_mm=point_inventory[2],
                        source_station_indices_preserved=True)
                    for suffix, values in (("point_xyz_mm",point_inventory[1]),("point_stations_mm",[a["station_mm"] for a in actions]),
                        ("point_footprints_mm",[a["footprint_mm"] for a in actions]),
                        ("point_rows",[-1 if a["row"] is None else a["row"] for a in actions]),("event_stations_mm",point_inventory[2])):
                        arrays[body+"__"+suffix] = np.asarray(values)
                timber_results.append({"member":body,"array_prefix":prefix,"point_action_count":len(actions),
                    "cut_trace_count":2*len(stations),"event_cut_trace_count":2*len(event_stations),"whole_member_balance_n_nmm":closure.tolist()})
            require(len(balances) == 50 and len(timber_results) == 44, "body result census incomplete")
            global_closure = global_load+global_support
            require(np.max(abs(global_closure[:3])) <= 5. and np.max(abs(global_closure[3:])) <= 100.,
                    "whole-frame external/support closure failed")
            old_force = (prior_permanent if case == PERMANENT else prior)[tag+"_raw_force_n"]
            # The original saved raw vector is compared only at retained rows;
            # new fields never inherit its shaft/contact capacity results.
            require(old_force.shape == (len(rows),), "prior canonical raw force shape differs")
            nonfloor = [r["row"] for r in rows if r["ownership"]["second_body"] != "floor"]
            old_lumped = np.r_[old_force[nonfloor],
                [old_force[np.flatnonzero(T[i])].sum() for i in range(len(nonfloor),len(T))]]
            require(old_lumped.shape == (len(T),), "prior response comparison vector differs")
            difference = force[:len(kept)]-old_lumped[kept]
            summaries.append({"state_tag":tag,"case_id":case,"gap_scale":gap,"body_balances":balances,
                "source_state_record":accepted_sources[(case,gap)],
                "load_scope":state["load_scope"],"section_branch":branch,
                "duration_factor_for_downstream_strength":.9 if case == PERMANENT else 1.,
                "source_load_wrench_about_global_origin_n_nmm":global_load.tolist(),
                "floor_wrench_about_global_origin_n_nmm":global_support.tolist(),
                "external_closure_n_nmm":global_closure.tolist(),"retained_force_bitwise_identical":bool(np.array_equal(force[:len(kept)],old_lumped[kept])),
                "retained_force_change_peak_n":float(np.max(abs(difference))),
                "retained_changed_force_rows":int(np.count_nonzero(difference)),"strength_comparisons_reused":False})
            branch_cases.setdefault(branch,[]).append({"state_tag":tag,"case_id":case,"gap_scale":gap,
                "source_state_record":accepted_sources[(case,gap)],
                "source_force_key":tag+"_force_n","members":timber_results})
    np.savez_compressed(output / "source-row-response.npz", **canonical_response)
    for branch, arrays in branch_arrays.items():
        directory = output / branch
        directory.mkdir()
        np.savez_compressed(directory / "action-section-arrays.npz", **arrays)
        write(directory / "geometry.json", branch_geometry[branch])
        write(directory / "member-actions.json", {"schema":"coupled_frame_member_action_export/v1",
            "source_force_basis":"reviewed104_coupled_knee_sensitivity","cases":branch_cases[branch],
            "same_state_dead_load_factor":revised["dead_load_factor"],
            "duration_factor_for_downstream_strength":.9 if branch.startswith("permanent-") else 1.,
            "resistance_comparisons_executed":False})
    counts = {"required_states":len(inventory),"accepted_states":len(states),
        "finite_floor_search_dispositions":sum(item["status"] == FLOOR_STOP for item in inventory),
        "unassessed_states":sum(item["status"] == "UNASSESSED_REQUIRED_STATE" for item in inventory),
        "unresolved_numerical_stops":sum(item["status"] == NUMERICAL_STOP for item in inventory),
        "rejected_force_fields_exported":0}
    counts["assessed_states"] = counts["accepted_states"]+counts["finite_floor_search_dispositions"]
    return finish(output,api,pins,{"schema":"joint_frame_action_reconciliation/v1",
        "status":"COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION",
        "source_response_status":comparison["status"],"required_state_inventory":inventory,"counts":counts,
        "finite_state_disposition_inventory_complete":all(item["finite_disposition_completed"] for item in inventory),
        "action_state_scope":"all14_accepted_states" if len(states) == 14 else "accepted_state_subset",
        "action_exports_complete_for_accepted_states":True,
        "states":summaries,"completed_states":len(states),
        "all12_live_states":{(c,g) for c,g in identities if c in CASES}=={(c,g) for c in CASES for g in (0.,1.)},
        "both_permanent_states":{(c,g) for c,g in identities if c == PERMANENT}=={(PERMANENT,g) for g in (0.,1.)},
        "all14_required_states":set(identities)=={(c,g) for c in ALL_CASES for g in (0.,1.)},
        "body_balance_count":50*len(states),"timber_members":44,"panel_bodies":6,
        "source_station_inventory_preserved":True,"source_force_basis":"reviewed104_coupled_knee_sensitivity",
        "strength_comparisons_complete":False,"source_producers_or_solves_executed":False},started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare","build"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--wood-reduction", type=Path, required=True)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "build" and args.response is None:
        parser.error("build requires --response")
    try:
        result = (build(args.output,args.preparation,args.wood_reduction,args.response)
                  if args.stage == "build" else prepare(args.output,args.preparation,args.wood_reduction))
    except (ValueError, KeyError, OSError) as error:
        output = args.output.resolve()
        if output.parent == RAW.resolve() and output.exists() and not (output / "receipt.json").exists():
            write(output / "stop.json", {"status":"STOP_ACTION_RECONCILIATION_INCOMPLETE",
                "error":str(error),"physical_frame_failure_claimed":False,"physical_release":False})
        raise
    print(json.dumps({"status":result["status"],"output":str(args.output)}))


if __name__ == "__main__":
    main()
