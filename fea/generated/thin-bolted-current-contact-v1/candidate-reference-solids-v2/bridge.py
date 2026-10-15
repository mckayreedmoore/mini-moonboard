"""Strict transparent-container bridge around the frozen twenty-owner census."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
V1 = OWN.parent.parent/"candidate-reference-solids-v1"
FIXED = {
    "plan.py": "beb017bc975fcabdc0ed3fea9c59f6db73daacf1f60ab4ad5286c598030edd58",
    "test_plan.py": "280415bcd304fda52744f21c2fa9a0c656a4e311474c3b8fea60de8802be1832",
    "plan.json": "18d942c2c42ff253a7bc79c613d03d34c3ccff69a0ea5d5bca5e24d8d2438a2f",
    "independent-method-review.json": "9be4f4e11beb11516832366c00b26acc1db97c3f1ce1990377ee4b3ecbf0c498",
    "census-attempt01-failure.json": "6a2e495248b57e116fadc926d3b3bb4c66061542a7096b72e69606c6acb733fa",
}
SCHEMA = "thin_bolted_candidate_reference_closed_solid_bridge_plan/v2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def original():
    for name, digest in FIXED.items():
        require(sha(V1/name) == digest, "preserved first census evidence differs: "+name)
    return load("preserved_twenty_owner_census_for_strict_container", V1/"plan.py")


def prepare_plan():
    old = original()
    fresh = old.prepare_plan()
    saved = json.loads((V1/"plan.json").read_bytes())
    require(all(saved.get(key) == value for key, value in fresh.items()), "preserved source plan differs from pure preparation")
    pins = {**saved["source_sha256"], **{str((V1/name).relative_to(ROOT)): digest for name, digest in FIXED.items()}}
    for path in (OWN, OWN.with_name("test_bridge.py"), OWN.with_name("input.json")):
        pins[str(path.relative_to(ROOT))] = sha(path)
    require(pins[str(OWN.relative_to(ROOT))] == LOADED_SHA, "loaded bridge source changed")
    old.verify(pins)
    inputs = json.loads(OWN.with_name("input.json").read_bytes())
    return {"schema": SCHEMA, "candidate": saved["candidate"], "revision": saved["revision"], "source_sha256": pins,
        "loaded_bridge_sha256": LOADED_SHA, "reused_source_plan_path": str((V1/"plan.json").relative_to(ROOT)),
        "reused_source_plan_sha256": FIXED["plan.json"], "reused_census_rows_source_path": str((V1/"plan.py").relative_to(ROOT)),
        "reused_census_rows_sha256": FIXED["plan.py"], "counts": saved["counts"],
        "owners": [row["owner_id"] for row in saved["owners"]], "package_versions": old.versions(),
        "adapter": saved["adapter"], "strict_container_contract": inputs,
        "preserved_failed_attempt": {"path": str((V1/"census-attempt01-failure.json").relative_to(ROOT)), "sha256": FIXED["census-attempt01-failure.json"]},
        "candidate_geometry_imported_or_queried": False, "candidate_closed_topology_verified": False,
        "q_K_force_or_native_solve_consumed": False, "release": dict(old.RELEASE)}


def read_plan(path, digest):
    require(sha(path) == digest, "exact v2 bridge plan required")
    saved = json.loads(path.read_bytes())
    fresh = prepare_plan()
    require(all(saved.get(key) == value for key, value in fresh.items()), "v2 plan differs from current source-only preparation")
    return saved, original()


def adapters(plan, old):
    old.verify(plan["source_sha256"])
    smooth = load("genuine_smooth_touch_for_strict_container", ROOT/old.TOUCH)
    reference = smooth.reference
    require(Path(reference.__file__).resolve() == ROOT/old.DISTANCE
            and reference.LOADED_SOURCE_SHA256 == old.FIXED[old.DISTANCE]
            and smooth.LOADED_SOURCE_SHA256 == old.FIXED[old.TOUCH]
            and all(plan["source_sha256"].get(path) == digest for path, digest in smooth.source_pins().items()), "loaded genuine adapters differ")
    reference.tools()
    return reference


def strict_solid(shape, reference):
    """Accept only immediate-child COMPOUND* -> SOLID, with cumulative flags."""
    from OCP.TopAbs import TopAbs_COMPOUND, TopAbs_SOLID
    from OCP.TopoDS import TopoDS_Iterator

    require(isinstance(shape, reference.cq.Shape) and not shape.wrapped.IsNull() and shape.isValid(), "valid nonnull original shape required")
    before = reference.brep_sha(shape)
    current, nodes, visited = shape.wrapped, [], []
    while True:
        require(not current.IsNull() and not any(current.IsPartner(node) for node in visited), "null or cyclic wrapper chain rejected")
        visited.append(current)
        wrapped = reference.cq.Shape.cast(current)
        trsf = current.Location().Transformation()
        record = {"shape_type": str(current.ShapeType()), "orientation": str(current.Orientation()),
            "location_3x4": [[trsf.Value(i, j) for j in range(1, 5)] for i in range(1, 4)],
            "native_serialized_brep_sha256": reference.brep_sha(wrapped), "immediate_children": current.NbChildren()}
        nodes.append(record)
        if current.ShapeType() == TopAbs_SOLID:
            break
        require(current.ShapeType() == TopAbs_COMPOUND, "only COMPOUND wrapper nodes may precede the SOLID")
        iterator = TopoDS_Iterator(current, True, True)
        require(iterator.More(), "empty compound rejected")
        child = reference.cq.Shape.cast(iterator.Value()).wrapped
        iterator.Next()
        require(not iterator.More() and current.NbChildren() == 1, "compound siblings/extra geometry rejected")
        current = child
    canonical = reference.cq.Shape.cast(current)
    require(canonical.wrapped.IsEqual(current), "canonical cast changed location/orientation/TShape")
    require(reference.brep_sha(shape) == before, "original imported wrapper changed")
    original_counts = {"solids": len(shape.Solids()), "shells": len(shape.Shells()), "faces": len(shape.Faces()), "edges": len(shape.Edges()), "vertices": len(shape.Vertices())}
    canonical_counts = {"solids": len(canonical.Solids()), "shells": len(canonical.Shells()), "faces": len(canonical.Faces()), "edges": len(canonical.Edges()), "vertices": len(canonical.Vertices())}
    require(original_counts == canonical_counts and canonical_counts["solids"] == 1, "transparent wrapper lost geometry")
    return canonical, {"schema": "thin_bolted_strict_single_child_solid_container/v2", "iterator_cumOri": True, "iterator_cumLoc": True,
        "nodes": nodes, "compound_wrapper_count": len(nodes)-1, "original_imported_topology_counts": original_counts,
        "canonical_solid_topology_counts": canonical_counts, "original_imported_serialized_brep_sha256": before,
        "canonical_solid_serialized_brep_sha256": reference.brep_sha(canonical),
        "original_wrapper_unchanged": True, "extra_geometry_dropped": False, "location_or_orientation_reset": False}


def wrapper_fixture(reference):
    cq = reference.cq
    solid = cq.Solid.makeBox(4., 6., 8.)
    inner = cq.Compound.makeCompound([solid]).located(cq.Location(cq.Vector(3., -2., 5.), cq.Vector(0., 0., 1.), 30.))
    inner.wrapped.Reverse()
    outer = cq.Compound.makeCompound([inner]).located(cq.Location(cq.Vector(10., 20., 30.)))
    outer.wrapped.Reverse()
    return solid, outer


def known_answer(reference):
    solid, outer = wrapper_fixture(reference)
    stream = io.BytesIO()
    require(outer.exportBrep(stream), "toy wrapper serialization failed")
    raw = stream.getvalue()
    import_original = reference.cq.Shape.importBrep

    def toy_only_import(value):
        require(isinstance(value, io.BytesIO), "method coupon must not import a candidate file")
        return import_original(value)

    with patch.object(reference.cq.Shape, "importBrep", side_effect=toy_only_import):
        restored = reference.cq.Shape.importBrep(io.BytesIO(raw))
        canonical, record = strict_solid(restored, reference)
        geometry = reference.ReferenceSolidDistance(canonical, owner_id="synthetic-serialized-wrapper",
            source_identity={"kind": "known-answer-only", "serialized_wrapper_raw_sha256": hashlib.sha256(raw).hexdigest()})
    expected = [13.+2.*math.cos(math.pi/6)-3.*math.sin(math.pi/6), 18.+2.*math.sin(math.pi/6)+3.*math.cos(math.pi/6), 39.]
    center = canonical.Center().toTuple()
    center_error = math.dist(center, expected)
    box = canonical.BoundingBox()
    bounds = [[box.xmin, box.xmax], [box.ymin, box.ymax], [box.zmin, box.zmax]]
    expected_bounds = [[13.-6.*math.sin(math.pi/6), 13.+4.*math.cos(math.pi/6)],
                       [18., 18.+4.*math.sin(math.pi/6)+6.*math.cos(math.pi/6)], [35., 43.]]
    bounds_error = max(abs(a-b) for aa, bb in zip(bounds, expected_bounds, strict=True) for a, b in zip(aa, bb, strict=True))
    require(abs(canonical.Volume()-192.) < 1e-10 and center_error < 1e-12
            and bounds_error < 1e-12
            and record["compound_wrapper_count"] == 2 and record["nodes"][-1]["orientation"] == "TopAbs_Orientation.TopAbs_FORWARD",
            "serialized wrapper location/orientation known answer failed")
    rejected = []
    extra = {"solid-sibling": solid, "extra-face": solid.Faces()[0], "extra-edge": solid.Edges()[0], "extra-wire": solid.Faces()[0].outerWire()}
    for name, sibling in extra.items():
        try:
            strict_solid(reference.cq.Compound.makeCompound([solid, sibling]), reference)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError("extra toy geometry was silently dropped: "+name)
    for name, item in (("empty", reference.cq.Compound.makeCompound([])), ("sole-face", reference.cq.Compound.makeCompound([solid.Faces()[0]]))):
        try:
            strict_solid(item, reference)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError("unsupported toy chain was accepted: "+name)
    return {"toy_serialized_brep_sha256": hashlib.sha256(raw).hexdigest(), "toy_serialized_bytes": len(raw),
        "strict_container_record": record, "actual_frozen_constructor_topology": geometry.topology,
        "expected_volume_mm3": 192., "volume_error_mm3": abs(canonical.Volume()-192.),
        "expected_centroid_xyz_mm": expected, "centroid_error_mm": center_error,
        "expected_bounds_xyz_mm": expected_bounds, "bounds_error_mm": bounds_error,
        "rejected_extra_or_unsupported_containers": rejected, "candidate_file_imports": 0, "distance_point_queries": 0}


def execute_census(plan, old, reference):
    source_plan = json.loads((ROOT/plan["reused_source_plan_path"]).read_bytes())
    contexts = []

    def import_finished(path):
        imported = reference.cq.Shape.importBrep(str(path))
        canonical, record = strict_solid(imported, reference)
        contexts.append({"finished_original_file_path": str(path.relative_to(ROOT)), "finished_original_file_sha256": sha(path), **record})
        return canonical

    records = old.census_rows(source_plan, import_finished=import_finished, geometry_factory=reference.ReferenceSolidDistance)
    require(len(contexts) == len(records) == 20, "twenty canonicalized imports required")
    return {"schema": "thin_bolted_candidate_reference_closed_solid_census/v2", "owners": records,
        "strict_container_canonicalizations": contexts, "closed_topology_census_completed": True,
        "counts": {"finished_imports": 20, "raw_imports": 0, "point_distance_queries": 0},
        "limits": plan["strict_container_contract"]["limits"], "reference_penalty_or_physical_pressure_adopted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "coupon", "census"))
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve prior strict-container evidence")
    if args.mode == "plan":
        require(args.plan is None and args.plan_sha256 is None, "plan mode has no prior input")
        result = prepare_plan()
    else:
        require(args.plan is not None and args.plan_sha256 is not None, "exact v2 plan path/SHA required")
        plan, old = read_plan(args.plan, args.plan_sha256)
        reference = adapters(plan, old)
        result = execute_census(plan, old, reference) if args.mode == "census" else {
            "schema": "thin_bolted_strict_solid_container_method_coupon/v2", "method_checks_pass": True, "known_answer": known_answer(reference)}
        result.update({"candidate": plan["candidate"], "revision": plan["revision"],
            "source_sha256": {**plan["source_sha256"], str(args.plan.resolve().relative_to(ROOT)): args.plan_sha256},
            "input_plan_sha256": args.plan_sha256, "preserved_failed_attempt": plan["preserved_failed_attempt"],
            "actual_adapter_tools": reference.tools(), "loaded_closed_solid_source_path": old.DISTANCE,
            "loaded_closed_solid_source_sha256": reference.LOADED_SOURCE_SHA256,
            "candidate_distance_q_K_force_or_native_solve_consumed": False, "release": dict(old.RELEASE)})
        require(sha(args.plan) == args.plan_sha256, "bridge plan changed during execution")
        old.verify(result["source_sha256"])
    result["execution"] = {"actual_sys_argv": sys.argv.copy(), "actual_sys_orig_argv": sys.orig_argv.copy(),
        "loaded_driver_source_path": str(OWN.relative_to(ROOT)), "loaded_driver_sha256": LOADED_SHA,
        "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}}
    original().verify(result["source_sha256"])
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
