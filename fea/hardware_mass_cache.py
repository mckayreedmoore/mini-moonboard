"""Cache per-element hardware mass operators; source-derived, not output-qualified."""
import argparse
import gzip
import hashlib
import json
import math
import sys
import tempfile
import types
from pathlib import Path

from fea import dynamic_momentum

LIMITS = "Source-derived untransformed native four-point and physical Gauss8 mass blocks only; no solver output, contact, momentum or strength qualification."
_PATHS = (Path(__file__).resolve(), Path(__file__).resolve().with_name("dynamic_momentum.py"))
_HASHES = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in _PATHS}
_LIMITS_AT_IMPORT = LIMITS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    if LIMITS != _LIMITS_AT_IMPORT:
        raise ValueError("Mass-cache configuration changed after import")
    result = {}
    for path, module in zip(_PATHS, (sys.modules[__name__], dynamic_momentum), strict=True):
        if Path(module.__file__).resolve() != path:
            raise ValueError("Imported mass-cache source outside this checkout")
        data = path.read_bytes()
        if sha(data) != _HASHES[path.name]:
            raise ValueError("Mass-cache source changed after import")
        for code in compile(data, str(path), "exec").co_consts:
            if isinstance(code, types.CodeType) and code.co_name.isidentifier():
                loaded = getattr(module, code.co_name, None)
                if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                    raise ValueError("Loaded mass-cache function differs from source")
        result[path.name] = data
    return result


def context_mesh(context):
    """Require exact disjoint body ownership and the serialized solver coordinates."""
    nodes = {int(n): tuple(p) for n, p in context["nodes"].items()}
    elements = {int(e): tuple(ids) for e, ids in context["elements"].items()}
    if len(nodes) != len(context["nodes"]) or len(elements) != len(context["elements"]):
        raise ValueError("Ambiguous numeric mesh identifiers")
    if (not nodes or not elements or any(n <= 0 for n in (*nodes, *elements))
            or any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in nodes.values())
            or any(len(ids) != 10 or len(set(ids)) != 10 or
                   any(type(n) is not int or n not in nodes for n in ids) for ids in elements.values())):
        raise ValueError("Invalid finite C3D10 mesh")
    bodies = context["bodies"]
    if set(bodies) != {"BOLT_NUT", "WASHER"}:
        raise ValueError("Exactly two hardware bodies required")
    used_nodes, used_elements = set(), set()
    for body in bodies.values():
        ids, ns = body["elements"], body["nodes"]
        if (not ids or any(type(e) is not int or e not in elements for e in ids)
                or any(type(n) is not int or n not in nodes for n in ns)
                or len(ids) != len(set(ids)) or len(ns) != len(set(ns))
                or set(ns) != {n for e in ids for n in elements[e]}
                or used_nodes.intersection(ns) or used_elements.intersection(ids)):
            raise ValueError("Incorrect or shared hardware ownership")
        used_nodes.update(ns)
        used_elements.update(ids)
    if used_nodes != set(nodes) or used_elements != set(elements):
        raise ValueError("Incomplete hardware mesh ownership")
    density = context["material"]["density_tonne_mm3"]
    if type(density) not in (int, float) or not math.isfinite(density) or density <= 0:
        raise ValueError("Positive finite density required")
    return nodes, elements, density


def deck_mesh(text, context):
    """Bind serialized mesh, two body sections and the actual shared density."""
    nodes, elements, mode = {}, {}, None
    owners, sections, materials, densities = {}, [], [], []
    owner = None
    for line in text.splitlines():
        if not line.strip() or line.startswith("**"):
            continue
        if line.startswith("*"):
            mode = "nodes" if line == "*NODE" else None
            if line.startswith("*ELEMENT"):
                allowed = {f"*ELEMENT,TYPE=C3D10,ELSET={name}": name for name in context["bodies"]}
                if line not in allowed or allowed[line] in owners:
                    raise ValueError("Actual element body assignment differs")
                owner = allowed[line]
                owners[owner] = []
                mode = "elements"
            elif line.split(",")[0].endswith(" SECTION"):
                sections.append(line)
            elif line.startswith("*MATERIAL"):
                materials.append(line)
            elif line.startswith("*DENSITY"):
                if line != "*DENSITY" or materials != ["*MATERIAL,NAME=STEEL"]:
                    raise ValueError("Actual density material assignment differs")
                densities.append([])
                mode = "density"
        elif mode:
            fields = line.split(",")
            if mode == "density":
                densities[-1].append(tuple(map(float, fields)))
                continue
            tag = int(fields[0])
            table = nodes if mode == "nodes" else elements
            if tag in table:
                raise ValueError("Duplicate serialized mesh tag")
            table[tag] = tuple(map(float if mode == "nodes" else int, fields[1:]))
            if mode == "elements":
                owners[owner].append(tag)
    expected_nodes, expected_elements, density = context_mesh(context)
    if nodes != expected_nodes or elements != expected_elements:
        raise ValueError("Serialized deck mesh differs from prepared context")
    if (set(owners) != set(context["bodies"])
            or any(set(ids) != set(context["bodies"][name]["elements"]) for name, ids in owners.items())
            or sorted(sections) != sorted(f"*SOLID SECTION,ELSET={name},MATERIAL=STEEL" for name in context["bodies"])
            or materials != ["*MATERIAL,NAME=STEEL"] or densities != [[(density,)]]):
        raise ValueError("Serialized deck body sections or density differ from context")


def validate_blocks(blocks, elements):
    """Check full symmetric blocks and Gmsh order; allow negative entries and rank four."""
    converted = {int(e): block for e, block in blocks.items()}
    if len(converted) != len(blocks) or set(converted) != set(elements):
        raise ValueError("Mass-block element inventory differs")
    masses = []
    for e, (ids, block) in converted.items():
        expected = tuple(elements[e][i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 8))
        if tuple(ids) != expected or any(type(n) is not int for n in ids):
            raise ValueError("Mass-block Gmsh connectivity differs")
        if len(block) != 10 or any(len(row) != 10 or not all(math.isfinite(v) for v in row) for row in block):
            raise ValueError("Finite full ten-by-ten block required")
        scale = max(abs(v) for row in block for v in row)
        if any(abs(block[i][j]-block[j][i]) > 1e-12*scale for i in range(10) for j in range(i)):
            raise ValueError("Mass block is not symmetric")
        mass = math.fsum(map(math.fsum, block))
        if not math.isfinite(mass) or mass <= 0:
            raise ValueError("Positive total element mass required")
        masses.append(mass)
    total = math.fsum(masses)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Positive finite body mass required")
    return total


def validate_cache(cache, context_bytes):
    context = json.loads(context_bytes)
    _, elements, density = context_mesh(context)
    if cache["context_sha256"] != sha(context_bytes) or cache["density_tonne_mm3"] != density:
        raise ValueError("Cache context/density binding differs")
    if set(cache["operators"]) != {"native_four_point", "physical_Gauss8"}:
        raise ValueError("Both declared mass operators required")
    result = {}
    for name, bodies in cache["operators"].items():
        if set(bodies) != set(context["bodies"]):
            raise ValueError("Mass-cache body inventory differs")
        result[name] = {body: validate_blocks(blocks, {e: elements[e] for e in context["bodies"][body]["elements"]})
                        for body, blocks in bodies.items()}
    return result


def build(context_path, parent=Path("fea/generated/hardware-mass-caches"), *, case="quiescent"):
    if type(case) is not str or case not in ("quiescent", "moving"):
        raise ValueError("Mass cache case must be quiescent or moving")
    before = sources()
    context_path = Path(context_path)
    data = context_path.read_bytes()
    freeze_bytes = (context_path.parent / "freeze.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    if freeze["files_sha256"][context_path.name] != sha(data):
        raise ValueError("Prepared context hash differs")
    context = json.loads(data)
    nodes, elements, density = context_mesh(context)
    deck_name = case + ".inp"
    if case not in context["deck_sha256"] or deck_name not in freeze["files_sha256"]:
        raise ValueError("Selected prepared case/deck is absent")
    deck_path = context_path.parent / deck_name
    deck_bytes = deck_path.read_bytes()
    if (freeze["files_sha256"][deck_name] != sha(deck_bytes)
            or context["deck_sha256"][case] != sha(deck_bytes)):
        raise ValueError("Prepared deck hash differs")
    deck_mesh(deck_bytes.decode(), context)
    import gmsh
    gmsh_version = gmsh.__version__
    if not isinstance(gmsh_version, str) or not gmsh_version.strip():
        raise ValueError("Installed Gmsh version is unavailable")
    Path(parent).mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="mass-cache-", dir=parent))
    (directory / "context.json").write_bytes(data)
    (directory / "prepared-freeze.json").write_bytes(freeze_bytes)
    (directory / deck_name).write_bytes(deck_bytes)
    for name, source in before.items():
        (directory / (name + ".snapshot")).write_bytes(source)
    cache = {"status": "SOURCE-DERIVED MASS CACHE ONLY", "limits": LIMITS,
             "context_sha256": sha(data), "density_tonne_mm3": density,
             "gmsh_version": gmsh_version, "operators": {}}
    for operator, integrate in (("native_four_point", dynamic_momentum.calculix_221_mass),
                                ("physical_Gauss8", dynamic_momentum.consistent_mass)):
        cache["operators"][operator] = {}
        for name, body in context["bodies"].items():
            owned_elements = {e: elements[e] for e in body["elements"]}
            kwargs = {"integration_rule": "Gauss8"} if operator == "physical_Gauss8" else {}
            blocks = integrate(owned_elements, {n: nodes[n] for n in body["nodes"]}, density, **kwargs)
            validate_blocks(blocks, owned_elements)
            cache["operators"][operator][name] = blocks
    masses = validate_cache(cache, data)
    if (sources() != before or gmsh.__version__ != gmsh_version
            or context_path.read_bytes() != data or deck_path.read_bytes() != deck_bytes
            or (context_path.parent / "freeze.json").read_bytes() != freeze_bytes):
        raise ValueError("Source or prepared input changed during integration")
    payload = gzip.compress(json.dumps(cache, allow_nan=False, separators=(",", ":")).encode(), mtime=0)
    (directory / "blocks.json.gz").write_bytes(payload)
    report = {"status": cache["status"], "limits": LIMITS, "body_mass_tonne": masses,
              "gmsh_version": gmsh_version,
              "context_sha256": sha(data), "prepared_freeze_sha256": sha(freeze_bytes),
              "deck_sha256": sha(deck_bytes),
              "blocks_sha256": sha(payload), "source_sha256": {n: sha(b) for n, b in before.items()}}
    if case != "quiescent":
        report["case"] = case
    (directory / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/hardware-mass-caches"))
    parser.add_argument("--case", choices=("quiescent", "moving"), default="quiescent")
    args = parser.parse_args()
    print(build(args.context, args.output, case=args.case))
