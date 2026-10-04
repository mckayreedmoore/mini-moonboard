"""Isolate added backing on one unchanged twelve-screw AC-fir panel.

Preparation authenticates source bytes and prepares geometry only. Build is
parent-serialized: one saved native panel KKT factor, two fixed-receiver full
vector equilibrium solves, and physical displacement/stress recovery. Neither
the reviewed candidate nor its whole-frame force packet is changed.
"""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import importlib.util
import importlib.metadata
import json
import math
import sys
import time
from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent))
import corner_frame as method
import simple_frame as solver

BODY, CASE = "main_upper_left", "a12-rear"
SOURCE = HERE / "operators-attempt02"
BASE = HERE.parent.parent / "mvp-acceleration-2026-09-28"
RAW = HERE / "rawlocal/panel-backing-comparison"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CONDENSATION = BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
QUOTIENT = BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py"
CONSUMER = HERE / "panel-compatible-response.py"
ORIENTATION = HERE / "panel_orientation.py"
OLD_BENCHMARK = HERE.parent / "panel-attachment/results/count20-benchmark-attempt01/comparison.json"
OLD_PANEL_H = HERE.parent / "panel-attachment/results/count20-operators-attempt01/panel-benchmark.npz"
GLOBAL_CONTEXT = HERE / "rawlocal/panel-compatible-response/attempt02/summary.json"
PHYSICAL = method.accounting.MODEL
CONTACT_GEOMETRY = method.accounting.CONTACTS
CONTACT_WIDTH_MM, CONTACT_PENALTY = 38.1, 100.0
MOON_SPACING_MM = 813.0
QP_SETTINGS = {**solver.SETTINGS, "eps_abs": 1e-12, "eps_rel": 1e-12,
               "eps_prim_inf": 1e-12, "eps_dual_inf": 1e-12,
               "max_iter": 300000, "time_limit": 30.0}
PINS = {
    RAW / "source-cache/How-to-build-a-MoonBoard_v2.3.pdf": "2f3d1563cf405a6dd297bf5ca61592806b39d56a024bce260e496305d88917c2",
    SOURCE / "operator-assessment.json": "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    CONSUMER: "56fc683c5713dec4e21a82557b5e406e2659462b3bcb4d75b4a91105b1b35841",
    ORIENTATION: "3268faa94ba050d82d66df1393fc4b8e4d9e4a79b87412fe0f4cfdbf72dd7e93",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    CONDENSATION: "7a887915cf84bcfef94c204baa2f47e428f81cead5c220101d9c225d2838de63",
    QUOTIENT: "2275929b42dff5f03b4e822a8050631519d15e4e0a94ed6f604e065cab4dade6",
    PHYSICAL: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    CONTACT_GEOMETRY: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    method.NATIVE / "model.sti": "7d22d2b013fcdc9fddfeab589b456615f0671db989a034e091bac855f3a93c01",
    method.NATIVE / "model.dof": "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    method.NATIVE / "model.inp": "71dc0b73450b597aba35c0458befff5ca3b85dd87f3cfbed9992f4755b5124d5",
    HERE / "panel-width-operators-attempt01/inputs.json": "d91791cb8451e71439dbb94240b702b720518a85c88831214ab000f033d4b3b3",
    HERE.parent / "panel-attachment/attachment_screen.py": "c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc",
    OLD_BENCHMARK: "833c1bc77eacdbe702fbf5bb2b3a458d4db43821c10c3ad92d931fcaa235967b",
    OLD_PANEL_H: "e51e244fa6d1759a7c7ebe179e30f12c9d0d30e55d9d0ed12096b428d20006a9",
    GLOBAL_CONTEXT: "2399bb5b863b3f26b7b5599f0f78fbfb41b444249f2c78d1b96c20c609257be7",
    Path(method.__file__): "726f058d488e2dc9e7f83abc5537246afd994102ccddaee17416a7126a610f5d",
    Path(solver.__file__): "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    ROOT / "fea/wood_joint_reduced_members.py": "825bd3a8463eef3fbd7df9bd4892b20b660d980f5c94088537ce7a0a5d058335",
    ROOT / "fea/floor_recess_mesh.py": "518e3ee913537fb0e42a6dd843166974a011299921e116759bf2d330f221d184",
    ROOT / "fea/wood_joint_patch_materials.py": "ecbbd11a8a0e99ece69aeb5cb4159e7cf17e0aa18c509c78b5c8f5a2e573ae78",
}
FLAGS = dict.fromkeys(("candidate_geometry_or_screw_policy_changed", "native_or_CAD_launched",
    "whole_frame_force_allocation_replaced", "Moon_assembly_or_capacity_qualified",
    "complete_panel_acceptance", "physical_release", "reference_layout_adopted"), False)


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def authenticate(pins):
    for path, digest in pins.items():
        require(path.is_file() and sha(path) == digest, "changed source: " + str(path))


def sources():
    versions = {name:importlib.metadata.version(name) for name in ("numpy","scipy","osqp")}
    require(versions=={"numpy":"2.5.2","scipy":"1.18.1","osqp":"1.0.4"}, "frozen existing-environment numerical dependency versions differ")
    authenticate(PINS)
    data = load(CONSUMER, "backing_resistance_source").static_sources()
    pins = {**data.pins, **PINS, Path(__file__).resolve(): sha(__file__)}
    # The prior orientation preparation separately froze this unchanged deck;
    # no width-grain operator or response is consumed in this comparison.
    assessment = read(HERE / "panel-width-operators-attempt01/inputs.json")
    native_deck = method.NATIVE / "model.inp"
    relative = native_deck.relative_to(ROOT).as_posix()
    require(relative in assessment["source_sha256"], "native material deck lacks source binding")
    pins[native_deck] = assessment["source_sha256"][relative]
    authenticate(pins)
    return data, pins


def partition_rectangles(rectangles, excluded):
    """Disjoint exact rectangle union minus old backing; no doubled pressure."""
    bounds = rectangles + excluded
    xs = sorted({v for r in bounds for v in r[0]})
    ys = sorted({v for r in bounds for v in r[1]})
    contains = lambda r, x, y: r[0][0] < x < r[0][1] and r[1][0] < y < r[1][1]
    result = []
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            x, y = (xa+xb)/2, (ya+yb)/2
            if any(contains(r, x, y) for r in rectangles) and not any(contains(r, x, y) for r in excluded):
                result.append([[xa, xb], [ya, yb]])
    return result


def contact_area_centroid(rectangle,panel,local):
    """Remove the same frozen/current back-face bores from a new support cell."""
    from scipy.integrate import quad
    (xa,xb),(ya,yb) = rectangle
    circles = [(h["xy_mm"],local.radius_at(h,-local.T/2)) for h in panel["openings"]]
    circles = [(xy,r) for xy,r in circles if xa < xy[0]+r and xb > xy[0]-r and ya < xy[1]+r and yb > xy[1]-r]
    for i,(xy,r) in enumerate(circles):
        require(all(math.dist(xy,other)>r+rr-1e-8 for other,rr in circles[i+1:]),
                "overlapping back-face voids need a first-moment union method")
    crossings=[xy[0]+sign*math.sqrt(r*r-(y-xy[1])**2) for xy,r in circles
               for y in (ya,yb) if abs(y-xy[1])<r for sign in (-1,1)]
    breaks = sorted({xa,xb,*[max(xa,min(xb,x)) for x in crossings],
                     *[max(xa,min(xb,xy[0]+sign*r)) for xy,r in circles for sign in (-1,1)]})
    xc,yc=(xa+xb)/2,(ya+yb)/2
    def intervals(x):
        result=[]
        for (cx,cy),r in circles:
            if abs(x-cx)<r:
                half=math.sqrt(max(0.,r*r-(x-cx)**2))
                lo,hi=max(ya,cy-half),min(yb,cy+half)
                if lo<hi:result.append((lo,hi))
        return result
    values,errors=[],[]
    for kind in range(3):
        def integrand(x):
            cuts=intervals(x)
            length=local.union_length(cuts)
            return length if kind==0 else (x-xc)*length if kind==1 else sum(((hi-yc)**2-(lo-yc)**2)/2 for lo,hi in cuts)
        parts=[quad(integrand,a,b,epsabs=1e-7,epsrel=1e-10,limit=100) for a,b in zip(breaks,breaks[1:])]
        values.append(sum(v for v,_ in parts));errors.append(sum(err for _,err in parts))
    gross=(xb-xa)*(yb-ya)
    area=gross-values[0]
    require(area>0 and errors[0]<=1e-4,"new support cell has invalid remaining area")
    center=[xc-values[1]/area,yc-values[2]/area]
    require(all(math.dist(center,xy)>r for xy,r in circles),"new support centroid lies inside a physical bore")
    return area,center,values[0],errors[0]


def layout(data):
    panel = data.geometry["panels"][BODY]
    basis = np.array(panel["basis"])
    bounds = np.array(panel["bounds_mm"])
    physical = read(PHYSICAL)
    source_cells = {r["name"]: r for r in physical["contact_cell_ownership"]}
    patches = read(CONTACT_GEOMETRY)["contact_patches"]
    screws = [r for r in data.rows if BODY in (r["ownership"]["first_body"], r["ownership"]["second_body"])
              and r["ownership"]["role"] in ("non_qualifying_parametric_screw_withdrawal", "panel_screw_lateral_plane")]
    contacts = [r for r in data.rows if BODY in (r["ownership"]["first_body"], r["ownership"]["second_body"])
                and r["ownership"]["role"] == "timber_or_panel_contact"
                and abs(np.dot(r["ownership"]["direction_global_xyz"], basis[2])) > 1-1e-8
                and not any(b.startswith(("main_", "kicker_")) and b != BODY
                            for b in (r["ownership"]["first_body"], r["ownership"]["second_body"]))]
    require(len(screws) == 36 and sum(r["family"] == "unilateral_springa" for r in screws) == 12,
            "upper-left twelve-screw full-vector census differs")
    patch_ids = sorted({source_cells[r["row_id"]]["source_patch_index"] for r in contacts})
    require(patch_ids == [43, 75, 82, 95], "original four backing bands differ")
    old_rectangles = []
    for index in patch_ids:
        xy = np.array(patches[index]["vertices_xyz_mm"]) @ basis[:2].T
        # Bounding rectangles deliberately reserve the old small screw cavities
        # too; a new backing spring is not placed into an old hole or overlap.
        old_rectangles.append([[float(xy[:, i].min()), float(xy[:, i].max())] for i in range(2)])
    uprights = [float(bounds[0, 0]+i*MOON_SPACING_MM) for i in range(4)]
    interior = uprights[1]
    new_rectangles = [
        [[interior-CONTACT_WIDTH_MM/2, interior+CONTACT_WIDTH_MM/2], bounds[1].tolist()],
        [bounds[0].tolist(), [float(bounds[1, 1]-CONTACT_WIDTH_MM/2), float(bounds[1, 1])]],
    ]
    pieces = partition_rectangles(new_rectangles, old_rectangles)
    added = []
    for piece_index, rectangle in enumerate(pieces):
        counts = [max(1, math.ceil((b-a)/90.)) for a, b in rectangle]
        edges = [np.linspace(a, b, n+1) for (a, b), n in zip(rectangle, counts)]
        for i, j in product(range(counts[0]), range(counts[1])):
            cell=[[float(edges[0][i]),float(edges[0][i+1])],[float(edges[1][j]),float(edges[1][j+1])]]
            area,xy,void_area,area_error = contact_area_centroid(cell,panel,data.local)
            point = basis.T @ np.r_[xy, bounds[2, 0]]
            added.append({"row_id": "added-backing/"+str(len(added)), "family": "unilateral_springa",
                "ownership": {"first_body": "fixed_added_backing", "second_body": BODY,
                    "point_mm": point.tolist(), "direction_global_xyz": (-basis[2]).tolist(),
                    "role": "timber_or_panel_contact"},
                "law": {"stiffness_N_per_mm": float(CONTACT_PENALTY*area), "intended_law": "compression_only"},
                "contact_area_mm2": float(area), "back_face_bore_area_removed_mm2":void_area,
                "contact_area_quadrature_error_estimate_mm2":area_error,"rectangle_piece": piece_index,
                "cell_xy_bounds_mm": [[float(edges[0][i]), float(edges[0][i+1])],
                                      [float(edges[1][j]), float(edges[1][j+1])]]})
    for row in contacts:
        require(math.isclose(row["law"]["stiffness_N_per_mm"],
                            source_cells[row["row_id"]]["area_mm2"]*CONTACT_PENALTY, rel_tol=1e-12),
                "original contact penalty changed")
    added_area = sum(r["contact_area_mm2"] for r in added)
    exact_area = sum((r[0][1]-r[0][0])*(r[1][1]-r[1][0]) for r in pieces)
    require(math.isclose(added_area+sum(r["back_face_bore_area_removed_mm2"] for r in added),exact_area,rel_tol=1e-12),
            "added-area/void partition differs")
    return {"panel": BODY, "case_id": CASE, "panel_basis_xyz": basis.tolist(),
        "official_reference": {"guide_url":"https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf",
            "Mini_printed_page":2,"document_internal_version":"2.2, July 2023",
            "uprights":4,"upright_spacing_mm":813.,
            "horizontal_joint_bracing_source":"https://eu.moonclimbing.com/build-your-moonboard",
            "panel_screw_pattern_or_grade_prescribed_here":False},
        "panel_bounds_local_mm": bounds.tolist(), "screw_source_rows": [r["row"] for r in screws],
        "contact_source_rows": [r["row"] for r in contacts], "source_patch_ids": patch_ids,
        "source_contact_areas_mm2": {r["row_id"]: source_cells[r["row_id"]]["area_mm2"] for r in contacts},
        "old_backing_reserved_rectangles_mm": old_rectangles,
        "conceptual_four_upright_centerlines_global_x_mm": uprights,
        "four_upright_datum_hypothesis": "First centerline at frozen left panel edge; three 813 mm spaces. Only upper-left panel is solved.",
        "added_interior_upright_centerline_global_x_mm": interior,
        "added_joint_brace_centerline_local_direction2_mm": float(bounds[1, 1]),
        "added_support_contact_width_mm_hypothesis": CONTACT_WIDTH_MM,
        "joint_brace_half_width_inside_panel_mm": CONTACT_WIDTH_MM/2,
        "new_support_requested_rectangles_mm": new_rectangles,
        "new_support_disjoint_rectangles_mm": pieces, "added_rows": added,
        "added_contact_area_mm2": added_area, "contact_penalty_n_per_mm3": CONTACT_PENALTY,
        "added_gross_nonoverlapping_area_mm2":exact_area,
        "added_back_face_bore_area_removed_mm2":sum(r["back_face_bore_area_removed_mm2"] for r in added),
        "all_existing_screw_receivers_preserved": True,
        "exact_Moon_mounting_pattern_or_frame": False, "source_applied_load": next(
            x for x in data.inputs["cases"] if x["case_id"] == CASE)["source_applied_load"], **FLAGS}


def tiny_coupons():
    benchmark = load(HERE.parent / "panel-attachment/count_benchmark.py", "backing_four_tie_coupon")
    old = solver.SETTINGS
    solver.SETTINGS = QP_SETTINGS
    try:
        tie = benchmark.known_answer()
    finally:
        solver.SETTINGS = old
    pieces = partition_rectangles([[[0., 2.], [0., 2.]], [[1., 3.], [0., 2.]]], [[[1., 2.], [.5, 1.5]]])
    area = sum((r[0][1]-r[0][0])*(r[1][1]-r[1][0]) for r in pieces)
    require(abs(area-5) < 1e-12, "rectangle union/subtraction coupon differs")
    from fea.floor_recess_mesh import shape20, CORNERS, EDGES
    from fea.wood_joint_reduced_members import shape20_derivatives
    point = np.array([.2, -.3, .1])
    require(abs(shape20(point).sum()-1) < 1e-12
            and np.max(abs(shape20_derivatives(point).sum(axis=0))) < 1e-12,
            "C3D20 constant-field coupon differs")
    positions = np.vstack((CORNERS,EDGES))*[50.,20.,10.]
    coordinates = {i+1:p for i,p in enumerate(positions)}
    labels = [(i+1,d) for i in range(20) for d in (1,2,3)]
    row_for = {label:i for i,label in enumerate(labels)}
    coupon = {"physical_body_elements":{"coupon":[1]}, "elements":{"1":["C3D20",list(range(1,21)),"coupon"]}}
    direction = np.array([.3,.4,.5])
    at = point*[50.,20.,10.]
    terms = method.point_terms("coupon",at,direction,coupon,coordinates,row_for)
    nodal = np.array([terms.get(i,0.) for i in range(60)]).reshape(20,3)
    resultant, couple = nodal.sum(axis=0), np.cross(positions,nodal).sum(axis=0)
    require(np.max(abs(resultant-direction)) < 1e-12 and np.max(abs(couple-np.cross(at,direction))) < 1e-12,
            "new point projection loses force/moment work")
    gradient = shape20_derivatives(point) @ np.linalg.inv(positions.T@shape20_derivatives(point))
    affine = positions@np.diag([.001,.002,.003])
    require(np.max(abs(affine.T@gradient-np.diag([.001,.002,.003]))) < 1e-12,
            "affine strain recovery differs")
    h, d, ee, ww, kk = np.zeros((2,2)), np.array([[1.],[-1.]]), np.zeros(2), np.array([200.]), np.full(2,1000.)
    refined_f, refined_a, refined_q = fixed_mask_refinement(h,d,ee,ww,kk,np.ones(2,dtype=bool),np.array([200.,0.]))
    require(np.max(abs(refined_f-[200.,0.])) < 1e-12 and np.max(abs(refined_q-[.2,-.2])) < 1e-12,
            "fixed-mask open/loaded tie coupon differs")
    return {"four_ties": tie, "overlap_subtraction_area_mm2": area,
            "C3D20_constant_translation_and_affine_strain": "PASS",
            "C3D20_point_force_and_couple_identity": "PASS", "fixed_mask_loaded_and_open_ties": "PASS",
            "source_response_or_K_not_opened": True}


def fixed_mask_refinement(H,D,e,W,k,unilateral,seed):
    """Solve the original linear KKT equations on the QP's one active mask.

    This supplies no alternate force law or selector search: inactive rows
    have their exact defining force zero. Original signed-motion and all-row
    spring-law gates decide whether this branch is actually acceptable.
    """
    ids = np.flatnonzero(~unilateral | (seed > 1e-7))
    s = H[np.ix_(ids,ids)]+np.diag(1/k[ids])
    d = D[ids]
    require(np.linalg.matrix_rank(d,tol=1e-9)==D.shape[1], "QP active mask cannot support the rigid wrench")
    matrix = np.block([[s,-d],[d.T,np.zeros((D.shape[1],D.shape[1]))]])
    solution = np.linalg.solve(matrix,np.r_[e[ids],W])
    f = np.zeros(len(k))
    f[ids] = solution[:len(ids)]
    a = solution[len(ids):]
    return f,a,D@a+e-H@f


def preparation(output):
    require(not output.exists(), "preserve previous preparation")
    started = time.monotonic()
    data, pins = sources()
    pins[HERE.parent / "panel-attachment/count_benchmark.py"] = "5d9aa3fc8411e7ca4256f82b58c472c22cc091e94dac7f40e693aed20da23648"
    authenticate(pins)
    record, coupons = layout(data), tiny_coupons()
    output.mkdir(parents=True)
    write(output / "layout.json", record)
    write(output / "known-answer.json", coupons)
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)): h for p,h in pins.items()},
        "package_versions":{name:importlib.metadata.version(name) for name in ("numpy","scipy","osqp")},
        "qp_settings": QP_SETTINGS, "case_count": 1, "branches": ["unchanged_backing", "additional_Moon_like_backing"],
        "rigid_receiver_dofs": 0, "panel_rigid_modes": 6, **FLAGS})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    authenticate(pins)
    write(output / "receipt.json", {"status": "READY_SOURCE_AND_LAYOUT_ONLY_NOT_NUMERICAL_COMPARISON",
        "source_sha256": {str(p.relative_to(ROOT)): h for p,h in pins.items()},
        "output_sha256": {name: sha(output / name) for name in
                          ("layout.json", "known-answer.json", "inputs.json", "producer.py.snapshot")},
        "elapsed_seconds": time.monotonic()-started, "screw_axes": 12,
        "original_contact_cells": len(record["contact_source_rows"]), "added_contact_cells": len(record["added_rows"]),
        "numerical_comparison_complete": False, **FLAGS})
    print(json.dumps({"preparation": str(output), "receipt_sha256": sha(output / "receipt.json"),
                      "source_count": len(pins), "status": "READY_SOURCE_AND_LAYOUT_ONLY_NOT_NUMERICAL_COMPARISON"}))


def physical_fields(physical, coordinates, labels, displacement, constants, axes, output):
    """Recover gross-mesh stress/strain at the original 3×3×3 Gauss points."""
    from fea.wood_joint_reduced_members import shape20_derivatives
    row_for = {label: i for i, label in enumerate(labels)}
    rotation = np.array([axes[k] for k in ("L", "R", "T")]).T
    points = np.polynomial.legendre.leggauss(3)[0]
    records, maxima = [], {"strain": np.zeros(6), "stress_mpa": np.zeros(6)}
    constitutives = {name: method.engineering_stiffness(value, axes) for name,value in constants.items()}
    for element in physical["physical_body_elements"][BODY]:
        kind, nodes, group = physical["elements"][str(element)]
        require(kind == "C3D20", "field recovery element differs")
        positions = np.array([coordinates[n] for n in nodes])
        u = np.array([[displacement[row_for[(n, d)]] for d in (1,2,3)] for n in nodes])
        C = constitutives["PANEL_LAYER_"+group.rsplit("_",1)[1]]
        for ix in product(range(3), repeat=3):
            natural = points[list(ix)]
            derivatives = shape20_derivatives(natural)
            jacobian = positions.T @ derivatives
            require(np.linalg.det(jacobian) > 0, "field recovery Jacobian differs")
            gradient = u.T @ (derivatives @ np.linalg.inv(jacobian))
            strain_tensor = (gradient+gradient.T)/2
            strain = np.array([strain_tensor[a,b]*(1 if a==b else 2) for a,b in method.PAIR])
            stress = C @ strain
            stress_tensor = np.zeros((3,3))
            for (a,b), value in zip(method.PAIR, stress):
                stress_tensor[a,b] = stress_tensor[b,a] = value
            local_strain, local_stress = rotation.T @ strain_tensor @ rotation, rotation.T @ stress_tensor @ rotation
            strain_local = np.array([local_strain[a,b]*(1 if a==b else 2) for a,b in method.PAIR])
            stress_local = np.array([local_stress[a,b] for a,b in method.PAIR])
            maxima["strain"] = np.maximum(maxima["strain"], abs(strain_local))
            maxima["stress_mpa"] = np.maximum(maxima["stress_mpa"], abs(stress_local))
            records.append({"element": element, "layer": group, "natural_xyz": natural.tolist(),
                "strain_local_engineering": strain_local.tolist(), "stress_local_mpa": stress_local.tolist()})
    with gzip.open(output, "wt") as stream:
        for record in records:
            stream.write(json.dumps(record, separators=(",",":"), allow_nan=False)+"\n")
    nodal = np.array([[displacement[row_for[(n,d)]] for d in (1,2,3)] for n in sorted({n for n,_ in labels})])
    return {"sample_count": len(records), "local_components": ["11","22","33","12","13","23"],
        "maximum_absolute_local_engineering_strain": maxima["strain"].tolist(),
        "maximum_absolute_local_stress_mpa": maxima["stress_mpa"].tolist(),
        "maximum_nodal_displacement_norm_mm": float(np.linalg.norm(nodal,axis=1).max()),
        "gauss_stress_is_head_contact_or_hole_fracture_capacity": False,
        "scope": "Gross filled-bore original panel mesh and equivalent material; discrete support/head/load footprints are not local fracture resolution."}


def build(prep, receipt_sha256, output):
    started = time.monotonic()
    require(not output.exists(), "preserve previous numerical result")
    require(sha(prep / "receipt.json") == receipt_sha256, "parent-frozen preparation receipt differs")
    receipt = read(prep / "receipt.json")
    require(receipt["status"] == "READY_SOURCE_AND_LAYOUT_ONLY_NOT_NUMERICAL_COMPARISON", "wrong preparation scope")
    pins = {ROOT / p: h for p,h in receipt["source_sha256"].items()}
    pins[prep / "receipt.json"] = receipt_sha256
    pins.update({prep / name: digest for name,digest in receipt["output_sha256"].items()})
    authenticate(pins)
    data, current_pins = sources()
    require(all(pins.get(p) == h for p,h in current_pins.items()), "source pins differ from frozen preparation")
    plan = read(prep / "layout.json")
    require(plan == layout(data), "prepared support layout differs")
    output.mkdir(parents=True)
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)):h for p,h in pins.items()},
                                  "package_versions":{name:importlib.metadata.version(name) for name in ("numpy","scipy","osqp")},
                                  "preparation_receipt_sha256": receipt_sha256, "qp_settings": QP_SETTINGS, **FLAGS})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    try:
        parser = load(PARSER, "backing_parser")
        helper = load(CONDENSATION, "backing_condensation")
        quotient = load(QUOTIENT, "backing_quotient")
        physical = parser.load_frame_source_model(PHYSICAL)
        coordinates = {int(n): np.array(v) for n,v in data.model["physical_node_coordinates_mm"].items()}
        labels = parser.parse_dof_file(method.NATIVE / "model.dof")
        owners = np.array([physical["owner_by_node"][n] for n,_ in labels])
        body_id = data.model["body_names"].index(BODY)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(i)] for i in dofs]
        local_row = {label:i for i,label in enumerate(body_labels)}
        center, R, Q = helper.rigid_basis(body_labels, coordinates)
        parsed = parser.parse_upper_triangle_file(method.NATIVE / "model.sti", len(labels),
            owner_by_row=owners, owner_names=data.model["body_names"])
        parser.require_no_cross_body_coupling(parsed)
        K = parsed["matrix"][dofs][:,dofs].tocsr()
        retained = plan["screw_source_rows"]+plan["contact_source_rows"]
        original_B = sparse.load_npz(SOURCE / "B.npz").tocsr()[retained][:,dofs]
        added_B = sparse.lil_matrix((len(plan["added_rows"]), len(dofs)))
        for i,row in enumerate(plan["added_rows"]):
            own = row["ownership"]
            for j,value in method.point_terms(BODY, own["point_mm"], np.array(own["direction_global_xyz"]),
                    physical["model"], coordinates, local_row).items():
                added_B[i,j] += value
        B = sparse.vstack((original_B, added_B.tocsr()), format="csr")
        with np.load(SOURCE / "operators.npz", allow_pickle=False) as operators:
            case_index = next(i for i,c in enumerate(data.inputs["cases"]) if c["case_id"] == CASE)
            F = data.model["dead_load_factor"]*operators["F"][dofs,2*case_index]+operators["F"][dofs,2*case_index+1]
            W_source = data.model["dead_load_factor"]*operators["W"][6*body_id:6*body_id+6,2*case_index]+operators["W"][6*body_id:6*body_id+6,2*case_index+1]
            D_source = operators["D"][retained,6*body_id:6*body_id+6]
        require(np.max(abs(original_B@R-D_source)) <= 1e-8, "original rigid projection differs")
        require(np.max(abs(R.T@F-W_source)) <= 1e-8, "full-vector source nodal load/wrench differs")
        D, W = B@R, R.T@F
        # Every new row has the same six rigid point-work coefficients.
        for i,row in enumerate(plan["added_rows"],start=len(retained)):
            direction = np.array(row["ownership"]["direction_global_xyz"])
            expected = np.r_[direction, np.cross(np.array(row["ownership"]["point_mm"])-center,direction)/1000]
            require(np.max(abs(D[i]-expected)) <= 1e-8, "added rigid projection lost point/couple identity")
        raw = np.column_stack((B.T.toarray(), F))
        projected = raw-Q@(Q.T@raw)
        factor, system = helper.factor_bordered(K,R)
        solved = quotient.solve_quotient_chunk(factor,system,K,R,projected)
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, "saved panel quotient failed: "+solved["status"])
        displacement_basis = solved["displacement_mm"]
        H, e = B@displacement_basis[:,:len(B.indptr)-1], B@displacement_basis[:,-1]
        reciprocity = float(np.linalg.norm(H-H.T,ord=np.inf)/np.linalg.norm(H,ord=np.inf))
        require(reciprocity <= 1e-8, "panel compliance loses reciprocity")
        H = (H+H.T)/2
        minimum = float(np.linalg.eigvalsh(H)[0])
        require(minimum >= -1e-9*np.linalg.norm(H,ord=np.inf), "panel compliance is indefinite")
        # Reproduce only the panel-normal block from the earlier saved helper;
        # no added-screw solve or source full-frame H is substituted here.
        rows = [data.rows[i] for i in retained]+plan["added_rows"]
        with np.load(OLD_PANEL_H, allow_pickle=False) as old:
            lookup = {int(row):i for i,row in enumerate(old["indices"])}
            ids = [i for i,row in enumerate(retained) if row in lookup]
            source_ids = [lookup[retained[i]] for i in ids]
            mismatch = float(np.max(abs(H[np.ix_(ids,ids)]-old["H"][np.ix_(source_ids,source_ids)]))
                             /np.max(abs(old["H"][np.ix_(source_ids,source_ids)])))
        require(mismatch <= 1e-7, "same-material source panel-normal compliance differs")
        np.savez_compressed(output / "panel-operators.npz",H=H,D=D,e=e,W=W,F=F,
                            displacement_basis_mm=displacement_basis)
        sparse.save_npz(output / "panel-projection.npz",B)
        write(output / "row-identities.json",rows)
        constants = load(ORIENTATION, "backing_deck_materials").deck_materials(method.NATIVE / "model.inp")
        binding = data.model["material_binding"]["panel_axes"][BODY]
        axes = {"L": binding["assumed_apa_direction_1_global_xyz"],
                "R": binding["assumed_apa_direction_2_global_xyz"], "T": binding["panel_normal_global_xyz"]}
        results = []
        for name,count in (("unchanged_backing",len(retained)),("additional_Moon_like_backing",len(rows))):
            selected, b, h, d, response = rows[:count], B[:count], H[:count,:count], D[:count], e[:count]
            k = np.array([r["law"]["stiffness_N_per_mm"] for r in selected])
            unilateral = np.array([r["family"] == "unilateral_springa" for r in selected])
            require(np.linalg.matrix_rank(d,tol=1e-9)==6, "fixed receiver rows fail full six-mode support")
            old_settings = solver.SETTINGS
            solver.SETTINGS = QP_SETTINGS
            try:
                seed,_,_,iterations = solver.solve_branch(h,d,response,W,k,unilateral,
                    np.empty((0,2),dtype=int),np.empty(0,dtype=bool))
            finally:
                solver.SETTINGS = old_settings
            f,a,q = fixed_mask_refinement(h,d,response,W,k,unilateral,seed)
            law = f-k*np.where(unilateral,np.maximum(q,0),q)
            balance = d.T@f-W
            u_elastic = displacement_basis[:,-1]-displacement_basis[:,:count]@f
            u = R@a+u_elastic
            nodal_load = F-b.T@f
            field_force_error = float(np.max(abs(K@u_elastic-nodal_load)))
            motion_error = float(np.max(abs(b@u-q)))
            metrics = {"force_balance_n": float(np.max(abs(balance[:3]))),
                "moment_balance_nmm": float(1000*np.max(abs(balance[3:]))),
                "spring_law_max_error_n": float(np.max(abs(law))),
                "minimum_unilateral_force_n": float(f[unilateral].min()),
                "maximum_positive_spring_motion_mm": float(q[unilateral].max()),
                "physical_nodal_equilibrium_error_n": field_force_error,
                "projection_vs_physical_motion_error_mm": motion_error, "qp_iterations": iterations,
                "QP_mask_single_original_KKT_refinement": True,
                "force_change_from_QP_seed_max_n": float(np.max(abs(f-seed)))}
            require(metrics["force_balance_n"] <= .1 and metrics["moment_balance_nmm"] <= 2
                and metrics["spring_law_max_error_n"] <= 1e-4 and metrics["minimum_unilateral_force_n"] >= -1e-4
                and metrics["maximum_positive_spring_motion_mm"] <= 10 and field_force_error <= 1e-4
                and motion_error <= 1e-8, name+": unchanged full-vector balance/law/field gates failed: "+json.dumps(metrics))
            branch = output / name
            branch.mkdir()
            groups = defaultdict(list)
            contacts, actions = [], []
            for i,row in enumerate(selected):
                own = row["ownership"]
                sign = 1 if own["second_body"] == BODY else -1
                force = -sign*np.array(own["direction_global_xyz"])*f[i]
                record = {"row_id": row["row_id"], "point_mm": own["point_mm"], "force_on_panel_n": force.tolist(),
                    "scalar_force_n": float(f[i]), "relative_motion_mm": float(q[i]),
                    "law_error_n": float(law[i]), "stiffness_n_per_mm": float(k[i]), "role": own["role"],
                    "elastic_panel_self_compliance_mm_per_n":float(h[i,i]),
                    "elastic_plus_spring_self_compliance_mm_per_n":float(h[i,i]+1/k[i])}
                actions.append(record)
                if own["role"] == "timber_or_panel_contact":
                    area = row.get("contact_area_mm2",plan["source_contact_areas_mm2"].get(row["row_id"]))
                    contacts.append({**record,"area_mm2":area,"average_pressure_mpa":float(f[i]/area)})
                else:
                    groups[row["row_id"].split("/")[0]].append(record)
            screws = []
            references = load(HERE.parent / "panel-attachment/attachment_screen.py", "backing_head_formula")
            head = [float(references.head_reference(.5,9.017,t)*1.6) for t in (17.25625,18.25625)]
            for axis,components in sorted(groups.items()):
                axial = next(r for r in components if r["role"] == "non_qualifying_parametric_screw_withdrawal")
                lateral = [r for r in components if r is not axial]
                require(len(lateral)==2, "same-state lateral screw pair missing")
                force = sum((np.array(r["force_on_panel_n"]) for r in components),np.zeros(3))
                screw = {"case_id": CASE,"panel":BODY,"axis_id":axis,"tension_n":axial["scalar_force_n"],
                    "lateral_n":float(np.linalg.norm(sum((np.array(r["force_on_panel_n"]) for r in lateral),np.zeros(3)))),
                    "signed_force_on_panel_n":force.tolist(),"point_mm":axial["point_mm"],
                    "opening_mm":axial["relative_motion_mm"],"scalar_components":components}
                require(screw["tension_n"] >= 0, "negative axial scalar cannot be clipped into resistance comparison")
                local = data.local.local_screw(screw,data.geometry["panels"][BODY],1.)
                screws.append({**screw,"generic_head_favorable_CD1_6_reference_n":head,
                    "generic_head_favorable_reference_ratio":[screw["tension_n"]/v for v in head],
                    "provisional_local_CD1":local,"complete_screw_acceptance":False})
            write(branch / "screws.json", screws)
            write(branch / "contacts.json", contacts)
            write(branch / "actions.json", actions)
            np.savez_compressed(branch / "response.npz", force_n=f,rigid_coordinates_mm=a,relative_motion_mm=q,
                displacement_mm=u,elastic_displacement_mm=u_elastic,physical_node_labels=np.array(body_labels),
                nodal_external_load_n=F,nodal_connection_load_n=-b.T@f)
            fields = physical_fields(physical["model"],coordinates,body_labels,u,constants,axes,branch / "gauss-fields.jsonl.gz")
            peak = max(screws,key=lambda s:s["tension_n"])
            results.append({"branch":name,"case_id":CASE,"panel":BODY,"screw_count":len(screws),
                "contact_cells":len(contacts),"added_contact_cells":max(0,count-len(retained)),"audit":metrics,
                "peak_screw_same_state":peak,"total_screw_tension_n":sum(s["tension_n"] for s in screws),
                "maximum_same_state_screw_lateral_n":max(s["lateral_n"] for s in screws),
                "total_normal_face_compression_n":sum(c["scalar_force_n"] for c in contacts),
                "peak_contact":max(contacts,key=lambda c:c["scalar_force_n"]),
                "peak_cell_average_contact_pressure_mpa":max(c["average_pressure_mpa"] for c in contacts),
                "panel_fields":fields, "provisional_local_ratio_envelope": {key:max(s["provisional_local_CD1"][key] for s in screws)
                    for key in ("head_face_bearing_ratio","local_punching_ratio","directional_two_ligament_shear_ratio")}})
            print(name,"peak T",peak["tension_n"],"N; full-vector audits",json.dumps(metrics),flush=True)
        previous = [s for s in read(OLD_BENCHMARK)["states"] if s["main_panel_screws"]==12 and s["case_id"]==CASE]
        global_source = read(GLOBAL_CONTEXT)
        global_witness = global_source["generic_screw_envelopes"]["live/nominal"]["combined_withdrawal_lateral"]["withdrawal_0/CD1.0/lateral_0"]["witness"]
        require(global_witness["case_id"]==CASE and global_witness["panel"]==BODY,"prior whole-frame context witness differs")
        write(output / "summary.json", {"status":"COMPLETED_CONDITIONAL_ADDITIONAL_BACKING_PANEL_COMPARISON",
            "states":results,"layout":plan,"external_force_n":W[:3].tolist(),"external_moment_about_datum_nmm":(1000*W[3:]).tolist(),
            "panel_datum_mm":center.tolist(),"source_panel_dofs":len(dofs),"source_panel_elements":len(physical["model"]["physical_body_elements"][BODY]),
            "same_material_panel_normal_compliance_relative_difference":mismatch,"compliance_reciprocity_relative":reciprocity,
            "minimum_compliance_eigenvalue_mm_per_n":minimum,"source_KKT_force_residual_relative":solved["KKT_upper_force_residual_relative"],
            "prior_normal_only_benchmarks_reused_as_context":previous,
            "prior_compatible_whole_frame_context_only": {"witness":global_witness,"source_status":global_source["status"],
                "accepted_states":global_source["counts"]["accepted_states"],"excluded_required_states":global_source["counts"]["excluded_required_states"],
                "force_basis_is_separate":True},
            "prior_context_not_full_vector_force_basis":True,
            "material":data.model["material_binding"], "numerical_comparison_complete":True,
            "limits":["Fixed screw receivers and added backing have no frame motion or physical attachment strength; no source whole-frame acceptance transfers.",
                "Original twelve screw stations and AC-fir material retained; this is augmented backing, not a four-upright replacement or a published Moon mounting prescription.",
                "All six panel wrench components balance through twelve unchanged screw triples and normal face contacts; lateral edge/panel-seam contacts omitted.",
                "Same unmeasured Hillman stiffness and source contact penalty; pressure samples use exact added-area centroids without overlapping old backing bands.",
                "Generic head references include flush countersunk heads but remain conditional ASD references. Local face-pressure/deformation and unrolled-strip punching are provisional screens, not empirical head failure capacities.",
                "Gross filled-bore native panel fields do not resolve countersink contact, loaded-hole stress concentration, crack initiation or delivered veneer failure."],**FLAGS})
        authenticate(pins)
        names = [p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()]
        write(output / "receipt.json", {"status":"COMPLETED_CONDITIONAL_ADDITIONAL_BACKING_PANEL_COMPARISON",
            "source_sha256":{str(p.relative_to(ROOT)):h for p,h in pins.items()},
            "output_sha256":{name:sha(output / name) for name in sorted(names)},
            "elapsed_seconds":time.monotonic()-started,"numerical_comparison_complete":True,**FLAGS})
    except Exception as error:
        write(output / "stop.json", {"status":"STOP_ADDITIONAL_BACKING_COMPARISON", "reason":str(error),
            "elapsed_seconds":time.monotonic()-started,"accepted_strength_or_response_from_terminal_iterate":False,
            "numerical_comparison_complete":False,**FLAGS})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command",required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--output",type=Path,required=True)
    run = sub.add_parser("build")
    run.add_argument("--preparation",type=Path,required=True)
    run.add_argument("--receipt-sha256",required=True)
    run.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        preparation(args.output.resolve())
    else:
        lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
        with lock.open("a") as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            require(read(lock.with_suffix(".json"))["slot"]["state"]=="idle","parent mechanics slot occupied")
            build(args.preparation.resolve(),args.receipt_sha256,args.output.resolve())
