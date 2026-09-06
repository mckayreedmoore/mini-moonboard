"""Prepare only a stationary DIRECT case at a separately frozen washer pose."""
import argparse
import copy
import hashlib
import json
import math
import sys
import tempfile
import types
from pathlib import Path

from fea import moving_hardware_control as control
from fea import moving_hardware_pose as pose

_SOURCE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def source_snapshot():
    own = Path(__file__).read_bytes()
    if control.digest(own) != _SOURCE_HASH:
        raise ValueError("Posed preparation source changed after import")
    for code in compile(own, str(Path(__file__).resolve()), "exec").co_consts:
        if isinstance(code, types.CodeType) and code.co_name.isidentifier():
            loaded = getattr(sys.modules[__name__], code.co_name, None)
            if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                raise ValueError("Loaded posed preparation differs from source")
    return {**control.source_snapshot(), **pose.source_snapshot(), "posed_hardware_control.py": own}


def read_inputs(centred, posed):
    centred, posed = Path(centred), Path(posed)
    freeze_bytes = (centred / "freeze.json").read_bytes()
    inventory = json.loads(freeze_bytes)["files_sha256"]
    inputs = {"centred/freeze.json": freeze_bytes}
    for name, digest in inventory.items():
        path = (centred / name).resolve()
        if not path.is_relative_to(centred.resolve()):
            raise ValueError("Invalid centred inventory path")
        data = path.read_bytes()
        if control.digest(data) != digest:
            raise ValueError("Centred preparation input hash differs")
        inputs["centred/" + name] = data
    for name in ("report.json", "original-context.json", "posed-nodes.json"):
        inputs["pose/" + name] = (posed / name).read_bytes()
    report = json.loads(inputs["pose/report.json"])
    if (report["translation_local_mm"] != list(pose.TRANSLATION_MM)
            or report["CAD"]["overlap_volume_mm3"] != 0
            or min(report["CAD"]["nominal_axial_gap_mm"], report["CAD"]["nominal_radial_gap_mm"]) <= 0):
        raise ValueError("Frozen pose is not the separated CAD fixture")
    if (inputs["pose/original-context.json"] != inputs["centred/context.json"]
            or report["context_sha256"] != control.digest(inputs["centred/context.json"])
            or report["prepared_freeze_sha256"] != control.digest(freeze_bytes)
            or report["posed_nodes_sha256"] != control.digest(inputs["pose/posed-nodes.json"])):
        raise ValueError("Pose/centred context or coordinate identity differs")
    context = json.loads(inputs["centred/context.json"])
    geometry_bytes = inputs["centred/frozen/geometry.json"]
    geometry = json.loads(geometry_bytes)
    expected_steps = {"leg_stitch_right_1_" + role + ".step": geometry["step_sha256"]["leg_stitch_right_1_" + role + ".step"]
                      for role in ("bolt_nut", "washer_inner")}
    if (report["CAD"]["geometry_sha256"] != control.digest(geometry_bytes)
            or context["input_sha256"]["geometry.json"] != control.digest(geometry_bytes)
            or report["CAD"]["step_sha256"] != expected_steps):
        raise ValueError("Pose CAD geometry/STEP identity differs from centred geometry")
    for name, data in pose.source_snapshot().items():
        snapshot = (posed / (name + ".snapshot")).read_bytes()
        if snapshot != data or report["source_sha256"].get(name) != control.digest(data):
            raise ValueError("Frozen pose source differs from loaded proof")
        inputs["pose/" + name + ".snapshot"] = snapshot
    return inputs


def translate_bounds(bounds, delta):
    return [v + delta[k % 3] for k, v in enumerate(bounds)]


def build_context(inputs):
    original = json.loads(inputs["centred/context.json"])
    if set(original["cases"]) != {"quiescent"} or original["cases"]["quiescent"].get("direct_quiescent") is not True:
        raise ValueError("Expected centred quiet-only DIRECT preparation")
    if control.deck(original, "quiescent").encode() != inputs["centred/quiescent.inp"]:
        raise ValueError("Centred deck does not match its context")
    report = json.loads(inputs["pose/report.json"])
    saved = json.loads(inputs["pose/posed-nodes.json"])
    expected_nodes, metadata = pose.posed_nodes(original)
    if saved != json.loads(json.dumps({"nodes": expected_nodes, "quantization": metadata})):
        raise ValueError("Pose serialized coordinates differ from the proven translation")
    proof = pose.mesh_clearance(original)
    if (json.loads(json.dumps(proof)) != report["quadratic_mesh"]
            or proof["strictly_separated_selected_surfaces"] is not True
            or min(proof["radial_gap_lower_mm"], proof["axial_gap_lower_mm"]) <= 0):
        raise ValueError("Pose clearance proof differs or is not positive")
    context = copy.deepcopy(original)
    context["nodes"] = expected_nodes
    delta, origin = pose.TRANSLATION_MM, context["origin_mm_global"]
    context["pose_variant"] = "separated-washer-stationary-preflight"
    context["angular_reference_mm_local"] = [1. + delta[0], delta[1], delta[2]]
    context["coordinate_transform"] = "Station-local reference coordinates plus physical washer-only translation; exact frozen .12g posed nodes. Core unchanged."
    context["reference_coordinate_quantization"] = context.pop("coordinate_quantization")
    context["coordinate_quantization"] = metadata
    context["reference_global_bounds_mm"] = context["global_bounds_mm"]
    context["global_bounds_mm"] = control.bounds([tuple(v + origin[k] for k, v in enumerate(p)) for p in expected_nodes.values()])
    context["initial_interface_gap_bounds_mm"] = {"radial": proof["radial_gap_lower_mm"], "axial": proof["axial_gap_lower_mm"]}
    for name, body in context["bodies"].items():
        shift = delta if name == "WASHER" else (0., 0., 0.)
        for key in ("local_bounds_mm", "global_bounds_mm"):
            body["reference_" + key] = body[key]
        body["local_bounds_mm"] = control.bounds([expected_nodes[n] for n in body["nodes"]])
        body["global_bounds_mm"] = translate_bounds(body["global_bounds_mm"], shift)
        body["serialized_global_bounds_mm"] = translate_bounds(body["local_bounds_mm"], origin)
        body["quality_metadata_scope"] = "Recorded original mesh quality; no remeshing or claim of recomputed posed Jacobian extrema"
        for surface in body["surfaces"].values():
            surface["reference_cad_bounds_mm"] = surface["cad_bounds_mm"]
            surface["cad_bounds_mm"] = translate_bounds(surface["cad_bounds_mm"], shift)
            surface["local_mesh_bounds_mm"] = control.bounds([expected_nodes[n] for n in surface["nodes"]])
    for surface in context["surfaces"].values():
        shift = delta if surface["body"] == "WASHER" else (0., 0., 0.)
        for key in ("cad_bounds_mm_global", "cad_bounds_mm_local"):
            surface["reference_" + key] = surface[key]
            surface[key] = translate_bounds(surface[key], shift)
        surface["local_mesh_bounds_mm"] = control.bounds([expected_nodes[n] for n in surface["nodes"]])
    washer = context["bodies"]["WASHER"]
    blocks = control.dynamic_momentum.calculix_221_mass(
        {e: context["elements"][str(e)] for e in washer["elements"]},
        {n: expected_nodes[n] for n in washer["nodes"]}, context["material"]["density_tonne_mm3"])
    mass = math.fsum(math.fsum(map(math.fsum, block)) for _, block in blocks.values())
    if not math.isfinite(mass) or mass <= 0:
        raise ValueError("Invalid posed native reference mass")
    reference = context["diagnostic_reference_scales"]
    reference.update(reference_mass_tonne=mass, P_star_tonne_mm_s=mass * math.sqrt(20000),
                     E_star_N_mm=mass * 10000, H_star_tonne_mm2_s=57.15 * mass * math.sqrt(20000))
    context["scope"] = "Two free separated hardware bodies; stationary DIRECT diagnostic only, no moving case or contact qualification"
    context["next_comparison"] = "Audit the posed stationary output before designing any moving case; no automatic solve"
    return context


def prepare(centred_directory, pose_directory, parent=Path("fea/generated/posed-hardware-controls")):
    sources = source_snapshot()
    inputs = read_inputs(centred_directory, pose_directory)
    context = build_context(inputs)
    context["input_sha256"] = {name: control.digest(data) for name, data in inputs.items()}
    context["source_sha256"] = {name: control.digest(data) for name, data in sources.items()}
    deck = control.deck(context, "quiescent").encode()
    context["deck_sha256"] = {"quiescent": control.digest(deck)}
    if source_snapshot() != sources or read_inputs(centred_directory, pose_directory) != inputs:
        raise ValueError("Input/source drift during posed preparation")
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="posed-control-", dir=parent))
    for name, data in {**inputs, **sources}.items():
        target = directory / "frozen" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (directory / "quiescent.inp").write_bytes(deck)
    (directory / "context.json").write_text(json.dumps(context, indent=2, allow_nan=False) + "\n")
    if source_snapshot() != sources or read_inputs(centred_directory, pose_directory) != inputs:
        raise ValueError("Input/source drift; no launchable posed freeze written")
    (directory / "freeze.json").write_text(json.dumps({"status": context["status"],
        "files_sha256": {p.relative_to(directory).as_posix(): control.digest(p.read_bytes()) for p in directory.rglob("*") if p.is_file()}}, indent=2) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("centred_directory", type=Path)
    parser.add_argument("pose_directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/posed-hardware-controls"))
    args = parser.parse_args()
    print(prepare(args.centred_directory, args.pose_directory, args.output))
