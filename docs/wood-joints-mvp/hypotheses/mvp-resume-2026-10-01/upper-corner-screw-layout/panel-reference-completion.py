"""N14 finite same-state references; the parent alone calls build(output).

Import performs no I/O. prepare(output) authenticates frozen inputs and joins
identities using the standard library, without reading numerical array values.
build(output) consumes saved arrays; it runs no producer, solve, CAD or coupon.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/panel-reference-completion"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02"
ASSESSMENT = GRAVITY / "operator-assessment.json"
COMPARISON = FRAME / "response/comparison.json"
RESPONSE = FRAME / "response/response.npz"
MODEL = GRAVITY / "model.json"
INPUTS = GRAVITY / "model-inputs.json"
ROWS = GRAVITY / "row-identities.json"
OPERATORS = GRAVITY / "operators.npz"
PROJECTION = GRAVITY / "B.npz"
BASE = PACKET.parent / "mvp-acceleration-2026-09-28"
DOF = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CLOSURE = HERE / "all-joint-splitting/closure.py"
ATTACHMENT = PACKET / "panel-attachment/attachment_screen.py"
LATERAL = PACKET / "panel-attachment/lateral_reference.py"
YIELD = ROOT / "fea/dowel_yield.py"
PANEL = ROOT / "fea/reinforced_panel_checks.py"
WRENCH = PACKET / "top_corner_actions.py"
HEAD = HERE / "head-reference-basis.md"
REFERENCE = PACKET / "panel-attachment/results/attempt08-all-two-receiver/comparison.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
AXIAL = "non_qualifying_parametric_screw_withdrawal"
SHEAR = "panel_screw_lateral_plane"
CONTACT = "timber_or_panel_contact"
N_PER_LBF = 4.4482216152605
PINS = {
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    GRAVITY / "receipt.json": "315c16d2a592b12dcd0160af47f9d4bababb6afaf54c6c74ddcbd41e01d45b6c",
    FRAME / "receipt.json": "6acb01eb1b07dc9f9175cb3a0e916fe74a9a32a7b90941cf3b18e84a24d9c599",
    CLOSURE: "095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d",
    ATTACHMENT: "c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc",
    LATERAL: "8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2",
    YIELD: "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    PANEL: "1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    DOF: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    HEAD: "577f75fa32889fdb5ee53f1076ebec924132b5251d6e92e571ab0b49e96588d3",
    HERE / "head_check.py": "352fd499f3486037a401ab3b4dabeb4838a93aa8db67564f4ca30d0b3ea9382a",
    HERE / "panel-material-fidelity.md": "5c411432f0c0f6abddaefa9ba2c27fe46a2c0b990e2513f3fe65f2f03f2e361f",
    HERE / "qualification-register.md": "2e76193522c6da1d009e2363e84f459d7ba7b01e1f64124858d1558fc12c9880",
    REFERENCE: "7146069ad3ecf913cbb354f3a37d1e6af6768fc3b577f574feb5a10bd483eb2f",
    ROOT / "docs/bolted-candidate-hillman-42605-dimensions.json": "d6c3c3ce8d27a02a98a4d9cdca7dce66d2cc5c982cb73b6fb3731ce80d70e72c",
    ROOT / "docs/purchased-materials.md": "3a1e09c02e223cdec91ad96e258046e73322a23c6417252453f818624c3b8bad",
    ROOT / "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    ROOT / "docs/wood-joints-mvp/criteria.json": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
}
FLAGS = dict.fromkeys((
    "proposal_adopted", "formal_criteria_updated", "N14_accepted", "Hillman_capacity_qualified",
    "geometry_hardware_load_or_stiffness_changed", "historical_acceptance_transferred",
    "SPAX_resistance_or_installation_transferred", "second_duration_or_dynamic_credit",
    "complete_joint_acceptance", "physical_release", "fabrication_release",
    "native_CAD_frame_or_coupon_run", "original_producer_pipelines_executed",
    "tests_or_review_loop_run", "new_contact_or_frame_sharing_solved",
), False)
LIMITS = [
    "The fresh source has 104 global bolt axes. The unadopted 108-axis proposal includes four internal ties with no added global receiver rows; their compatibility is not supplied here.",
    "Generic NDS screw geometry, DF-L G=.50, plywood G=.42/.50, thread reach and dry/ordinary-temperature factors are declared scenarios, not delivered Hillman or plywood properties.",
    "CD=1 and the existing favorable CD=1.6 short-duration scenario are separate; 1.6 is applied once to unadjusted references. The saved 2x force is unchanged and receives no further dynamic credit.",
    "The listed 9.017-mm head is retailer nominal. Bugle/flat profile descriptions, actual head depth/tolerance, flush countersink net thickness and B18.6.1 conformity remain unqualified.",
    "Withdrawal thread lengths are hypotheses within gross receiver projection, not measured installed engagement. Gross rectangular receiver intervals do not resolve bores, passages, splitting or pilot conformity.",
    "Lateral references assume contacting faces, standard .152-inch root and Fyb=80 ksi. Saved positive opening remains visible; a contacting-face diagnostic does not establish loaded contact or product applicability.",
    "Fyb for dowel bending is not a tensile yield or allowable stress. Root T/V stress requirements are finite demand diagnostics; Hillman steel strengths and screw bending/head-neck profile are missing specific bases.",
    "Returned absolute panel/receiver motions are the saved rigid components. Total relative motion includes elasticity from q=Da+e-Hf. Individual absolute elastic fields, unique poses, seating-motion bounds and serviceability limits are not available.",
    "Panel cuts integrate saved simultaneous loads and connector actions across a gross full width. Mean component comparisons are necessary section diagnostics, not local plate stresses, effective strip widths, net-hole strength, combined interaction or complete panel acceptance.",
    "APA Group 1 references use the saved declared Group 1/23-32-category strength-axis scenario. The existing Group 4 family envelope is separately labeled; neither stiffness nor sheet placement is changed. APA PDF identity is quoted by the frozen helper, not newly authenticated PDF bytes.",
    "Contact wrenches reuse existing forces without redistribution. Small-screw detailing/splitting, plywood seat bearing, complete receiver/backer continuation and N09 washers remain separate checks.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def definitions(path, names, namespace, constants=()):
    """Load authenticated pure definitions only, never module import/workflows."""
    tree = ast.parse(path.read_text(), filename=str(path))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(functions) == len(names) and all(not n.decorator_list for n in functions), "helper definitions differ")
    selected = [n for n in tree.body if n in functions or
                (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                 and n.targets[0].id in constants)]
    require({n.targets[0].id for n in selected if isinstance(n, ast.Assign)} == set(constants), "helper constants differ")
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, *selected], type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**namespace)


def headers(path):
    """Only ZIP/NPY headers; preparation never consumes array values."""
    result = {}
    with ZipFile(path) as archive:
        for name in archive.namelist():
            require(name.endswith(".npy") and name[:-4] not in result, "unexpected NPZ entry")
            with archive.open(name) as stream:
                magic = stream.read(8)
                require(magic[:6] == b"\x93NUMPY" and magic[6:8] in (b"\x01\x00", b"\x02\x00", b"\x03\x00"), "NPY version differs")
                size = struct.unpack("<H" if magic[6] == 1 else "<I", stream.read(2 if magic[6] == 1 else 4))[0]
                require(size < 65536, "unexpected NPY header size")
                value = ast.literal_eval(stream.read(size).decode("utf-8" if magic[6] == 3 else "latin1"))
                require(value["descr"] in ("<f8", "<i4", "<i8", "|S3") and not value["fortran_order"], "array representation differs")
                result[name[:-4]] = {**value, "shape": list(value["shape"])}
    return result


def sources():
    require(sha(CLOSURE) == PINS[CLOSURE], "authentication helper changed")
    api = definitions(CLOSURE, ("read", "key", "bind", "authenticate", "receipt_sources"),
                      {"Path": Path, "json": json, "ROOT": ROOT, "require": require, "sha": sha})
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    api.authenticate(pins)
    api.receipt_sources(pins, GRAVITY / "receipt.json")
    api.receipt_sources(pins, FRAME / "receipt.json")
    assessment, comparison, model, inputs, rows = map(api.read, (ASSESSMENT, COMPARISON, MODEL, INPUTS, ROWS))
    for name, digest in assessment["output_sha256"].items():
        api.bind(pins, GRAVITY / name, digest)
    for record in (assessment, comparison, inputs):
        for name, digest in record["source_sha256"].items():
            api.bind(pins, ROOT / name, digest)
    cache = PACKET.parent / "upper-block-strength-2026-10-01/source-cache"
    for name, digest in {
        "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
        "chapter11-2024-awc-20260911.pdf": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
        "chapter2-2024-awc.pdf": "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
        "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
    }.items():
        api.bind(pins, cache / name, digest)
    api.authenticate(pins)
    require(assessment["operator_ready"] and assessment["case_ids"] == list(CASES), "fresh operators not ready")
    require(comparison["response_sha256"] == PINS[RESPONSE]
            and comparison["frame_operator_directory"] == api.key(GRAVITY), "fresh response binding differs")
    require([(s["gap_scale"], s["case_id"]) for s in comparison["states"]]
            == [(gap, case) for gap in (0.0, 1.0) for case in CASES]
            and all(s["status"].startswith("PASS_CONDITIONAL_") for s in comparison["states"]), "source states incomplete")
    require(comparison["source_climber_weight_lb"] == comparison["comparison_climber_weight_lb"] == 250
            and comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1
            and comparison["comparison_horizontal_force_n"] == 300, "load envelope differs")
    require(all(r["modeled_mass_kg"] == 225.19791414318078 and r["dead_load_factor"] == 1.1110134616260479
                for r in (assessment, comparison, model, inputs))
            and model["planning_accessory_mass_kg"] == 25, "gravity/accessory basis differs")
    require(not comparison["complete_joint_acceptance"] and not comparison["physical_release"], "unexpected acceptance")
    candidate = api.read(ROOT / "wood-joints-candidate.json")
    criteria = api.read(ROOT / "docs/wood-joints-mvp/criteria.json")
    obligations = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    require(len(obligations) == 47 and all(c["status"] == "pending" for c in obligations)
            and len(candidate["release_flags"]) == 8 and all(v is False for v in candidate["release_flags"].values())
            and candidate["release"] is False, "47-criterion/eight-flag authority differs")
    require(model["material_binding"]["panel_group_factor"] == 1
            and model["material_binding"]["panel_targets"]["thickness_mm"] == 18.25625, "panel scenario differs")
    receipt = api.read(FRAME / "receipt.json")
    require(receipt["global_receiver_bolt_axes"] == 104 and receipt["total_unique_proposal_bolt_axes"] == 108
            and not receipt["new_internal_bolts_are_global_connectors"], "104/108 distinction differs")
    for case in inputs["cases"]:
        load = case["source_applied_load"]
        require(load["case_inputs"]["pounds"] == 250 and load["case_inputs"]["dynamic_factor"] == 2,
                "saved downward force basis differs")
        delta = [a - b for a, b in zip(load["force_application_point_global_xyz_mm"], load["patch_center_global_xyz_mm"], strict=True)]
        require(math.isclose(math.sqrt(sum(v*v for v in delta)), 100, abs_tol=1e-7), "hold lever differs")
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "row ordering differs")
    members = {m["member_id"]: m for m in inputs["members"]}
    axes = {c["axis_id"]: c for c in inputs["connections"] if c["kind"] == "panel_screw"}
    axial, lateral = {}, defaultdict(list)
    for row in rows:
        axis = row["row_id"].split("/")[0]
        if row["ownership"]["role"] == AXIAL:
            require(axis not in axial, "duplicate screw tie")
            axial[axis] = row
        elif row["ownership"]["role"] == SHEAR:
            lateral[axis].append(row)
    require(len(axes) == len(axial) == 66 and set(axes) == set(axial) == set(lateral), "66-axis join differs")
    groups = []
    for axis, connection in sorted(axes.items()):
        station = connection["source_record"]
        panel, receiver = station["panel_member"], station["receiver_member"]
        components = [*lateral[axis], axial[axis]]
        require(len(components) == 3 and len(lateral[axis]) == 2, "incomplete screw components")
        require(all({r["ownership"]["first_body"], r["ownership"]["second_body"]} == {panel, receiver}
                    and r["ownership"]["point_mm"] == axial[axis]["ownership"]["point_mm"] for r in components), "mixed screw hosts/datum")
        require(members[panel]["member_kind"] == "panel" and members[receiver]["member_kind"] == "timber"
                and station["purchased_nominal_length_mm"] == 63.5, "receiver/product identity differs")
        groups.append({"axis_id": axis, "panel": panel, "receiver": receiver,
                           "rows": [r["row"] for r in components], "point_mm": axial[axis]["ownership"]["point_mm"],
                           "axis": connection["axis_xyz"], "source_axis_record": station,
                           "receiver_geometry": members[receiver]["reduced_geometry_descriptor"]})
    require(Counter(g["panel"] for g in groups) == {"main_upper_left": 12, "main_upper_right": 12,
            "main_lower_left": 12, "main_lower_right": 12, "kicker_left": 9, "kicker_right": 9}, "panel screw counts differ")
    laws = comparison["panel_screw_stiffness_n_per_mm"]
    for role, key in ((AXIAL, "withdrawal"), (SHEAR, "lateral_components")):
        source_laws = [r["law"]["stiffness_N_per_mm"] for r in rows if r["ownership"]["role"] == role]
        require(laws[key] == laws["source_" + key] == source_laws, "screw law tuning is outside scope")
    require(laws["product_laws_measured"] is False, "product law claim differs")
    arrays = {"operators": headers(OPERATORS), "response": headers(RESPONSE), "projection": headers(PROJECTION)}
    require(arrays["operators"]["D"]["shape"] == [1888, 300]
            and arrays["operators"]["H"]["shape"] == [1888, 1888], "operator dimensions differ")
    for case in CASES:
        for suffix, shape in (("raw_force_n", [1888]), ("lumped_q_mm", [1612]), ("rigid_coordinates", [300])):
            require(arrays["response"][case + "_gap_" + suffix]["shape"] == shape, "nominal response dimensions differ")
    parser = definitions(PARSER, ("parse_dof_lines", "parse_dof_file"), {"Path": Path, "re": re, "AssessmentError": ValueError})
    labels = parser.parse_dof_file(DOF)
    require(len(labels) == arrays["operators"]["F"]["shape"][0] == 37647, "physical load DOF join differs")
    api.authenticate(pins)
    return SimpleNamespace(api=api, pins=pins, comparison=comparison, model=model, inputs=inputs,
                           rows=rows, members=members, axes=groups, headers=arrays, labels=labels)


def references():
    """Existing pure arithmetic, isolated from producers and solver imports."""
    head = definitions(ATTACHMENT, ("head_reference", "withdrawal_reference"),
                       {"np": SimpleNamespace(pi=math.pi), "N_PER_LBF": N_PER_LBF})
    shear = definitions(YIELD, ("single_shear",), {"math": math})
    lateral = definitions(LATERAL, ("generic_lateral_reference", "combined_reference"),
                          {"math": math, "require": require, "single_shear": shear.single_shear},
                          ("N_PER_LBF", "D_IN", "DR_IN", "FYB_PSI", "PLYWOOD_MM", "LENGTH_MM", "TIP_MM", "NOMINAL_P_MM", "MODES"))
    panel = definitions(PANEL, ("size_factor", "panel_reference"),
                        {"math": math, "LBF_N": N_PER_LBF, "PSI_MPA": N_PER_LBF/25.4**2}, ("BASE",))
    saved = json.loads(REFERENCE.read_text())
    withdrawal = []
    for i, row in enumerate(saved["withdrawal_sensitivities"]):
        g, p = row["timber_G_hypothesis"], row["effective_thread_penetration_mm_hypothesis"]
        value = head.withdrawal_reference(g, p)
        require(math.isclose(value, row["unadjusted_generic_withdrawal_n"], rel_tol=1e-12), "retained withdrawal formula differs")
        withdrawal.append({"id": f"withdrawal_{i}", "timber_G": g, "effective_thread_mm": p, "unadjusted_n": value})
    require(len(withdrawal) == 12, "withdrawal scenario count differs")
    heads = []
    scenarios = ((.42, 7.5, 14), (.42, 9.2202, 17.25625), (.50, 9.2202, 17.25625),
                 (.50, 9.2202, 18.25625), (.42, 9.017, 17.25625), (.50, 9.017, 17.25625), (.50, 9.017, 18.25625))
    for i, (g, diameter, thickness) in enumerate(scenarios):
        heads.append({"id": f"head_{i}", "plywood_G": g, "diameter_mm": diameter, "net_thickness_mm": thickness,
                          "unadjusted_n": float(head.head_reference(g, diameter, thickness)),
                          "geometry_basis": "retailer nominal 42605" if diameter == 9.017 else "generic/hypothetical"})
    return SimpleNamespace(heads=heads, withdrawal=withdrawal, lateral=[lateral.generic_lateral_reference(fe) for fe in (3350.0, 4650.0)],
                           combined=lateral.combined_reference, panel=panel, duration_factors=[1.0, 1.6])


def nominal_receiver(np, axis):
    """Gross source envelope interval only; not an exact finished-solid check."""
    geometry = axis["receiver_geometry"]
    basis = np.array([geometry[k] for k in ("axis", "section_u", "section_v")], dtype=float)
    basis /= np.linalg.norm(basis, axis=1)[:, None]
    require(np.max(abs(basis @ basis.T - np.eye(3))) < 1e-7, "receiver frame differs")
    start = np.asarray(geometry["start"])
    origin = np.asarray(axis["source_axis_record"]["origin_global_xyz_mm"])
    direction = np.asarray(axis["axis"], dtype=float)
    require(abs(np.linalg.norm(direction) - 1) < 1e-7, "screw axis not unit")
    point, ray = basis @ (origin - start), basis @ direction
    low, high = 0.0, 63.5
    bounds = ((0, geometry["length_mm"]), (-geometry["width_mm"]/2, geometry["width_mm"]/2),
              (-geometry["depth_mm"]/2, geometry["depth_mm"]/2))
    for coordinate, slope, (lo, hi) in zip(point, ray, bounds, strict=True):
        if abs(slope) < 1e-9:
            require(lo - 1e-5 <= coordinate <= hi + 1e-5, "axis misses gross receiver")
        else:
            hits = sorted(((lo - coordinate)/slope, (hi - coordinate)/slope))
            low, high = max(low, hits[0]), min(high, hits[1])
    low = max(low, 18.25625)
    require(high > low, "no nominal projection into current receiver")
    grain = np.asarray(geometry["grain_global_xyz"], dtype=float)
    grain /= np.linalg.norm(grain)
    return {"gross_interval_from_head_mm": [low, high], "gross_overlap_mm": high-low,
                "sidegrain_axis_dot_abs": float(abs(direction @ grain)), "exact_finished_embedment_established": False}


def comparison_row(value):
    require(math.isfinite(value) and value >= 0, "nonfinite reference ratio")
    return {"ratio": value, "status": "EXCEEDS_DECLARED_REFERENCE" if value > 1 else "WITHIN_DECLARED_REFERENCE"}


def screw_references(tension, shear, geometry, refs):
    head, withdrawal, lateral, combined = {}, {}, {}, {}
    lateral_geometry = (geometry["sidegrain_axis_dot_abs"] < 1e-7
                        and geometry["gross_overlap_mm"] + 1e-5 >= 63.5 - 18.25625)
    for cd in refs.duration_factors:
        for row in refs.heads:
            head[f"{row['id']}/CD{cd}"] = comparison_row(tension/(cd*row["unadjusted_n"]))
        for i, row in enumerate(refs.lateral):
            lateral[f"lateral_{i}/CD{cd}"] = comparison_row(shear/(cd*row["unadjusted_generic_lateral_reference_n"])) if lateral_geometry else {
                "ratio": None, "status": "UNSUPPORTED_GEOMETRY", "reason": "saved reference requires side-grain and its full nominal bearing projection"}
        for row in refs.withdrawal:
            applicable = geometry["sidegrain_axis_dot_abs"] < 1e-7 and row["effective_thread_mm"] <= geometry["gross_overlap_mm"] + 1e-5
            key = f"{row['id']}/CD{cd}"
            withdrawal[key] = comparison_row(tension/(cd*row["unadjusted_n"])) if applicable else {
                "ratio": None, "status": "UNSUPPORTED_GEOMETRY", "reason": "side-grain insertion or proposed thread length outside gross receiver interval"}
            for i, lat in enumerate(refs.lateral):
                ckey = key + f"/lateral_{i}"
                if not applicable or not lateral_geometry:
                    combined[ckey] = {"ratio": None, "status": "UNSUPPORTED_GEOMETRY"}
                    continue
                result = refs.combined(shear, tension, cd*lat["unadjusted_generic_lateral_reference_n"], cd*row["unadjusted_n"])
                combined[ckey] = {**result, **comparison_row(result["combined_index"])}
    root = .152*25.4
    area = math.pi*root**2/4
    return {"head": head, "withdrawal": withdrawal, "contacting_lateral": lateral, "combined_withdrawal_lateral": combined,
                "steel": {"root_diameter_mm_hypothesis": root, "root_area_mm2_hypothesis": area,
                           "tensile_mean_stress_mpa": tension/area, "shear_mean_stress_mpa": shear/area,
                           "required_same_section_von_mises_yield_mpa": math.hypot(tension/area, math.sqrt(3)*shear/area),
                           "actual_steel_ratio": None, "status": "MISSING_HILLMAN_STEEL_AND_PROFILE_BASIS",
                           "missing": ["actual minimum root/head-neck section", "tensile/yield or allowable steel stress", "screw bending field/profile"],
                           "Fyb_80ksi_is_tensile_strength": False}}


def assess(data):
    """Parent-only finite array arithmetic; no equation system is solved."""
    import numpy as np

    refs = references()
    wrench = definitions(WRENCH, ("wrench",), {"np": np}).wrench
    bodies, rows = data.model["body_names"], data.rows
    centers = {body: np.mean([data.model["physical_node_coordinates_mm"][str(n)] for n in sorted(set(data.model["body_nodes"][body]))], axis=0) for body in bodies}
    retained = [r["row"] for r in rows if r["ownership"]["second_body"] != "floor"]
    positions = {raw: i for i, raw in enumerate(retained)}
    require(len(retained) == 1588, "nonfloor motion prefix differs")
    axes = {row["axis_id"]: row for row in data.axes}
    geometries = {axis: nominal_receiver(np, row) for axis, row in axes.items()}
    screws, groups, panels, cuts, audits = [], [], [], [], []
    label_rows = {label: i for i, label in enumerate(data.labels)}
    with np.load(OPERATORS, allow_pickle=False) as operator, np.load(RESPONSE, allow_pickle=False) as response, \
            np.load(PROJECTION, allow_pickle=False) as projection:
        D, H, e, W, F = (operator[name] for name in ("D", "H", "e", "W", "F"))
        require(all(np.isfinite(a).all() for a in (D, H, e, W, F)), "nonfinite operator array")
        require(projection["format"].item() == b"csr" and projection["shape"].tolist() == [1888, 37647], "physical projection format differs")
        indices, indptr, coefficients = (projection[k] for k in ("indices", "indptr", "data"))
        require(indptr.shape == (1889,) and indptr[0] == 0 and indptr[-1] == len(indices) == len(coefficients)
                and np.all(np.diff(indptr) >= 0) and np.all((indices >= 0) & (indices < 37647))
                and np.isfinite(coefficients).all(), "invalid physical projection")
        for ci, case in enumerate(CASES):
            tag = case + "_gap"
            force, q, rigid = (response[tag + "_" + suffix] for suffix in ("raw_force_n", "lumped_q_mm", "rigid_coordinates"))
            require(all(np.isfinite(a).all() for a in (force, q, rigid)), "nonfinite saved response")
            # Reuse the frozen port footprints. This is -B.T f, not a new allocation.
            nodal_connector = np.bincount(indices, weights=-coefficients*np.repeat(force, np.diff(indptr)), minlength=37647)
            load = data.comparison["dead_load_factor"]*W[:, 2*ci] + W[:, 2*ci+1]
            relative = D @ rigid + data.comparison["dead_load_factor"]*e[:, 2*ci] + e[:, 2*ci+1] - H @ force
            residual = (D.T @ force - load).reshape(-1, 6)
            compatibility = float(np.max(abs(relative[retained] - q[:len(retained)])))
            require(np.max(abs(residual[:, :3])) < 1e-5 and 1000*np.max(abs(residual[:, 3:])) < .01
                    and compatibility < 1e-6, "saved equilibrium/motion does not close")
            actions_by_panel = {}
            for panel in sorted({a["panel"] for a in axes.values()}):
                block = 6*bodies.index(panel)
                incident = [r for r in rows if panel in (r["ownership"]["first_body"], r["ownership"]["second_body"])]
                actions = []
                for row in incident:
                    index, point = row["row"], row["ownership"]["point_mm"]
                    f = -D[index, block:block+3]*force[index]
                    moment = np.cross(np.asarray(point) - centers[panel], f)
                    free_moment = -1000*D[index, block+3:block+6]*force[index] - moment
                    actions.append({"row": index, "role": row["ownership"]["role"], "point_mm": point, "force_n": f.tolist(),
                                        "free_moment_nmm": free_moment.tolist(), "other": next(b for b in (row["ownership"]["first_body"], row["ownership"]["second_body"]) if b != panel)})
                actions_by_panel[panel] = actions
            max_law_error = 0.0
            for axis, station in axes.items():
                ids, panel, receiver = station["rows"], station["panel"], station["receiver"]
                pb, rb = 6*bodies.index(panel), 6*bodies.index(receiver)
                basis = D[ids, pb:pb+3]
                require(np.max(abs(basis @ basis.T - np.eye(3))) < 1e-10
                        and np.max(abs(basis + D[ids, rb:rb+3])) < 1e-10, "screw basis/signs differ")
                motions = q[[positions[i] for i in ids]]
                expected = [rows[i]["law"]["stiffness_N_per_mm"]*(max(0.0, m) if i == ids[2] else m) for i, m in zip(ids, motions, strict=True)]
                error = float(np.max(abs(force[ids] - expected)))
                max_law_error = max(max_law_error, error)
                require(error < 1e-4 and force[ids[2]] >= -1e-4, "saved screw law differs")
                point = np.asarray(station["point_mm"])
                def rigid_motion(body, block, coordinates=rigid, datum=point):
                    return coordinates[block:block+3] + np.cross(coordinates[block+3:block+6]/1000, datum - centers[body])
                pm, rm = rigid_motion(panel, pb), rigid_motion(receiver, rb)
                require(np.max(abs(basis @ (pm-rm) - D[ids] @ rigid)) < 1e-7, "rigid motion datum differs")
                tension, shear = max(0.0, float(force[ids[2]])), float(np.linalg.norm(force[ids[:2]]))
                own = [a for a in actions_by_panel[panel] if a["row"] in ids]
                signed = -basis.T @ force[ids]
                receiver_wrench = -D[ids, rb:rb+6].T @ force[ids] * [1, 1, 1, 1000, 1000, 1000]
                panel_at_point = wrench(own, point)
                receiver_at_point = receiver_wrench.copy()
                receiver_at_point[3:] += np.cross(centers[receiver]-point, receiver_at_point[:3])
                require(np.max(abs(panel_at_point+receiver_at_point)) < 1e-5, "opposite complete screw wrenches differ")
                screws.append({"case_id": case, "gap_scale": 1, "axis_id": axis, "panel": panel, "receiver": receiver,
                    "source_rows": ids, "point_mm": point.tolist(), "component_basis_on_panel_xyz": basis.tolist(),
                    "component_signed_force_n": force[ids].tolist(), "signed_axial_raw_n": float(force[ids[2]]),
                    "tension_n": tension, "lateral_n": shear, "signed_force_on_panel_n": signed.tolist(),
                    "signed_force_on_receiver_n": (-signed).tolist(), "screw_wrench_about_panel_datum_n_nmm": wrench(own, centers[panel]).tolist(),
                    "screw_wrench_about_receiver_datum_n_nmm": receiver_wrench.tolist(),
                    "saved_port_free_couple_on_panel_nmm": panel_at_point[3:].tolist(),
                    "panel_datum_mm": centers[panel].tolist(), "receiver_datum_mm": centers[receiver].tolist(),
                    "panel_rigid_motion_xyz_mm": pm.tolist(), "receiver_rigid_motion_xyz_mm": rm.tolist(),
                    "total_relative_components_mm": motions.tolist(), "total_panel_minus_receiver_xyz_mm": (basis.T @ motions).tolist(),
                    "relative_elastic_panel_minus_receiver_xyz_mm": (basis.T @ motions - (pm-rm)).tolist(),
                    "signed_axial_relative_mm": float(motions[2]), "positive_opening_mm": max(0.0, float(motions[2])),
                    "absolute_elastic_panel_or_receiver_motion": None,
                    "geometry": geometries[axis], "references": screw_references(tension, shear, geometries[axis], refs),
                    "lateral_contacting_faces_demonstrated": False, "loaded_opening_present": bool(motions[2] > 1e-8),
                    "bending_couple_returned_by_scalar_frame": False, "complete_screw_acceptance": False})
            for panel, actions in actions_by_panel.items():
                selected = [s for s in screws if s["case_id"] == case and s["panel"] == panel]
                for receiver in sorted({s["receiver"] for s in selected}):
                    states = [s for s in selected if s["receiver"] == receiver]
                    ids = {i for s in states for i in s["source_rows"]}
                    own = [a for a in actions if a["row"] in ids]
                    contact = [a for a in actions if a["role"] == CONTACT and a["other"] == receiver]
                    datum = np.mean([s["point_mm"] for s in states], axis=0)
                    sw, cw = wrench(own, datum), wrench(contact, datum)
                    groups.append({"case_id": case, "panel": panel, "receiver": receiver, "axis_ids": [s["axis_id"] for s in states],
                        "common_datum_mm": datum.tolist(), "screw_wrench_on_panel_n_nmm": sw.tolist(),
                        "screw_wrench_on_receiver_n_nmm": (-sw).tolist(), "contact_rows": [a["row"] for a in contact],
                        "saved_contact_wrench_on_panel_n_nmm": cw.tolist(), "saved_pair_wrench_on_panel_n_nmm": (sw+cw).tolist(),
                        "complete_receiver_or_contact_resistance": False})
                block = 6*bodies.index(panel)
                nodal, total_nodal, connector_nodal = [], [], []
                for node in sorted(set(data.model["body_nodes"][panel])):
                    ids = [label_rows[(node, dof)] for dof in (1, 2, 3)]
                    f = data.comparison["dead_load_factor"]*F[ids, 2*ci] + F[ids, 2*ci+1]
                    nodal.append({"row": -1, "role": "saved_nodal_load", "point_mm": data.model["physical_node_coordinates_mm"][str(node)], "force_n": f.tolist(), "free_moment_nmm": [0, 0, 0]})
                    connector = nodal_connector[ids]
                    connector_nodal.append({**nodal[-1], "role": "saved_B_connector_load", "force_n": connector.tolist()})
                    total_nodal.append({**nodal[-1], "role": "saved_total_nodal_load", "force_n": (f+connector).tolist()})
                external = wrench(nodal, centers[panel])
                require(np.max(abs(external - load[block:block+6]*[1, 1, 1, 1000, 1000, 1000])) < 1e-5, "panel F/W loads differ")
                require(np.max(abs(wrench(connector_nodal, centers[panel])-wrench(actions, centers[panel]))) < 1e-5,
                        "panel nodal B projection/complete D wrench differs")
                balance = wrench([*actions, *nodal], centers[panel])
                require(np.max(abs(balance[:3])) < 1e-5 and np.max(abs(balance[3:])) < .01, "panel actions not balanced")
                panels.append({"case_id": case, "panel": panel, "datum_mm": centers[panel].tolist(),
                    "screw_wrench_n_nmm": wrench([a for a in actions if a["role"] in (AXIAL, SHEAR)], centers[panel]).tolist(),
                    "contact_wrench_n_nmm": wrench([a for a in actions if a["role"] == CONTACT], centers[panel]).tolist(),
                    "external_load_wrench_n_nmm": external.tolist(), "balance_residual_n_nmm": balance.tolist()})
                cuts.extend(panel_sections(np, refs.panel, wrench, data, case, panel, total_nodal, centers[panel]))
            audits.append({"case_id": case, "force_residual_n": float(np.max(abs(residual[:, :3]))),
                "moment_residual_nmm": float(1000*np.max(abs(residual[:, 3:]))), "compatibility_residual_mm": compatibility,
                "screw_law_error_n": max_law_error})
    require(len(screws) == len({(s["case_id"], s["axis_id"]) for s in screws}) == 396 and len(panels) == 36, "worksheet coverage incomplete")
    return {"screws": screws, "groups": groups, "panels": panels, "cuts": cuts, "audits": audits,
                "catalog": {"heads": refs.heads, "withdrawal": refs.withdrawal, "lateral": refs.lateral,
                             "duration_factors": refs.duration_factors, "CD_applied_once": True}, "numpy_version": np.__version__}


def panel_sections(np, helper, wrench, data, case, panel, actions, center):
    """Gross whole-cut component diagnostics; never infer a local strip width."""
    orientation = data.model["material_binding"]["panel_axes"][panel]
    basis = np.asarray([orientation[k] for k in ("assumed_apa_direction_1_global_xyz", "assumed_apa_direction_2_global_xyz", "panel_normal_global_xyz")])
    require(np.max(abs(basis @ basis.T - np.eye(3))) < 1e-10, "panel axes differ")
    coordinates = np.asarray([a["point_mm"] for a in actions])
    local = (coordinates - center) @ basis.T
    node_ids = data.model["body_nodes"][panel]
    nodes = (np.asarray([data.model["physical_node_coordinates_mm"][str(n)] for n in node_ids]) - center) @ basis.T
    records = []
    for axis in (0, 1):
        transverse = 1-axis
        width = float(np.ptp(nodes[:, transverse]))
        minimum, maximum = float(nodes[:, axis].min()), float(nodes[:, axis].max())
        stations = sorted({round(float(s), 6) for s in local[:, axis] if minimum+1e-5 < s < maximum-1e-5})
        family = "perpendicular" if axis == 0 else "parallel"
        base, cs = helper.BASE[family], helper.size_factor(width)
        group1 = {"bending_nmm_per_mm": base["bending"]*cs*N_PER_LBF*25.4/304.8,
                      "tension_n_per_mm": base["tension"]*cs*N_PER_LBF/304.8,
                      "compression_n_per_mm": base["compression"]*N_PER_LBF/304.8,
                      "transverse_shear_n_per_mm": 350*N_PER_LBF/304.8}
        group4 = helper.panel_reference(width, family)
        for station in stations:
            for side in ("before", "after"):
                cut = station + (-1e-5 if side == "before" else 1e-5)
                datum = (center + basis[axis]*cut
                         + basis[transverse]*(float(nodes[:, transverse].min())+float(nodes[:, transverse].max()))/2
                         + basis[2]*(float(nodes[:, 2].min())+float(nodes[:, 2].max()))/2)
                left = [a for a, location in zip(actions, local, strict=True) if location[axis] < cut]
                right = [a for a, location in zip(actions, local, strict=True) if location[axis] >= cut]
                negative, positive = -wrench(left, datum), wrench(right, datum)
                require(np.max(abs((negative-positive)[:3])) < 1e-5 and np.max(abs((negative-positive)[3:])) < .01, "opposite panel cut halves differ")
                f, m = basis @ negative[:3], basis @ negative[3:]
                demands = {"axial_mean_n_per_mm": float(f[axis]/width), "bending_mean_nmm_per_mm": float(m[transverse]/width), "transverse_shear_mean_n_per_mm": float(f[2]/width)}
                comparisons = {}
                for label, reference in (("Group1_saved_scenario", group1), ("Group4_existing_family_envelope", group4)):
                    axial_key = "tension_n_per_mm" if f[axis] >= 0 else "compression_n_per_mm"
                    comparisons[label] = {"axial": comparison_row(abs(demands["axial_mean_n_per_mm"])/reference[axial_key]),
                        "bending": comparison_row(abs(demands["bending_mean_nmm_per_mm"])/reference["bending_nmm_per_mm"]),
                        "transverse_shear": comparison_row(abs(demands["transverse_shear_mean_n_per_mm"])/reference["transverse_shear_n_per_mm"])}
                records.append({"case_id": case, "panel": panel, "cut_axis": axis, "family": family, "station_from_panel_datum_mm": cut,
                    "side": side, "gross_stressed_width_mm": width, "datum_mm": datum.tolist(), "signed_cut_force_xyz_n": negative[:3].tolist(),
                    "signed_cut_moment_xyz_nmm": negative[3:].tolist(), "demands": demands, "references": {"Group1": group1, "Group4": group4},
                    "comparisons": comparisons, "CD": 1, "applicable_as_gross_mean_component_diagnostic": True,
                    "local_plate_or_net_section_strength_ratio": None, "complete_panel_acceptance": False})
    return records


def summarize(result):
    screws, cuts = result["screws"], result["cuts"]
    references_summary = {}
    for kind in ("head", "withdrawal", "contacting_lateral", "combined_withdrawal_lateral"):
        envelope = {}
        for key in screws[0]["references"][kind]:
            finite = [s for s in screws if s["references"][kind][key]["ratio"] is not None]
            peak = max(finite, key=lambda s: s["references"][kind][key]["ratio"]) if finite else None
            envelope[key] = {"finite_states": len(finite), "unsupported_states": 396-len(finite),
                "exceeded_states": sum(s["references"][kind][key]["ratio"] > 1 for s in finite),
                "maximum_ratio": peak["references"][kind][key]["ratio"] if peak else None,
                "witness": {k: peak[k] for k in ("case_id", "axis_id", "panel", "receiver", "tension_n", "lateral_n")} if peak else None}
        references_summary[kind] = envelope
    panel_summary = {}
    for family in ("Group1_saved_scenario", "Group4_existing_family_envelope"):
        panel_summary[family] = {}
        for metric in ("axial", "bending", "transverse_shear"):
            peak = max(cuts, key=lambda c: c["comparisons"][family][metric]["ratio"])
            panel_summary[family][metric] = {"maximum_ratio": peak["comparisons"][family][metric]["ratio"],
                "exceeded_traces": sum(c["comparisons"][family][metric]["ratio"] > 1 for c in cuts),
                "witness": {k: peak[k] for k in ("case_id", "panel", "cut_axis", "station_from_panel_datum_mm", "gross_stressed_width_mm", "demands")}}
    return {"status": "CONDITIONAL_REFERENCE_WORKSHEET_WITH_UNRESOLVED_N14_BASES",
        "counts": {"screw_states": 396, "nominal_cases": 6, "panel_states": 36, "screw_receiver_group_states": len(result["groups"]),
                    "panel_cut_traces": len(cuts), "steel_demand_states": 396, "Hillman_steel_resistance_states": 0},
        "reference_envelopes": references_summary, "panel_gross_mean_envelopes": panel_summary,
        "same_state_head_peak": {k: max(screws, key=lambda s: s["tension_n"])[k] for k in
                             ("case_id", "axis_id", "panel", "receiver", "tension_n", "lateral_n", "positive_opening_mm")},
        "reference_catalog": result["catalog"], "audits": result["audits"], "numpy_version": result["numpy_version"],
        "genuine_missing_bases": {"Hillman_steel_and_profile": "Root/head-neck section, tensile/yield/allowable steel property and bending response",
            "Hillman_wood_screw_conformity": "Applicable B18.6.1 geometry, actual thread reach, head/countersink profile and pilot conformity",
            "plywood": "Delivered grade/group/strength-axis placement and local/net-hole or combined plate strength",
            "load_transfer": "Actual screw/contact stiffness and loaded contact applicability, individual elastic fields and complete receiver/backer continuation"}}


def execute(output, numerical):
    output = Path(output)
    require(not output.is_symlink() and not RAW.is_symlink(), "output/root symlink refused")
    output = output.resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned RAW child required")
    data = sources()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    def write(name, value, jsonl=False):
        with (output / name).open("x") as stream:
            if jsonl:
                for row in value:
                    stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            else:
                stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    report = dict(schema="panel_reference_completion/v1", mode="build" if numerical else "prepare", limits=LIMITS,
                  authority_scope={"reviewed_global_axes": 104, "unadopted_proposal_axes": 108, "Hillman_screws": 66},
                  fresh_source_sha256={"operator_assessment": PINS[ASSESSMENT], "comparison": PINS[COMPARISON], "response": PINS[RESPONSE]},
                  load_envelope={"climber_pounds": 250, "downward_dynamic_factor": 2, "signed_horizontal_magnitude_n": 300,
                                     "hold_lever_mm": 100, "accessory_kg": 25, "modeled_mass_kg": 225.19791414318078,
                                     "dead_load_factor": 1.1110134616260479, "source_gap_scale": 1}, **FLAGS)
    error = None
    try:
        if numerical:
            result = assess(data)
            for name, key in (("screw-states.jsonl", "screws"), ("screw-groups.jsonl", "groups"),
                              ("panel-balances.jsonl", "panels"), ("panel-cuts.jsonl", "cuts")):
                write(name, result[key], jsonl=True)
            report.update(summarize(result))
        else:
            report.update(status="PREPARED_NO_MECHANICS_EVALUATED", identities=data.axes, array_headers=data.headers,
                          planned_screw_states=396, mechanics_evaluated=False, numerical_imports=False,
                          API={"prepare": "prepare(output): stdlib authentication/identity/NPY-header joins",
                                   "build": "build(output): parent-only saved-state arithmetic; no solve"})
        data.api.authenticate(data.pins)
    except Exception as caught:  # noqa: BLE001 -- preserve a STOP receipt, then re-raise.
        error = caught
        report.update(status="STOP", terminal_exception=f"{type(caught).__name__}: {caught}")
    sources_map = {data.api.key(path): digest for path, digest in sorted(data.pins.items())}
    write("sources.json", sources_map)
    write("summary.json", report)
    artifacts = {path.name: sha(path) for path in sorted(output.iterdir())}
    receipt = dict(schema="panel_reference_completion_receipt/v1", status=report["status"],
                   producer_sha256=sha(__file__), source_sha256=sources_map, output_sha256=artifacts,
                   sources_authenticated_before_and_after=error is None, mode=report["mode"], **FLAGS)
    write("receipt.json", receipt)
    if error is not None:
        raise error
    return {"status": report["status"], "output": data.api.key(output), "producer_sha256": sha(__file__),
                "summary_sha256": sha(output / "summary.json"), "receipt_sha256": sha(output / "receipt.json"),
                "source_pin_count": len(data.pins)}


def prepare(output):
    """Standard-library source preparation only; not a resistance result."""
    return execute(output, numerical=False)


def build(output):
    """The parent runs this serialized saved-state arithmetic entry point."""
    return execute(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true", help="stdlib joins only; omit only during parent-owned execution")
    args = parser.parse_args()
    print(json.dumps(prepare(args.output) if args.prepare else build(args.output), indent=2))
