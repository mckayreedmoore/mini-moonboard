"""Separated moving-fixture geometry preflight; no deck, mesh or solver changes."""
import argparse
import hashlib
import json
import math
import sys
import tempfile
import types
from fractions import Fraction
from pathlib import Path

from fea import quiescent_hardware_diagnostic as retained

TRANSLATION_MM = (.001, .7356, 0.)
FACES = ((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
         (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6))
POWERS = ((2, 0, 0), (0, 2, 0), (0, 0, 2), (1, 1, 0), (0, 1, 1), (1, 0, 1))
_SOURCE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_CONFIG = (TRANSLATION_MM, FACES, POWERS)


def source_snapshot():
    data = Path(__file__).read_bytes()
    if hashlib.sha256(data).hexdigest() != _SOURCE_HASH or (TRANSLATION_MM, FACES, POWERS) != _CONFIG:
        raise ValueError("Pose source/configuration changed after import")
    for code in compile(data, str(Path(__file__).resolve()), "exec").co_consts:
        if isinstance(code, types.CodeType) and code.co_name.isidentifier():
            loaded = getattr(sys.modules[__name__], code.co_name, None)
            if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                raise ValueError("Loaded pose function differs from source")
    return {"moving_hardware_pose.py": data, "quiescent_hardware_diagnostic.py": retained.source_snapshot()}


def bezier(points):
    """Exact binary-float input → rational quadratic Bézier control vectors."""
    if len(points) != 6 or any(len(p) != 3 or not all(map(math.isfinite, p)) for p in points):
        raise ValueError("Expected finite TRI6 coordinates")
    p = [tuple(Fraction(v) for v in xyz) for xyz in points]
    return p[:3] + [tuple(2 * p[m][k] - (p[a][k] + p[b][k]) / 2 for k in range(3))
                    for a, b, m in ((0, 1, 3), (1, 2, 4), (2, 0, 5))]


def multinomial(power):
    return math.factorial(sum(power)) // math.prod(math.factorial(i) for i in power)


def quadratic_bounds(points):
    """Global patch bounds: nonnegative Bernstein bases partition unity.

    Products B²_a B²_b = C(2,a) C(2,b)/C(4,a+b) B⁴_(a+b).
    Thus coefficient extrema enclose y²+z² over the entire parameter triangle.
    Fraction arithmetic avoids cancellation/roundoff invalidating that enclosure.
    """
    controls = bezier(points)
    coefficients = {}
    for a, pa in zip(POWERS, controls, strict=True):
        for b, pb in zip(POWERS, controls, strict=True):
            power = tuple(i + j for i, j in zip(a, b, strict=True))
            factor = Fraction(multinomial(a) * multinomial(b), multinomial(power))
            coefficients[power] = coefficients.get(power, Fraction(0)) + factor * (pa[1]*pb[1] + pa[2]*pb[2])
    return min(p[0] for p in controls), max(p[0] for p in controls), min(coefficients.values()), max(coefficients.values())


def outward(value, direction):
    return math.nextafter(float(value), direction)


def subdivide(points):
    """Four exact affine restrictions; their union is the full parent triangle."""
    controls = bezier(points)
    e0, e1, e2 = (Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1))
    def midpoint(a, b):
        return tuple((i + j) / 2 for i, j in zip(a, b, strict=True))
    def evaluate(bary):
        weights = [multinomial(power) * math.prod(bary[k]**power[k] for k in range(3)) for power in POWERS]
        return tuple(sum(w * p[k] for w, p in zip(weights, controls, strict=True)) for k in range(3))
    m01, m12, m20 = midpoint(e0, e1), midpoint(e1, e2), midpoint(e2, e0)
    return [[evaluate(p) for p in (a, b, c, midpoint(a, b), midpoint(b, c), midpoint(c, a))]
            for a, b, c in ((e0, m01, m20), (m01, e1, m12), (m20, m12, e2), (m01, m12, m20))]


def refined_bounds(points, threshold_squared=None, lower=True, depth=0):
    bound = quadratic_bounds(points)
    proven = threshold_squared is None or (bound[2] >= threshold_squared if lower else bound[3] <= threshold_squared)
    if proven or depth == 4:
        return bound, depth, 1
    children = [refined_bounds(p, threshold_squared, lower, depth + 1) for p in subdivide(points)]
    bounds = [b for b, _, _ in children]
    return (min(b[0] for b in bounds), max(b[1] for b in bounds), min(b[2] for b in bounds), max(b[3] for b in bounds)), max(d for _, d, _ in children), sum(n for _, _, n in children)


def posed_nodes(context, translation=TRANSLATION_MM):
    if len(translation) != 3 or not all(map(math.isfinite, translation)):
        raise ValueError("Invalid rigid translation")
    washer = set(context["bodies"]["WASHER"]["nodes"])
    result = {}
    for n, p in context["nodes"].items():
        result[int(n)] = tuple(float(format(v + translation[k], ".12g")) if int(n) in washer else v
                               for k, v in enumerate(p))
    error = max(abs(result[int(n)][k] - (v + translation[k]))
                for n, p in context["nodes"].items() if int(n) in washer for k, v in enumerate(p))
    if error > 5e-10:
        raise ValueError("Pose serialization error exceeds bound")
    return result, {"translation_local_mm": translation, "format": ".12g",
                    "maximum_serialization_error_mm": error, "serialization_error_bound_mm": 5e-10,
                    "core_nodes_unchanged": True}


def mesh_clearance(context, translation=TRANSLATION_MM):
    nodes, quantization = posed_nodes(context, translation)
    elements = {int(e): ns for e, ns in context["elements"].items()}
    bounds, depths, leaves = {}, {}, {}
    gap = 5.4991 - 4.7625 - math.hypot(*translation[1:])
    for name in ("WASHER_HEAD", "CORE_HEAD", "WASHER_BORE", "CORE_SHANK"):
        faces = context["surfaces"][name]["faces"]
        if not faces or len({tuple(f) for f in faces}) != len(faces):
            raise ValueError("Empty or duplicate selected surface")
        threshold = (4.7625 + .75 * gap)**2 if name == "WASHER_BORE" else (4.7625 + .25 * gap)**2 if name == "CORE_SHANK" else None
        refined = [refined_bounds([nodes[elements[e][i]] for i in FACES[f-1]],
                                  Fraction(threshold) if threshold is not None else None,
                                  name == "WASHER_BORE") for e, f in faces]
        patches = [b for b, _, _ in refined]
        depths[name], leaves[name] = max(d for _, d, _ in refined), sum(n for _, _, n in refined)
        bounds[name] = (min(p[0] for p in patches), max(p[1] for p in patches),
                        min(p[2] for p in patches), max(p[3] for p in patches))
    bore_squared = max(Fraction(0), bounds["WASHER_BORE"][2])
    shank_squared = max(Fraction(0), bounds["CORE_SHANK"][3])
    bore_min = math.nextafter(math.sqrt(max(0., outward(bore_squared, -math.inf))), -math.inf)
    shank_max = math.nextafter(math.sqrt(outward(shank_squared, math.inf)), math.inf)
    radial = math.nextafter(bore_min - shank_max, -math.inf)
    axial = outward(bounds["WASHER_HEAD"][0] - bounds["CORE_HEAD"][1], -math.inf)
    return {"method": "Exact rational Bernstein coefficient bounds over complete quadratic triangles; outward-rounded square roots and subtraction. No point sampling.",
            "surface_face_counts": {n: len(context["surfaces"][n]["faces"]) for n in bounds},
            "subdivision_maximum_depth": depths, "bounded_subpatches": leaves,
            "washer_bore_min_radius_lower_mm": bore_min, "core_shank_max_radius_upper_mm": shank_max,
            "radial_gap_lower_mm": radial, "axial_gap_lower_mm": axial,
            "strictly_separated_selected_surfaces": radial > 0 and axial > 0,
            "coordinate_rule": "Washer translated then .12g serialized; core node values unchanged",
            "quantization": quantization}


def cad_clearance(geometry_directory, context, translation=TRANSLATION_MM):
    import cadquery as cq

    directory = Path(geometry_directory)
    geometry_bytes = (directory / "geometry.json").read_bytes()
    geometry = json.loads(geometry_bytes)
    if hashlib.sha256(geometry_bytes).hexdigest() != context["input_sha256"]["geometry.json"]:
        raise ValueError("Geometry/context hash differs")
    if geometry.get("geometry_variant") != "locked-thread-fw38-minimum-bore-11-body":
        raise ValueError("Expected catalog-clearance geometry")
    origin = geometry["stitches"][0]["start_mm"]
    shapes, step_hashes = {}, {}
    for role in ("bolt_nut", "washer_inner"):
        name = "leg_stitch_right_1_" + role + ".step"
        path = directory / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != geometry["step_sha256"][name]:
            raise ValueError("STEP hash differs")
        step_hashes[name] = geometry["step_sha256"][name]
        shapes[role] = cq.importers.importStep(str(path)).val().translate(tuple(-v for v in origin))
    core, washer = shapes["bolt_nut"], shapes["washer_inner"]
    posed = washer.translate(translation)
    if not posed.isValid() or len(posed.Solids()) != 1 or abs(posed.Volume() - washer.Volume()) > 1e-6:
        raise ValueError("Invalid rigid CAD pose")
    overlap = posed.intersect(core).Volume()
    distance = posed.distance(core)
    axial = translation[0]
    eccentricity = math.hypot(*translation[1:])
    radial = 5.4991 - 4.7625 - eccentricity
    if overlap > 1e-6 or min(axial, radial) <= 0 or not math.isclose(distance, min(axial, radial), abs_tol=1e-6):
        raise ValueError("CAD overlap or nominal gap disagreement")
    if eccentricity + 9 >= 12.7 or eccentricity + 4.7625 >= 5.4991:
        raise ValueError("Proposed bearing-containment derivation does not apply")
    # Plane-face intersection after removing axial offset measures projected bearing.
    head = [f for f in core.Faces() if f.geomType() == "PLANE" and abs(f.Center().x) < 1e-6]
    bearing = [f for f in posed.Faces() if f.geomType() == "PLANE" and abs(f.Center().x - axial) < 1e-6]
    if len(head) != 1 or len(bearing) != 1:
        raise ValueError("Ambiguous CAD bearing face")
    area = head[0].intersect(bearing[0].translate((-axial, 0, 0))).Area()
    expected = math.pi * (9**2 - 5.4991**2)
    if not math.isclose(area, expected, rel_tol=1e-7):
        raise ValueError("Projected bearing area differs")
    if (directory / "geometry.json").read_bytes() != geometry_bytes or any(
            hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest for name, digest in step_hashes.items()):
        raise ValueError("CAD inputs changed during preflight")
    return {"cadquery_version": cq.__version__, "overlap_volume_mm3": overlap, "CAD_min_distance_mm": distance,
            "geometry_sha256": hashlib.sha256(geometry_bytes).hexdigest(), "step_sha256": step_hashes,
            "nominal_axial_gap_mm": axial, "nominal_radial_gap_mm": radial,
            "projected_head_bearing_area_mm2": area,
            "nominal_constant_velocity_engagement_time_s": {"head": axial / 100, "bore": radial / 100},
            "engagement_scope": "Kinematic undeformed extrapolation for V=(-100,+100,0) mm/s, not a contact event prediction"}


def preflight(geometry_directory, prepared_directory):
    before = source_snapshot()
    prepared = Path(prepared_directory)
    data = (prepared / "context.json").read_bytes()
    freeze_bytes = (prepared / "freeze.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    if hashlib.sha256(data).hexdigest() != freeze["files_sha256"]["context.json"]:
        raise ValueError("Prepared context hash differs")
    context = json.loads(data)
    for name, expected in freeze["files_sha256"].items():
        if hashlib.sha256((prepared / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Prepared evidence hash differs")
    deck = (prepared / "quiescent.inp").read_bytes()
    if hashlib.sha256(deck).hexdigest() != context["deck_sha256"]["quiescent"]:
        raise ValueError("Prepared deck hash differs")
    retained.actual_mesh(deck.decode(), context)
    report = {"status": "POSE GEOMETRY ONLY; NO SOLVER", "translation_local_mm": TRANSLATION_MM,
            "CAD": cad_clearance(geometry_directory, context), "quadratic_mesh": mesh_clearance(context),
            "limits": "Selected interface separation only; no contact search/normal/enforcement, dynamics, material or strength qualification. Nominal geometry, not purchased tolerances."}
    if source_snapshot() != before or (prepared / "freeze.json").read_bytes() != freeze_bytes:
        raise ValueError("Source or freeze changed during preflight")
    for name, expected in freeze["files_sha256"].items():
        if hashlib.sha256((prepared / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Prepared evidence changed during preflight")
    report["prepared_freeze_sha256"] = hashlib.sha256(freeze_bytes).hexdigest()
    report["source_sha256"] = {name: hashlib.sha256(b).hexdigest() for name, b in before.items()}
    report["context_sha256"] = hashlib.sha256(data).hexdigest()
    return report


def write_preflight(geometry_directory, prepared_directory, parent):
    before = source_snapshot()
    report = preflight(geometry_directory, prepared_directory)
    original = (Path(prepared_directory) / "context.json").read_bytes()
    if hashlib.sha256(original).hexdigest() != report["context_sha256"]:
        raise ValueError("Original context changed before publication")
    nodes, metadata = posed_nodes(json.loads(original))
    node_bytes = (json.dumps({"nodes": nodes, "quantization": metadata}, indent=2, allow_nan=False) + "\n").encode()
    if source_snapshot() != before:
        raise ValueError("Pose source changed before publication")
    report["posed_nodes_sha256"] = hashlib.sha256(node_bytes).hexdigest()
    Path(parent).mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="moving-pose-", dir=parent))
    (directory / "original-context.json").write_bytes(original)
    (directory / "posed-nodes.json").write_bytes(node_bytes)
    for name, data in before.items():
        (directory / (name + ".snapshot")).write_bytes(data)
    (directory / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry_directory", type=Path)
    parser.add_argument("prepared_directory", type=Path)
    parser.add_argument("--output", type=Path, help="Optional parent for a unique frozen pose preflight; no deck or solver")
    args = parser.parse_args()
    print(write_preflight(args.geometry_directory, args.prepared_directory, args.output) if args.output else
          json.dumps(preflight(args.geometry_directory, args.prepared_directory), indent=2, allow_nan=False))
