"""Frozen-action local plywood and perforated-section calculations.

Import is inert. build(output) performs NumPy/standard-library postprocessing only.
No producer workflow, frame/native/CAD solve, software test or review is run.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import hashlib
import json
import math
import platform
import re
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/panel-local-net-completion"
N14_PATH = HERE / "panel-reference-completion.py"
LIVE = HERE / "rawlocal/panel-reference-completion/attempt01"
PERMANENT = HERE / "rawlocal/panel-permanent-completion/attempt01"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
ORIGINAL = HERE / "operators-attempt02"
ORIGINAL_FRAME = HERE / "frame-250-attempt02"
ORIGINAL_DEAD = HERE / "rawlocal/dead-load-check/parent-attempt06"
WRENCH = HERE.parent / "top_corner_actions.py"
DOF_BASE = HERE.parent.parent / "mvp-acceleration-2026-09-28"
DOF = DOF_BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
PARSER = DOF_BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
MATERIAL = ROOT / "fea/current_response_materials.py"
PANEL = ROOT / "fea/reinforced_panel_checks.py"
N = 4.4482216152605
T = 18.25625
HEAD_R = 9.017 / 2
SCREW_R = .190 * 25.4 / 2
HEAD_ANGLE_DEG = 82.0
PLANAR = 350 * N / 304.8
MEMBRANE = 105 * N / 25.4
FACE_BEARING = 360 * N / 25.4**2
SOURCE_PINS = {
    N14_PATH: "1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1",
    MATERIAL: "72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135",
    PANEL: "1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d",
    HERE / "panel-permanent-applicability.md": "e019b8ae2e635dd903c3bb3a4a7db7a0942250083f7183bd0291ddf8f2a93492",
    ROOT / "docs/bolted-candidate-hillman-42605-dimensions.json": "d6c3c3ce8d27a02a98a4d9cdca7dce66d2cc5c982cb73b6fb3731ce80d70e72c",
    ROOT / "mini_moonboard/model.py": "aa4f80cbb1400d21ba9fa8c74b0773bd95f7c9644e7eecc06f94cd9f712b65ef",
    LIVE / "receipt.json": "5b42272f49c1924546abab3bd4d036a0a95f7afb2700055fb2e769ab56a3db91",
    PERMANENT / "receipt.json": "7aa5d81d425ce46006943cb37cc44f78fea569b5c0cff454cd8eeb8dc75ea69d",
    GRAVITY / "model.json": "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    GRAVITY / "model-inputs.json": "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    ORIGINAL_FRAME / "response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    ORIGINAL_FRAME / "comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    ORIGINAL / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ORIGINAL / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    ORIGINAL / "operator-assessment.json": "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    ORIGINAL / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    ORIGINAL / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    ORIGINAL / "B.npz": "d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    DOF: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    RAW / "source-cache/apa-D510C-2012.pdf": "6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca",
    RAW / "source-cache/nasa-cr-179435-1988.pdf": "b7fa67627be473b748953795a546711a484c51fe5da9d0f66bc27255a027f811",
}
PRIMARY = {
    "APA_D510C_2012": {
        "url": "https://design.medeek.com/resources/structural/D510C_2012.pdf",
        "sections": "4.4.1-4.4.7, 4.5.1, 4.5.5, 4.6; Table 9 A-A/A-C 23/32",
        "sha256": SOURCE_PINS[RAW / "source-cache/apa-D510C-2012.pdf"],
    },
    "NASA_CR_179435_1988": {
        "url": "https://ntrs.nasa.gov/api/citations/19880017310/downloads/19880017310.pdf",
        "sections": "printed pp. 2-3, equations 1-6; membrane circular-hole elasticity only",
        "sha256": SOURCE_PINS[RAW / "source-cache/nasa-cr-179435-1988.pdf"],
    },
}
ORIGINAL_DEAD_PINS = {
    ORIGINAL_DEAD / "comparison.json": "20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75",
    ORIGINAL_DEAD / "response.npz": "9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14",
}
FLAGS = dict.fromkeys(("geometry_hardware_load_or_stiffness_changed", "native_CAD_or_frame_run",
    "tests_or_review_loop_run", "proposal_adopted", "N14_accepted", "complete_panel_acceptance",
    "complete_joint_acceptance", "physical_release", "fabrication_release"), False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def authenticate(pins):
    for path, expected in pins.items():
        require(path.is_file() and sha(path) == expected, "Source hash differs: " + str(path))


def basis_and_sources():
    pins = {**SOURCE_PINS, Path(__file__).resolve(): sha(__file__)}
    authenticate(pins)
    tree = ast.parse(N14_PATH.read_text(), filename=str(N14_PATH))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "definitions"]
    require(len(nodes) == 1, "One reused pure-definition loader expected")
    namespace = {"ast": ast, "SimpleNamespace": SimpleNamespace, "require": require}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(N14_PATH), "exec"), namespace)  # noqa: S102 -- pinned pure AST loader
    cases = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "CASES" for t in node.targets))
    helper = SimpleNamespace(definitions=namespace["definitions"], CASES=cases)
    for packet in (LIVE, PERMANENT):
        receipt = read(packet / "receipt.json")
        require(receipt["sources_authenticated_before_and_after"], "Frozen source authentication absent")
        # The pinned receipt preserves its complete historical dependency map.
        # Authenticate the leaves actually consumed here. In particular, the
        # permanent producer was later annotated; its frozen executed snapshot
        # remains authoritative, and that producer is not imported here.
        for name in ("screw-states.jsonl", "panel-cuts.jsonl", "panel-balances.jsonl", "summary.json"):
            pins[packet / name] = receipt["output_sha256"][name]
    authenticate(pins)
    inputs, model = read(GRAVITY / "model-inputs.json"), read(GRAVITY / "model.json")
    # Reuse the frozen equivalent-section fit without importing its NumPy/CAD dependencies.
    material = helper.definitions(MATERIAL, ("equivalent_layers",),
        {"math": math, "validate_constants": tuple, "WOOD_E": 1600000*N/25.4**2,
         "APA_EA": (3150000*N/304.8, 5100000*N/304.8),
         "APA_EI": (90500*N*25.4**2/304.8, 320000*N*25.4**2/304.8),
         "APA_GA": 50500*N/25.4})
    panel = helper.definitions(PANEL, ("size_factor", "hold_demand"),
                              {"math": math, "PSI_MPA": N/25.4**2})
    targets = model["material_binding"]["panel_targets"]
    require(read(ROOT / "docs/bolted-candidate-hillman-42605-dimensions.json")["retailer_listed_nominal_head_diameter_mm"] == 2*HEAD_R,
            "Retailer nominal head input differs")
    owner_tree = ast.parse((ROOT / "mini_moonboard/model.py").read_text())
    for variable, expected in (("V1_SELECTED_TNUT_FLANGE_DIAMETER_MM", 25.4),
                               ("V1_SELECTED_TNUT_FLANGE_SCREW_HOLE_DIAMETER_MM", 3.2)):
        value = next(ast.literal_eval(n.value) for n in owner_tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == variable for t in n.targets))
        require(value == expected, "Owner T-nut dimension differs")
    layers = material.equivalent_layers(T, targets["ea_n_per_mm"], targets["ei_nmm"], targets["ga_n_per_mm"])
    require(all(min(row["constants"][:3]) > 0 for row in layers), "Layer modulus not positive")
    require(model["material_binding"]["panel_group_factor"] == 1, "Group 1 force basis differs")
    for member in inputs["members"]:
        if member["member_kind"] == "panel":
            binding = member["current_finished_step_binding"]
            pins[ROOT / binding["path"]] = binding["file_sha256"]
    authenticate(pins)
    return helper, panel, inputs, model, layers, pins


def step_openings(path, basis):
    """Read elementary STEP surfaces as text; no CAD kernel is loaded.

    Cylinders are through-thickness circular-hole hypotheses. Trimmed duplicate
    surfaces at the same axis are joined. The six pinned panels contain only
    plane/cylinder/cone surfaces; trims do not create another hole.
    """
    entities = {int(i): value for i, value in re.findall(r"#(\d+)\s*=\s*(.*?);", path.read_text(), re.DOTALL)}
    grouped = {}
    for entity_id, value in entities.items():
        if not value.startswith(("CYLINDRICAL_SURFACE", "CONICAL_SURFACE")):
            continue
        placement = entities[int(re.findall(r"#(\d+)", value)[0])]
        refs = [int(v) for v in re.findall(r"#(\d+)", placement)]
        def vector(ref):
            return [float(v) for v in re.search(r"\(([^()]*)\)\s*\)$", entities[ref]).group(1).split(",")]
        point, axis = vector(refs[0]), vector(refs[1])
        require(abs(abs(dot(axis, basis[2]))-1) < 1e-8, "Non-normal panel opening")
        local = [dot(point, b) for b in basis]
        key = tuple(round(v, 5) for v in local[:2])
        row = grouped.setdefault(key, {"xy_mm": local[:2], "bore_radius_mm": 0., "cones": [], "surface_ids": []})
        row["surface_ids"].append(entity_id)
        if value.startswith("CYLINDRICAL_SURFACE"):
            radius = float(value.split(",")[-1].rstrip(")"))
            row["bore_radius_mm"] = max(row["bore_radius_mm"], radius)
        else:
            radius, angle = map(float, value.split(",")[-2:][0:1] + [value.split(",")[-1].rstrip(")")])
            row["cones"].append({"radius_mm": radius, "semiangle_rad": angle})
    for row in grouped.values():
        require(row["bore_radius_mm"] > 0, "Cone without joined cylindrical hole")
        radius = row["bore_radius_mm"]
        row["kind"] = "hold" if abs(radius-5.55625) < 1e-8 else "LED" if abs(radius-6.5) < 1e-8 else "screw"
        require(row["kind"] != "screw" or abs(radius-1.4605) < 1e-8 or abs(radius-3.5) < 1e-8,
                "Unrecognized screw cavity")
    return list(grouped.values())


def geometry(inputs, model, screws):
    result, moves = {}, []
    for member in inputs["members"]:
        if member["member_kind"] != "panel":
            continue
        name = member["member_id"]
        orientation = model["material_binding"]["panel_axes"][name]
        basis = [orientation[k] for k in ("assumed_apa_direction_1_global_xyz", "assumed_apa_direction_2_global_xyz", "panel_normal_global_xyz")]
        nodes = [model["physical_node_coordinates_mm"][str(n)] for n in model["body_nodes"][name]]
        bounds = [[min(dot(p, b) for p in nodes), max(dot(p, b) for p in nodes)] for b in basis]
        require(abs(bounds[2][1]-bounds[2][0]-T) < 1e-7, "Thickness differs")
        openings = step_openings(ROOT / member["current_finished_step_binding"]["path"], basis)
        available = [o for o in openings if o["kind"] == "screw"]
        current = [s for s in screws if s["panel"] == name]
        require(len(available) == len(current), "Panel screw cavity count differs")
        for s in current:
            xy = [dot(s["point_mm"], b) for b in basis[:2]]
            hole = min(available, key=lambda o: math.dist(o["xy_mm"], xy))
            distance = math.dist(hole["xy_mm"], xy)
            require(distance < 1e-5 or (distance < 65.950001 and s["axis_id"].endswith(("center_4", "rim_4"))),
                    "Unrecognized cavity substitution")
            available.remove(hole)
            hole["axis_id"] = s["axis_id"]
            hole["frozen_xy_mm"] = hole["xy_mm"][:]
            hole["frozen_bore_radius_mm"] = hole["bore_radius_mm"]
            hole["frozen_cones"] = list(hole["cones"])
            if distance > 1e-5:
                moves.append({"axis_id": s["axis_id"], "panel": name, "obsolete_xy_mm": hole["xy_mm"][:],
                              "current_xy_mm": xy, "distance_mm": distance,
                              "dimensions": {"bore_radius_mm": hole["bore_radius_mm"], "cones": hole["cones"][:]}})
            hole["xy_mm"] = xy
            # This is a local-model profile hypothesis, never a drill instruction.
            hole["bore_radius_mm"] = max(hole["bore_radius_mm"], SCREW_R)
            hole["cones"].append({"radius_mm": HEAD_R, "semiangle_rad": math.radians(HEAD_ANGLE_DEG/2)})
        require(not available, "Unassigned screw cavity")
        result[name] = {"basis": basis, "bounds_mm": bounds, "openings": openings,
                        "STEP_binding": member["current_finished_step_binding"]}
    require(len(moves) == 4, "Four moved cavity substitutions expected")
    counts = Counter(o["kind"] for p in result.values() for o in p["openings"])
    require(counts == {"screw": 66, "hold": 142, "LED": 132}, "Opening inventory differs")
    return {"panels": result, "four_substitutions": moves, "counts": dict(counts),
            "current_geometry_has_extra_obsolete_holes": False, "CAD_bores_are_drill_specs": False,
            "profile_hypothesis": {"head_diameter_mm": 2*HEAD_R, "generic_nominal_screw_diameter_mm": 2*SCREW_R,
                                   "included_angle_deg": HEAD_ANGLE_DEG, "flush_seat": True,
                                   "old_bore_larger_than_nominal_is_retained": True}}


def radius_at(hole, z):
    """z measured from the panel midsurface; countersinks start at front +t/2."""
    return max([hole["bore_radius_mm"], *[c["radius_mm"]-(T/2-z)*math.tan(c["semiangle_rad"]) for c in hole["cones"]]])


def union_length(intervals):
    total, end = 0., -math.inf
    for lo, hi in sorted(intervals):
        if hi > max(end, lo):
            total += hi-max(end, lo)
        end = max(end, hi)
    return total


def width_at(panel, axis, station, z):
    transverse = 1-axis
    lo, hi = panel["bounds_mm"][transverse]
    intervals = []
    for hole in panel["openings"]:
        radius = radius_at(hole, z)
        offset = station-hole["xy_mm"][axis]
        if abs(offset) < radius:
            chord = math.sqrt(radius*radius-offset*offset)
            left, right = max(lo, hole["xy_mm"][transverse]-chord), min(hi, hole["xy_mm"][transverse]+chord)
            if right > left:
                intervals.append((left, right))
    return hi-lo-union_length(intervals)


def section(panel, axis, station, layers, divisions=32):
    """Composite Simpson integration of geometric and E-weighted net sections."""
    values = [0.]*6
    zlo = -T/2
    for layer in layers:
        zhi = zlo+layer["thickness_mm"]
        modulus = layer["constants"][axis]
        dz = (zhi-zlo)/divisions
        for i in range(divisions+1):
            z = zlo+i*dz
            weight = (1 if i in (0, divisions) else 4 if i % 2 else 2)*dz/3
            width = width_at(panel, axis, station, z)
            require(width > 0, "No remaining net panel section")
            for j in range(3):
                values[j] += weight*width*z**j
                values[j+3] += weight*width*modulus*z**j
        zlo = zhi
    area, first, second, ea, eb, ei = values
    require(ea*ei-eb*eb > 0, "Nonpositive net constitutive determinant")
    neutral, bending_stiffness = eb/ea, ei-eb*eb/ea
    q0, q1, maximum, witness_z = 0., 0., 0., -T/2
    zlo = -T/2
    for layer in layers:
        zhi = zlo+layer["thickness_mm"]
        modulus = layer["constants"][axis]
        dz = (zhi-zlo)/divisions
        for i in range(divisions):
            left, right = zlo+i*dz, zlo+(i+1)*dz
            middle = (left+right)/2
            widths = [width_at(panel, axis, station, z) for z in (left, middle, right)]
            for z, width, factor in zip((left, middle, right), widths, (1., 4., 1.), strict=True):
                q0 += factor*dz/6*modulus*width
                q1 += factor*dz/6*modulus*width*z
            coefficient = abs(q1-neutral*q0)/(bending_stiffness*widths[-1])
            if coefficient > maximum:
                maximum, witness_z = coefficient, right
        zlo = zhi
    return {"A_mm2": area, "geometric_centroid_z_mm": first/area,
            "I_about_net_centroid_mm4": second-first*first/area,
            "EA_n": ea, "EB_nmm": eb, "EI_nmm2": ei,
            "elastic_transverse_shear_peak_mpa_per_n": maximum,
            "elastic_transverse_shear_peak_z_mm": witness_z,
            "minimum_remaining_width_mm": min(width_at(panel, axis, station, z) for z in (-T/2, 0., T/2))}


def elastic_field(section_data, force, moment):
    a, b, d = (section_data[k] for k in ("EA_n", "EB_nmm", "EI_nmm2"))
    determinant = a*d-b*b
    return (d*force-b*moment)/determinant, (a*moment-b*force)/determinant


def circular_kt(e1, e2, g12, nu12=0.):
    """NASA equations 1-4 at the principal uniaxial tension maximum."""
    return 1+math.sqrt(2*math.sqrt(e1/e2)-2*nu12+e1/g12)


def original104_adapter(helper, *, permanent=False):
    """Recover original 104-axis saved actions; reuse the existing cut consumer.

    This reads NPZ arrays and multiplies saved forces by their frozen B/D maps.
    It solves no system, changes no sharing and executes no producer workflow.
    """
    import numpy as np

    packet = ORIGINAL_DEAD if permanent else ORIGINAL_FRAME
    model, inputs, rows, comparison = map(read, (ORIGINAL / "model.json", ORIGINAL / "model-inputs.json",
                                               ORIGINAL / "row-identities.json", packet / "comparison.json"))
    require(comparison["modeled_mass_kg"] == model["modeled_mass_kg"] == 224.9499553141194
            and comparison["dead_load_factor"] == 1.1111358300342407,
            "Original104 load/mass binding differs")
    if permanent:
        require(comparison["output_sha256"]["response.npz"] == ORIGINAL_DEAD_PINS[packet / "response.npz"]
                and comparison["equipment_mass_kg"] == 25
                and comparison["load_columns"] == {"gravity": 0, "live": None}
                and all(comparison[k] == 0 for k in ("live_gravity_scale", "live_horizontal_scale", "live_moment_scale"))
                and comparison["original_gravity_multiplier"] == comparison["additional_dead_load_multiplier"] == 1,
                "Original104 permanent load binding differs")
        state = next(s for s in comparison["states"] if s["gap_scale"] == 1)
        certificate = state["fixed_force_clearance_certificate"]
        require(state["status"] == "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING"
                and certificate["bounded"] and certificate["nullity"] == 4
                and not certificate["fixed_force_unique"] and not state["full_frame_acceptance"],
                "Original104 permanent nominal state scope differs")
        cases = (("permanent-only", "dead-only_gap", 0, None),)
    else:
        require(comparison["response_sha256"] == SOURCE_PINS[packet / "response.npz"]
                and comparison["source_climber_weight_lb"] == comparison["comparison_climber_weight_lb"] == 250
                and comparison["climber_load_scale"] == 1, "Original104 live load binding differs")
        cases = tuple((case, case+"_gap", 2*ci, 2*ci+1) for ci, case in enumerate(helper.CASES))
    require(len({c["axis_id"] for c in inputs["connections"] if c["kind"] != "panel_screw"}) == 104,
            "Original104 bolt inventory differs")
    parser = helper.definitions(PARSER, ("parse_dof_lines", "parse_dof_file"),
                                {"Path": Path, "re": re, "AssessmentError": ValueError})
    labels = parser.parse_dof_file(DOF)
    label_rows = {label: i for i, label in enumerate(labels)}
    wrench = helper.definitions(WRENCH, ("wrench",), {"np": np}).wrench
    references = helper.definitions(PANEL, ("size_factor", "panel_reference"),
                                   {"math": math, "LBF_N": N, "PSI_MPA": N/25.4**2}, ("BASE",))
    consumer = helper.definitions(N14_PATH, ("comparison_row", "panel_sections"),
                                 {"np": np, "math": math, "N_PER_LBF": N, "require": require})
    bodies = model["body_names"]
    centers = {body: np.mean([model["physical_node_coordinates_mm"][str(n)]
                             for n in sorted(set(model["body_nodes"][body]))], axis=0) for body in bodies}
    axial, lateral = {}, defaultdict(list)
    for row in rows:
        axis = row["row_id"].split("/")[0]
        if row["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal":
            axial[axis] = row
        elif row["ownership"]["role"] == "panel_screw_lateral_plane":
            lateral[axis].append(row)
    axes = [c for c in inputs["connections"] if c["kind"] == "panel_screw"]
    require(len(axes) == len(axial) == len(lateral) == 66, "Original66 screw join differs")
    screws, cuts, balances = [], [], []
    max_equilibrium_force, max_equilibrium_moment, max_screw_moment = 0., 0., 0.
    with np.load(ORIGINAL / "operators.npz", allow_pickle=False) as operators, \
            np.load(packet / "response.npz", allow_pickle=False) as response, \
            np.load(ORIGINAL / "B.npz", allow_pickle=False) as projection:
        d, physical, w = (operators[k] for k in ("D", "F", "W"))
        require(d.shape == (1888, 300) and physical.shape == (37647, 12)
                and projection["shape"].tolist() == [1888, 37647]
                and projection["format"].item() == b"csr", "Original saved array shapes differ")
        indices, indptr, coefficients = (projection[k] for k in ("indices", "indptr", "data"))
        for case, state_key, dead_column, live_column in cases:
            force = response[state_key+"_raw_force_n"]
            require(force.shape == (1888,) and np.isfinite(force).all(), "Original force row differs")
            connector = np.bincount(indices, weights=-coefficients*np.repeat(force, np.diff(indptr)), minlength=37647)
            applied = comparison["dead_load_factor"]*physical[:, dead_column]
            load = comparison["dead_load_factor"]*w[:, dead_column]
            if live_column is not None:
                applied = applied+physical[:, live_column]
                load = load+w[:, live_column]
            residual = (d.T @ force-load).reshape(-1, 6)
            max_equilibrium_force = max(max_equilibrium_force, float(np.max(abs(residual[:, :3]))))
            max_equilibrium_moment = max(max_equilibrium_moment, float(1000*np.max(abs(residual[:, 3:]))))
            require(np.max(abs(residual[:, :3])) < 1e-5 and 1000*np.max(abs(residual[:, 3:])) < .01,
                    "Original prescribed action equilibrium differs")
            for connection in axes:
                axis = connection["axis_id"]
                source = connection["source_record"]
                panel, receiver = source["panel_member"], source["receiver_member"]
                ids = [r["row"] for r in [*lateral[axis], axial[axis]]]
                block = 6*bodies.index(panel)
                basis = d[ids, block:block+3]
                require(np.max(abs(basis @ basis.T-np.eye(3))) < 1e-10, "Original screw component basis differs")
                signed = -basis.T @ force[ids]
                point_moment = np.cross(np.array(axial[axis]["ownership"]["point_mm"])-centers[panel], signed)
                source_moment = -1000*d[ids, block+3:block+6].T @ force[ids]
                moment_error = float(np.max(abs(point_moment-source_moment)))
                require(moment_error < .01, "Original screw signed datum/moment differs")
                max_screw_moment = max(max_screw_moment, moment_error)
                screws.append({"case_id": case, "axis_id": axis, "panel": panel, "receiver": receiver,
                    "point_mm": axial[axis]["ownership"]["point_mm"], "panel_datum_mm": centers[panel].tolist(),
                    "tension_n": max(0., float(force[ids[2]])), "lateral_n": float(np.linalg.norm(force[ids[:2]])),
                    "signed_force_on_panel_n": signed.tolist(), "source_rows": ids})
            for panel in sorted({s["panel"] for s in screws}):
                actions = []
                for node in sorted(set(model["body_nodes"][panel])):
                    ids = [label_rows[(node, dof)] for dof in (1, 2, 3)]
                    actions.append({"row": -1, "role": "saved_total_nodal_load",
                        "point_mm": model["physical_node_coordinates_mm"][str(node)],
                        "force_n": (applied[ids]+connector[ids]).tolist(), "free_moment_nmm": [0., 0., 0.]})
                balance = wrench(actions, centers[panel])
                require(np.max(abs(balance[:3])) < 1e-5 and np.max(abs(balance[3:])) < .01,
                        "Original panel B/F balance differs")
                cuts.extend(consumer.panel_sections(np, references, wrench, SimpleNamespace(model=model),
                                                   case, panel, actions, centers[panel]))
                balances.append({"case_id": case, "panel": panel, "balance_residual_n_nmm": balance.tolist()})
    require(len(screws) == 66*len(cases) and len(balances) == 6*len(cases)
            and len(cuts) == 376*len(cases), "Original panel coverage differs")
    return {"screws": screws, "cuts": cuts, "balances": balances, "numpy_version": np.__version__,
            "model": model, "inputs": inputs, "comparison": comparison,
            "audits": {"maximum_body_force_residual_n": max_equilibrium_force,
                       "maximum_body_moment_residual_nmm": max_equilibrium_moment,
                       "maximum_screw_point_moment_join_error_nmm": max_screw_moment}}


def method_examples(layers):
    width = 100.
    panel = {"bounds_mm": [[-50., 50.], [-50., 50.], [-T/2, T/2]],
             "openings": [{"xy_mm": [0., 0.], "bore_radius_mm": 10., "cones": []}]}
    ea = sum(l["constants"][0]*l["thickness_mm"] for l in layers)
    ei, z = 0., -T/2
    for layer in layers:
        hi = z+layer["thickness_mm"]
        ei += layer["constants"][0]*(hi**3-z**3)/3
        z = hi
    s = section(panel, 0, 0., layers)
    expected = {"A_mm2": 80*T, "EA_n": 80*ea, "EI_nmm2": 80*ei}
    error = max(abs(s[k]/v-1) for k, v in expected.items())
    kt = circular_kt(7000., 7000., 7000./(2*1.3), .3)
    require(error < 1e-12 and abs(kt-3) < 1e-12, "Known-answer method example differs")
    strain, curvature = elastic_field(s, 800., 1600.)
    require(abs(strain-800/expected["EA_n"]) < 1e-12 and abs(curvature-1600/expected["EI_nmm2"]) < 1e-12,
            "Known-answer constitutive calculation differs")
    homogeneous = [{"thickness_mm": T, "constants": (7000., 7000.)}]
    shear_example = section(panel, 0, 0., homogeneous, 64)
    shear_expected = 1.5/(80*T)
    require(abs(shear_example["elastic_transverse_shear_peak_mpa_per_n"]/shear_expected-1) < 1e-12,
            "Known-answer parabolic shear differs")
    return {"perforated_rectangular_section": {"width_mm": width, "hole_diameter_mm": 20.,
        "calculated": s, "expected": expected, "maximum_relative_error": error},
        "isotropic_circular_hole": {"E_mpa": 7000., "nu": .3, "calculated_Kt": kt, "expected_Kt": 3.},
        "homogeneous_perforated_section_shear": {
            "calculated_peak_mpa_per_n": shear_example["elastic_transverse_shear_peak_mpa_per_n"],
            "expected_1_5_over_net_area_mpa_per_n": shear_expected,
            "peak_z_mm": shear_example["elastic_transverse_shear_peak_z_mm"]},
        "uncoupled_net_section": {"force_n": 800., "moment_nmm": 1600., "strain": strain, "curvature_per_mm": curvature}}


def local_screw(screw, panel, cd):
    hole = next(h for h in panel["openings"] if h.get("axis_id") == screw["axis_id"])
    r = hole["bore_radius_mm"]
    depth = max(max(0., (c["radius_mm"]-r)/math.tan(c["semiangle_rad"])) for c in hole["cones"])
    remaining = T-depth
    head_r = max(HEAD_R, *(c["radius_mm"] for c in hole["cones"]))
    # Uniform projected cone contact; no pressure spread beyond the nominal head.
    annulus = math.pi*(HEAD_R**2-r**2)
    require(annulus > 0 and remaining > 0, "No head annulus or remaining thickness")
    edge = min(hole["xy_mm"][i]-panel["bounds_mm"][i][0]-head_r for i in (0, 1))
    edge = min(edge, *(panel["bounds_mm"][i][1]-hole["xy_mm"][i]-head_r for i in (0, 1)))
    neighbor = min(math.dist(hole["xy_mm"], h["xy_mm"])-head_r-radius_at(h, T/2)
                   for h in panel["openings"] if h is not hole)
    require(min(edge, neighbor) > 0, "Local head perimeter intersects another void/edge")
    tension, lateral = screw["tension_n"], screw["lateral_n"]
    perimeter = 2*math.pi*head_r
    # The planar table is converted via the gross rectangular shear constant 2t/3.
    # Equal line load and the same parabolic z distribution are declared locally.
    shear_stress = 1.5*tension/(perimeter*remaining)
    shear_reference = 1.5*PLANAR/T*cd
    # Two uniform membrane-shear ligaments to the nearest boundary/void;
    # all lateral demand is assigned to this shortest path as an explicit hypothesis.
    ligament = min(edge, neighbor)
    shear_out_capacity = 2*ligament*remaining/T*MEMBRANE*cd
    planar_force = [dot(screw["signed_force_on_panel_n"], b) for b in panel["basis"][:2]]
    require(abs(math.hypot(*planar_force)-lateral) < 1e-6, "Signed lateral component join differs")
    paths = directional_ligaments(panel, hole, head_r, planar_force)
    directional_capacity = sum(path["length_mm"] for path in paths)*remaining/T*MEMBRANE*cd
    return {"case_id": screw["case_id"], "axis_id": screw["axis_id"], "panel": screw["panel"], "CD": cd,
        "same_state_tension_n": tension, "same_state_lateral_n": lateral,
        "bore_diameter_hypothesis_mm": 2*r, "countersink_depth_envelope_mm": depth,
        "remaining_thickness_mm": remaining, "head_to_edge_ligament_mm": edge,
        "head_to_nearest_void_ligament_mm": neighbor, "projected_head_bearing_area_mm2": annulus,
        "uniform_projected_head_pressure_mpa": tension/annulus,
        "head_face_bearing_ratio": tension/annulus/FACE_BEARING,
        "punching_perimeter_mm": perimeter, "local_punching_peak_shear_mpa": shear_stress,
        "planar_reference_stress_mpa": shear_reference,
        "local_punching_ratio": shear_stress/shear_reference,
        "shortest_two_ligament_shear_out_capacity_n": shear_out_capacity,
        "shortest_two_ligament_shear_out_ratio": lateral/shear_out_capacity,
        "signed_panel_in_plane_force_n": planar_force,
        "directional_two_ligament_paths": paths,
        "directional_two_ligament_shear_capacity_n": directional_capacity,
        "directional_two_ligament_shear_ratio": lateral/directional_capacity,
        "simultaneous_linear_shear_budget_hypothesis": shear_stress/shear_reference+lateral/directional_capacity,
        "bearing_CD_applied": False, "complete_screw_or_local_panel_acceptance": False}


def directional_ligaments(panel, hole, radius, planar_force):
    """Two rays from a square circumscribing the head, along the saved load.

    Intervening voids shorten the available material. This is a two-ligament
    resistance hypothesis; the recorded endpoints identify its physical path.
    It supplies no unsupported assertion of a complete block-shear mechanism.
    """
    magnitude = math.hypot(*planar_force)
    direction = [v/magnitude for v in planar_force] if magnitude else [1., 0.]
    perpendicular = [-direction[1], direction[0]]
    result = []
    for sign in (-1, 1):
        start = [hole["xy_mm"][i]+radius*(direction[i]+sign*perpendicular[i]) for i in (0, 1)]
        limits = []
        for i in (0, 1):
            if abs(direction[i]) > 1e-12:
                edge = panel["bounds_mm"][i][1 if direction[i] > 0 else 0]
                limits.append(((edge-start[i])/direction[i], f"panel_edge_axis{i}"))
        for other in panel["openings"]:
            if other is hole:
                continue
            delta = [other["xy_mm"][i]-start[i] for i in (0, 1)]
            along = dot(delta, direction)
            across = dot(delta, perpendicular)
            other_radius = radius_at(other, T/2)
            if abs(across) < other_radius:
                intersection = along-math.sqrt(other_radius**2-across**2)
                if intersection >= 0:
                    limits.append((intersection, "void/"+other.get("axis_id", other["kind"])))
        length, endpoint = min(limits)
        require(length > 0, "Directional head ligament is outside the panel")
        result.append({"sign": sign, "start_xy_mm": start, "direction_xy": direction,
                       "length_mm": length, "endpoint": endpoint})
    return result


def net_rows(cuts, geometry_data, model, layers, panel_helper, cds):
    result, cache, integration = [], {}, []
    by_group = defaultdict(list)
    for cut in cuts:
        by_group[(cut["case_id"], cut["panel"], cut["cut_axis"])].append(cut)
    targets = model["material_binding"]["panel_targets"]
    gross_shear = {}
    for axis in (0, 1):
        gross = {"bounds_mm": [[0., 1.], [0., 1.], [-T/2, T/2]], "openings": []}
        gross_shear[axis] = section(gross, axis, .5, layers, 64)["elastic_transverse_shear_peak_mpa_per_n"]
    for (case, name, axis), group in by_group.items():
        p = geometry_data["panels"][name]
        b = p["basis"]
        width = p["bounds_mm"][1-axis][1]-p["bounds_mm"][1-axis][0]
        stations = sorted((dot(c["datum_mm"], b[axis]), c) for c in group)
        locations = [x[0] for x in stations]
        requests = [(x, c, "saved_action_station") for x, c in stations]
        # Add the actual hole-center net cuts; source forces are transported exactly
        # within the intervals bounded by every saved nodal action station.
        for x in sorted({round(h["xy_mm"][axis], 6) for h in p["openings"]}):
            index = bisect.bisect_right(locations, x)-1
            if index < 0 or index >= len(stations)-1:
                continue
            c = stations[index][1]
            requests.append((x, c, "hole_center_in_source_load_free_interval"))
        for x, c, origin in requests:
            key = (name, axis, round(x, 6))
            if key not in cache:
                cache[key] = section(p, axis, x, layers)
                if any(abs(x-h["xy_mm"][axis]) < radius_at(h, T/2) for h in p["openings"]):
                    finer = section(p, axis, x, layers, 64)
                    relative = max(abs(cache[key][k]/finer[k]-1) for k in
                                   ("A_mm2", "EA_n", "EI_nmm2", "elastic_transverse_shear_peak_mpa_per_n"))
                    integration.append({"panel": name, "cut_axis": axis, "station_mm": x, "relative_32_64_change": relative})
                    cache[key] = finer
            s = cache[key]
            old = c["datum_mm"]
            datum = [old[i]+(x-dot(old, b[axis]))*b[axis][i] for i in range(3)]
            f = c["signed_cut_force_xyz_n"]
            shift = cross([old[i]-datum[i] for i in range(3)], f)
            moment = [c["signed_cut_moment_xyz_nmm"][i]+shift[i] for i in range(3)]
            # The scalar section moment conjugate to axial epsilon + kappa*z.
            # In a right-handed x/y/normal basis M_y=-integral(z*sigma_x)dA.
            normal_force = dot(f, b[axis])
            bending_moment = (-1 if axis == 0 else 1)*dot(moment, b[1-axis])
            axial_field = elastic_field(s, normal_force, 0.)
            bending_field = elastic_field(s, 0., bending_moment)
            base = {"parallel": {"tension": 5100., "compression": 4800., "bending": 775.},
                    "perpendicular": {"tension": 3400., "compression": 2900., "bending": 455.}}[c["family"]]
            size = panel_helper.size_factor(width)
            ea, ei = targets["ea_n_per_mm"][axis], targets["ei_nmm"][axis]
            strain_t = base["tension"]*N/304.8*size/ea
            strain_c = base["compression"]*N/304.8/ea
            strain_b = base["bending"]*N*25.4/304.8*size*T/2/ei
            z_values = (-T/2, -T/4, T/4, T/2)
            axial_ratio = max(abs(axial_field[0]+axial_field[1]*z)/
                              (strain_t if axial_field[0]+axial_field[1]*z >= 0 else strain_c) for z in z_values)
            bending_ratio = max(abs(bending_field[0]+bending_field[1]*z)/strain_b for z in z_values)
            kt = circular_kt(ea/T, targets["ea_n_per_mm"][1-axis]/T, targets["ga_n_per_mm"]/T)
            for cd in cds:
                result.append({"case_id": case, "panel": name, "cut_axis": axis, "family": c["family"], "CD": cd,
                    "origin": origin, "station_absolute_local_mm": x, "source_side": c["side"],
                    "source_station_from_panel_datum_mm": c["station_from_panel_datum_mm"],
                    "signed_axial_n": normal_force, "signed_bending_nmm": bending_moment,
                    "signed_normal_shear_n": dot(f, b[2]), "signed_membrane_shear_n": dot(f, b[1-axis]),
                    "gross_width_mm": width, "net_section": s,
                    "axial_field_strain_curvature": axial_field, "bending_field_strain_curvature": bending_field,
                    "net_axial_ratio": axial_ratio/cd, "net_bending_ratio": bending_ratio/cd,
                    "linear_axial_bending_budget_hypothesis": (axial_ratio+bending_ratio)/cd,
                    "elastic_net_transverse_shear_peak_mpa": abs(dot(f, b[2]))*s["elastic_transverse_shear_peak_mpa_per_n"],
                    "equivalent_layer_planar_shear_reference_mpa": PLANAR*gross_shear[axis]*cd,
                    "net_planar_shear_ratio": abs(dot(f, b[2]))*s["elastic_transverse_shear_peak_mpa_per_n"]/(PLANAR*gross_shear[axis]*cd),
                    "net_membrane_shear_ratio": abs(dot(f, b[1-axis]))/(MEMBRANE*(s["A_mm2"]/T)*cd),
                    "isolated_hole_membrane_Kt": kt,
                    "isolated_hole_membrane_reference_sensitivity": axial_ratio*kt/cd,
                    "Kt_applied_to_bending_or_shear": False, "complete_panel_acceptance": False})
    return result, {"geometry_sections": len(cache), "32_to_64_subdivision_comparisons": len(integration),
                    "maximum_relative_change": max((r["relative_32_64_change"] for r in integration), default=0.),
                    "largest_change_witness": max(integration, key=lambda r: r["relative_32_64_change"]) if integration else None}


def hold_rows(inputs, geometry_data, panel_helper):
    """Existing hold equilibrium helper; current six loads and explicit arm scenarios."""
    result = []
    for case in inputs["cases"]:
        load = case["source_applied_load"]
        point = load["patch_center_global_xyz_mm"]
        name = min(geometry_data["panels"], key=lambda p: min(math.dist([dot(point, b) for b in geometry_data["panels"][p]["basis"][:2]],
                    h["xy_mm"]) for h in geometry_data["panels"][p]["openings"] if h["kind"] == "hold"))
        p = geometry_data["panels"][name]
        force = load["applied_force_global_xyz_n"]
        normal = dot(force, p["basis"][2])
        shear = math.hypot(dot(force, p["basis"][0]), dot(force, p["basis"][1]))
        for arm in (25., 50., 100.):
            # Reuse the existing equilibrium/bearing helper in its aligned force plane.
            row = panel_helper.hold_demand(downward_n=shear, horizontal_outward_n=normal,
                angle_deg=0., standoff_mm=100., contact_lever_arm_mm=arm,
                flange_diameter_mm=25.4, panel_hole_mm=11.1125, retention_hole_mm=3.2, retention_hole_count=3)
            tension = row["minimum_bolt_tension_n"]
            for cd in (1., 1.25):
                result.append({"case_id": case["case_id"], "panel": name, "hold_id": load["hold_id"], "CD": cd,
                    "contact_arm_hypothesis_mm": arm, "force_basis": row,
                    "local_flange_punching_ratio": tension/(math.pi*25.4*PLANAR*cd),
                    "bearing_CD_applied": False, "actual_contact_arm_known": False,
                    "retention_holes_are_flange_holes_not_extra_plywood_through_holes": True})
    return result


def envelope(records, metrics):
    result = {}
    for metric in metrics:
        for label in sorted({("permanent" if r["case_id"] == "permanent-only" else "live", r["CD"]) for r in records}):
            selected = [r for r in records if ("permanent" if r["case_id"] == "permanent-only" else "live", r["CD"]) == label]
            witness = max(selected, key=lambda r: r[metric])
            result[f"{metric}/{label[0]}/CD{label[1]}"] = {"finite": len(selected),
                "exceeded": sum(r[metric] > 1 for r in selected), "maximum_ratio": witness[metric], "witness": witness}
    return result


def build_original_permanent(output):
    """One saved original-mass nominal permanent state; no frame solve.

    The authenticated attempt05 geometry and known-answer results are reused;
    live/proposal numerical outputs and their receipts remain frozen.
    """
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh immediate owned output child required")
    helper, panel_helper, _, proposal_model, layers, pins = basis_and_sources()
    pins.update(ORIGINAL_DEAD_PINS)
    reused = RAW / "attempt05"
    for name, digest in {
        "geometry.json": "758b5156f0d5ce9d0c46a0fd7f29b47d59fe408a122c6eec7e4d7de34fc0dd4c",
        "method-validation.json": "7575cf1af8ee9342d8992cfc26e8f39c3eb6da90173bf1620d03bf1c9f51e49c",
        "receipt.json": "cc0913beefa78e9cb146f257049b45a6388eedcd29fc483b2b1ab5351b171073",
    }.items():
        pins[reused / name] = digest
    authenticate(pins)
    original = original104_adapter(helper, permanent=True)
    require(original["model"]["material_binding"] == proposal_model["material_binding"],
            "Original/proposal material and panel frames differ")
    g = read(reused / "geometry.json")
    for screw in original["screws"]:
        panel = g["panels"][screw["panel"]]
        hole = next(h for h in panel["openings"] if h.get("axis_id") == screw["axis_id"])
        require(math.dist(hole["xy_mm"], [dot(screw["point_mm"], b) for b in panel["basis"][:2]]) < 1e-8,
                "Original104 permanent force/current cavity geometry differs")
    local = [local_screw(s, g["panels"][s["panel"]], .9) for s in original["screws"]]
    net, quadrature = net_rows(original["cuts"], g, original["model"], layers, panel_helper, (.9,))
    report = {
        "schema": "panel_local_net_original104_permanent/v1",
        "status": "COMPLETED_CONDITIONAL_ORIGINAL104_PERMANENT_LOCAL_NET_NUMERICAL_COMPARISON",
        "force_basis": {"global_bolt_axes": 104, "panel_screw_axes": 66,
            "case_id": "permanent-only", "saved_state": "dead-only_gap", "gap_scale": 1.,
            "modeled_mass_kg": original["comparison"]["modeled_mass_kg"],
            "dead_load_factor": original["comparison"]["dead_load_factor"], "accessory_mass_kg": 25,
            "equipment_multiplier_applied_once": True, "live_load_included": False,
            "proposal_mass_or_internal_tie_actions_included": False, "no_slip_support": True,
            "bounded_nominal_seating": True, "nominal_state_nullity": 4,
            "fixed_force_unique": False, "alternative_seating_envelope_computed": False,
            "zero_gap_sensitivity_used": False},
        "material": {"Group1_AC_23_32_hypothesis": True, "thickness_mm": T,
            "equivalent_layers": layers, "primary": PRIMARY, "CD": .9,
            "face_bearing_CD_applied": False, "source_material_axes_retained": True},
        "counts": {"screw_states": len(local), "panel_balances": len(original["balances"]),
            "recovered_gross_source_cuts": len(original["cuts"]), "net_section_records": len(net),
            "openings": g["counts"]},
        "local_screw_envelopes": envelope(local, ("head_face_bearing_ratio", "local_punching_ratio",
            "shortest_two_ligament_shear_out_ratio", "directional_two_ligament_shear_ratio",
            "simultaneous_linear_shear_budget_hypothesis")),
        "net_section_envelopes": envelope(net, ("net_axial_ratio", "net_bending_ratio",
            "linear_axial_bending_budget_hypothesis", "net_planar_shear_ratio", "net_membrane_shear_ratio",
            "isolated_hole_membrane_reference_sensitivity")),
        "action_recovery_audits": original["audits"], "quadrature": quadrature,
        "reused_geometry_and_method_packet": str(reused.relative_to(ROOT)),
        "applicability": [
            "The same local/net resistance hypotheses as authenticated attempt05 are used on the separate original104-only nominal permanent force tuple, without force redistribution.",
            "The saved nominal force solution has four bounded seating freedoms and does not supply a strict stability result or an envelope over alternative seating forces.",
            "Plywood sheet group/layup, Hillman delivered profile/bore/contact, and actual hold/front-contact distributions remain unmeasured physical bindings.",
            "Local punching/two-ligament allocation and additive interaction are declared resistance hypotheses, not tested fastener capacities or codified multiaxial panel acceptance.",
            "NASA isolated-hole membrane Kt is a sensitivity, not a loaded-hole, close-edge, bending, thick-hole or combined plate comparison.",
            "Live Hillman head reference deficits remain independently recorded and are not resolved by the permanent-only result."], **FLAGS}
    authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    for name, value in (("screw-actions.jsonl", original["screws"]),
                        ("panel-cut-actions.jsonl", original["cuts"]),
                        ("panel-balances.jsonl", original["balances"]),
                        ("screw-local.jsonl", local), ("net-sections.jsonl", net)):
        with (output / name).open("x") as stream:
            for row in value:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False)+"\n")
    for name, value in (("summary.json", report),
                        ("sources.json", {str(p.relative_to(ROOT)): s for p, s in sorted(pins.items())})):
        (output / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")
    authenticate(pins)
    output_hashes = {p.name: sha(p) for p in sorted(output.iterdir())}
    (output / "receipt.json").write_text(json.dumps({
        "schema": "panel_local_net_completion_receipt/v1", "status": report["status"],
        "source_sha256": {str(p.relative_to(ROOT)): s for p, s in sorted(pins.items())},
        "output_sha256": output_hashes, "producer_sha256": sha(__file__),
        "sources_authenticated_before_and_after": True,
        "runtime": {"python": platform.python_version(), "numpy": original["numpy_version"], "numerical_solver": None},
        **FLAGS}, sort_keys=True, indent=2, allow_nan=False)+"\n")
    return report


def build(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh immediate owned output child required")
    helper, panel_helper, inputs, model, layers, pins = basis_and_sources()
    live_screws, dead_screws = jsonl(LIVE / "screw-states.jsonl"), jsonl(PERMANENT / "screw-states.jsonl")
    live_cuts, dead_cuts = jsonl(LIVE / "panel-cuts.jsonl"), jsonl(PERMANENT / "panel-cuts.jsonl")
    require(len(live_screws) == 396 and len(dead_screws) == 66, "66-axis/six-case basis differs")
    original = original104_adapter(helper)
    original_by_axis = {s["axis_id"]: s for s in original["screws"] if s["case_id"] == helper.CASES[0]}
    require(all(original_by_axis[s["axis_id"]]["point_mm"] == s["point_mm"]
                and original_by_axis[s["axis_id"]]["panel"] == s["panel"] for s in live_screws),
            "Original/proposal force-axis geometry differs")
    current_screws = [s for s in live_screws if s["case_id"] == helper.CASES[0]]
    g = geometry(inputs, model, current_screws)
    validation = method_examples(layers)
    local = [local_screw(s, g["panels"][s["panel"]], cd) for s in live_screws for cd in (1., 1.25)]
    local.extend(local_screw(s, g["panels"][s["panel"]], .9) for s in dead_screws)
    net, quadrature = net_rows(live_cuts, g, model, layers, panel_helper, (1., 1.25))
    permanent_net, dead_quadrature = net_rows(dead_cuts, g, model, layers, panel_helper, (.9,))
    net.extend(permanent_net)
    holds = hold_rows(inputs, g, panel_helper)
    original_local = [local_screw(s, g["panels"][s["panel"]], cd) for s in original["screws"] for cd in (1., 1.25)]
    original_net, original_quadrature = net_rows(original["cuts"], g, original["model"], layers, panel_helper, (1., 1.25))
    report = {"schema": "panel_local_net_completion/v1", "status": "COMPLETED_CONDITIONAL_LOCAL_NET_NUMERICAL_COMPARISON",
        "force_basis": {"global_bolt_axes": 104, "panel_screw_axes": 66,
            "response_mass_scope": "Unadopted 108-axis knee-bridge proposal planning mass/actions on unchanged 104-axis stiffness/connector rows",
            "reviewed_104_mass_kg": 224.9499553141194, "proposal_planning_mass_kg": model["modeled_mass_kg"],
            "proposal_delta_mass_kg": model["knee_bridge_planning_gravity"]["net_mass_delta_kg"],
            "planning_accessory_mass_kg": 25, "equipment_multiplier_applied_once": True,
            "climber_lb": 250, "downward_dynamic_factor": 2, "horizontal_force_n": 300,
            "hold_lever_mm": 100, "six_cases_are_alternatives": True, "no_slip_support": True,
            "reviewed_104_only_mass_response_recomputed": False},
        "material": {"Group1_AC_23_32_hypothesis": True, "dry_ordinary_temperature": True,
            "thickness_mm": T, "equivalent_layers": layers, "measured_veneer_properties": False,
            "source_material_axes_retained": True, "PLANAR_N_per_mm_CD1": PLANAR,
            "MEMBRANE_N_per_mm_CD1": MEMBRANE, "face_bearing_reference_mpa": FACE_BEARING,
            "bearing_deformation_reference_mm": 1.016, "primary": PRIMARY},
        "counts": {"live_screw_states_per_duration": 396, "permanent_screw_states": 66,
            "net_section_duration_records": len(net), "hold_duration_records": len(holds), "openings": g["counts"]},
        "local_screw_envelopes": envelope(local, ("head_face_bearing_ratio", "local_punching_ratio",
            "shortest_two_ligament_shear_out_ratio", "directional_two_ligament_shear_ratio",
            "simultaneous_linear_shear_budget_hypothesis")),
        "net_section_envelopes": envelope(net, ("net_axial_ratio", "net_bending_ratio", "linear_axial_bending_budget_hypothesis",
            "net_planar_shear_ratio", "net_membrane_shear_ratio", "isolated_hole_membrane_reference_sensitivity")),
        "hold_envelopes": envelope(holds, ("local_flange_punching_ratio",)),
        "original_reviewed104_live": {
            "force_basis": {"global_bolt_axes": 104, "panel_screw_axes": 66,
                "modeled_mass_kg": original["comparison"]["modeled_mass_kg"],
                "dead_load_factor": original["comparison"]["dead_load_factor"],
                "response_sha256": SOURCE_PINS[ORIGINAL_FRAME / "response.npz"],
                "proposal_mass_or_internal_tie_actions_included": False},
            "counts": {"screw_states_per_duration": 396, "net_section_duration_records": len(original_net),
                       "recovered_gross_source_cuts": len(original["cuts"]), "panel_balances": len(original["balances"])},
            "local_screw_envelopes": envelope(original_local, ("head_face_bearing_ratio", "local_punching_ratio",
                "directional_two_ligament_shear_ratio", "simultaneous_linear_shear_budget_hypothesis")),
            "net_section_envelopes": envelope(original_net, ("net_axial_ratio", "net_bending_ratio",
                "linear_axial_bending_budget_hypothesis", "net_planar_shear_ratio", "net_membrane_shear_ratio",
                "isolated_hole_membrane_reference_sensitivity")),
            "quadrature": original_quadrature, "numpy_version": original["numpy_version"]},
        "quadrature": {"live": quadrature, "permanent": dead_quadrature},
        "specific_missing_physical_inputs": {
            "countersink_and_bore": "Delivered Hillman external/head profile, actual installed bore diameter, included angle and depth; the local model declares these explicitly.",
            "hold": "Actual hold front-contact lever arm/footprint for each loaded hold; 25/50/100 mm scenarios are finite hypotheses, not measured actions.",
            "plywood": "Actual sheet group/grain/layup, local damage/defects and veneer properties; use the stated Group1 equivalent section until bound.",
            "local_force_distribution": "Delivered cone-seat pressure and through-thickness/perimeter load distribution; uniform projected bearing and parabolic transverse shear are the declared calculation model."},
        "applicability": [
            "Net section uses plane sections and directional equivalent laminate; finite hole/countersink A/EB/EI and elastic transverse shear V*Q_E/(D_net*remaining_width(z)) are integrated, not the former gross full-width means.",
            "Prescribed existing actions are transported without redistribution. Changed net stiffness is used only in the local resistance model, not as a new global compatible solution.",
            "Local punching is a stated circular strip model calibrated to APA planar shear, not an APA screw pull-through table or a tested punching capacity.",
            "Directional two-ligament shear uses the signed saved lateral force, actual panel boundaries and intervening voids. A separate shortest-path allocation sensitivity is retained. The additive shear budget is a declared allocation hypothesis, not a codified multiaxial failure criterion.",
            "NASA isolated-hole Kt is a membrane sensitivity for an infinite thin orthotropic plate. It is not applied to bending, thick-hole constraints, close edge/neighbor interaction or loaded holes.",
            "Existing screw/head/gross rolling-shear exceedances remain frozen and repairs deferred; finite completion does not set acceptance/release flags.",
            "The source is 104-axis stiffness with proposal-specific mass/actions. These outputs do not silently become a reviewed104-only gravity response."], **FLAGS}
    report["specific_missing_physical_inputs"]["original104_permanent_actions"] = (
        "No frozen original104-only gravity response supplied. The existing permanent comparison remains proposal planning gravity; parent owns the future coupled original104 permanent state.")
    authenticate(pins)
    output.mkdir(parents=True)
    def write(name, value, lines=False):
        with (output / name).open("x") as stream:
            if lines:
                for row in value:
                    stream.write(json.dumps(row, sort_keys=True, allow_nan=False)+"\n")
            else:
                stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write("geometry.json", g)
    write("method-validation.json", validation)
    write("screw-local.jsonl", local, True)
    write("net-sections.jsonl", net, True)
    write("hold-local.jsonl", holds, True)
    write("original104-screw-actions.jsonl", original["screws"], True)
    write("original104-panel-cut-actions.jsonl", original["cuts"], True)
    write("original104-panel-balances.jsonl", original["balances"], True)
    write("original104-screw-local.jsonl", original_local, True)
    write("original104-net-sections.jsonl", original_net, True)
    write("summary.json", report)
    write("sources.json", {str(p.relative_to(ROOT)): s for p, s in sorted(pins.items())})
    authenticate(pins)
    output_hashes = {p.name: sha(p) for p in sorted(output.iterdir())}
    write("receipt.json", {"schema": "panel_local_net_completion_receipt/v1", "status": report["status"],
        "source_sha256": {str(p.relative_to(ROOT)): s for p, s in sorted(pins.items())},
        "output_sha256": output_hashes, "producer_sha256": sha(__file__),
        "sources_authenticated_before_and_after": True, "runtime": {"python": platform.python_version(),
        "numpy": original["numpy_version"], "numerical_solver": None}, **FLAGS})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--original104-permanent", action="store_true",
                        help="Consume the separate saved original104-only nominal permanent state")
    arguments = parser.parse_args()
    summary = (build_original_permanent if arguments.original104_permanent else build)(arguments.output)
    print(json.dumps({"status": summary["status"], "counts": summary["counts"]}, sort_keys=True))
