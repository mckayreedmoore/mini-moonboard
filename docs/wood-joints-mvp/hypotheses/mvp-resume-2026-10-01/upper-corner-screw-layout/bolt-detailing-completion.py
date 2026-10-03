"""Prepare N03; only a parent's explicit build(output) evaluates detailing.

Import and prepare(output) are inert with respect to mechanics and geometry.
Saved plane/cylinder/profile recipes are inputs, never CAD instructions. N02
resistance, Cg, common shaft compatibility and release remain separate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import replace
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
HYPOTHESES = BASE.parent
RAW = HERE / "rawlocal/bolt-detailing-completion"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02"
EXPORT = HERE / "rawlocal/knee-bridge-response/attempt02"
KNEE = HERE / "rawlocal/knee-bridge-joint-replay/attempt01"
CORNER = HERE / "rawlocal/knee-bridge-corner-replay/attempt01"
FRESH = BASE / "member-screen-attempt02/knee-bridge-gravity01"
SURFACES = HYPOTHESES / "current-finished-feature-register-2026-10-01/surfaces.json"
CORRECTION = BASE / "top-corner-correction/proposal.json"
SIGNED = ROOT / "mini_moonboard/wood_joint_directional_geometry.py"
FINISHED = HYPOTHESES / "retained-frame-bolt-finished-edges-2026-10-01/method.py"
PRIMARY = HYPOTHESES / "upper-block-strength-2026-10-01/source-cache"
MATERIAL = HYPOTHESES / "hardware-material-specification-2026-09-30/material-inputs.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
TOL_MM = 1e-5
ANGLE_TOL = 1e-7
# The saved frame's own force-law resolution; not a fitted acceptance limit.
ZERO_N = 1e-4
ATTEMPT01 = RAW / "attempt01"
ATTEMPT01_PINS = {
    ATTEMPT01 / "summary.json": "c7825f8e93e882391c11a5ebfa65630326bfb92c8023eef457de26a0b78a5a4f",
    ATTEMPT01 / "receipt.json": "7d7a3314adba1cb1798371a346278e1dcf7db599bffb3ee27017874285f48947",
    ATTEMPT01 / "producer.py.snapshot": "1f3f363b80ca5e0182440a63d767151ecb4e70857f9fb5345fe50ac5be2c0004",
}
PINS = {
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    FRAME / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    GRAVITY / "model-inputs.json": "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    GRAVITY / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    INTEGRATION / "manifest.json": "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    INTEGRATION / "receipt.json": "8a2813419289bee46e2e0985ab702a602a8ff3a0d3aacdd43d1aad841c92c8df",
    EXPORT / "summary.json": "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    EXPORT / "receipt.json": "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    EXPORT / "global-demands.jsonl": "f0d9bb8a8a25775a2571692183860b209708111b089f16538f7eab5d9adbe4c3",
    KNEE / "checks.json": "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891",
    KNEE / "receipt.json": "10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b",
    KNEE / "allocations.jsonl": "5428cf793ba59c0ca1d75dbfedb62036518f29d31cefe63101df9b3d0a5bdb17",
    CORNER / "checks.json": "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976",
    CORNER / "receipt.json": "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    FRESH / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    FRESH / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    SURFACES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    CORRECTION: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    SIGNED: "ce9b67012047732a3bbca496cba78231d7d6b2c28f01dfd57e7ba34aeb1df95d",
    FINISHED: "3aabafb6c1ce25545ae00050dc213ba82a749a9c6ef5a8c0d4819f47c2532aa4",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    PRIMARY / "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    PRIMARY / "source-bounds.json": "91c8c0c33cb7cc35dc31ba332778a80e1c5a972a6134e5e277a473a2adf719c9",
    ROOT / "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    ROOT / "docs/wood-joints-mvp/criteria.json": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
}
FLAGS = dict.fromkeys((
    "proposal_adopted", "formal_criteria_updated", "N03_accepted", "N02_resistance_calculated",
    "Cg_assigned", "historical_acceptance_transferred", "reviewed_geometry_changed",
    "geometry_hardware_load_or_material_laws_changed", "common_shaft_compatibility_qualified",
    "complete_joint_acceptance", "fabrication_release", "physical_release",
    "native_CAD_or_frame_execution", "tests_or_review_run", "original_producer_pipelines_executed",
), False)
REFERENCE_BASIS = {
    "document": "NDS 2024 Chapter 12, pinned specification (not Commentary)",
    "sha256": PINS[PRIMARY / "chapter12-2024-awc-20260911.pdf"],
    "official_url": "https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf",
    "printed_pages": [81, 96, 97, 98, 99],
    "clauses": ["12.1.2.1-.4", "12.1.3.4", "12.3.9.1", "12.5.1.2(a)-(c)", "12.5.1.3"],
    "tables": {
        "12.5.1A": {"softwood_tension_toward_end_min_full_D": [3.5, 7.0],
                     "compression_away_end_min_full_D": [2.0, 4.0],
                     "perpendicular_min_full_D": [2.0, 4.0]},
        "12.5.1B": {"parallel_in_row_min_full_D": [3.0, 4.0],
                     "perpendicular_in_row_min_D": 3.0,
                     "perpendicular_full": "Required spacing for attached members; not universally 4D."},
        "12.5.1C": {"parallel_l_over_D_le_6_D": 1.5,
                     "parallel_l_over_D_gt_6": "max(1.5D, half spacing BETWEEN rows)",
                     "perpendicular_loaded_D": 4.0, "perpendicular_unloaded_D": 1.5},
        "12.5.1D": {"parallel_between_rows_D": 1.5,
                     "perpendicular": "2.5D for l/D<=2; (5l+10D)/8 for 2<l/D<6; 5D for l/D>=6"},
    },
    "bearing_length_basis": "lesser of main-member length and TOTAL side-member length(s)",
    "outermost_cross_grain_limit_mm": 127.0,
    "oblique_grain_interpolation": None,
    "historical_primary_verification": {
        "edition": "2018 Commentary, historical explanation only; not adopted as 2024 wording",
        "official_url": "https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf",
        "printed_pages": [263, 264],
        "C12_5_1_2": "Tension end distances may be linearly interpolated between parallel and perpendicular grain endpoints.",
        "C12_5_1_3": "No specific edge guidance at angles other than 0/90 degrees; no reduced-edge geometry factor.",
        "current_commentary_status": "2024 text not verified; AWC resources/2024-nds offers its Commentary in the purchase package.",
    },
    "angular_method": "Conservative component/full-factor eligibility hypothesis from the pinned 2024 endpoints. No angular interpolation or oblique Cdelta is adopted.",
    "end_hypothesis": "Toward-end nonzero grain component: envelope 3.5D/7D; away-end or pure cross-grain: 2D/4D. Unknown zero sign: display both possible branches and their upper envelope, without applicability pass.",
    "edge_hypothesis": "Maximum of parallel edge bound and signed perpendicular edge requirement. Half-row term bounded by the entire host's projected finite bore-centerline span; no Cg or row partition inferred.",
    "limit": "Endpoint domination is a conservative geometry hypothesis, not a proved oblique failure law or complete connection factor. Loading at an angle to a FASTENER in 12.5.1.2(b) remains a separate equivalent-shear-area case.",
}
LIMITS = [
    "The reviewed 104-axis authority and unadopted 108-axis planning geometry remain distinct. All 47 formal criteria remain pending and all eight release flags remain false.",
    "Distances use modeled nominal bolt diameters and bore envelopes. They are not drill, pilot, purchased-length, thread-root or delivered-hardware instructions.",
    "No-slip floor restraint, gross stiffness, clearance/contact laws, original 100 mm hold lever and conditional DF-L grain/material assumptions remain the saved frame's assumptions.",
    "Finished rays reuse the pinned analytic plane/cylinder kernel. Parent-only closed-form prism/cylinder/taper references address the primitive scope extension; they do not validate every frozen topology or manufactured member.",
    "NDS distances are reference geometry. Convex profiles supply exact affine endpoint bounds, including constant ordinary-prism distances. Nonconvex profiles retain exact trimmed midpoint reference and three diagnostic samples; no universal continuous sampling prerequisite is imposed.",
    "Signed integrated lateral allocations select geometric toward/away directions. They do not classify whole-member tensile stress, infer preload from bolt tension, or assign contact forces to bolts.",
    "Oblique-grain actions supply finite conservative endpoint eligibility comparisons, with no adopted oblique Cdelta or edge factor. Zero directions retain an unresolved sign and no applicability pass. End-grain/oblique bolt axes have geometry envelopes, not ordinary side-grain table qualification.",
    "The four internal bolts have equal inward axial end pairs and no global receiver shear interface. Lateral NDS end/edge factors are not inferred from those axial pairs.",
    "All shared-host pairs are inventoried, including crossed bores. A candidate row requires alignment with the actual load; opposing vectors, serial duties and multi-interface couples do not establish an ordinary group or Cg.",
    "N02 resistance, connection-level Cdelta, reinforcement against perpendicular tension, complete joint mechanics and actual hardware qualification remain separate.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def key(path):
    return Path(path).relative_to(ROOT).as_posix()


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and (path not in pins or pins[path] == digest),
            "conflicting or external source: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "frozen source changed: " + key(path))


def source_map(pins):
    return {key(path): digest for path, digest in sorted(pins.items())}


def receipt_sources(pins, directory, result_name):
    receipt = read(directory / "receipt.json")
    require(receipt["output_sha256"][result_name] == pins[directory / result_name],
            "receipt/result binding differs: " + str(directory))
    for name, digest in receipt.get("source_sha256", {}).items():
        bind(pins, ROOT / name, digest)
    for name, digest in receipt["output_sha256"].items():
        artifact = (directory / name).resolve()
        require(artifact.parent == directory.resolve(), "receipt output leaves packet")
        bind(pins, artifact, digest)


def prepare_sources():
    """Authenticate source/census joins using stdlib; evaluate no force or ray."""
    pins = {**PINS, **ATTEMPT01_PINS, Path(__file__).resolve(): sha(__file__)}
    authenticate(pins)
    old_receipt = read(ATTEMPT01 / "receipt.json")
    require(old_receipt["source_count"] == 215
            and old_receipt["output_sha256"]["summary.json"] == ATTEMPT01_PINS[ATTEMPT01 / "summary.json"]
            and old_receipt["output_sha256"]["producer.py.snapshot"] == ATTEMPT01_PINS[ATTEMPT01 / "producer.py.snapshot"],
            "preserved parent attempt01 binding differs")
    for name, digest in old_receipt["output_sha256"].items():
        artifact = (ATTEMPT01 / name).resolve()
        require(artifact.parent == ATTEMPT01.resolve(), "attempt01 output leaves packet")
        bind(pins, artifact, digest)
    for directory, result in ((INTEGRATION, "manifest.json"), (EXPORT, "summary.json"),
                              (KNEE, "checks.json"), (CORNER, "checks.json")):
        receipt_sources(pins, directory, result)
    data = {"gravity": read(GRAVITY / "operator-assessment.json"),
            "comparison": read(FRAME / "comparison.json"), "inputs": read(GRAVITY / "model-inputs.json"),
            "rows": read(GRAVITY / "row-identities.json"), "integration": read(INTEGRATION / "manifest.json"),
            "export": read(EXPORT / "summary.json"), "knee": read(KNEE / "checks.json"),
            "corner": read(CORNER / "checks.json"), "fresh": read(FRESH / "member-results.json"),
            "members": read(FRESH / "geometry.json")["members"], "correction": read(CORRECTION),
            "surfaces": {r["member_id"]: r for r in read(SURFACES)["records"]},
            "material": read(MATERIAL)}
    for name in ("fresh", "knee", "corner"):
        for relative, digest in data[name]["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for name, digest in data["gravity"]["output_sha256"].items():
        bind(pins, GRAVITY / name, digest)
    for item in data["integration"]["authority"]["files_unchanged"]:
        bind(pins, ROOT / item["source"], item["sha256"])
    effective = data["integration"]["geometry"]["effective_members"]
    for member in effective:
        for field in ("current_step", "effective_proposal_step"):
            binding = member[field]
            bind(pins, ROOT / binding["path"], binding["sha256"])
    for member in data["members"].values():
        bind(pins, ROOT / member["current_finished_step"], member["current_finished_step_sha256"])
    authenticate(pins)
    comparison, gravity = data["comparison"], data["gravity"]
    require(gravity["operator_ready"] is True and gravity["case_ids"] == list(CASES), "gravity cases differ")
    require(comparison["response_sha256"] == PINS[FRAME / "response.npz"]
            and comparison["source_sha256"][key(GRAVITY / "operator-assessment.json")]
            == PINS[GRAVITY / "operator-assessment.json"], "ce69/c3a8/62bd join differs")
    require(data["export"]["source_comparison_sha256"] == PINS[FRAME / "comparison.json"]
            and data["export"]["census"]["global_structural_bolt_states"] == 624,
            "fresh export binding/census differs")
    require(data["fresh"]["output_sha256"]["geometry.json"] == PINS[FRESH / "geometry.json"]
            and data["material"]["conditional_DF_L_No2_base_row"]["base_properties"]["G_for_dowel_bearing"] == 0.5,
            "current geometry/material scenario differs")
    require([s["case_id"] for s in comparison["states"] if s["gap_scale"] == 1.0] == list(CASES),
            "six nominal states differ")
    require(comparison["dead_load_factor"] == gravity["dead_load_factor"] == data["knee"]["dead_load_factor"]
            == data["corner"]["dead_load_factor"] == 1.1110134616260479, "same-state dead factor differs")
    require(data["knee"]["status"] == "FINITE_FRESH_KNEE_STATIC_REPLAY_COMPLETE"
            and data["knee"]["internal_allocation_count"] == 24
            and data["knee"]["source_sha256"][key(FRAME / "comparison.json")] == PINS[FRAME / "comparison.json"],
            "fresh internal allocation differs")
    require(data["corner"]["fresh_load_sources"] == {key(p): PINS[p] for p in
            (GRAVITY / "operator-assessment.json", FRAME / "comparison.json", FRAME / "response.npz")},
            "fresh corner basis differs")
    candidate, criteria = read(ROOT / "wood-joints-candidate.json"), read(ROOT / "docs/wood-joints-mvp/criteria.json")
    criteria_rows = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    require(len(criteria_rows) == 47 and all(r["status"] == "pending" for r in criteria_rows)
            and candidate["release"] is False and len(candidate["release_flags"]) == 8
            and all(v is False for v in candidate["release_flags"].values()), "47/8 authority differs")
    data["release_flags"] = candidate["release_flags"]
    data["axes"] = {a["axis_id"]: a for a in data["integration"]["existing_bolt_axes"]}
    data["internal_axes"] = {a["axis_id"]: a for a in data["integration"]["proposed_internal_bolt_axes"]}
    data["bolts"] = {c["axis_id"]: c for c in data["inputs"]["connections"]
                     if c["kind"] in ("candidate_bolt", "retained_bolt")}
    require(len(data["axes"]) == len(data["bolts"]) == 104 and set(data["axes"]) == set(data["bolts"])
            and len(data["internal_axes"]) == 4 and not set(data["axes"]) & set(data["internal_axes"]),
            "104+4 physical axes differ")
    require(len(effective) == 50 and len(data["members"]) == len(data["surfaces"]) == 44
            and len(data["rows"]) == 1888, "50/44/1888 source census differs")
    for member in effective:
        body = member["body"]
        if body in data["members"]:
            current = data["members"][body]
            require(member["current_step"]["sha256"] == current["current_finished_step_sha256"],
                    "current descriptor/STEP mismatch: " + body)
    data["effective"] = {m["body"]: m for m in effective}
    census = {"effective_STEP_descriptors": 50, "timber_hosts_in_source": 44,
              "global_physical_axes": 104, "internal_physical_axes": 4, "planning_physical_axes": 108,
              "global_bolt_case_states": 624, "internal_bolt_case_states": 24,
              "global_host_incidences": sum(len(a["receivers"]) for a in data["axes"].values()),
              "internal_host_incidences": sum(len(a["receivers"]) for a in data["internal_axes"].values()),
              "global_lateral_interfaces": sum(len(a["interfaces"]) for a in data["axes"].values()),
              "raw_force_rows": 1888, "nominal_cases": 6}
    census["planning_host_case_states"] = (census["global_host_incidences"] + census["internal_host_incidences"]) * 6
    require(census["global_host_incidences"] == 212 and census["internal_host_incidences"] == 4
            and census["global_lateral_interfaces"] == 108 and census["planning_host_case_states"] == 1296,
            "complete all-host/all-plane census differs")
    data["load_basis"] = {
        "fresh_load_sources": {key(p): PINS[p] for p in
            (GRAVITY / "operator-assessment.json", FRAME / "comparison.json", FRAME / "response.npz")},
        "modeled_mass_kg": comparison["modeled_mass_kg"],
        "dead_load_factor": comparison["dead_load_factor"],
        "source_frame_assumptions": data["fresh"]["source_frame_assumptions"],
        "case_ids": list(CASES), "gap_scale": 1.0,
        "direction_basis": "Signed first/second-body saved global rows; fresh corner bore resultants replace only the corresponding local direction. Fresh internal equal end pairs remain separate.",
        "wood_reference": "Conditional DF-L No. 2, G=0.50; delivered grain, grade and service observations absent.",
        "row_direction_zero_resolution_n": ZERO_N,
    }
    authenticate(pins)
    prepared = {"schema": "bolt_detailing_preparation/v1", "status": "PREPARED_NOT_EXECUTED",
                "qualification": "N03", "source_count": len(pins), "source_sha256": source_map(pins),
                "census": census, "case_ids": list(CASES), "reference_basis": REFERENCE_BASIS,
                "load_basis": data["load_basis"],
                "release_flags": data["release_flags"], "formal_pending_criteria_count": 47,
                "limits": LIMITS, "arithmetic_executed": False, **FLAGS}
    return pins, prepared, data


def write_packet(output, records):
    output = Path(output).absolute()
    require(output.parent == RAW and output.resolve() == output and not output.exists(),
            "fresh immediate owned RAW child required")
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in records.items():
        require(Path(name).name == name, "artifact name leaves owned output")
        with (output / name).open("x", encoding="utf-8") as stream:
            stream.write(payload if isinstance(payload, str) else json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return output


def prepare(output):
    """Parent or worker may freeze the read-only preparation; no arrays/math."""
    pins, prepared, _ = prepare_sources()
    output = write_packet(output, {".gitignore": "*\n", "preparation.json": prepared})
    authenticate(pins)
    receipt = {"status": prepared["status"], "source_sha256": source_map(pins),
               "output_sha256": {"preparation.json": sha(output / "preparation.json")},
               "sources_authenticated_before_and_after": True, "arithmetic_executed": False, **FLAGS}
    with (output / "receipt.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    authenticate(pins)
    return {"output": str(output), "source_count": len(pins), "census": prepared["census"],
            "preparation_sha256": sha(output / "preparation.json"), "receipt_sha256": sha(output / "receipt.json"), **FLAGS}


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scaled(a, scale):
    return [x * scale for x in a]


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def unit(a):
    length = math.hypot(*a)
    require(len(a) == 3 and math.isfinite(length) and length > 0, "invalid finite direction")
    return scaled(a, 1 / length)


@contextmanager
def helpers():
    """Import only two inert stdlib kernels; restore interpreter settings."""
    bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    loaded = []
    try:
        for path, name in ((SIGNED, "bolt_detailing_signed"), (FINISHED, "bolt_detailing_finished")):
            require(sha(path) == PINS[path], "supplied-input helper changed")
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            previous = sys.modules.get(name)
            sys.modules[name] = module
            loaded.append((name, previous, module))
            spec.loader.exec_module(module)
        yield loaded[0][2], loaded[1][2]
    finally:
        for name, previous, _ in loaded:
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
        sys.dont_write_bytecode = bytecode


def plane_line_interval(planes, point, axis):
    """Intersect a line with supplied convex outer planes, not stock AABBs."""
    low, high = -math.inf, math.inf
    for plane in planes:
        rate = dot(plane.normal, axis)
        rhs = plane.station - dot(plane.normal, point)
        if abs(rate) < ANGLE_TOL:
            require(rhs >= -TOL_MM, "bore line is outside finished outer planes")
        elif rate > 0:
            high = min(high, rhs / rate)
        else:
            low = max(low, rhs / rate)
    require(math.isfinite(low) and math.isfinite(high) and high - low > TOL_MM,
            "no finite bore interval in supplied finished profile")
    return low, high


def rectangle_planes(body, member, api):
    """Six faces of the frozen corrected rectangular blank, excluding holes."""
    geom = member["geometry"]
    axes = [unit(geom[k]) for k in ("axis", "section_u", "section_v")]
    length = dot(sub(geom["end"], geom["start"]), axes[0])
    bounds = [(0.0, length), (-geom["width_mm"] / 2, geom["width_mm"] / 2),
              (-geom["depth_mm"] / 2, geom["depth_mm"] / 2)]
    planes = []
    for i, (lo, hi) in enumerate(bounds):
        other = [j for j in range(3) if j != i]
        for sign, coordinate in ((-1, lo), (1, hi)):
            normal = scaled(axes[i], sign)
            p = add(geom["start"], scaled(axes[i], coordinate))
            u, v = api._plane_basis(tuple(normal))
            vertices = []
            for a, b in ((0, 0), (1, 0), (1, 1), (0, 1)):
                q = add(add(p, scaled(axes[other[0]], bounds[other[0]][a])),
                        scaled(axes[other[1]], bounds[other[1]][b]))
                vertices.append((dot(q, u), dot(q, v)))
            loop = api._Loop(1, "POLYGON", points=tuple(vertices))
            planes.append(api._Plane(f"{body}/frozen_blank_{i}_{sign}", tuple(normal),
                                     dot(normal, p), u, v, (loop,), True, ()))
    return planes


def supplied_member_recipe(body, member, surface, correction, internal_axes, api):
    """Compile frozen descriptors; never read STEP topology or call CAD."""
    original_target = body in api.TARGET_MEMBERS
    try:
        planes = [api._compile_plane(f) for f in surface["features"] if f["surface_kind"] == "PLANE"]
        cylinders = [api._compile_cylinder(f) for f in surface["features"] if f["surface_kind"] == "CYLINDER"]
        changed = member["current_finished_step_sha256"] != surface["step_binding"]["file_sha256"]
        proposed = next((p for p in correction["proposals"] if p["block"] == body), None)
        side_proposal = next((p for p in correction["proposals"]
                              if "base_side_" + p["block"].split("_")[-2] == body), None)
        added = []
        if changed:
            require(proposed is not None or side_proposal is not None, "finished STEP change has no frozen recipe")
            if proposed:
                planes = rectangle_planes(body, member, api)
                cylinders = []
            else:
                removed = {c.feature_id for c in cylinders if c.feature_id in member["replaced_original_bore_features"]}
                old_cylinders = [c for c in cylinders if c.feature_id in removed]
                # Remove the old bore's inner planar trim loops as well as its wall.
                replaced_planes = []
                for plane in planes:
                    remove_wires = {wi for wi, center, axis, radius in plane.circle_loops
                                    if any(api._circle_matches_endpoint(center, axis, radius, c)[0]
                                           for c in old_cylinders)}
                    replaced_planes.append(replace(plane,
                        loops=tuple(loop for loop in plane.loops if loop.wire_index not in remove_wires),
                        circle_loops=tuple(row for row in plane.circle_loops if row[0] not in remove_wires)))
                planes = replaced_planes
                cylinders = [c for c in cylinders if c.feature_id not in removed]
            # Bore-free polygon faces define these two convex correction shapes.
            outer = [p for p in planes if p.outer_is_polygon]
            proposal = proposed or side_proposal
            for axis in proposal["axes"]:
                if side_proposal and "/rail_" in axis["axis_id"]:
                    continue
                axis_id = axis["axis_id"]
                interval = next((b for b in member["bore_or_passage_intervals"]
                                 if b["id"] == axis_id + "/corrected_bore"), None)
                # Existing side bores in the corrected blank are included even
                # when the elementary grain-section register excludes end grain.
                require(interval is not None or "/side_" in axis_id, "corrected bore recipe is absent")
                # The canonical direction is supplied separately by build below.
                added.append({"axis_id": axis_id, "point": axis["proposed_axis_point_mm"],
                              "radius": axis["proposed_CAD_bore_envelope_mm"] / 2,
                              "outer": outer})
        for axis in internal_axes:
            if axis["body"] == body:
                cylinders.append(api._Cylinder(axis["axis_id"], tuple(axis["axis_origin_global_xyz_mm"]),
                    tuple(unit(axis["axis_unit_global_xyz"])), axis["bore_envelope_diameter_mm"] / 2,
                    *axis["axis_parameter_interval_mm"], -1.0, "bore_like"))
        return {"status": "COMPILED_FROZEN_RECIPE", "body": body, "planes": planes,
                "cylinders": cylinders, "added": added, "original_helper_target": original_target,
                "modified_recipe": changed or any(a["body"] == body for a in internal_axes)}
    except (ValueError, KeyError, StopIteration) as error:
        return {"status": "METHOD_LIMIT", "body": body, "reason": str(error),
                "original_helper_target": original_target}


def finish_recipe(recipe, axes, api):
    if recipe["status"] != "COMPILED_FROZEN_RECIPE":
        return recipe
    try:
        for bore in recipe["added"]:
            axis = unit(axes[bore["axis_id"]]["axis_xyz"])
            low, high = plane_line_interval(bore["outer"], bore["point"], axis)
            recipe["cylinders"].append(api._Cylinder(bore["axis_id"] + "/corrected_bore",
                tuple(bore["point"]), tuple(axis), bore["radius"], low, high, -1.0, "bore_like"))
        recipe["member"] = api._Member(recipe["body"], tuple(recipe["planes"]), tuple(recipe["cylinders"]),
            frozenset(p.feature_id for p in recipe["planes"]) | frozenset(c.feature_id for c in recipe["cylinders"]))
        exterior_recipe(recipe, api)
    except ValueError as error:
        recipe.update(status="METHOD_LIMIT", reason=str(error))
    return recipe


def exterior_recipe(recipe, api):
    """Separate finished profile from circular bore trims and blind bore caps.

    Fill only circular loops matched to authenticated bore endpoints. Polygon
    cuts, tapers and recesses stay intact. Other curved boundaries are refused.
    """
    planes, filled, excluded = [], [], []
    reason = None
    for plane in recipe["planes"]:
        if not plane.outer_is_polygon:
            if (len(plane.loops) == 1 and plane.loops[0].kind == "CIRCLE"
                    and any(api._circle_matches_endpoint(center, axis, radius, c)[0]
                            for _, center, axis, radius in plane.circle_loops for c in recipe["cylinders"]
                            if c.material_side == "bore_like")):
                excluded.append(plane.feature_id)
                continue
            reason = "nonpolygon exterior/cap recipe is unclassified"
            continue
        matched = {wi for wi, center, axis, radius in plane.circle_loops
                   if any(c.material_side == "bore_like"
                          and api._circle_matches_endpoint(center, axis, radius, c)[0]
                          for c in recipe["cylinders"])}
        if any(loop.kind == "CIRCLE" and loop.wire_index not in matched for loop in plane.loops):
            reason = "a circular trim has no bore-endpoint binding; exterior filling refused"
        filled.extend((plane.feature_id, wi) for wi in sorted(matched))
        planes.append(replace(plane,
            loops=tuple(loop for loop in plane.loops if loop.wire_index not in matched),
            circle_loops=tuple(row for row in plane.circle_loops if row[0] not in matched)))
    if any(c.material_side != "bore_like" for c in recipe["cylinders"]):
        reason = "curved non-bore exterior is outside the supplied plane-profile method"
    recipe["exterior_member"] = api._Member(recipe["body"], tuple(planes), (),
                                            frozenset(p.feature_id for p in planes))
    recipe["exterior_recipe_limit"] = reason
    recipe["filled_bore_trim_loops"] = filled
    recipe["excluded_circular_caps"] = excluded
    # Convexity is proved against actual polygon vertices, not a stock box.
    vertices = [add(add(scaled(p.basis_u, x), scaled(p.basis_v, y)), scaled(p.normal, p.station))
                for p in planes for loop in p.loops if loop.kind == "POLYGON" for x, y in loop.points]
    recipe["convex_finished_profile"] = bool(planes and vertices) and reason is None and all(
        len(p.loops) == 1 and p.loops[0].kind == "POLYGON" for p in planes) and all(
        dot(p.normal, vertex) <= p.station + TOL_MM for p in planes for vertex in vertices)


def match_bore(recipe, point, axis, radius=None):
    if recipe["status"] != "COMPILED_FROZEN_RECIPE":
        return None
    matches = []
    for bore in recipe["cylinders"]:
        delta = sub(point, bore.origin)
        off = math.hypot(*sub(delta, scaled(bore.axis, dot(delta, bore.axis))))
        if abs(dot(axis, bore.axis)) >= 1 - ANGLE_TOL and off <= TOL_MM and (
                radius is None or abs(radius - bore.radius) <= TOL_MM):
            matches.append(bore)
    return matches[0] if len(matches) == 1 else None


def finished_ray(recipe, bore, origin, direction, api):
    """Reuse original trimmed ray/crossing helpers on one supplied recipe."""
    if math.hypot(*direction) <= ANGLE_TOL:
        return {"status": "ZERO_DIRECTION_METHOD_LIMIT", "distance_mm": None}
    direction = unit(direction)
    own_wires = frozenset((p.feature_id, wi) for p in recipe["planes"]
        for wi, center, axis, radius in p.circle_loops
        if api._circle_matches_endpoint(center, axis, radius, bore)[0])
    member = recipe["member"]
    raw, ambiguities = api._raw_hits(member, tuple(origin), tuple(direction), bore.feature_id,
                                    own_wires, fill_own_hole=False)
    events = api._group_hits(raw)
    membership = api._origin_membership(member, tuple(origin), tuple(direction), bore.feature_id, own_wires)
    _, path_reason = api._trace_state(events, initially_inside=True)
    material_reason = (ambiguities[0] if ambiguities else path_reason)
    if membership["status"] != "inside_filled_own_bore":
        material_reason = membership["reason"]
    profile = recipe["exterior_member"]
    outer_hits, outer_ambiguities = api._raw_hits(profile, tuple(origin), tuple(direction),
                                                bore.feature_id, frozenset(), fill_own_hole=False)
    outer_events = api._group_hits(outer_hits)
    outer_membership = api._origin_membership(profile, tuple(origin), tuple(direction),
                                              bore.feature_id, frozenset())
    _, outer_path_reason = api._trace_state(outer_events, initially_inside=True)
    exterior = next((e for e in outer_events if e["entry_or_exit"] == "exit"
                     and e["exterior_classification"] == "polygon_outerwire_plane"), None)
    reason = recipe["exterior_recipe_limit"] or (outer_ambiguities[0] if outer_ambiguities else outer_path_reason)
    if outer_membership["status"] != "inside_filled_own_bore":
        reason = reason or outer_membership["reason"]
    if exterior is None:
        reason = reason or "no supported finished-profile exterior crossing"
    material = next((e for e in events if e["entry_or_exit"] == "exit"), None)
    first_bore = next((e for e in events if e["exterior_classification"] == "bore_wall"), None)
    result = {"status": "METHOD_LIMIT" if reason else "FINITE_FINISHED_EXTERIOR_DISTANCE",
              "reason": reason, "origin_xyz_mm": origin, "ray_unit_xyz": direction,
              "distance_mm": None if reason else exterior["distance_mm"],
              "first_material_exit": material, "first_other_bore_event": first_bore,
              "first_exterior_exit": exterior, "events": events,
              "material_trace_limit": material_reason, "exterior_events": outer_events,
              "bore_trims_filled_only_for_exterior_reference": recipe["filled_bore_trim_loops"],
              "through_depth_minimum_established": False}
    if exterior:
        planes = [p for p in profile.planes if p.feature_id in exterior["feature_ids"]]
        result["exterior_normals_xyz"] = [list(p.normal) for p in planes]
        result["normal_distance_mm"] = (abs(planes[0].station - dot(planes[0].normal, origin))
                                         if len(planes) == 1 else None)
    return result


def reference_geometry(recipe, bore, ray, midpoint_ray):
    """Exact NDS reference geometry, with affine bounds for convex profiles.

    For a fixed ray, distance to an outward plane is affine in bore station.
    The first convex-profile exit is their minimum; its minimum over the finite
    bearing interval occurs at an endpoint. Constant prism references need no
    sampled approximation. A nonconvex profile keeps its exact trimmed midpoint.
    """
    result = dict(midpoint_ray)
    result["reference_basis"] = "EXACT_TRIMMED_MID_BEARING_REFERENCE"
    result["continuous_minimum_required_by_table"] = False
    if math.hypot(*ray) <= ANGLE_TOL or not recipe["convex_finished_profile"]:
        return result
    ray = unit(ray)
    candidates = []
    for plane in recipe["exterior_member"].planes:
        rate = dot(plane.normal, ray)
        if rate <= ANGLE_TOL:
            continue
        slope = -dot(plane.normal, bore.axis) / rate
        values = [(plane.station - dot(plane.normal, add(bore.origin, scaled(bore.axis, s)))) / rate
                  for s in (bore.low, (bore.low + bore.high) / 2, bore.high)]
        candidates.append((plane, slope, values))
    if not candidates or any(min(row[2]) < -TOL_MM for row in candidates):
        result["affine_reference_limit"] = "bearing endpoints are not inside the certified convex finished profile"
        return result
    endpoint_min = min(min(values[0], values[2]) for _, _, values in candidates)
    exact_mid = min(values[1] for _, _, values in candidates)
    terminal = [plane for plane, _, values in candidates if min(values[0], values[2]) <= endpoint_min + TOL_MM]
    constant = all(abs(slope) * (bore.high - bore.low) <= TOL_MM for _, slope, _ in candidates)
    result.update(status="FINITE_FINISHED_EXTERIOR_DISTANCE", reason=None,
        distance_mm=max(0.0, endpoint_min), midpoint_distance_mm=max(0.0, exact_mid),
        reference_basis="EXACT_CONSTANT_PRISM_REFERENCE" if constant else "EXACT_CONVEX_PROFILE_AFFINE_ENDPOINT_BOUND",
        through_depth_minimum_established=True, convexity_certified_from_finished_polygon_vertices=True,
        exterior_normals_xyz=[list(p.normal) for p in terminal],
        affine_plane_witnesses=[{"feature_id": p.feature_id, "distance_slope_per_mm": slope,
            "low_mid_high_distances_mm": values} for p, slope, values in candidates])
    return result


def distance_comparison(ray, diameter, minimum_D, full_D=None, square_grain=None):
    distance = ray.get("distance_mm")
    reason = ray.get("reason")
    if square_grain is not None:
        normals = ray.get("exterior_normals_xyz", [])
        if not normals or any(abs(dot(n, square_grain)) < 1 - ANGLE_TOL for n in normals):
            reason = "terminal plane is not a classified square-cut grain end"
    valid = distance is not None and reason is None
    if not valid and reason is None:
        reason = ray.get("status", "no finite classified exterior distance")
    return {"measured_mm": distance, "minimum_mm": minimum_D * diameter,
            "full_value_mm": full_D * diameter if full_D is not None else None,
            "minimum_margin_mm": distance - minimum_D * diameter if valid else None,
            "full_value_margin_mm": distance - full_D * diameter if valid and full_D is not None else None,
            "conditional_ratio_to_full": distance / (full_D * diameter) if valid and full_D is not None else None,
            "conditional_Cdelta": min(1.0, distance / (full_D * diameter))
                if valid and full_D is not None and distance >= minimum_D * diameter else None,
            "status": "FINITE_CONDITIONAL_COMPARISON" if valid else "METHOD_LIMIT",
            "reason": reason, "resistance_pass": None}


def supplied_direction(force, bolt_axis, member, center, signed_api):
    """Reuse the signed source classifier, never adopt its box distances."""
    geom = member["geometry"]
    grain = unit(geom["axis"])
    magnitude = math.hypot(*force)
    axial = dot(force, bolt_axis)
    lateral = sub(force, scaled(bolt_axis, axial))
    value = math.hypot(*lateral)
    parallel = dot(lateral, grain)
    cross = sub(lateral, scaled(grain, parallel))
    result = {"force_xyz_n": force, "lateral_xyz_n": lateral, "lateral_n": value,
              "axial_projection_n": axial, "signed_grain_n": parallel,
              "load_to_grain_degrees": None, "classification": "ZERO_DIRECTION_METHOD_LIMIT",
              "source_signed_classification": None, "source_classifier_limit": None}
    if magnitude <= ZERO_N or value <= ZERO_N:
        return result
    angle = math.degrees(math.atan2(math.hypot(*cross), abs(parallel)))
    result["load_to_grain_degrees"] = angle
    result["classification"] = ("PARALLEL_TO_GRAIN" if angle <= ANGLE_TOL else
                                 "PERPENDICULAR_TO_GRAIN" if abs(angle - 90) <= ANGLE_TOL else
                                 "OBLIQUE_TO_GRAIN")
    axes = [grain, unit(geom["section_u"]), unit(geom["section_v"])]
    bounds = [[0.0, dot(sub(geom["end"], geom["start"]), grain)],
              [-geom["width_mm"] / 2, geom["width_mm"] / 2],
              [-geom["depth_mm"] / 2, geom["depth_mm"] / 2]]
    try:
        raw = signed_api.classify_member_fastener_load(force_on_member_global_n=force,
            grain_axis_global_unit=grain, bolt_axis_global_unit=bolt_axis,
            bolt_center_global_mm=center, member_frame_origin_global_mm=geom["start"],
            member_axes_global_unit=axes, member_bounds_local_mm=bounds)
        result["source_signed_classification"] = {
            k: raw[k] for k in ("force_parallel_to_grain_signed_n", "grain_end_direction", "cross_grain_edge_direction")}
        result["source_box_distances_adopted"] = False
    except ValueError as error:
        result["source_classifier_limit"] = str(error)
    return result


def comparison_applicability(comparison, direction, ordinary, hypothesis, unresolved):
    """Keep finite geometric eligibility separate from a selected table factor."""
    pure = direction["classification"]
    comparison.update(direction_status=pure, ordinary_side_grain_axis=ordinary,
        source_classifier_limit=direction["source_classifier_limit"],
        conservative_hypothesis=hypothesis, applicability_pass=None, physical_failure=None)
    if comparison["status"] == "METHOD_LIMIT":
        comparison["conditional_Cdelta"] = None
        return comparison
    if pure == "ZERO_DIRECTION_METHOD_LIMIT":
        comparison.update(status="FINITE_UNORIENTED_GEOMETRY_ENVELOPE", conditional_Cdelta=None,
            applicability_limit="zero same-state lateral direction; neither end/edge sign is selected")
    elif not ordinary or direction["source_classifier_limit"]:
        comparison.update(status="FINITE_NONORDINARY_AXIS_GEOMETRY_HYPOTHESIS", conditional_Cdelta=None,
            applicability_limit="end-grain or oblique/frame-unaligned bolt geometry needs its own applicability basis")
    elif hypothesis:
        comparison.update(status="FINITE_CONSERVATIVE_HYPOTHESIS_COMPARISON", conditional_Cdelta=None,
            applicability_limit="oblique component envelope is a conservative hypothesis; no adopted angular edge/end factor")
    elif unresolved:
        comparison.update(status="FINITE_TABULATED_BASE_COMPARISON", conditional_Cdelta=None,
                          applicability_limit=unresolved)
    else:
        comparison["applicability_limit"] = None
    return comparison


def host_row_span_bound(host_bores, edge_axis):
    """Bound every possible between-row projection by finite host centerlines.

    This deliberately includes crossed and unrelated axes. It bounds geometry
    without classifying them as a group, assigning Cg or choosing load shares.
    """
    if not host_bores or any(b is None for _, b in host_bores) or math.hypot(*edge_axis) <= ANGLE_TOL:
        return None
    coordinates = [dot(add(b.origin, scaled(b.axis, s)), edge_axis)
                   for _, b in host_bores for s in (b.low, b.high)]
    return max(coordinates) - min(coordinates)


def host_details(member, recipe, bore, force, axis, diameter, l_mm, signed_api, api, host_bores=()):
    """Finite signed NDS references and explicitly hypothetical eligibility."""
    if bore is None:
        return {"status": "METHOD_LIMIT", "reason": recipe.get("reason", "no unique current bore/axis match"),
                "force_xyz_n": force, "modeled_diameter_mm": diameter, "Cdelta": None}
    center = add(bore.origin, scaled(bore.axis, (bore.low + bore.high) / 2))
    grain = unit(member["geometry"]["axis"])
    direction = supplied_direction(force, axis, member, center, signed_api)
    ordinary = abs(dot(axis, grain)) <= ANGLE_TOL
    edge_axis = sub(direction["lateral_xyz_n"], scaled(grain, direction["signed_grain_n"]))
    if math.hypot(*edge_axis) > ZERO_N:
        edge_axis = unit(edge_axis)
    elif math.hypot(*api._cross(tuple(grain), tuple(axis))) > ANGLE_TOL:
        edge_axis = unit(api._cross(tuple(grain), tuple(axis)))
    else:
        edge_axis = unit(member["geometry"]["section_u"])
    rays = {"grain_plus": grain, "grain_minus": scaled(grain, -1),
            "cross_plus": edge_axis, "cross_minus": scaled(edge_axis, -1)}
    rays["actual_lateral_ray"] = (unit(direction["lateral_xyz_n"])
                                  if direction["lateral_n"] > ZERO_N else [0.0, 0.0, 0.0])
    if abs(dot(axis, grain)) >= 1 - ANGLE_TOL:
        second_edge = unit(member["geometry"]["section_v"])
        rays.update(cross_second_plus=second_edge, cross_second_minus=scaled(second_edge, -1))
    midpoint = {name: finished_ray(recipe, bore, center, ray, api) for name, ray in rays.items()}
    reference = {name: reference_geometry(recipe, bore, ray, midpoint[name]) for name, ray in rays.items()}
    pure = direction["classification"]
    unknown = pure == "ZERO_DIRECTION_METHOD_LIMIT"
    oblique = pure == "OBLIQUE_TO_GRAIN"

    def comparisons(queried):
        end_comparisons, edge_comparisons = {}, {}
        for name in ("grain_minus", "grain_plus"):
            component = dot(rays[name], direction["lateral_xyz_n"])
            # Unresolved tiny grain sign receives both possible endpoint tiers.
            sign_unknown = unknown or (oblique and abs(component) <= ZERO_N)
            toward = component > ZERO_N
            minimum, full = (3.5, 7.0) if sign_unknown or toward else (2.0, 4.0)
            if pure == "PERPENDICULAR_TO_GRAIN":
                minimum, full = 2.0, 4.0
            comparison = distance_comparison(queried[name], diameter, minimum, full, grain)
            comparison.update(bearing_relation=None if sign_unknown else
                "toward_end" if toward else "away_from_end" if abs(component) > ZERO_N else "cross_grain",
                Table_12_5_1A_applicability=pure, reference_basis=queried[name].get("reference_basis"),
                endpoint_comparisons={
                    "parallel_toward_softwood": distance_comparison(queried[name], diameter, 3.5, 7.0, grain),
                    "parallel_away_or_perpendicular": distance_comparison(queried[name], diameter, 2.0, 4.0, grain)},
                signed_grain_component_n=component)
            # Nested endpoint ratios are sensitivities, never a chosen factor.
            for endpoint in comparison["endpoint_comparisons"].values():
                endpoint["conditional_Cdelta"] = None
                endpoint["selected_applicability"] = False
            end_comparisons[name] = comparison_applicability(comparison, direction, ordinary,
                oblique or sign_unknown, "component sign is below resolution" if sign_unknown else None)
        for name in (n for n in rays if n.startswith("cross_")):
            loaded_component = dot(rays[name], direction["lateral_xyz_n"])
            loaded_unknown = unknown or (oblique and abs(loaded_component) <= ZERO_N)
            loaded = loaded_component > ZERO_N
            span = host_row_span_bound(host_bores, rays[name])
            needs_half_row = l_mm is None or l_mm / diameter > 6 + ANGLE_TOL
            base = 1.5 * diameter
            parallel_bound = max(base, span / 2) if needs_half_row and span is not None else base
            perpendicular = (4.0 if loaded or loaded_unknown else 1.5) * diameter
            threshold = parallel_bound if pure == "PARALLEL_TO_GRAIN" else perpendicular
            if oblique or unknown or not ordinary:
                threshold = max(parallel_bound, perpendicular)
            comparison = distance_comparison(queried[name], diameter, threshold / diameter)
            comparison.update(loaded_edge=None if loaded_unknown else loaded,
                signed_cross_grain_component_n=loaded_component, Table_12_5_1C_applicability=pure,
                l_over_D=l_mm / diameter if l_mm is not None else None,
                reference_basis=queried[name].get("reference_basis"),
                parallel_base_mm=base, parallel_edge_upper_bound_mm=parallel_bound,
                finite_host_row_span_upper_bound_mm=span,
                complete_row_partition_established=False,
                half_row_bound_basis="half the entire finite host-axis projection span, including crossed duties",
                perpendicular_loaded_requirement_mm=4.0 * diameter,
                perpendicular_unloaded_requirement_mm=base)
            unresolved = "half BETWEEN-row term is unbounded; base comparator only" if needs_half_row and span is None else None
            hypothesis = oblique or (needs_half_row and span is not None and parallel_bound > base + TOL_MM)
            edge_comparisons[name] = comparison_applicability(comparison, direction, ordinary, hypothesis, unresolved)
        return end_comparisons, edge_comparisons

    reference_ends, reference_edges = comparisons(reference)
    fractions = (0.01, 0.5, 0.99)
    stations = []
    for fraction in fractions:
        origin = add(bore.origin, scaled(bore.axis, bore.low + fraction * (bore.high - bore.low)))
        queried = {name: finished_ray(recipe, bore, origin, ray, api) for name, ray in rays.items()}
        end_comparisons, edge_comparisons = comparisons(queried)
        stations.append({"bearing_fraction": fraction, "origin_xyz_mm": origin, "rays": queried,
                         "end_comparisons": end_comparisons, "edge_comparisons": edge_comparisons})
    return {"status": "FINITE_REFERENCE_DETAILING_WITH_EXPLICIT_APPLICABILITY", "direction": direction,
            "bore_feature_id": bore.feature_id, "bore_radius_mm": bore.radius,
            "bearing_length_mm": bore.high - bore.low, "modeled_diameter_mm": diameter,
            "NDS_l_mm": l_mm, "mid_bearing_xyz_mm": center, "stations": stations,
            "reference_rays": reference, "reference_end_comparisons": reference_ends,
            "reference_edge_comparisons": reference_edges,
            "original_helper_target": recipe["original_helper_target"],
            "modified_frozen_recipe": recipe["modified_recipe"],
            "through_depth_minimum_established": all(reference[n].get("through_depth_minimum_established", False)
                for n in rays if n != "actual_lateral_ray"),
            "continuous_minimum_required_by_table": False,
            "member_tension_stress_classification": None, "Cdelta": None, "N03_accepted": False}


def analytical_geometry_known_answer(api):
    """Parent-only tiny geometry reference; no model loads or software runner.

    One 100 x 40 x 20 prism, two cylindrical bores, and one tapered variant
    exercise profile filling, ordinary constant distances and an affine bound.
    Closed-form answers are supplied independently of the queried kernel.
    """
    body = "N03_analytical_reference"
    member = {"geometry": {"axis": [1.0, 0.0, 0.0], "section_u": [0.0, 1.0, 0.0],
        "section_v": [0.0, 0.0, 1.0], "start": [0.0, 0.0, 0.0], "end": [100.0, 0.0, 0.0],
        "width_mm": 40.0, "depth_mm": 20.0}}
    own = api._Cylinder(body + "/own", (30.0, 0.0, 0.0), (0.0, 0.0, 1.0), 2.0,
                        -10.0, 10.0, -1.0, "bore_like")
    other = api._Cylinder(body + "/other", (45.0, 0.0, 0.0), (0.0, 0.0, 1.0), 3.0,
                          -10.0, 10.0, -1.0, "bore_like")
    planes = rectangle_planes(body, member, api)
    trimmed = []
    for plane in planes:
        loops, circles = list(plane.loops), []
        if abs(plane.normal[2]) > 1 - ANGLE_TOL:
            for index, bore in enumerate((own, other), 2):
                endpoint = add(bore.origin, scaled(bore.axis, -10.0 if plane.normal[2] < 0 else 10.0))
                loops.append(api._Loop(index, "CIRCLE", center=(dot(endpoint, plane.basis_u),
                    dot(endpoint, plane.basis_v)), radius=bore.radius))
                circles.append((index, tuple(endpoint), bore.axis, bore.radius))
        trimmed.append(replace(plane, loops=tuple(loops), circle_loops=tuple(circles)))

    def recipe_for(planes, bores):
        recipe = {"status": "COMPILED_FROZEN_RECIPE", "body": body, "planes": planes,
            "cylinders": bores, "added": [], "original_helper_target": False, "modified_recipe": False}
        return finish_recipe(recipe, {}, api)

    prism = recipe_for(trimmed, [own, other])
    # The taper is y = 20 - x/10, while the opposite edge remains y = -20.
    faces = [
        ((-1, 0, 0), [(0, -20, -10), (0, 20, -10), (0, 20, 10), (0, -20, 10)]),
        ((1, 0, 0), [(100, -20, -10), (100, 10, -10), (100, 10, 10), (100, -20, 10)]),
        ((0, -1, 0), [(0, -20, -10), (100, -20, -10), (100, -20, 10), (0, -20, 10)]),
        ((0.1, 1, 0), [(0, 20, -10), (100, 10, -10), (100, 10, 10), (0, 20, 10)]),
        ((0, 0, -1), [(0, -20, -10), (100, -20, -10), (100, 10, -10), (0, 20, -10)]),
        ((0, 0, 1), [(0, -20, 10), (100, -20, 10), (100, 10, 10), (0, 20, 10)]),
    ]
    tapered_planes = []
    for index, (normal, vertices) in enumerate(faces):
        normal = tuple(unit(normal))
        u, v = api._plane_basis(normal)
        loop = api._Loop(1, "POLYGON", points=tuple((dot(p, u), dot(p, v)) for p in vertices))
        tapered_planes.append(api._Plane(f"{body}/taper_{index}", normal, dot(normal, vertices[0]),
                                         u, v, (loop,), True, ()))
    taper = recipe_for(tapered_planes, [own, other])
    oblique_bore = api._Cylinder(body + "/oblique", (30.0, 0.0, 0.0), (0.6, 0.0, 0.8), 2.0,
                                  -12.5, 12.5, -1.0, "bore_like")
    oblique_taper = recipe_for(tapered_planes, [oblique_bore, other])
    descriptions = [
        ("prism_grain_plus_with_other_bore", prism, own, [1, 0, 0], 70.0, 12.0),
        ("prism_grain_minus", prism, own, [-1, 0, 0], 30.0, None),
        ("prism_cross_plus_constant_through_bearing", prism, own, [0, 1, 0], 20.0, None),
        ("taper_cross_plus_actual_exterior", taper, own, [0, 1, 0], 17.0, None),
        ("taper_45_degree_ray", taper, own, [1, 1, 0], 17.0 * math.sqrt(2.0) / 1.1, None),
        ("taper_oblique_bore_affine_endpoint_bound", oblique_taper, oblique_bore, [0, 1, 0], 16.25, None),
    ]
    rows = []
    for name, recipe, bore, ray, expected, expected_bore in descriptions:
        measured = finished_ray(recipe, bore, list(bore.origin), ray, api)
        reference = reference_geometry(recipe, bore, ray, measured)
        value = reference.get("distance_mm")
        first_other = measured.get("first_other_bore_event")
        other_value = first_other["distance_mm"] if first_other else None
        rows.append({"reference_id": name, "expected_exterior_reference_mm": expected,
            "observed_exterior_reference_mm": value, "residual_mm": value - expected if value is not None else None,
            "expected_first_other_bore_mm": expected_bore, "observed_first_other_bore_mm": other_value,
            "other_bore_residual_mm": other_value - expected_bore if other_value is not None and expected_bore is not None else None,
            "ray": measured, "reference": reference})
    agrees = all(r["residual_mm"] is not None and abs(r["residual_mm"]) <= TOL_MM
        and (r["expected_first_other_bore_mm"] is None or r["other_bore_residual_mm"] is not None
             and abs(r["other_bore_residual_mm"]) <= TOL_MM) for r in rows)
    return {"schema": "N03_analytical_geometry_reference/v1", "reference_rows": rows,
        "reference_agrees_with_closed_form": agrees, "tolerance_mm": TOL_MM,
        "domains": ["closed polygon prism", "matched circular endpoint trims", "finite bore cylinders",
                    "actual planar taper", "oblique ray", "convex affine bearing endpoint bound"],
        "limit": "Primitive geometry reference only. No complete frozen-topology, traction, connection, group or resistance qualification.",
        "model_loads_evaluated": False, **FLAGS}


def pair_spacing(first, second, grain):
    """Inventory one shared-host pair; never create a group resistance."""
    delta = sub(second["center_xyz_mm"], first["center_xyz_mm"])
    pitch = math.hypot(*delta)
    along = dot(delta, grain)
    across = math.hypot(*sub(delta, scaled(grain, along)))
    a, b = first["axis_unit_xyz"], second["axis_unit_xyz"]
    parallel_axes = abs(dot(a, b)) >= 1 - ANGLE_TOL
    # Exact infinite-line distance is a geometric lower bound for finite bores.
    normal = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    line_distance = (math.hypot(*sub(delta, scaled(a, dot(delta, a)))) if parallel_axes else
                     abs(dot(delta, unit(normal))))
    result = {"first_axis_id": first["axis_id"], "second_axis_id": second["axis_id"],
              "center_delta_xyz_mm": delta, "center_pitch_mm": pitch, "grain_pitch_signed_mm": along,
              "cross_grain_pitch_mm": across, "infinite_line_distance_mm": line_distance,
              "other_bore_clearance_lower_bound_mm":
                  line_distance - first["bore_radius_mm"] - second["bore_radius_mm"]
                  if all(r["bore_radius_mm"] is not None for r in (first, second)) else None,
              "axes_parallel": parallel_axes, "Cg": None, "connection_Cdelta": None,
              "center_bases": [first["center_basis"], second["center_basis"]],
              "row_status": "GROUP_CLASSIFICATION_METHOD_LIMIT", "in_row": None, "between_rows": None,
              "outermost_127mm_comparator_margin_mm": 127.0 - across, "shrinkage_detailing_qualified": False}
    diameter = max(first["diameter_mm"], second["diameter_mm"])
    matched = all(r["center_basis"] == "matched_finished_bore_midpoint" for r in (first, second))
    finite_pitch = line_distance if parallel_axes and matched else None
    lengths = [r["NDS_l_mm"] for r in (first, second)]
    l_mm = min(lengths) if all(v is not None for v in lengths) else None
    perp_between = (2.5 * diameter if l_mm / diameter <= 2 else 5 * diameter
                    if l_mm / diameter >= 6 else (5 * l_mm + 10 * diameter) / 8) if l_mm is not None else 5 * diameter
    result["spacing_geometry_envelope"] = {
        "status": "FINITE_PARALLEL_AXIS_ENDPOINT_GEOMETRY" if finite_pitch is not None else "FINITE_CROSSED_AXIS_GEOMETRY_ONLY",
        "parallel_centerline_pitch_mm": finite_pitch, "modeled_diameter_basis_mm": diameter,
        "conditional_in_row_minimum_mm": 3 * diameter, "conditional_parallel_in_row_full_mm": 4 * diameter,
        "conditional_in_row_minimum_margin_mm": finite_pitch - 3 * diameter if finite_pitch is not None else None,
        "conditional_parallel_in_row_full_margin_mm": finite_pitch - 4 * diameter if finite_pitch is not None else None,
        "parallel_between_rows_mm": 1.5 * diameter, "perpendicular_between_rows_endpoint_mm": perp_between,
        "grain_projection_minus_3D_mm": abs(along) - 3 * diameter,
        "cross_projection_minus_parallel_between_rows_mm": across - 1.5 * diameter,
        "cross_projection_minus_perpendicular_between_rows_mm": across - perp_between,
        "unknown_l_uses_maximum_5D_endpoint": l_mm is None,
        "basis": "Finite geometry and possible tabulated endpoint comparators; actual in-row/between-row classification remains separate.",
        "limit": "A pitch margin applies only if this pair belongs to the corresponding ordinary row. Crossed-line clearance is a lower bound, not a finite-bore collision finding. No universal oblique row law.",
        "applicability_pass": None, "Cg": None, "connection_Cdelta": None, "physical_failure": None}
    if any(r["center_basis"] != "matched_finished_bore_midpoint" for r in (first, second)):
        result["reason"] = "nominal centerline geometry is finite; finished host bore match is missing"
        return result
    if not parallel_axes or first["partners"] != second["partners"] or not first["partners"]:
        result["reason"] = "crossed, internal or serial duties have no common ordinary lateral group"
        return result
    forces = (first["force_xyz_n"], second["force_xyz_n"])
    if any(math.hypot(*f) <= ZERO_N for f in forces):
        result["reason"] = "zero same-state direction"
        return result
    f, h = map(unit, forces)
    if dot(f, h) < 1 - ANGLE_TOL:
        result["reason"] = "unequal or opposing directions do not establish a load-aligned row"
        return result
    if abs(first["diameter_mm"] - second["diameter_mm"]) > TOL_MM:
        result["reason"] = "mixed modeled diameters require a separately classified row rule"
        return result
    diameter = first["diameter_mm"]
    angle = math.degrees(math.acos(min(1.0, abs(dot(f, grain)))))
    if ANGLE_TOL < angle < 90 - ANGLE_TOL or abs(dot(f, a)) > ANGLE_TOL:
        result["reason"] = "oblique grain or axial-only direction is outside the tabulated row branches"
        return result
    load_pitch = abs(dot(delta, f))
    row_separation = math.hypot(*sub(delta, scaled(f, dot(delta, f))))
    result.update(load_to_grain_degrees=angle, load_pitch_mm=load_pitch,
                  candidate_row_separation_mm=row_separation)
    if row_separation <= TOL_MM:
        full = 4 * diameter if angle <= ANGLE_TOL else None
        result.update(row_status="CONDITIONAL_LOAD_ALIGNED_PAIR", in_row={
            "minimum_mm": 3 * diameter, "minimum_margin_mm": pitch - 3 * diameter,
            "full_value_mm": full, "full_value_margin_mm": pitch - full if full else None,
            "conditional_Cdelta": min(1.0, pitch / full) if full and pitch >= 3 * diameter else None,
            "limit": None if full else "full-factor spacing requires the attached-member rule"})
    else:
        lengths = [r["NDS_l_mm"] for r in (first, second)]
        l_mm = min(lengths) if all(v is not None for v in lengths) else None
        required = 1.5 * diameter if angle <= ANGLE_TOL else None
        if required is None and l_mm is not None:
            required = (2.5 * diameter if l_mm / diameter <= 2 else
                        5 * diameter if l_mm / diameter >= 6 else (5 * l_mm + 10 * diameter) / 8)
        result.update(row_status="BETWEEN_POTENTIAL_ROWS_GEOMETRY_ONLY", between_rows={
            "minimum_mm": required, "margin_mm": row_separation - required if required else None,
            "NDS_l_mm": l_mm, "complete_row_partition_established": False})
    return result


def global_actions(case, axis, raw, rows, exported):
    """Recover signed first/second-body forces from the saved same-state rows."""
    actions = defaultdict(list)
    require(exported["axis_id"] == axis["axis_id"] and exported["case_id"] == case
            and set(exported["receivers"]) == set(axis["receivers"]), "export/axis identity differs")
    for interface, saved in zip(axis["interfaces"], exported["interfaces"], strict=True):
        indices = interface["component_rows"]
        directions = interface["component_directions_xyz"]
        require(len(indices) == len(directions) == 2 and saved["component_rows"] == indices
                and saved["component_directions_xyz"] == directions, "interface component census differs")
        first, second = interface["receivers"]
        values = [float(raw[i]) for i in indices]
        require(values == saved["components_n"], "same-state raw/export force differs")
        for i, direction in zip(indices, directions, strict=True):
            row = rows[i]
            require(row["row_id"] == interface["plane_id"]
                    and row["ownership"]["first_body"] == first and row["ownership"]["second_body"] == second
                    and row["ownership"]["direction_global_xyz"] == direction, "signed ownership differs")
        vector = [math.fsum(value * direction[k] for value, direction in zip(values, directions, strict=True))
                  for k in range(3)]
        for body, sign, partner in ((first, 1, second), (second, -1, first)):
            actions[body].append({"plane_id": interface["plane_id"], "component_rows": indices,
                "components_n": values, "force_xyz_n": scaled(vector, sign), "partner": partner,
                "point_xyz_mm": interface["point_xyz_mm"], "basis": "fresh_global_nominal_same_plane"})
    tie = axis["outer_tie"]
    require(float(raw[tie["row"]]) == exported["signed_axial_n"]
            and rows[tie["row"]]["row_id"] == tie["row_id"], "signed outer tie differs")
    return actions


def detailing_census(records):
    """Count reference geometry, hypotheses and unresolved direction separately."""
    counts, reference_counts, directions, reasons = Counter(), Counter(), Counter(), Counter()
    short, full_short, limits = [], [], []
    for index, record in enumerate(records):
        details = [record["detail"], *record.get("per_interface_details", [])]
        for detail_index, detail in enumerate(details):
            directions[detail.get("direction", {}).get("classification", "NO_DIRECTION_RECORD")] += 1
            for kind in ("end", "edge"):
                for label, comparison in detail.get("reference_" + kind + "_comparisons", {}).items():
                    reference_counts[kind + "/" + comparison["status"]] += 1
                    witness = {"host_state_row": index, "detail_index": detail_index,
                        "case_id": record["case_id"], "axis_id": record["axis_id"], "body": record["body"],
                        "kind": kind, "ray": label, "status": comparison["status"],
                        "measured_mm": comparison["measured_mm"], "reference_basis": comparison["reference_basis"],
                        "applicability_limit": comparison.get("applicability_limit"), "physical_failure": None}
                    if comparison["status"] == "METHOD_LIMIT":
                        reasons[comparison["reason"]] += 1
                        if len(limits) < 100:
                            limits.append({**witness, "reason": comparison["reason"]})
                    for field, destination in (("minimum_margin_mm", short), ("full_value_margin_mm", full_short)):
                        margin = comparison.get(field)
                        if margin is not None and margin < -TOL_MM:
                            destination.append({**witness, field: margin,
                                "interpretation": "reference geometry falls below this stated endpoint/envelope tier; no physical failure or resistance claim"})
            for station in detail.get("stations", []):
                for kind in ("end_comparisons", "edge_comparisons"):
                    for label, comparison in station[kind].items():
                        counts[kind + "/" + comparison["status"]] += 1
            if not detail.get("stations"):
                reason = detail.get("reason", "no supported finished stations")
                reasons[reason] += 1
                if len(limits) < 100:
                    limits.append({"host_state_row": index, "detail_index": detail_index,
                        "case_id": record["case_id"], "axis_id": record["axis_id"], "body": record["body"], "reason": reason})
    return {"sampled_status_counts": dict(counts), "reference_status_counts": dict(reference_counts),
            "direction_counts_including_per_interface_details": dict(directions),
            "reference_minimum_tier_shortfalls": short, "reference_full_factor_tier_shortfalls": full_short,
            "reference_method_limit_reason_counts": dict(reasons), "method_limit_witnesses_first_100": limits,
            "all_witnesses_retained_in_host_states": True, "zero_directions_are_not_applicability_passes": True,
            "hypothesis_shortfalls_are_not_physical_failure": True, "N03_accepted": False}


def write_geometry_reference_packet(output, pins, prepared, reference):
    status = "FINITE_ANALYTICAL_GEOMETRY_REFERENCE" if reference["reference_agrees_with_closed_form"] else "ANALYTICAL_GEOMETRY_REFERENCE_METHOD_LIMIT"
    packet = {".gitignore": "*\n", "producer.py.snapshot": Path(__file__).read_text(),
        "geometry-reference.json": reference, "summary.json": {"schema": "N03_geometry_reference_packet/v1",
            "status": status, "source_count": len(pins), "source_sha256": source_map(pins),
            "census": prepared["census"], "load_arithmetic_executed": False, **FLAGS}}
    authenticate(pins)
    output = write_packet(output, packet)
    authenticate(pins)
    receipt = {"source_count": len(pins), "source_sha256": source_map(pins), "status": status,
        "output_sha256": {name: sha(output / name) for name in packet},
        "sources_authenticated_before_and_after": True, "load_arithmetic_executed": False, **FLAGS}
    with (output / "receipt.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    authenticate(pins)
    return {"status": status, "source_count": len(pins), "summary_sha256": sha(output / "summary.json"),
            "reference_sha256": sha(output / "geometry-reference.json"), "receipt_sha256": sha(output / "receipt.json"), **FLAGS}


def geometry_reference(output):
    """Parent-only analytical reference, without any saved-force arithmetic."""
    pins, prepared, _ = prepare_sources()
    with helpers() as (_, api):
        reference = analytical_geometry_known_answer(api)
    return write_geometry_reference_packet(output, pins, prepared, reference)


def build(output):
    """Parent-only saved-array arithmetic; fresh output, no solve or CAD calls."""
    output = Path(output).absolute()
    require(output.parent == RAW and output.resolve() == output and not output.exists(), "fresh owned child required")
    pins, prepared, data = prepare_sources()
    exported = {(r["case_id"], r["axis_id"]): r for r in map(json.loads,
        (EXPORT / "global-demands.jsonl").read_text().splitlines()) if r["kind"] == "structural_bolt"}
    internal = {(r["case_id"], r["canonical_axis_id"]): r for r in map(json.loads,
        (KNEE / "allocations.jsonl").read_text().splitlines())}
    require(set(exported) == {(c, a) for c in CASES for a in data["axes"]}
            and set(internal) == {(c, a) for c in CASES for a in data["internal_axes"]}, "648 load-state identities differ")
    corner = {}
    for state in data["corner"]["states"]:
        for host, record in state["hosts"].items():
            for bolt in record["state"]["bolts"]:
                corner[state["case_id"], bolt["axis_id"], host] = bolt["bore_force_on_host_xyz_n"]
                corner[state["case_id"], bolt["axis_id"], state["cleat"]] = scaled(bolt["bore_force_on_host_xyz_n"], -1)
    corrections = {a["axis_id"]: a for p in data["correction"]["proposals"] for a in p["axes"]}
    axes = {**data["axes"], **data["internal_axes"]}
    records, spacing, geometry_rows = [], [], []
    with helpers() as (signed_api, api):
        known_answer = analytical_geometry_known_answer(api)
        if not known_answer["reference_agrees_with_closed_form"]:
            # Preserve the exact failed reference and avoid evaluating model loads.
            return write_geometry_reference_packet(output, pins, prepared, known_answer)
        recipes = {body: finish_recipe(supplied_member_recipe(body, member, data["surfaces"][body],
                    data["correction"], list(data["internal_axes"].values()), api), data["axes"], api)
                   for body, member in data["members"].items()}
        matches = {}
        for axis_id, axis in axes.items():
            is_internal = axis_id in data["internal_axes"]
            direction = unit(axis["axis_unit_global_xyz"] if is_internal else axis["axis_xyz"])
            point = (axis["center_global_xyz_mm"] if is_internal else
                     corrections.get(axis_id, {}).get("proposed_axis_point_mm", axis["axis_point_xyz_mm"]))
            diameter = (axis["nominal_shaft_record"]["diameter_mm"] if is_internal else
                        data["bolts"][axis_id]["source_record"]["source_occupied_diameter_mm"]
                        if axis["kind"] == "retained_bolt" else
                        data["bolts"][axis_id]["source_record"]["geometry"]["modeled_shaft_diameter_mm"])
            lengths = {}
            for body in axis["receivers"]:
                bore = match_bore(recipes[body], point, direction)
                matches[axis_id, body] = (bore, direction, diameter)
                if bore:
                    lengths[body] = bore.high - bore.low
                geometry_rows.append({"axis_id": axis_id, "body": body, "proposal_internal_axis": is_internal,
                    "axis_point_xyz_mm": point, "axis_unit_xyz": direction,
                    "effective_STEP": data["effective"][body]["effective_proposal_step"],
                    "current_STEP": data["effective"][body]["current_step"], "modeled_diameter_mm": diameter,
                    "bore_feature_id": bore.feature_id if bore else None, "bore_radius_mm": bore.radius if bore else None,
                    "recipe_status": recipes[body]["status"], "recipe_reason": recipes[body].get("reason")})
            if is_internal or len(lengths) != len(axis["receivers"]):
                l_mm = None
            elif len(lengths) == 2:
                l_mm = min(lengths.values())
            else:
                # The middle receiver is incident to both recorded shear planes.
                counts = Counter(b for i in axis["interfaces"] for b in i["receivers"])
                middle = [b for b, count in counts.items() if count == 2]
                require(len(middle) == 1 and len(lengths) == 3, "three-host stack identity differs")
                l_mm = min(lengths[middle[0]], sum(v for b, v in lengths.items() if b != middle[0]))
            axis["N03_l_mm"] = l_mm
        host_bores = {body: [(axis_id, matches[axis_id, body][0]) for axis_id, axis in axes.items()
                            if body in axis["receivers"]] for body in data["members"]}
        # Import NumPy only for the parent's supplied saved-array calculation.
        bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            import numpy as np

            with np.load(FRAME / "response.npz", allow_pickle=False) as response:
                for case in CASES:
                    raw = response[case + "_gap_raw_force_n"]
                    require(raw.shape == (1888,) and np.isfinite(raw).all(), "nominal force array differs")
                    host_pairs = defaultdict(list)
                    for axis_id, axis in axes.items():
                        is_internal = axis_id in data["internal_axes"]
                        actions = {} if is_internal else global_actions(case, axis, raw, data["rows"], exported[case, axis_id])
                        for body in axis["receivers"]:
                            bore, direction, diameter = matches[axis_id, body]
                            body_actions = actions.get(body, [])
                            local = corner.get((case, axis_id, body))
                            force = local if local is not None else [math.fsum(a["force_xyz_n"][k] for a in body_actions) for k in range(3)]
                            # Sum on a continuous middle host is recorded alongside
                            # each plane; a cancelling resultant never hides them.
                            details = host_details(data["members"][body], recipes[body], bore, force,
                                                   direction, diameter, axis["N03_l_mm"], signed_api, api, host_bores[body])
                            row = {"case_id": case, "gap_scale": 1.0, "axis_id": axis_id, "body": body,
                                "proposal_internal_axis": is_internal, "global_plane_actions": body_actions,
                                "direction_basis": "fresh_physical_corner_bore_resultant" if local is not None else
                                    "axial_internal_end_pair_no_lateral_interface" if is_internal else
                                    "fresh_global_host_sum_with_each_plane_preserved",
                                "detail": details, "release_flags": data["release_flags"], **FLAGS}
                            if len(body_actions) > 1:
                                row["per_interface_details"] = [host_details(data["members"][body], recipes[body], bore,
                                    action["force_xyz_n"], direction, diameter, axis["N03_l_mm"], signed_api, api, host_bores[body])
                                    for action in body_actions]
                            if is_internal:
                                allocation = internal[case, axis_id]
                                row["internal_allocation"] = allocation
                                row["axial_NDS_limit"] = "12.3.9.1 bearing path is separate; no lateral geometry factor is assigned"
                                require(all(e["force_on_wood_xyz_n"] == scaled(e["outward_unit_xyz"], -allocation["axial_tension_n"])
                                            for e in allocation["end_seats"]), "internal end pair direction differs")
                            else:
                                tie = axis["outer_tie"]
                                sign = 1 if body == tie["first_body"] else -1 if body == tie["second_body"] else 0
                                row["separate_outer_tie_xyz_n"] = scaled(tie["direction_global_xyz"], sign * float(raw[tie["row"]]))
                            records.append(row)
                            nominal_point = (axis["center_global_xyz_mm"] if is_internal else
                                corrections.get(axis_id, {}).get("proposed_axis_point_mm", axis["axis_point_xyz_mm"]))
                            # Every incidence enters the spacing census even if
                            # the finished analytic recipe refuses its host.
                            host_pairs[body].append({"axis_id": axis_id, "axis_unit_xyz": direction,
                                    "center_xyz_mm": details["mid_bearing_xyz_mm"] if bore else nominal_point,
                                    "center_basis": "matched_finished_bore_midpoint" if bore else "frozen_nominal_axis_point",
                                    "bore_radius_mm": bore.radius if bore else None,
                                    "diameter_mm": diameter, "NDS_l_mm": axis["N03_l_mm"],
                                    "force_xyz_n": force, "partners": sorted(a["partner"] for a in body_actions)})
                    for body, members in host_pairs.items():
                        for first, second in combinations(members, 2):
                            spacing.append({"case_id": case, "body": body,
                                **pair_spacing(first, second, unit(data["members"][body]["geometry"]["axis"])), **FLAGS})
        finally:
            sys.dont_write_bytecode = bytecode
    require(len(records) == prepared["census"]["planning_host_case_states"], "every-host state census differs")
    authenticate(pins)
    summary = {"schema": "bolt_detailing_completion/v2", "status": "FINITE_N03_REFERENCE_AND_CONSERVATIVE_ELIGIBILITY_INVENTORY",
        "qualification": "N03", "census": {**prepared["census"], "host_state_records": len(records),
            "geometry_host_records": len(geometry_rows), "pair_case_records": len(spacing)},
        "host_detail_status_counts": dict(Counter(r["detail"]["status"] for r in records)),
        "pair_status_counts": dict(Counter(r["row_status"] for r in spacing)),
        "pair_geometry_status_counts": dict(Counter(r["spacing_geometry_envelope"]["status"] for r in spacing)),
        "analytical_geometry_reference_agrees": known_answer["reference_agrees_with_closed_form"],
        "reference_basis": REFERENCE_BASIS, "load_basis": data["load_basis"],
        "detailing_census": detailing_census(records),
        "source_count": len(pins), "source_sha256": source_map(pins),
        "release_flags": data["release_flags"], "formal_pending_criteria_count": 47, "limits": LIMITS,
        "per_state_results_are_not_envelope_resistance": True, **FLAGS}
    packet = {".gitignore": "*\n", "producer.py.snapshot": Path(__file__).read_text(),
              "geometry-reference.json": known_answer,
              "summary.json": summary, "geometry-bindings.json": geometry_rows,
              "host-states.jsonl": "".join(json.dumps(r, allow_nan=False) + "\n" for r in records),
              "pair-spacing.jsonl": "".join(json.dumps(r, allow_nan=False) + "\n" for r in spacing)}
    output = write_packet(output, packet)
    authenticate(pins)
    receipt = {"schema": "bolt_detailing_receipt/v1", "status": summary["status"],
        "source_sha256": source_map(pins), "source_count": len(pins),
        "output_sha256": {name: sha(output / name) for name in packet},
        "sources_authenticated_before_and_after": True, "census": summary["census"],
        "release_flags": data["release_flags"], **FLAGS}
    with (output / "receipt.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    authenticate(pins)
    return {"status": summary["status"], "census": summary["census"], "source_count": len(pins),
            "summary_sha256": sha(output / "summary.json"), "receipt_sha256": sha(output / "receipt.json"), **FLAGS}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true", help="stdlib source/census preparation only")
    mode.add_argument("--geometry-reference", action="store_true", help="parent-only closed-form analytical geometry reference")
    args = parser.parse_args()
    function = prepare if args.prepare else geometry_reference if args.geometry_reference else build
    print(json.dumps(function(args.output), allow_nan=False))
