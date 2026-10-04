"""Complete twelve central washer contacts on their unchanged supported masks.

Import and prepare() are inert with respect to numerical mechanics. The parent
serializes build(): one existing fine radial assembly, its sine parity extension,
known-answer method validation, and twelve prescribed own-end contact solves.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-restricted-contact-completion"
ORDINARY = HERE / "washer-ordinary-fine-reference.py"
ORDINARY_SHA = "5501c39ca510f576a77f4ccb3256848f88aff2854263e06cba4fcfd44e469fcf"
GEOMETRY = HERE.parent / "member-screen-attempt02/four-screw-layout01/geometry.json"
GEOMETRY_SHA = "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af"
REVIEWED_RESPONSE = HERE / "frame-250-attempt02/response.npz"
REVIEWED_RESPONSE_SHA = "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7"
AXIS = "center_principal_right_2"
PROFILE = {"inner_radius_mm": 4.1529, "outer_radius_mm": 9.2329,
           "head_radius_mm": 5.0, "thickness_mm": 1.2954}
FLAGS = {"geometry_changed": False, "hardware_changed": False,
         "proposal_adopted": False, "complete_joint_acceptance": False,
         "physical_release": False, "fabrication_release": False,
         "actual_washer_capacity_n": None, "actual_washer_yield_mpa": None,
         "actual_hardware_inspected": False, "global_frame_feedback": False,
         "native_or_CAD_or_frame_run": False, "tests_or_review_run": False}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Missing saved module: " + str(path))
    prior = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior
    return module


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def lens_area(radius, passage_radius, distance):
    """Area of the overlap of two disks, from their two circular segments."""
    if distance >= radius + passage_radius:
        return 0.0
    if distance <= abs(radius - passage_radius):
        return math.pi * min(radius, passage_radius)**2
    a = math.acos((distance**2 + radius**2 - passage_radius**2)/(2*distance*radius))
    b = math.acos((distance**2 + passage_radius**2 - radius**2)/(2*distance*passage_radius))
    radical = (-distance+radius+passage_radius)*(distance+radius-passage_radius)
    radical *= (distance-radius+passage_radius)*(distance+radius+passage_radius)
    return radius**2*a + passage_radius**2*b - math.sqrt(radical)/2


def inputs():
    """Reuse the ordinary loader and exact joined ends without its 994 solves."""
    if digest(ORDINARY) != ORDINARY_SHA:
        raise ValueError("Frozen ordinary consumer changed")
    ordinary = load(ORDINARY, "central_saved_ordinary")
    fine = ordinary.load_fine48()
    helper = fine.load_helper()
    api = helper.load_n09()
    pins = {**api.PINS, ORDINARY: ORDINARY_SHA, ordinary.FINE48: ordinary.FINE48_SHA,
            fine.HELPER: fine.HELPER_SHA, helper.N09: helper.N09_SHA,
            GEOMETRY: GEOMETRY_SHA, REVIEWED_RESPONSE: REVIEWED_RESPONSE_SHA,
            Path(__file__).resolve(): digest(__file__)}
    _, receipt = helper.packet(pins, ordinary.SOURCE, ordinary.SOURCE_SHA,
                               "washer-end-reference-join", "washer_end_reference_join_receipt/v1")
    helper.require(receipt["output_sha256"]["washer-end-states.jsonl"] == ordinary.ROWS_SHA,
                   "joined own-end rows changed")
    rows = [json.loads(line) for line in (ordinary.SOURCE / "washer-end-states.jsonl").read_text().splitlines()]
    selected = [row for row in rows if row["scope"] == "outside_corner_axial_reference"
                and row["axis_id"] == AXIS]
    helper.require(len(selected) == len({tuple(row["join_key"]) for row in selected}) == 12
                   and {row["case_id"] for row in selected} == set(api.CASES), "central twelve census changed")
    contract = helper.read(api.CENTRAL)
    wood = contract["wood_support_mask"]
    cy, cz = wood["local_passage_center_yz_mm"]
    distance, passage_radius = math.hypot(cy, cz), float(wood["passage_radius_mm"])
    inner, outer = PROFILE["inner_radius_mm"], PROFILE["outer_radius_mm"]
    helper.require(wood["own_bore_radius_mm"] < inner and distance-passage_radius > PROFILE["head_radius_mm"]
                   and distance+passage_radius > outer
                   and min(wood["natural_edge_distances_mm"]) > outer,
                   "central mask topology changed")
    geometry = helper.read(GEOMETRY)
    saved_support = helper.read(api.REMAINING_SUPPORT)
    seats = {seat["role"]: seat for seat in saved_support["seats"] if seat["axis_id"] == AXIS}
    reviewed = helper.read(api.REGISTER)
    axis = next(axis for axis in reviewed["axes"] if axis["axis_id"] == AXIS)
    helper.require(len(reviewed["axes"]) == reviewed["accounting"]["total_unique_frame_bolt_axes"] == 104
                   and reviewed["accounting"]["hillman_panel_kicker_axes_separate"] == 66,
                   "reviewed geometry census changed")
    masks = {}
    for role, member in (("head", "center_principal_cleat_right"), ("nut", "base_principal_center_right")):
        seat, geom = seats[role], geometry["members"][member]
        step = ROOT / geom["current_finished_step"]
        helper.add_pin(pins, step, geom["current_finished_step_sha256"])
        helper.require(step.name == member + ".step" and seat["member"] == member,
                       "central receiver STEP binding changed")
        if role == "head":
            helper.require(helper.close_vector(seat["point_xyz_mm"], axis["outer_tie"]["point_mm"], 1e-7)
                           and all(x["support_fraction"] >= 1-1e-9 for x in
                                   next(s for s in seat["nominal"] if s["scenario"] == "plain_minimum_area")["inward_measurements"]),
                           "head support or reviewed underhead datum changed")
        else:
            helper.require(helper.close_vector(seat["point_xyz_mm"], contract["seat_point_global_xyz_mm"], 1e-7)
                           and geom["current_finished_step_sha256"] == contract["source_sha256"][str(step.relative_to(ROOT))],
                           "nut mask receiver or seat changed")
        area = math.pi*(outer**2-inner**2)
        if role == "nut":
            area -= lens_area(outer, passage_radius, distance) - lens_area(inner, passage_radius, distance)
        measurements = next(s for s in seat["nominal"] if s["scenario"] == "plain_minimum_area")["inward_measurements"]
        helper.require(max(abs(area-x["supported_area_mm2"]) for x in measurements) < 1e-6,
                       "analytical supported mask disagrees with saved CAD areas")
        masks[role] = {"receiver": member, "seat_xyz_mm": seat["point_xyz_mm"],
            "step_path": str(step.relative_to(ROOT)), "step_sha256": geom["current_finished_step_sha256"],
            "chart": "x=global_Y-seat_Y; y=global_Z-seat_Z; w is positive into the receiver",
            "wood_mask": "catalog annulus" if role == "head" else "catalog annulus minus saved passage disk",
            "passage_center_xy_mm": None if role == "head" else [cy, cz],
            "passage_radius_mm": None if role == "head" else passage_radius,
            "own_bore_radius_mm": wood["own_bore_radius_mm"], "supported_area_analytic_mm2": area,
            "saved_CAD_area_measurements": measurements,
            "head_contact_inner_outer_radii_mm": [inner, PROFILE["head_radius_mm"]],
            "nominal_mask_fixed_during_normal_deformation": True}
    sources = []
    for row in sorted(selected, key=lambda row: tuple(row["join_key"])):
        end, role = row["own_end_source"], row["end_role"]
        h, moment, normal = end["contact_hypotheses"], end["own_end_M_signed_xyz_nmm"], end["normal_into_receiver_xyz"]
        tension = float(end["normal_compression_T_n"])
        helper.require(end["status"] == "COMPLETE_ISOLATED_END_SOURCE" and tension > 0
                       and row["seat_datum_match"] is True and h["partial_supported_ring_route"] is True
                       and h["wood_contact_inner_outer_radii_mm"] == [inner, 5.]
                       and h["head_nut_contact_inner_outer_radii_mm"] == [inner, 5.]
                       and (h["Kwood_mpa_per_mm"], h["Khead_mpa_per_mm"], h["preload_n"]) == (20.,10000.,0)
                       and helper.close_vector(end["end_wrench_datum_global_xyz_mm"], masks[role]["seat_xyz_mm"],1e-7)
                       and end["source_join"]["source_response_sha256"] == api.PINS[api.RESPONSE]
                       and helper.close_vector(end["force_on_receiver_xyz_n"],[tension*x for x in normal],1e-6),
                       "central prescribed own-end load or geometry changed")
        # These two fixed world-chart directions avoid aligning the mask with a load.
        xmoment, ymoment = api.cross([0.,1.,0.],normal), api.cross([0.,0.,1.],normal)
        target = [api.dot(moment,xmoment),api.dot(moment,ymoment)]
        recovered = [target[0]*a+target[1]*b for a,b in zip(xmoment,ymoment)]
        helper.require(helper.close_vector(recovered,moment,1e-8) and abs(api.dot(normal,moment)) < 1e-8,
                       "normal pressure cannot reproduce prescribed moment")
        trial = row["central_recovered_moment_static_trial"]
        helper.require((trial is not None) == (role == "nut"), "six recovered static trials changed")
        sources.append({"state_id":"/".join(row["join_key"]), "join_key":row["join_key"],
            "case_id":row["case_id"], "axis_id":AXIS, "end_role":role,
            "receiver_member":row["receiver_member"], "family":"rail", "T_n":tension,
            "M_magnitude_nmm":float(end["own_end_M_magnitude_nmm"]),
            "source_signed_own_M_xyz_nmm":moment, "force_on_receiver_xyz_n":end["force_on_receiver_xyz_n"],
            "normal_into_receiver_xyz":normal, "own_seat_xyz_mm":end["end_wrench_datum_global_xyz_mm"],
            "plate_pressure_first_moment_targets_nmm":target,
            "saved_rigid_contact":end["saved_end_contact"], "saved_rigid_initialization_only":True,
            "conditional_wood_reference_mpa":row["wood_reference_mpa"],
            "wood_reference_route":row["wood_reference_route"], "source_join":end["source_join"],
            "force_basis":"conditional_proposal_gravity_104_global_axes",
            "reviewed104_original_T_n":next(s["single_axial_tie_n"] for s in axis["per_state"] if s["case_id"] == row["case_id"]),
            "reviewed104_original_force_not_substituted":True,
            "existing_recovered_moment_static_trial":trial,
            "elastic_wood_domain_extension":"Supported head annulus or nut annulus minus passage; source's rigid restricted ring is not retained as elastic support."})
    helper.authenticate(pins)
    return ordinary, helper, api, pins, sources, masks


def create_output(output):
    output = Path(output).absolute()
    if output.resolve() != output or output.parent != RAW or output.exists():
        raise ValueError("Use a fresh unaliased immediate child of " + str(RAW))
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def plan(sources,masks):
    return {"schema":"central_actual_mask_washer_plan/v1", "source_end_states":12,
            "profile":PROFILE, "source_rows":sources, "support_masks":masks,
            "reviewed_geometry_scope":"104 axes, 66 Hillman axes; only the two unchanged central receivers enter plate/contact geometry",
            "force_scope":"Newer saved full-assessment forces remain conditional proposal-gravity comparisons, not reviewed104 original force qualification",
            "resolution":{"inside_elements":4,"outside_elements":12,"fourier_order":8,"full_sine_cosine":True,"unknowns":2198},
            "hypotheses":{"E_mpa":200000.,"nu":.3,"Fy_mpa":250.,"Kwood_mpa_per_mm":20.,"Khead_mpa_per_mm":10000.},
            "method_sources":["https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html",
                              "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.block_diag.html",
                              "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html"],
            "planned_calls":{"existing_fine_radial_assemblies":1,"own_end_solves":12,"known_answer_method_examples":2},**FLAGS}


def prepare(output):
    _,helper,api,pins,sources,masks = inputs()
    output = create_output(output)
    dump(output/"input-plan.json",plan(sources,masks))
    helper.authenticate(pins)
    dump(output/"receipt.json",{"status":"PREPARED_NOT_NUMERICALLY_EXECUTED", "source_sha256":{api.display(p):h for p,h in sorted(pins.items())},
        "output_sha256":{p.name:digest(p) for p in output.iterdir() if p.is_file()},**FLAGS})
    return {"status":"PREPARED_NOT_NUMERICALLY_EXECUTED","sources":len(pins),"states":len(sources),"masks":masks}


def point_map(edge,model,r,theta,elements):
    np,sparse = edge.np,edge.sparse
    r,theta,elements = np.asarray(r),np.asarray(theta),np.asarray(elements)
    rowids,cols,values = [np.arange(len(r))],[np.zeros(len(r),dtype=int)],[np.ones(len(r))]
    outer = model["family"]["outer_radius_mm"]
    for element in np.unique(elements):
        selection = np.flatnonzero(elements == element)
        h = edge.radial_shapes(model["edges"][element],model["edges"][element+1],r[selection],outer)[0]
        for mode in range(model["settings"]["fourier_order"]+1):
            ids = model["u_indices"][mode,element:element+2].ravel()
            angulars = [(ids,np.cos(mode*theta[selection]))]
            if mode:
                angulars.append((model["sine_ids"][ids],np.sin(mode*theta[selection])))
            for ids,angular in angulars:
                for local,index in enumerate(ids):
                    if index >= 0:
                        rowids.append(selection); cols.append(np.full(len(selection),index))
                        values.append(r[selection]/outer*h[:,local]*angular)
    return sparse.coo_matrix((np.concatenate(values),(np.concatenate(rowids),np.concatenate(cols))),
                             shape=(len(r),model["width"])).tocsr()


def clipped_quadrature(edge,model,mask):
    """Integrate supported radial intervals; split angles at every circle/edge crossing."""
    np = edge.np
    center = mask["passage_center_xy_mm"]
    if center is None:
        return model["area"],model["r"],model["theta"],model["element"]
    distance,alpha = math.hypot(*center),math.atan2(center[1],center[0])
    passage = mask["passage_radius_mm"]
    gauss,gw = np.polynomial.legendre.leggauss(24)
    rg,rw = np.polynomial.legendre.leggauss(6)
    areas,radii,angles,elements = [],[],[],[]
    for element,(left,right) in enumerate(zip(model["edges"][:-1],model["edges"][1:])):
        breaks = [-math.pi,math.pi]
        for radius in (left,right):
            cosine = (distance**2+radius**2-passage**2)/(2*distance*radius)
            if -1 < cosine < 1:
                crossing = math.acos(cosine)
                breaks.extend([-crossing,crossing])
        breaks = sorted(set(breaks))
        for alo,ahi in pairwise(breaks):
            phi = alo+(gauss+1)*(ahi-alo)/2
            angular_weight = gw*(ahi-alo)/2
            for angle,weight in zip(phi,angular_weight):
                discriminant = passage**2-distance**2*math.sin(angle)**2
                near = distance*math.cos(angle)-math.sqrt(max(discriminant,0))
                hit = discriminant >= 0 and distance*math.cos(angle)>0
                upper = min(right,near) if hit else right
                if upper <= left:
                    continue
                r = left+(rg+1)*(upper-left)/2
                areas.extend(rw*(upper-left)/2*r*weight)
                radii.extend(r); angles.extend([angle+alpha]*len(r)); elements.extend([element]*len(r))
    return tuple(np.asarray(v) for v in (areas,radii,angles,elements))


def mask_supported(model,x,y):
    center = model["support_mask"]["passage_center_xy_mm"]
    return True if center is None else (x-center[0])**2+(y-center[1])**2 >= model["support_mask"]["passage_radius_mm"]**2-1e-10


def full_model(edge,flexure):
    """Extend the unchanged plate Gram matrices by their sine parity blocks."""
    np,sparse = edge.np,edge.sparse
    base = edge.make_model(flexure,"fine")
    plate_width = base["width"]-3
    positive = np.unique(np.r_[base["u_indices"][1:].ravel(),base["a_indices"][1:].ravel(),base["b_indices"].ravel()])
    model = dict(base)
    model["sine_ids"] = np.full(base["width"],-1,dtype=int)
    model["sine_ids"][positive] = np.arange(plate_width,plate_width+len(positive))
    model["positive_ids"] = positive
    model["width"] = base["width"]+len(positive)
    edge.require(model["width"] == 2198,"full angular basis census differs")
    for name in ("bending_stiffness","shear_stiffness"):
        original = base[name]
        model[name] = sparse.block_diag((original[:plate_width,:plate_width],original[positive][:,positive],sparse.csr_matrix((3,3))),format="csr")
    model["stiffness"] = model["bending_stiffness"]+model["shear_stiffness"]
    model["wood_map"] = point_map(edge,model,model["r"],model["theta"],model["element"])
    plane = np.column_stack((np.ones(len(model["area"])),model["x"]/PROFILE["outer_radius_mm"],model["y"]/PROFILE["outer_radius_mm"]))
    model["head_map"] = sparse.coo_matrix((plane.ravel(),(np.repeat(np.arange(len(plane)),3),np.tile(np.arange(model["width"]-3,model["width"]),len(plane)))),shape=(len(plane),model["width"])).tocsr()
    return model


def supported_model(edge,base,mask):
    model = {**base,"support_mask":mask}
    area,r,theta,element = clipped_quadrature(edge,model,mask)
    mapping = point_map(edge,model,r,theta,element)
    x,y = r*edge.np.cos(theta),r*edge.np.sin(theta)
    select = model["head_selection"]
    model["contact_maps"] = ((area,mapping,model["Kwood"],x,y),
        (model["area"][select],(model["head_map"]-model["wood_map"])[select],model["Khead"],model["x"][select],model["y"][select]))
    area_error = float(sum(area))-mask["supported_area_analytic_mm2"]
    edge.require(abs(area_error)<1e-6,"contact quadrature disagrees with analytical mask area")
    edge.require(all(mask_supported(model,float(a),float(b)) for a,b in zip(x,y)),"wood contact point in passage")
    model["mask_validation"] = {"quadrature_area_mm2":float(sum(area)),"analytic_area_mm2":mask["supported_area_analytic_mm2"],
        "area_residual_mm2":area_error,"wood_points":len(area),"head_points":int(sum(select)),
        "unsupported_wood_contact_points":0,"minimum_head_to_passage_clearance_mm":None if mask["passage_center_xy_mm"] is None else math.hypot(*mask["passage_center_xy_mm"])-mask["passage_radius_mm"]-PROFILE["head_radius_mm"]}
    return model


def install_wrappers(edge):
    """Keep the saved Newton/evaluation/recovery implementation; extend only its maps."""
    base_fields,base_recover,base_balance = edge.field_values,edge.recover_fields,edge.contact_balance

    def fields(model,pose,element,radii,angles):
        np = edge.np
        # The saved helper multiplies angles by each Fourier mode. Python lists
        # would repeat (or empty at mode zero), rather than scale the angles.
        radii,angles = np.asarray(radii,dtype=float),np.asarray(angles,dtype=float)
        edge.require(radii.ndim == angles.ndim == 1,"field coordinates must be one-dimensional arrays")
        w,beta,curvature,gamma = base_fields(model,pose,element,radii,angles)
        outer = model["family"]["outer_radius_mm"]
        h,hr,l,lr = edge.radial_shapes(model["edges"][element],model["edges"][element+1],radii,outer)
        for mode in range(1,model["settings"]["fourier_order"]+1):
            u,a,b = edge.element_indices(model,element,mode)
            uc,ac,bc = (pose[model["sine_ids"][ids]] for ids in (u,a,b))
            uv,ur,av,ar,bv,br = h@uc,hr@uc,l@ac,lr@ac,l@bc,lr@bc
            sine,cosine = np.sin(mode*angles),np.cos(mode*angles)
            w += (radii*uv/outer)[:,None]*sine
            beta[:,:,0] += (av/outer)[:,None]*sine
            beta[:,:,1] -= (bv/outer)[:,None]*cosine
            curvature[:,:,0] += (ar/outer)[:,None]*sine
            curvature[:,:,1] += ((mode*bv+av)/(outer*radii))[:,None]*sine
            curvature[:,:,2] -= ((br-(mode*av+bv)/radii)/outer)[:,None]*cosine
            gamma[:,:,0] += ((uv+radii*ur-av)/outer)[:,None]*sine
            gamma[:,:,1] += ((mode*uv+bv)/outer)[:,None]*cosine
        return w,beta,curvature,gamma

    def recover(model,pose):
        rows,witnesses = base_recover(model,pose)
        for row in rows:
            supported = mask_supported(model,row["x_mm"],row["y_mm"])
            row["wood_supported"] = supported
            if not supported:
                row["wood_pressure_mpa"] = 0.
        return rows,witnesses

    def drive(model,tension,moment):
        result = edge.np.zeros(model["width"])
        result[-3:] = [tension,*[x/PROFILE["outer_radius_mm"] for x in model["target_first"]]]
        return result

    def balance(maps,pressures,tension,moment):
        rows = base_balance(maps,pressures,tension,0.)
        target = edge._central_target_first
        for row in rows:
            row["first_moment_targets_nmm"] = list(target)
            row["first_moment_residuals_nmm"] = [x-y for x,y in zip(row["first_moments_nmm"],target)]
        return rows

    edge.field_values,edge.recover_fields,edge.drive_vector,edge.contact_balance = fields,recover,drive,balance
    edge.contacts = lambda model,full_head=False: model["contact_maps"]


def affine_pose(edge,model,closure,tx,ty):
    pose,outer = edge.np.zeros(model["width"]),PROFILE["outer_radius_mm"]
    pose[0] = closure
    for slope,sine in ((tx,False),(ty,True)):
        for ids,coefficient in ((model["u_indices"][1,:,0],outer*slope),
                               (model["a_indices"][1],outer*slope),(model["b_indices"][0],-outer*slope)):
            pose[model["sine_ids"][ids] if sine else ids] = coefficient
    pose[-3:] = (1+model["Kwood"]/model["Khead"])*edge.np.array([closure,outer*tx,outer*ty])
    return pose


def known_answers(edge,model):
    """Known rigid affine zero-strain plate fields validate both angular parities and lift-off."""
    np = edge.np
    area = math.pi*(PROFILE["outer_radius_mm"]**2-PROFILE["inner_radius_mm"]**2)
    second = math.pi*(PROFILE["outer_radius_mm"]**4-PROFILE["inner_radius_mm"]**4)/4
    maps = ((model["area"],model["wood_map"],model["Kwood"],model["x"],model["y"]),
            (model["area"],model["head_map"]-model["wood_map"],model["Khead"],model["x"],model["y"]))
    records = []
    for label,c,tx,ty in (("affine_two_axis_full_face",.003,.00005,-.000025),
                         ("unilateral_half_annulus",0.,.00001,0.)):
        pose = affine_pose(edge,model,c,tx,ty)
        if label.startswith("affine"):
            force,target = model["Kwood"]*c*area,[model["Kwood"]*tx*second,model["Kwood"]*ty*second]
            exact_active = area
        else:
            force = model["Kwood"]*tx*2/3*(PROFILE["outer_radius_mm"]**3-PROFILE["inner_radius_mm"]**3)
            target,exact_active = [model["Kwood"]*tx*second/2,0.],area/2
        model["target_first"],edge._central_target_first = target,target
        energy,gradient,_,pressures,_ = edge.evaluate(model,pose,edge.drive_vector(model,force,0.),maps)
        balances = edge.contact_balance(maps,pressures,force,0.)
        edge.check_balances(balances)
        fields = edge.field_values(model,pose,0,[model["edges"][0],model["edges"][1]],[.3,1.7])
        strain = max(float(np.max(np.abs(value))) for value in fields[2:])
        action = float(np.max(np.abs(model["stiffness"]@pose)))
        edge.require(strain<1e-10 and action<1e-4 and np.max(np.abs(gradient))<1e-4,
                     "known affine plate/contact answer failed")
        edge.require(all(abs(row["active_area_mm2"]-exact_active)<1e-6 for row in balances),
                     "known unilateral active mask failed")
        records.append({"example":label,"exact_force_n":force,"exact_first_moments_nmm":target,
            "exact_active_area_mm2":exact_active,"returned_contacts":balances,
            "maximum_strain":strain,"plate_action_max_n":action,
            "gradient_max_n":float(np.max(np.abs(gradient))),"energy_nmm":float(energy),
            "solved":False,"known_pose_evaluated":True,"satisfied":True})
    return records


def equilibrium_validation(edge,model,source,state):
    np = edge.np
    pose = np.array(state["scaled_variables_mm"])
    maps = model["contact_maps"]
    pressure = [k*np.maximum(mapping@pose,0.) for _,mapping,k,_,_ in maps]
    records = []
    for (area,mapping,k,x,y),p,balance in zip(maps,pressure,state["contact_balances"]):
        indentation = mapping@pose
        force = balance["force_n"]
        first = balance["first_moments_nmm"]
        normal = source["normal_into_receiver_xyz"]
        returned_force = [force*a for a in normal]
        returned_moment = [first[0]*a+first[1]*b for a,b in zip(edge._central_api.cross([0.,1.,0.],normal),edge._central_api.cross([0.,0.,1.],normal))]
        ferr = max(abs(a-b) for a,b in zip(returned_force,source["force_on_receiver_xyz_n"]))
        merr = max(abs(a-b) for a,b in zip(returned_moment,source["source_signed_own_M_xyz_nmm"]))
        law = float(np.max(np.abs(p-k*np.maximum(indentation,0.))))
        inactive = float(np.max(np.abs(p[indentation <= 0]))) if np.any(indentation<=0) else 0.
        edge.require(ferr<=.001 and merr<=.02 and np.min(p)>=0 and law<=1e-12 and inactive==0,
                     "physical signed equilibrium or unilateral contact law failed")
        records.append({"contact":balance["contact"],"force_on_receiver_xyz_n":returned_force,
            "own_seat_M_xyz_nmm":returned_moment,"force_vector_max_residual_n":ferr,
            "moment_vector_max_residual_nmm":merr,"minimum_pressure_mpa":float(np.min(p)),
            "inactive_pressure_max_mpa":inactive,"contact_law_residual_mpa":law,
            "minimum_signed_indentation_mm":float(np.min(indentation)),
            "active_quadrature_points":int(np.sum(p>0)),"inactive_quadrature_points":int(np.sum(p==0)),
            "pressure_peak_mpa":float(np.max(p)),"supported_pressure_peak_location_xy_mm":[float(x[np.argmax(p)]),float(y[np.argmax(p)])]})
    return records,pressure


def build(output):
    """Parent-only serialized mechanics call. Existing sources are never modified."""
    started = time.monotonic()
    _ordinary,helper,api,pins,sources,masks = inputs()
    before = {api.display(p):digest(p) for p in sorted(pins)}
    output = create_output(output)
    dump(output/"input-plan.json",plan(sources,masks))
    flexure = api.load_module(api.FLEXURE,"central_pinned_material")
    edge = api.load_module(api.EDGE,"central_pinned_plate")
    helper.require(flexure.FAMILIES["rail"] == PROFILE
                   and (flexure.ESTEEL,flexure.NU,flexure.FY_HYPOTHESIS,flexure.KWOOD,flexure.KHEAD)==(200000.,.3,250.,20.,10000.),
                   "declared material/contact scenario changed")
    base = full_model(edge,flexure)
    install_wrappers(edge)
    edge._central_api = api
    examples = known_answers(edge,base)
    dump(output/"known-answers.json",examples)
    models = {role:supported_model(edge,base,mask) for role,mask in masks.items()}
    dump(output/"mask-validation.json",{role:model["mask_validation"] for role,model in models.items()})
    records = []
    with (output/"end-states.jsonl").open("x") as stream:
        for source in sources:
            model,debug = models[source["end_role"]],{}
            model["target_first"] = source["plate_pressure_first_moment_targets_nmm"]
            edge._central_target_first = model["target_first"]
            edge.STATE_ID = source["state_id"]
            state_started = time.monotonic()
            try:
                state,fields = edge.solve_state(model,source,debug)
                validation,pressures = equilibrium_validation(edge,model,source,state)
                wood = max(fields,key=lambda row:row["wood_pressure_mpa"])
                stress = state["sampled_stress_peak_witness"]
                sampled = stress["sampled_through_thickness_maximum_proxy_mpa"]
                wood_peak = max(wood["wood_pressure_mpa"],validation[0]["pressure_peak_mpa"])
                metrics = {"sampled_stress_proxy_mpa":sampled,"stress_proxy_over_Fy250":sampled/250.,
                    "wood_pressure_peak_mpa":wood_peak,"wood_peak_over_base_reference":wood_peak/source["conditional_wood_reference_mpa"],
                    "sampled_wood_witness":wood,"signed_equilibrium_and_contact":validation,
                    "mask_validation":model["mask_validation"]}
                array_name = source["case_id"]+"-"+source["end_role"]+".npz"
                edge.np.savez_compressed(output/array_name,pose=edge.np.array(state["scaled_variables_mm"]),wood_pressure_mpa=pressures[0],head_pressure_mpa=pressures[1])
                record = {"status":"FINITE_ACTUAL_MASK_ELASTIC_CONTACT_REFERENCE","source":source,"state":api.json_value(state),"metrics":metrics,"arrays":array_name}
            except (ValueError,RuntimeError,ArithmeticError,OSError) as error:
                record = {"status":"NUMERICAL_STOP_NOT_COMPLETE","source":source,"failure":{"error":str(error),"last_accepted_state":api.json_value(debug),"physical_failure_proved":False}}
            record["elapsed_seconds"] = time.monotonic()-state_started
            record = api.json_value(record)
            records.append(record)
            stream.write(json.dumps(record,sort_keys=True,allow_nan=False)+"\n"); stream.flush()
            print(json.dumps({"join_key":source["join_key"],"status":record["status"],"seconds":record["elapsed_seconds"]}),flush=True)
    finite = [r for r in records if r["status"] == "FINITE_ACTUAL_MASK_ELASTIC_CONTACT_REFERENCE"]
    peaks = {}
    for key in ("sampled_stress_proxy_mpa","stress_proxy_over_Fy250","wood_peak_over_base_reference"):
        row = max(finite,key=lambda r:r["metrics"][key]) if finite else None
        peaks[key] = None if row is None else {"join_key":row["source"]["join_key"],"value":row["metrics"][key],"T_n":row["source"]["T_n"],"M_nmm":row["source"]["M_magnitude_nmm"]}
    helper.authenticate(pins)
    after = {api.display(p):digest(p) for p in sorted(pins)}
    helper.require(before==after,"source bytes changed during central contact run")
    result = {"schema":"central_actual_mask_elastic_washer_reference/v1",
        "status":"COMPLETE_TWELVE_CONDITIONAL_MASK_CONTACT_REFERENCES" if len(finite)==12 else "INCOMPLETE_NUMERICAL_CONTACT_REFERENCES",
        "counts":{"source_states":12,"completed_states":len(finite),"numerical_stops":12-len(finite),"plate_assemblies":1,"supported_models":2,"own_end_solves":12,
                  "Fy250_exceedances":sum(r["metrics"]["stress_proxy_over_Fy250"]>1 for r in finite),"wood_reference_exceedances":sum(r["metrics"]["wood_peak_over_base_reference"]>1 for r in finite),"old_static_trials_retained":6},
        "same_state_peaks":peaks,"support_masks":masks,"known_answer_method_validation":examples,
        "force_scope":plan(sources,masks)["force_scope"],"runtime":{"python":sys.version.split()[0],"numpy":edge.np.__version__,"scipy":edge.scipy.__version__,"elapsed_seconds":time.monotonic()-started},
        "limits":["Own-end T and both signed pressure moments are prescribed; no local washer response is fed back into shaft or frame.",
                  "Only unchanged central receiver masks enter this model; six-bore knee spines and four added internal-v ties are excluded.",
                  "Fresh source forces retain proposal-gravity provenance; reviewed104 original forces are recorded separately and not qualified by these twelve calls.",
                  "Concentric catalog minimum plate and circular 5 mm pressing land, E, nu, Fy and spring laws remain declared hypotheses.",
                  "The sampled plate bending/shear stress proxy excludes thickness-normal stress, three-dimensional contact edges, plasticity, preload and friction.",
                  "Normal deformation retains the fixed supported mask; in-plane slip, installed centering, finite rotations and delivered wood/hardware are unverified.",
                  "Known affine examples validate dimensional assembly, both moment directions and lift-off; they do not establish stress convergence or complete joint capacity.",
                  "Existing ordinary and side-family exceedances and all six static trials remain unchanged; no capacity is transferred.",
                  "Numerical STOP is incomplete execution and never numerical qualification."],**FLAGS}
    dump(output/"washer-restricted-contact-completion.json",result)
    dump(output/"receipt.json",{"schema":"central_actual_mask_washer_receipt/v1","status":result["status"],"counts":result["counts"],
        "source_sha256":before,"source_before_sha256":before,"source_after_sha256":after,"sources_authenticated_before_and_after":True,
        "output_sha256":{p.name:digest(p) for p in sorted(output.iterdir()) if p.is_file()},**FLAGS})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--prepare-only",action="store_true")
    args = parser.parse_args()
    result = prepare(args.output) if args.prepare_only else build(args.output)
    print(json.dumps(result if args.prepare_only else {k:result[k] for k in ("status","counts","same_state_peaks","runtime")},indent=2,sort_keys=True))
    if not args.prepare_only and result["counts"]["completed_states"] != 12:
        raise SystemExit(1)
