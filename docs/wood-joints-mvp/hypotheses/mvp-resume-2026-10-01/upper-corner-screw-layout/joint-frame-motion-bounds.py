"""Certify saved 344-coordinate fixed-force seating and its stability limits.

Preparation freezes existing receipts without solving. Build performs only
small nullspace/LP calculations: it changes no force, contact law, floor,
geometry, spring stiffness, or reference resistance. Import is inert.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RESUME = HERE.parent
RAW = HERE / "rawlocal/joint-frame-motion-bounds"
FRAME = HERE / "rawlocal/joint-frame-compatibility-completion/frame-attempt08"
PREPARATION = HERE / "rawlocal/joint-frame-compatibility-completion/prepare-attempt03"
REDUCTION = HERE / "rawlocal/joint-frame-port-reduction/attempt01"
ACTIONS = HERE / "rawlocal/joint-frame-action-reconciliation/attempt03"
ACTION_API = HERE / "joint-frame-action-reconciliation.py"
BOUNDS_API = RESUME / "bounded_clearance.py"
PINS = {
    FRAME / "receipt.json": "74930ca8ace4a79cbf9165f570bd2bb7785faba631324a83c0728f673e27ac2d",
    ACTIONS / "receipt.json": "370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e",
    BOUNDS_API: "35c0ceb7609c7ff77118ddf0a8e9f0da681ae41ad3396e4a95a71792724a9c7b",
}
MOTION_TOL = 1e-8
COEFFICIENT_TOL = 1e-11
ROTATION_SCALE = 1000.0
RUNTIME = {"numpy": "2.5.2", "scipy": "1.18.1"}
LIMITS = [
    "Fixed saved forces retain their recorded finite-law residuals; this is an audited numerical fixed-force pose set, not exact arithmetic force equality.",
    "Active finite-law and held no-slip motions are preserved. Inactive unilateral rows and free circular pairs retain the original laws; only certificate outer boxes are inflated by 1e-8 mm.",
    "Outer-box bounds enclose admissible circular-law poses. Box vertices are not admissible poses; witnesses are separately checked on the original disks.",
    "Bounds on rigid increments apply to every member point because elastic deformation is fixed at fixed force in this linear model. Absolute elastic nodal deformation is not recovered by this calculation.",
    "The fixed-force set does not envelope changed forces, coupled crack branches, stiffness changes, tolerance changes, or geometrically updated equilibria.",
    "First-order tangent freedoms, finite seating bounds, and finite rotation remainder estimates are separate results. No buckling eigenvalue, geometric stiffness, inertia, or dynamic stability is supplied by the source model.",
    "104 reviewed bolt axes, 66 Hillman screw axes, actual source geometry, the source 100 mm load lever, and the no-slip analytical floor assumption are unchanged.",
    "No resistance exceedance is repaired, numerical serviceability threshold invented, inspection claimed, or physical release made.",
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


def key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "missing helper loader")
    result = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(result)
    finally:
        sys.dont_write_bytecode = old
    return result


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "frozen source changed: " + key(path))


def fresh(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def sources(preparation, reduction, response, actions):
    """Reuse receipt closure and the exact accepted/excluded action inventory."""
    action = module(ACTION_API, "motion_bound_action_bindings")
    closure, pins, request = action.sources(preparation, reduction, response)
    pins[Path(__file__).resolve()] = sha(__file__)
    pins[BOUNDS_API] = PINS[BOUNDS_API]
    preparation, reduction, response, actions = [Path(p).resolve() for p in (preparation, reduction, response, actions)]
    for path, digest in PINS.items():
        if path == BOUNDS_API or path.parent in (response, actions):
            closure.bind(pins, path, digest)
    closure.bind(pins, actions / "receipt.json", sha(actions / "receipt.json"))
    closure.receipt_sources(pins, actions / "receipt.json")
    summary, action_inputs = read(actions / "summary.json"), read(actions / "inputs.json")
    require(summary["status"] == "COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION",
            "completed accepted-field action export required")
    require(all(action_inputs[name] == key(value) for name, value in (
        ("preparation", preparation), ("wood_reduction", reduction), ("response", response))),
        "action export does not consume the requested force basis")
    require(summary["counts"]["rejected_force_fields_exported"] == 0
            and summary["finite_state_disposition_inventory_complete"] is True,
            "action/disposition inventory incomplete")
    loader = module(HERE / "panel-reference-completion.py", "motion_bound_pure_source_definitions")
    comparison, inputs = read(response / "comparison.json"), read(response / "inputs.json")
    inventory, accepted = action.response_inventory(closure, pins, response, comparison, inputs, loader)
    require(inventory == action_inputs["required_state_inventory"], "force/disposition inventories disagree")
    require(inputs["panel_screw_component_count"] == 198 and request["reviewed_bolt_axes"] == 104
            and inputs["proposal_ties_included"] is False, "reviewed hardware policy changed")
    authenticate(pins)
    return pins, inventory, accepted


def prepare(output, preparation=PREPARATION, reduction=REDUCTION, response=FRAME, actions=ACTIONS):
    started = time.monotonic()
    pins, inventory, accepted = sources(preparation, reduction, response, actions)
    output = fresh(output)
    request = {
        "schema": "joint_frame_fixed_force_motion_request/v1",
        "preparation": key(preparation), "wood_reduction": key(reduction),
        "response": key(response), "actions": key(actions),
        "source_sha256": {key(p): h for p, h in pins.items()},
        "required_state_inventory": inventory, "accepted_tags": [item["state_tag"] for item in inventory
            if item["accepted_force_field_exists"]],
        "fixed_force_only": True, "motion_tolerance_mm": MOTION_TOL,
        "coefficient_roundoff_threshold": COEFFICIENT_TOL,
        "baseline_300_certificate_transferred": False,
        "current_system_coordinate_count": 344,
        "runtime": RUNTIME, "limits": LIMITS,
        "source_producers_frame_native_or_CAD_executed": False,
    }
    write(output / "request.json", request)
    authenticate(pins)
    write(output / "receipt.json", {
        "status": "PREPARED_FIXED_FORCE_MOTION_REQUEST_NOT_MOTION_RESULTS",
        "source_sha256": request["source_sha256"],
        "output_sha256": {name: sha(output / name) for name in (".gitignore", "producer.py.snapshot", "request.json")},
        "elapsed_seconds": time.monotonic()-started, "accepted_states": len(accepted), "physical_release": False,
    })
    return {"status": "PREPARED_FIXED_FORCE_MOTION_REQUEST_NOT_MOTION_RESULTS",
            "request": key(output / "request.json"), "request_sha256": sha(output / "request.json")}


def peak(np, values):
    return float(np.max(np.abs(values), initial=0.0))


def pose_problem(np, bounds, D, q, k, uni, normals, tangents, bearing, pairs, gaps):
    """Original fixed-law nullspace with a conservative disk-box enclosure.

    The existing helper's nullspace routine is reusable; its complete old
    certificate is limited to 300 body coordinates and is deliberately unused.
    """
    columns = D.shape[1]
    free = np.linalg.norm(q[pairs], axis=1) <= gaps + MOTION_TOL
    active = (k > 0) & (~uni | (q > MOTION_TOL))
    active[pairs] = ~free[:, None]
    active[tangents[bearing]] = True
    inactive = np.flatnonzero(uni & ~active)
    fixed = np.flatnonzero(active)
    free_rows = pairs[free].ravel()
    require(np.max(q[inactive], initial=0) <= MOTION_TOL, "inactive source contact is outside its original law")
    N, svd = bounds.nullspace(D[fixed], columns, normalize=True)
    require(peak(np, D[fixed] @ N) < MOTION_TOL, "fixed-motion nullspace residual too large")
    DN = D @ N
    # Discard only recorded SVD roundoff, avoiding enormous false bounds from
    # 1e-16 leakage into otherwise identically absent rigid coordinates.
    cleaned = DN.copy()
    cleaned[abs(cleaned) < COEFFICIENT_TOL] = 0
    A = np.vstack((cleaned[inactive], cleaned[free_rows], -cleaned[free_rows]))
    radii = np.repeat(gaps[free], 2)
    b = np.r_[-q[inactive], radii-q[free_rows], radii+q[free_rows]] + MOTION_TOL
    return {"N": N, "DN": DN, "A": A, "b": b, "fixed": fixed, "inactive": inactive,
            "free_rows": free_rows, "free_pairs": pairs[free], "free_gaps": gaps[free],
            "svd": svd, "coefficient_roundoff_peak": peak(np, cleaned-DN), "calls": 0,
            "dual": [], "extrema": [], "rays": [], "certificates": []}


def extremum(np, optimize, problem, objective, label, *, retain=False):
    """LP support with checked nonnegative dual, or original-law recession ray."""
    c = np.asarray(objective, dtype=float).copy()
    c[abs(c) < COEFFICIENT_TOL] = 0
    A, b, N, DN = [problem[name] for name in ("A", "b", "N", "DN")]
    m, scale = N.shape[1], peak(np, c)
    if m == 0 or scale == 0:
        return {"status": "finite", "maximum": 0.0, "zero_observable": True}, np.zeros(m)
    options = {"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9}
    problem["calls"] += 1
    result = optimize.linprog(-c/scale, A_ub=A, b_ub=b, bounds=[(None, None)]*m,
                              method="highs", options=options)
    if result.status == 3:
        problem["calls"] += 1
        ray_lp = optimize.linprog(np.zeros(m), A_ub=np.vstack((A, -c[None]/scale)),
            b_ub=np.r_[np.zeros(len(b)), -1.], bounds=[(None, None)]*m, method="highs", options=options)
        require(ray_lp.success, "unbounded objective has no recession certificate: " + label)
        ray = ray_lp.x / peak(np, ray_lp.x)
        delta = N @ ray
        dq = DN @ ray
        checks = {"fixed_motion_residual_mm": peak(np, dq[problem["fixed"]]),
                  "disk_direction_residual_mm": peak(np, dq[problem["free_rows"]]),
                  "inactive_direction_excess_mm": float(np.max(dq[problem["inactive"]], initial=0)),
                  "objective_gain": float(c @ ray)}
        require(all(checks[name] < MOTION_TOL for name in checks if name != "objective_gain")
                and checks["objective_gain"] > 0, "recession ray violates original laws: " + label)
        record = {"objective": label, "null_direction": ray.tolist(), "coordinate_direction": delta.tolist(),
                  "body_projection_norm": float(np.linalg.norm(delta[:min(300, len(delta))])), "checks": checks}
        problem["rays"].append(record)
        return {"status": "unbounded", "maximum": None, "recession_certificate": len(problem["rays"])-1}, None
    require(result.success, "unresolved bound " + label + ": " + result.message)
    dual = -scale * result.ineqlin.marginals
    primal, upper = float(c @ result.x), float(b @ dual)
    residual = peak(np, A.T @ dual-c)
    violation = float(np.max(A @ result.x-b, initial=0))
    require(np.min(dual, initial=0) >= -1e-9*max(scale, 1)
            and residual < 1e-8*max(scale, 1) and violation < MOTION_TOL
            and abs(primal-upper) < 1e-7*max(abs(primal), 1), "primal/dual certificate failed: " + label)
    record = {"status": "finite", "maximum": upper, "primal_value": primal,
              "dual_residual": residual, "primal_violation_mm": violation,
              "minimum_dual": float(np.min(dual, initial=0))}
    if retain:
        record["dual_multiplier_row"] = len(problem["dual"])
        problem["dual"].append(dual)
        problem["certificates"].append({"objective": label, **record})
        problem["extrema"].append(result.x)
    return record, result.x


def component_bounds(np, optimize, problem, mapping, label, *, retain=False):
    projected = mapping @ problem["N"]
    intervals, certificates = [], []
    for i, row in enumerate(projected):
        low, _ = extremum(np, optimize, problem, -row, f"{label}/{i}/minimum", retain=retain)
        high, _ = extremum(np, optimize, problem, row, f"{label}/{i}/maximum", retain=retain)
        intervals.append([-low["maximum"] if low["maximum"] is not None else None, high["maximum"]])
        certificates.append({"lower": low, "upper": high})
    return intervals, certificates


def original_law_witness(np, problem, q, W):
    """Shorten an LP extremum into the actual disks and unilateral halfspaces."""
    N, DN, inactive = [problem[name] for name in ("N", "DN", "inactive")]
    for endpoint in sorted(problem["extrema"], key=lambda z: np.linalg.norm((N @ z)[:min(300, len(q))]), reverse=True):
        dq = DN @ endpoint
        fraction = 1.
        for row in inactive:
            if dq[row] > 1e-11:
                fraction = min(fraction, max(0., -q[row])/dq[row])
        for pair, gap in zip(problem["free_pairs"], problem["free_gaps"], strict=True):
            u, v = q[pair], dq[pair]
            aa, bb, cc = float(v@v), float(2*u@v), float(u@u-gap**2)
            require(cc <= MOTION_TOL, "witness source lies outside original disk")
            if aa > 1e-22:
                fraction = min(fraction, max(0., (-bb+np.sqrt(max(0., bb**2-4*aa*min(cc, 0.))))/(2*aa)))
        z = .5*fraction*endpoint
        delta = N @ z
        if np.linalg.norm(delta[:min(300, len(delta))]) <= 1e-5:
            continue
        moved = q + DN @ z
        errors = {"fixed_motion_change_mm": peak(np, (DN @ z)[problem["fixed"]]),
                  "inactive_positive_motion_mm": float(np.max(moved[inactive], initial=0)),
                  "disk_excess_mm": float(np.max(np.linalg.norm(moved[problem["free_pairs"]], axis=1)
                                                  -problem["free_gaps"], initial=0)),
                  "external_work_nmm": float(W @ delta)}
        require(max(errors[name] for name in errors if name != "external_work_nmm") <= MOTION_TOL,
                "shortened witness violates original contact laws")
        return {"coordinate_increment": delta.tolist(), "null_coordinates": z.tolist(),
                "body_coordinate_increment_norm_mm": float(np.linalg.norm(delta[:min(300,len(delta))])),
                "checks": errors, "force_field_changed": False}, moved
    return None, None


def norm_bound(np, intervals):
    if any(value is None for row in intervals for value in row):
        return None
    return float(np.linalg.norm(np.max(abs(np.asarray(intervals)), axis=1)))


def known_answer():
    """Analytic disk, bounded seating, metal-only line and unilateral ray coupons."""
    import numpy as np
    from scipy import optimize
    bounds = module(BOUNDS_API, "motion_bound_existing_nullspace_coupon")
    D, q = np.eye(3), np.zeros(3)
    problem = pose_problem(np, bounds, D, q, np.array([1.,1.,0.]), np.zeros(3,dtype=bool),
        np.array([],dtype=int), np.empty((0,2),dtype=int), np.array([],dtype=bool), np.array([[0,1]]), np.array([2.]))
    intervals, _ = component_bounds(np, optimize, problem, np.eye(3), "disk_metal", retain=True)
    require(all(abs(value-expected) < 1e-7 for row in intervals[:2] for value,expected in zip(row,(-2.,2.),strict=True))
            and intervals[2] == [None,None], "disk or metal-only analytic bound differs")
    witness, _ = original_law_witness(np,problem,q,np.zeros(3))
    require(witness is not None and witness["checks"]["disk_excess_mm"] <= MOTION_TOL,
            "analytic disk witness missing")
    p = pose_problem(np,bounds,np.eye(1),np.zeros(1),np.ones(1),np.ones(1,dtype=bool),
        np.array([],dtype=int),np.empty((0,2),dtype=int),np.array([],dtype=bool),np.empty((0,2),dtype=int),np.array([]))
    ray_intervals,_ = component_bounds(np,optimize,p,np.eye(1),"open_unilateral")
    require(ray_intervals[0][0] is None and abs(ray_intervals[0][1]) <= 1e-7,
            "open unilateral analytic recession differs")
    return {"status":"PASS_ANALYTIC_FIXED_FORCE_POSE_COUPONS", "disk_intervals":intervals,
            "open_unilateral_interval":ray_intervals[0], "original_disk_witness":witness,
            "recession_ray_checks":[ray["checks"] for ray in problem["rays"]+p["rays"]]}


def assemble(np, preparation, reduction):
    with np.load(preparation / "joint-operators.npz",allow_pickle=False) as source:
        joint = {name:source[name].copy() for name in source.files}
    with np.load(reduction / "wood-operators.npz",allow_pickle=False) as source:
        H,Dwood,e,Wwood = [source[name].copy() for name in ("Hwood","Dwood","ewood","Wwood")]
    nold = len(joint["old_kept_lumped_rows"])
    Bbolt = np.vstack((np.zeros((nold,joint["Bbolt"].shape[1])),joint["Bbolt"]))
    H[nold:,nold:] += joint["Bbolt"] @ joint["Cbolt"] @ joint["Bbolt"].T
    D = np.column_stack((Dwood,Bbolt @ joint["Rbolt"],np.vstack((np.zeros((nold,24)),joint["Dwasher"]))))
    require(D.shape[1] == 344 and Dwood.shape[1] == 300, "344-coordinate response layout changed")
    return joint,H,D,e,np.vstack((Wwood,np.zeros((44,12))))


def build(output, request_path, expected_sha256):
    import numpy as np
    import scipy
    from scipy import optimize

    started = time.monotonic()
    request_path = Path(request_path).resolve()
    require(sha(request_path) == expected_sha256, "request hash differs")
    request = read(request_path)
    require(request["schema"] == "joint_frame_fixed_force_motion_request/v1"
            and request["fixed_force_only"] is True and request["runtime"] == RUNTIME,
            "unsupported frozen request")
    require(request["baseline_300_certificate_transferred"] is False
            and request["current_system_coordinate_count"] == 344, "request transfers another coordinate certificate")
    require(np.__version__ == RUNTIME["numpy"] and scipy.__version__ == RUNTIME["scipy"], "pinned arithmetic runtime differs")
    preparation,reduction,response,actions = [ROOT/request[name] for name in ("preparation","wood_reduction","response","actions")]
    pins,inventory,accepted = sources(preparation,reduction,response,actions)
    require({key(p):h for p,h in pins.items()} == request["source_sha256"]
            and inventory == request["required_state_inventory"], "prepared inputs or inventory changed")
    pins[request_path] = expected_sha256
    bounds = module(BOUNDS_API,"motion_bound_existing_nullspace")
    loader = module(HERE / "panel-reference-completion.py","motion_bound_pure_laws")
    law = loader.definitions(response / "producer.py.snapshot", ("spring_expected","force_law_audit"),
        {"np":np,"require":require,"math":__import__("math")})
    joint,H,D,e,W = assemble(np,preparation,reduction)
    model = read(HERE / "operators-attempt02/model.json")
    geometry = read(RESUME / "member-screen-attempt02/four-screw-layout01/geometry.json")["members"]
    names = model["body_names"]
    require(len(names) == 50 and len(geometry) == 44 and set(geometry).issubset(names), "timber/panel body census changed")
    rows = read(HERE / "operators-attempt02/row-identities.json")
    pure = loader.definitions(response / "producer.py.snapshot", ("panel_screw_ports",),
        {"np":np,"require":require,"PANEL_SCREW_ROLES":("panel_screw_lateral_plane","non_qualifying_parametric_screw_withdrawal")})
    screw_ports = pure.panel_screw_ports(rows,joint)
    k,uni,normals,tangents,pairs,gaps = [joint[name] for name in
        ("k","unilateral","floor_normals","floor_tangents","clearance_pairs","clearance_gaps")]
    output = fresh(output)
    write(output / "request.json",request)
    write(output / "known-answer.json",known_answer())
    comparison,inputs = read(response / "comparison.json"),read(response / "inputs.json")
    result_states,arrays = [],{}
    with np.load(response / "response.npz",allow_pickle=False) as saved:
        for state in comparison["states"]:
            case,gap = state["case_id"],state["gap_scale"]
            tag = case+("_gap" if gap else "_zero")
            f,q,a,bearing = [saved[tag+suffix] for suffix in ("_force_n","_relative_motion_mm","_rigid_scaled_mm","_bearing")]
            index = 0 if case == "dead-only" else (
                "a12-rear","a12-forward","a12-left","k12-right","k12-rear","a1-rear").index(case)
            load_e = inputs["dead_load_factor"]*e[:,2*index]
            work = inputs["dead_load_factor"]*W[:,2*index]
            if case != "dead-only":
                load_e = load_e+e[:,2*index+1]
                work = work+W[:,2*index+1]
            audit = law.force_law_audit(f,q,a,H,D,load_e,work,k,uni,normals,tangents,bearing,pairs,gap*gaps,screw_ports)
            require(audit["all_passed"] is True, "saved original law audit fails: "+tag)
            problem = pose_problem(np,bounds,D,q,k,uni,normals,tangents,bearing,pairs,gap*gaps)
            intervals,certificates = component_bounds(np,optimize,problem,np.eye(344),tag+"/coordinates",retain=True)
            witness,moved = original_law_witness(np,problem,q,work)
            if witness is not None:
                witness_a = a+np.asarray(witness["coordinate_increment"])
                witness_audit = law.force_law_audit(f,moved,witness_a,H,D,load_e,work,k,uni,normals,tangents,
                    bearing,pairs,gap*gaps,screw_ports)
                require(witness_audit["all_passed"], "original-law witness fails unchanged acceptance: "+tag)
                witness["original_physical_law_audit"] = witness_audit
            body_bounds = []
            for i,name in enumerate(names):
                inc = intervals[6*i:6*i+6]
                translations,rotations = inc[:3],[[v/ROTATION_SCALE if v is not None else None for v in row] for row in inc[3:]]
                points = np.asarray([model["physical_node_coordinates_mm"][str(node)] for node in model["body_nodes"][name]])
                center = points.mean(axis=0)
                radius = float(np.max(np.linalg.norm(points-center,axis=1)))
                tn,rn = norm_bound(np,translations),norm_bound(np,rotations)
                total = [[a[6*i+j]+v if v is not None else None for v in row] for j,row in enumerate(inc)]
                total_rotation = [[v/ROTATION_SCALE if v is not None else None for v in row] for row in total[3:]]
                trn = norm_bound(np,total_rotation)
                body_bounds.append({"body":name,"kind":"timber" if name in geometry else "panel",
                    "centroid_translation_increment_component_intervals_mm":translations,
                    "rotation_increment_component_intervals_rad":rotations,
                    "translation_increment_norm_upper_bound_mm":tn,"rotation_increment_norm_upper_bound_rad":rn,
                    "every_material_point_rigid_increment_norm_upper_bound_mm":None if tn is None or rn is None else tn+radius*rn,
                    "representative_centroid_translation_mm":a[6*i:6*i+3].tolist(),
                    "representative_rotation_rad":(a[6*i+3:6*i+6]/ROTATION_SCALE).tolist(),
                    "total_rigid_translation_norm_upper_bound_mm":norm_bound(np,total[:3]),
                    "total_rigid_rotation_norm_upper_bound_rad":trn,
                    "maximum_reference_node_radius_mm":radius,
                    "rotation_linearization_remainder_upper_bound_mm":None if trn is None else .5*radius*trn**2,
                    "absolute_elastic_deformed_node_motion_recovered":False})
            timber_projection_rank = int(np.linalg.matrix_rank(problem["N"][:300],tol=1e-10))
            body_bounded = all(all(v is not None for row in intervals[i:i+6] for v in row) for i in range(0,300,6))
            full_bounded = all(v is not None for row in intervals for v in row)
            rays = problem["rays"]
            for ray in rays:
                ray["external_work_nmm_per_unit"] = float(work @ np.asarray(ray["coordinate_direction"]))
                ray["timber_participation"] = ray["body_projection_norm"] > 1e-6
            arrays[tag+"_nullspace"] = problem["N"]
            arrays[tag+"_A_ub"] = problem["A"]
            arrays[tag+"_b_ub"] = problem["b"]
            arrays[tag+"_fixed_rows"] = problem["fixed"]
            arrays[tag+"_inactive_rows"] = problem["inactive"]
            arrays[tag+"_free_pairs"] = problem["free_pairs"]
            arrays[tag+"_free_gaps"] = problem["free_gaps"]
            arrays[tag+"_dual_multipliers"] = np.asarray(problem["dual"]).reshape(-1,len(problem["b"]))
            arrays[tag+"_coordinate_extrema"] = np.asarray(problem["extrema"]).reshape(-1,problem["N"].shape[1]) if problem["N"].shape[1] else np.empty((0,0))
            result_states.append({"case_id":case,"gap_scale":gap,"state_tag":tag,"source_state_record":accepted[(case,gap)],
                "status":"BOUNDED_FIXED_FORCE_BODY_SEATING_WITH_METAL_FREEDOM" if body_bounded and not full_bounded else
                    "BOUNDED_FIXED_FORCE_SEATING" if full_bounded else "UNBOUNDED_FIXED_FORCE_BODY_MECHANISM",
                "original_law_audit":audit,"fixed_row_svd":problem["svd"],"coordinate_nullity":problem["N"].shape[1],
                "body_projection_rank":timber_projection_rank,"metal_only_nullity":problem["N"].shape[1]-timber_projection_rank,
                "body_seating_bounded":body_bounded,"all_coordinate_seating_bounded":full_bounded,
                "coordinate_increment_intervals_scaled_mm":intervals,"coordinate_bound_certificates":certificates,
                "free_circular_pairs":len(problem["free_pairs"]),"inactive_unilateral_rows":len(problem["inactive"]),
                "fixed_motion_null_residual_mm":peak(np,D[problem["fixed"]] @ problem["N"]),
                "coefficient_roundoff_peak":problem["coefficient_roundoff_peak"],"lp_call_count":problem["calls"],
                "recession_certificates":rays,"original_law_nonunique_body_witness":witness,"body_motion_bounds":body_bounds,
                "stability_implications":{
                    "fixed_force_local_reactions_changed":False,
                    "first_order_body_restoring_stiffness_strict":timber_projection_rank == 0,
                    "first_order_all_rigid_restoring_stiffness_strict":problem["N"].shape[1] == 0,
                    "admissible_body_flat_direction_demonstrated":witness is not None,
                    "source_linear_elastic_field_unchanged_at_fixed_forces":True,
                    "second_order_buckling_or_dynamic_stability_established":False,
                    "geometric_rotation_remainders_are_diagnostic_not_updated_equilibria":True,
                    "scope":"Null energy motions preserve active spring deformations and elastic body/shaft fields; open contact and clearance can bound their extent without furnishing local restoring stiffness. Source first-order geometry omits prestress/geometric stiffness."}})
            print(tag, "null",problem["N"].shape[1],"body bounded",body_bounded,"all bounded",full_bounded,flush=True)
    authenticate(pins)
    np.savez_compressed(output / "certificates.npz",**arrays)
    report = {"schema":"joint_frame_fixed_force_motion_bounds/v1",
        "status":"COMPLETE_FIXED_FORCE_MOTION_AND_FINITE_STABILITY_DISPOSITION",
        "required_state_inventory":inventory,"states":result_states,
        "counts":{"required_states":len(inventory),"accepted_states_assessed":len(result_states),
            "source_floor_stops_without_pose_field":sum(not item["accepted_force_field_exists"] for item in inventory),
            "body_seating_bounded_states":sum(item["body_seating_bounded"] for item in result_states),
            "all_coordinate_bounded_states":sum(item["all_coordinate_seating_bounded"] for item in result_states),
            "nonunique_body_witness_states":sum(item["original_law_nonunique_body_witness"] is not None for item in result_states)},
        "source_sha256":{key(p):h for p,h in pins.items()},"limits":LIMITS,
        "baseline_300_certificate_transferred":False,
        "current_system_coordinate_count":344,
        "fixed_force_reference_bounds":{
            "classification":"CONSERVATIVE_NUMERICAL_FIXED_FORCE_POSE_BOUNDS",
            "source_force_basis":"current_receipt_bound_accepted_fields",
            "coordinate_layout":{"body_scaled_coordinates":300,"shaft_scaled_coordinates":20,
                                 "washer_scaled_coordinates":24},
            "coordinate_interval_count":344*len(result_states),
            "original_contact_clearance_and_spring_laws_preserved":True,
            "original_no_slip_floor_law_preserved":True,
            "source_geometry_and_hardware_changed":False,
            "reviewed_bolt_axis_count":104,"Hillman_screw_axis_count":66,
            "source_100_mm_hold_lever_preserved":True,
            "absolute_elastic_deformed_node_motion_envelope_established":False,
            "changed_force_branch_envelope_established":False,
            "norm_bounds_are_conservative_component_box_bounds":True,
            "outer_polyhedron_extrema_are_accepted_contact_poses":False,
            "actual_disk_witnesses_original_law_audited":True},
        "certificate_arrays":{"path":key(output / "certificates.npz"),"sha256":sha(output / "certificates.npz")},
        "first_order_stability_implication_assessment_complete":True,
        "second_order_stability_established":False,"source_force_fields_changed":False,
        "source_producers_frame_native_or_CAD_executed":False,"complete_joint_acceptance":False,
        "numerical_goal_complete":False,"physical_release":False}
    write(output / "summary.json",report)
    files = {p.relative_to(output).as_posix():sha(p) for p in output.iterdir() if p.is_file()}
    write(output / "receipt.json",{"schema":"joint_frame_fixed_force_motion_receipt/v1","status":report["status"],
        "source_sha256":report["source_sha256"],"output_sha256":files,"counts":report["counts"],
        "elapsed_seconds":time.monotonic()-started,"physical_release":False})
    authenticate(pins)
    return {"status":report["status"],"counts":report["counts"],"elapsed_seconds":time.monotonic()-started,
            "receipt_sha256":sha(output / "receipt.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",choices=("prepare","build","known-answer"),required=True)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--preparation",type=Path,default=PREPARATION)
    parser.add_argument("--wood-reduction",type=Path,default=REDUCTION)
    parser.add_argument("--response",type=Path,default=FRAME)
    parser.add_argument("--actions",type=Path,default=ACTIONS)
    parser.add_argument("--request",type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    if args.stage == "known-answer":
        result = known_answer()
    elif args.stage == "prepare":
        require(args.output is not None,"prepare output required")
        result = prepare(args.output,args.preparation,args.wood_reduction,args.response,args.actions)
    else:
        require(args.output is not None and args.request is not None and args.expected_sha256 is not None,
                "build output and frozen request hash required")
        result = build(args.output,args.request,args.expected_sha256)
    print(json.dumps(result,separators=(",",":"),allow_nan=False))


if __name__ == "__main__":
    main()
