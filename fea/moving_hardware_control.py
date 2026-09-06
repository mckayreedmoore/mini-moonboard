"""Prepare two free hardware bodies and two frictionless penalty pairs; no solver."""
import argparse
import hashlib
import json
import math
import sys
import tempfile
import types
from pathlib import Path

from fea import dynamic_momentum
from fea.floor_contact import mesh, node_set
from fea.stitch_joint_mesh import external_faces, geometry_names, validate_ownership

_SOURCE_HASHES_AT_IMPORT = {
    name: hashlib.sha256(Path(__file__).resolve().with_name(name).read_bytes()).hexdigest()
    for name in ("moving_hardware_control.py", "floor_contact.py", "stitch_joint_mesh.py", "dynamic_momentum.py")
}

STATION = "leg_stitch_right_1"
BODY_NAMES = {"BOLT_NUT": STATION + "_bolt_nut", "WASHER": STATION + "_washer_inner"}
RADIUS = 4.7625
CATALOG_WASHER_RADIUS = 10.9982 / 2
CAD_TOLERANCE_MM = 1e-5
AREA_RELATIVE_TOLERANCE = 1e-7
COORDINATE_FORMAT = ".12g"
QUANTIZATION_BOUND_MM = 5e-10
MATERIAL = {"youngs_modulus_N_mm2": 210000., "poisson_ratio": .3, "density_tonne_mm3": 7.85e-9,
            "scope": "Generic elastic steel assumption, not measured properties or capacity"}
CASE_SETTINGS = {"initial_dt_s": 1e-8, "max_dt_s": 1e-7, "min_dt_s": 1e-11, "total_time_s": 2e-6,
                 "maximum_increment_count": 1000, "alpha": 0.}
SURFACE_SPECS = {
    "WASHER_HEAD": ("WASHER", "Plane", (0., -12.7, -12.7, 0., 12.7, 12.7), math.pi*(12.7**2-RADIUS**2)),
    "CORE_HEAD": ("BOLT_NUT", "Plane", (0., -9., -9., 0., 9., 9.), math.pi*(9**2-RADIUS**2)),
    "WASHER_BORE": ("WASHER", "Cylinder", (0., -RADIUS, -RADIUS, 2., RADIUS, RADIUS), 2*math.pi*RADIUS*2),
    "CORE_SHANK": ("BOLT_NUT", "Cylinder", (0., -RADIUS, -RADIUS, 42.1, RADIUS, RADIUS), 2*math.pi*RADIUS*42.1),
}


def declared_configuration():
    return json.dumps({"station": STATION, "body_names": BODY_NAMES, "radius": RADIUS,
                       "catalog_washer_radius": CATALOG_WASHER_RADIUS,
                       "cad_tolerance": CAD_TOLERANCE_MM, "area_tolerance": AREA_RELATIVE_TOLERANCE,
                       "material": MATERIAL, "cases": CASE_SETTINGS, "surfaces": SURFACE_SPECS,
                       "coordinate_format": COORDINATE_FORMAT, "quantization_bound_mm": QUANTIZATION_BOUND_MM}, sort_keys=True)


_CONFIGURATION_AT_IMPORT = declared_configuration()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_snapshot():
    """Bind imported code to this checkout before preparing any result."""
    root = Path(__file__).resolve().parent
    if declared_configuration() != _CONFIGURATION_AT_IMPORT:
        raise ValueError("Declared configuration changed after module import")
    paths = [root / name for name in ("moving_hardware_control.py", "floor_contact.py", "stitch_joint_mesh.py", "dynamic_momentum.py")]
    snapshots = {}
    for path in paths:
        module = sys.modules[__name__] if path == Path(__file__).resolve() else sys.modules["fea." + path.stem]
        if Path(module.__file__).resolve() != path:
            raise ValueError("Imported source outside this checkout: " + path.name)
        data = path.read_bytes()
        if digest(data) != _SOURCE_HASHES_AT_IMPORT[path.name]:
            raise ValueError("Source bytes changed after module import: " + path.name)
        compiled = compile(data, str(path), "exec")
        expected = {code.co_name: code for code in compiled.co_consts
                    if isinstance(code, types.CodeType) and code.co_name.isidentifier()}
        for name, code in expected.items():
            loaded = getattr(module, name, None)
            if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                raise ValueError("Loaded code differs from source snapshot: " + path.name)
        snapshots[path.name] = data
    test = root.parent / "tests/test_moving_hardware_control.py"
    snapshots[test.name] = test.read_bytes()
    for module_name, bindings in (("fea.floor_contact", (mesh, node_set)),
                                  ("fea.stitch_joint_mesh", (external_faces, geometry_names, validate_ownership))):
        if any(getattr(sys.modules[module_name], function.__name__, None) is not function for function in bindings):
            raise ValueError("Imported helper binding differs from source module")
    return snapshots


def bounds(points):
    return [fn(p[a] for p in points) for fn in (min, max) for a in range(3)]


def quantize_coordinates(local):
    # CalculiX 2.21 nodes.f:140/150/160 reads only (1:20) with f20.0.
    # Raw repr can truncate an exponent; .12g fits all finite float fields.
    quantized = {n: tuple(float(format(v, COORDINATE_FORMAT)) for v in p) for n, p in local.items()}
    error = max(abs(v-quantized[n][a]) for n, p in local.items() for a, v in enumerate(p))
    if not math.isfinite(error) or error > QUANTIZATION_BOUND_MM:
        raise ValueError("Coordinate quantization exceeds the declared error bound")
    return quantized, {"format": COORDINATE_FORMAT, "native_reader_field_width": 20,
                       "max_abs_component_error_mm": error, "maximum_allowed_error_mm": QUANTIZATION_BOUND_MM,
                       "original_coordinates": "Unmodified global coordinates retained in frozen/mesh.inp",
                       "scope": "Decimal roundoff after station translation; these same quantized coordinates define deck and reference mass"}


def surface_specs(washer_radius=RADIUS):
    """Keep the shank/head stencil fixed while changing only the washer bore."""
    specs = dict(SURFACE_SPECS)
    specs["WASHER_HEAD"] = ("WASHER", "Plane", (0., -12.7, -12.7, 0., 12.7, 12.7), math.pi*(12.7**2-washer_radius**2))
    specs["WASHER_BORE"] = ("WASHER", "Cylinder", (0., -washer_radius, -washer_radius, 2., washer_radius, washer_radius), 4*math.pi*washer_radius)
    return specs


def select_surface(label, body, xyz, elements, origin, *, washer_radius=RADIUS):
    """Match complete CAD surface groups by type, bounds, area and all TRI6 nodes."""
    role, kind, expected_bounds, area = surface_specs(washer_radius)[label]
    inner_radius = washer_radius if role == "WASHER" else RADIUS
    matches = []
    for tag, surface in body["surfaces"].items():
        local_bounds = [v-origin[i % 3] for i, v in enumerate(surface["cad_bounds_mm"])]
        if (surface["cad_type"] == kind and len(local_bounds) == 6 and
                all(math.isfinite(v) and abs(v-e) <= CAD_TOLERANCE_MM for v, e in zip(local_bounds, expected_bounds)) and
                math.isclose(surface["cad_area_mm2"], area, rel_tol=AREA_RELATIVE_TOLERANCE)):
            matches.append((tag, surface))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one CAD surface for {label}; found {len(matches)}")
    tag, surface = matches[0]
    exterior = {(e, f): ids for e, f, ids in external_faces({e: elements[e] for e in body["elements"]}).values()}
    faces = [tuple(pair) for pair in surface["faces"]]
    if not faces or len(set(faces)) != len(faces) or any(face not in exterior for face in faces):
        raise ValueError("Contact surface must contain unique exterior faces")
    used = {n for face in faces for n in exterior[face]}
    if len(surface["nodes"]) != len(set(surface["nodes"])) or set(surface["nodes"]) != used:
        raise ValueError("Contact surface must include every TRI6 node, including midsides")
    def on_stencil(n):
        p = tuple(x-origin[a] for a, x in enumerate(xyz[n]))
        radial = math.hypot(p[1], p[2])
        if not all(math.isfinite(x) for x in p):
            raise ValueError("Nonfinite contact coordinates")
        if kind == "Plane":
            return abs(p[0]) <= CAD_TOLERANCE_MM and inner_radius-CAD_TOLERANCE_MM <= radial <= expected_bounds[4]+CAD_TOLERANCE_MM
        return abs(radial-inner_radius) <= CAD_TOLERANCE_MM and -CAD_TOLERANCE_MM <= p[0] <= expected_bounds[3]+CAD_TOLERANCE_MM
    if not all(on_stencil(n) for n in used):
        raise ValueError("TRI6 node is off the selected " + ("annular plane" if kind == "Plane" else "cylinder"))
    complete = {face for face, ids in exterior.items() if all(on_stencil(n) for n in ids)}
    if set(faces) != complete:
        raise ValueError("Contact surface omits matching exterior TRI6 faces")
    return {"body": role, "source_surface": tag, "cad_type": kind,
            "cad_bounds_mm_global": surface["cad_bounds_mm"], "cad_bounds_mm_local": list(expected_bounds),
            "cad_area_mm2": surface["cad_area_mm2"], "faces": [list(face) for face in faces], "nodes": sorted(used)}


def build_context(mesh_text, mesh_record, geometry_record):
    names = geometry_names(geometry_record)
    catalog = geometry_record.get("catalog_washer_bore", False)
    if type(catalog) is not bool:
        raise ValueError("catalog_washer_bore must be a boolean")
    washer_radius = CATALOG_WASHER_RADIUS if catalog else RADIUS
    if geometry_record.get("locked_threads") is not True or len(names) != 11:
        raise ValueError("Exactly eleven explicitly locked-thread geometry bodies required")
    if (mesh_record.get("locked_threads") is not True or mesh_record.get("body_count") != 11 or
            set(mesh_record["bodies"]) != set(names) or mesh_record.get("status") != "VERIFIED MESH ONLY; NO SOLVER"):
        raise ValueError("Verified locked-thread eleven-body mesh required")
    if digest(mesh_text.encode()) != mesh_record["mesh_sha256"]:
        raise ValueError("Frozen eleven-body mesh hash differs")
    xyz, elements = mesh(mesh_text)
    validate_ownership(xyz, elements, mesh_record["bodies"])
    stations = [s for s in geometry_record["stitches"] if s["name"] == STATION]
    if len(stations) != 1:
        raise ValueError("Unique station1 geometry required")
    station = stations[0]
    if catalog and (geometry_record.get("geometry_variant") != "locked-thread-fw38-minimum-bore-11-body" or
                    station.get("washer_bore_diameter_mm") != 2*CATALOG_WASHER_RADIUS):
        raise ValueError("Expected explicit FW38 minimum-bore geometry")
    if (station["axis"] != [1., 0., 0.] or not math.isclose(station["shank_diameter_mm"], 2*RADIUS, abs_tol=1e-10) or
            not math.isclose(station["grip_mm"], 38.1, abs_tol=1e-10) or not math.isclose(station["length_mm"], 57.15, abs_tol=1e-10)):
        raise ValueError("Station geometry does not match the declared surface stencil")
    origin = station["start_mm"]
    if len(origin) != 3 or not all(map(math.isfinite, origin)):
        raise ValueError("Finite station origin required")
    bodies = {role: {**mesh_record["bodies"][name], "source_name": name} for role, name in BODY_NAMES.items()}
    for body in bodies.values():
        if any(not math.isfinite(body[key]) or body[key] <= 0 for key in ("min_sampled_jacobian", "min_integration_jacobian")):
            raise ValueError("Positive mesh Jacobian evidence required")
        if not math.isclose(body["mesh_volume_mm3"], body["cad_volume_mm3"], rel_tol=.001):
            raise ValueError("Mesh volume differs from CAD")
    surfaces = {name: select_surface(name, bodies[spec[0]], xyz, elements, origin, washer_radius=washer_radius)
                for name, spec in surface_specs(washer_radius).items()}
    for first, second in (("WASHER_HEAD", "WASHER_BORE"), ("CORE_HEAD", "CORE_SHANK")):
        if set(map(tuple, surfaces[first]["faces"])) & set(map(tuple, surfaces[second]["faces"])):
            raise ValueError("Bearing and cylindrical contact faces overlap")
    selected_nodes = {n for body in bodies.values() for n in body["nodes"]}
    selected_elements = {e: elements[e] for body in bodies.values() for e in body["elements"]}
    local = {n: tuple(x-origin[a] for a, x in enumerate(xyz[n])) for n in sorted(selected_nodes)}
    if any(not all(map(math.isfinite, p)) for p in local.values()):
        raise ValueError("Finite body coordinates required")
    local, quantization = quantize_coordinates(local)
    validate_ownership(local, selected_elements, bodies)
    for body in bodies.values():
        body["local_bounds_mm"] = bounds([local[n] for n in body["nodes"]])
        body["global_bounds_mm"] = geometry_record["parts"][body["source_name"]]["bounds_mm"]
    return {"status": "PREPARED ONLY; NO SOLVER OR OUTPUT QUALIFICATION", "station": STATION,
            "scope": "Two-body numerical moving-hardware control only; no wood, preload, physical validation or frame inference",
            "origin_mm_global": origin, "angular_reference_mm_local": [1., 0., 0.],
            "washer_bore_diameter_mm": 2*washer_radius,
            "nominal_washer_shank_radial_clearance_mm": washer_radius-RADIUS,
            "geometry_variant": geometry_record.get("geometry_variant", "locked-thread-11-body"),
            "coordinate_transform": "Local XYZ = global XYZ minus station start, then .12g decimal quantization within the recorded bound; no intended physical geometry change",
            "coordinate_quantization": quantization,
            "nodes": local, "elements": selected_elements, "bodies": bodies, "surfaces": surfaces,
            "global_bounds_mm": bounds([xyz[n] for n in selected_nodes]), "material": MATERIAL,
            "contact_pairs": [{"slave": slave, "master": master, "normal_penalty_n_mm3": 1e5,
                               "formulation": "ordinary surface-to-surface penalty", "friction": 0.}
                              for slave, master in (("WASHER_HEAD", "CORE_HEAD"), ("WASHER_BORE", "CORE_SHANK"))],
            "cases": {name: {**CASE_SETTINGS, "initial_velocity_mm_s": {"BOLT_NUT": [0., 0., 0.], "WASHER": list(v)}}
                      for name, v in (("quiescent", (0., 0., 0.)), ("moving", (-100., 100., 0.)))
                      if not catalog or name == "quiescent"},
            "diagnostic_reference_scales": {"status": "FORMULAS ONLY; native washer mass not yet integrated or output-qualified",
                "washer_mass": "mW = reference CalculiX2.21 four-point mass, density7.85e-9 tonne/mm3",
                "P_star_tonne_mm_s": "mW*sqrt(100**2+100**2)", "E_star_N_mm": "0.5*mW*(100**2+100**2)",
                "H_star_tonne_mm2_s": "57.15*P_star"},
            "quiescent_diagnostic_gates": {"status": "PREDECLARED NUMERICAL DIAGNOSTICS; not qualified",
                "max_displacement_mm": 1e-6, "max_velocity_mm_s": .01,
                "max_total_ELSE_ELKE_CELS_over_E_star": 1e-4, "max_each_pair_cumulative_impulse_over_P_star": 1e-4,
                "max_normal_penetration_mm": 1e-6},
            "time_step_basis": "maxdt1e-7s retained for the quiet diagnostic; not a qualified stability or accuracy limit. Positive bore clearance requires a separately designed moving fixture/event before two-interface qualification.",
            "next_comparison": "No half-dt or extended-duration deck until first output qualification; no automatic reruns"}


def deck(context, case):
    if case not in ("quiescent", "moving") or case not in context["cases"]:
        raise ValueError("Only explicitly prepared qualification cases may be emitted")
    settings = context["cases"][case]
    elements = {int(e): ids for e, ids in context["elements"].items()}
    lines = ["*HEADING", "Two free hardware bodies; numerical control only", "*NODE"]
    lines += [str(n) + "," + ",".join(format(v, COORDINATE_FORMAT) for v in p) for n, p in context["nodes"].items()]
    for name, body in context["bodies"].items():
        lines += [f"*ELEMENT,TYPE=C3D10,ELSET={name}"]
        lines += [str(e) + "," + ",".join(map(str, elements[e])) for e in body["elements"]]
        lines += node_set(name, body["nodes"])
        lines += [f"*SOLID SECTION,ELSET={name},MATERIAL=STEEL"]
    lines += ["*MATERIAL,NAME=STEEL", "*ELASTIC", "210000.,0.3", "*DENSITY", "7.85e-9",
              "*SURFACE INTERACTION,NAME=FRICTIONLESS", "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR", "100000."]
    for name, surface in context["surfaces"].items():
        lines += [f"*SURFACE,NAME={name}"] + [f"{e},S{f}" for e, f in surface["faces"]]
    for pair in context["contact_pairs"]:
        lines += ["*CONTACT PAIR,INTERACTION=FRICTIONLESS,TYPE=SURFACE TO SURFACE", f"{pair['slave']},{pair['master']}"]
    lines += ["*INITIAL CONDITIONS,TYPE=VELOCITY"]
    for name, body in context["bodies"].items():
        lines += [f"{n},{axis},{value!r}" for n in body["nodes"]
                  for axis, value in enumerate(settings["initial_velocity_mm_s"][name], 1)]
    lines += [f"*STEP,NLGEOM,INC={settings['maximum_increment_count']}", "*DYNAMIC,ALPHA=0",
              ",".join(repr(settings[key]) for key in ("initial_dt_s", "total_time_s", "min_dt_s", "max_dt_s"))]
    for name in context["bodies"]:
        lines += [f"*NODE PRINT,NSET={name},FREQUENCY=1", "U,V",
                  f"*EL PRINT,ELSET={name},FREQUENCY=1,TOTALS=ONLY", "ELKE,EMAS,ELSE"]
    lines += ["*NODE FILE,FREQUENCY=1", "U,V", "*CONTACT FILE,FREQUENCY=1", "CDIS,CSTR",
              "*CONTACT PRINT,FREQUENCY=1,TOTALS=YES", "CDIS,CSTR,CELS,CNUM"]
    for pair in context["contact_pairs"]:
        lines += [f"*CONTACT PRINT,SLAVE={pair['slave']},MASTER={pair['master']},FREQUENCY=1", "CF"]
    return "\n".join(lines + ["*END STEP"]) + "\n"


def prepare(mesh_directory, geometry_path, parent=Path("fea/generated/moving-hardware-controls"), *, integrate_reference=False):
    sources = source_snapshot()
    mesh_directory, geometry_path = Path(mesh_directory), Path(geometry_path)
    inputs = {"mesh.inp": (mesh_directory / "mesh.inp").read_bytes(),
              "mesh.json": (mesh_directory / "mesh.json").read_bytes(), "geometry.json": geometry_path.read_bytes()}
    mesh_record, geometry_record = json.loads(inputs["mesh.json"]), json.loads(inputs["geometry.json"])
    if mesh_record["geometry_sha256"] != digest(inputs["geometry.json"]):
        raise ValueError("Mesh geometry hash differs from provided geometry")
    context = build_context(inputs["mesh.inp"].decode(), mesh_record, geometry_record)
    if integrate_reference:
        washer = context["bodies"]["WASHER"]
        blocks = dynamic_momentum.calculix_221_mass(
            {e: context["elements"][e] for e in washer["elements"]},
            {n: context["nodes"][n] for n in washer["nodes"]}, MATERIAL["density_tonne_mm3"])
        mass = math.fsum(math.fsum(map(math.fsum, block)) for _, block in blocks.values())
        if not math.isfinite(mass) or mass <= 0:
            raise ValueError("Positive finite native reference washer mass required")
        momentum_scale = mass*math.hypot(100, 100)
        context["diagnostic_reference_scales"] = {
            "status": "SOURCE-RECONSTRUCTED REFERENCE SCALES; no contact output qualification",
            "formulae": context["diagnostic_reference_scales"], "reference_mass_tonne": mass,
            "P_star_tonne_mm_s": momentum_scale, "E_star_N_mm": .5*mass*(100**2+100**2),
            "H_star_tonne_mm2_s": 57.15*momentum_scale}
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="control-", dir=parent)).resolve()
    frozen = directory / "frozen"
    frozen.mkdir()
    for name, data in {**inputs, **sources}.items():
        (frozen / name).write_bytes(data)
    context.update(input_sha256={name: digest(data) for name, data in inputs.items()},
                   source_sha256={name: digest(data) for name, data in sources.items()})
    context["deck_sha256"] = {}
    for case in context["cases"]:
        data = deck(context, case).encode()
        (directory / (case + ".inp")).write_bytes(data)
        context["deck_sha256"][case] = digest(data)
    (directory / "context.json").write_text(json.dumps(context, indent=2, allow_nan=False) + "\n")
    if source_snapshot() != sources:
        raise ValueError("Source changed during preparation; retained outputs are not launch-qualified")
    (directory / "freeze.json").write_text(json.dumps({"status": context["status"],
        "files_sha256": {str(p.relative_to(directory)): digest(p.read_bytes()) for p in directory.rglob("*") if p.is_file()}}, indent=2) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh_directory", type=Path)
    parser.add_argument("geometry_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/moving-hardware-controls"))
    parser.add_argument("--integrate-reference", action="store_true", help="Cache source-derived washer mass/scales using Gmsh; no solver")
    args = parser.parse_args()
    print(prepare(args.mesh_directory, args.geometry_path, args.output, integrate_reference=args.integrate_reference))
