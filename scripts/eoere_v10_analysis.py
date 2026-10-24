"""Versioned v10 preparation and own six-case response using existing kernels.

Inventory and row routing are explicit v10 extensions. Frozen v9 records are
never rewritten. This adapter retains conditional bond, screw and floor laws.
"""
from __future__ import annotations

import argparse
import ast
import copy
import fcntl
import inspect
import json
import math
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import FunctionType
from unittest.mock import patch

import cadquery as cq
import numpy as np

from scripts import eoere_v6_analysis as v6
from scripts import eoere_v9_analysis as v9
from scripts import eoere_leg_header_mechanics as mechanics
from scripts.eoere_load_parameters import LoadParameters, parameterize_inputs
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
WORK = v9.WORK
SCHEMA = "eoere_v10_first_order_inputs/v1"
PHYSICAL_REVISION = "eoere-strengthened-bolt-cleat-v10"
REVISION = "eoere-v10-perfect-bond-four-host-analysis-v1"
HOSTS = v6.HOSTS
METAL_GRAVITY = v9.METAL_GRAVITY
require = v9.require
FROZEN_METHODS = {
    **v9.FROZEN_METHODS,
    "scripts/eoere_v9_analysis.py": "f2afcdeda0ef6d6d67fc5e04f5bb4d90990e1b0ae65dd81cfdd2f584da6e70c9",
    "scripts/eoere_load_parameters.py": "83edcc05b778fc677204d1cc39597cd3e2a739f32de4b0f67ce0c2a051bf2772",
}


def row_port(flange, transverse, row="far"):
    require(flange in ("beam", "post") and transverse in (-1, 1)
            and row in ("near", "far"), "explicit factory row/flange/sign required")
    return ("arm-x" if flange == "beam" else "arm-z") + "/" + row + ("-plus" if transverse == -1 else "-minus")


def verify_attachment_axes(axes, expected_ports):
    seen = set()
    for axis in axes:
        point, direction = np.asarray(axis["point_xyz_mm"]), np.asarray(axis["direction_xyz"])
        require(abs(float(direction @ direction)-1) < 1e-8, "unit shaft required")
        for a in axis["attachments"]:
            delta = np.asarray(a["point"])-point
            station = float(delta @ direction)
            require(np.linalg.norm(delta-station*direction) < 1e-6
                    and min(abs(station), abs(station-axis["grip_mm"])) < 1e-6,
                    "factory attachment off physical shaft: "+axis["id"])
            require(a["installed_bolt_axis_id"] == axis["id"], "attachment identity differs")
            key = (a["angle_id"], a["flange"], a.get("row", "far"), a["transverse"])
            require(key not in seen, "factory hole bound twice")
            seen.add(key)
    require(len(seen) == expected_ports, "complete row-aware port census required")


def inventory(geometry):
    shafts = len(geometry["axes"])
    ports = sum(len(a["attachments"]) for a in geometry["axes"])
    wood = sum(p["kind"] == "timber" for p in geometry["profiles"].values())
    fittings = len(geometry["fitting_poses"])
    walls = sum(len(a["receivers"]) for a in geometry["axes"])
    roles = sum(5+bool(a.get("nut_side_spacer_mm", 0)) for a in geometry["axes"])
    return dict(shafts=shafts, ports=ports, wood=wood, fittings=fittings,
                walls=walls, roles=roles, bodies=wood+fittings+shafts+6)


def replace_once(source, before, after):
    require(source.count(before) == 1, "frozen source hook differs: "+before[:100])
    return source.replace(before, after)


def verify_frozen_methods(pins=None):
    for path, expected in (pins or FROZEN_METHODS).items():
        require(sha(ROOT/path) == expected, "frozen method changed: "+path)


def generalized_validator(factory, data):
    """Retain numerical/ownership validation; replace only explicit census.

    Exact row-aware hole mappings are additionally checked against shafts.
    No tolerance, floor law, contact coefficient or load rule is relaxed.
    """
    count = dict(wood=len(data['timber_rows']), fittings=len(data['fitting_poses']),
                 shafts=len(data['shafts']), ports=len(data['fitting_port_bindings']),
                 roles=sum(len(a['metal_roles']) for a in data['shafts']))
    count['bodies']=count['wood']+count['fittings']+count['shafts']+len(data['panel_ids'])
    source=inspect.getsource(factory.validate_rows)
    replacements=[
        ('(22, 22, 100, 6, 150)', repr((count['wood'],count['fittings'],count['shafts'],6,count['bodies']))),
        ('len(data["factory_holes"]) == 176', f'len(data["factory_holes"]) == {8*count["fittings"]}'),
        ('sum(row["used"] for row in data["factory_holes"]) == 88', f'sum(row["used"] for row in data["factory_holes"]) == {count["ports"]}'),
        ('len(role_ids) == 500', f'len(role_ids) == {count["roles"]}'),
        ('all(len(row["metal_roles"]) == 5 for row in data["shafts"])', 'all(len(row["metal_roles"]) in (5,6) for row in data["shafts"])'),
        ('len(data["fitting_port_bindings"]) == 88', f'len(data["fitting_port_bindings"]) == {count["ports"]}'),
        ('len({(row["angle_id"], row["model_port_id"]) for row in data["fitting_port_bindings"]}) == 88', f'len({{(row["angle_id"], row["model_port_id"]) for row in data["fitting_port_bindings"]}}) == {count["ports"]}'),
    ]
    for old,new in replacements:source=replace_once(source,old,new)
    scope={**vars(factory),'SCHEMA':SCHEMA}
    exec(compile(source,str(OWN),'exec'),scope)
    original=scope['validate_rows']
    def validate(value, *, synthetic=False):
        result=original(value,synthetic=synthetic)
        if synthetic:return result
        physical_axes=[r['source_axis'] for r in value['shafts']]
        verify_attachment_axes(physical_axes,count['ports'])
        expected={(a['angle_id'],a['flange'],a.get('row','far'),a['transverse']):s['axis_id']
                  for s in value['shafts'] for a in s['source_axis']['attachments']}
        for hole in value['factory_holes']:
            key=(hole['angle_id'],hole['flange'],hole['row'],hole['transverse'])
            require(hole['installed_bolt_axis_id']==expected.get(key), 'factory row metadata differs')
        for row in value['fitting_port_bindings']:
            require(row['model_port_id']==row_port(row['source_flange'],row['source_transverse'],row['source_row']),
                    'near/far physical routing differs')
        return result
    return validate


def generalized_shafts(ex, count, namespace):
    source = inspect.getsource(ex.shafts)
    source = replace_once(source, "port_id(attachment['flange'], attachment['transverse'])",
                          "ROW_PORT(attachment['flange'], attachment['transverse'], attachment.get('row','far'))")
    source = replace_once(source, "len(result) == 100 and len(wall_rows) == 120 and sum(s['kind'] == 'steel' for a in result for s in a['surfaces']) == 88",
                          f"len(result) == {count['shafts']} and len(wall_rows) == {count['walls']} and sum(s['kind'] == 'steel' for a in result for s in a['surfaces']) == {count['ports']}")
    scope = {**vars(ex), **namespace, "ROW_PORT": row_port}
    exec(compile(source, str(OWN), "exec"), scope)
    return scope["shafts"]


def generalized_preparation_source(count):
    source = inspect.getsource(mechanics.prepare)
    replacements = [
        ("geometry['revision'] == 'eoere-single-leg-bolts-header-angles-v3'", "geometry['revision'] == "+repr(REVISION)),
        ("shaft_count, fitting_count, port_count, role_count = ((106, 26, 102, 556) if three_pin else\n        ((104, 26, 100, 544) if single_cleat else ((108, 26, 104, 568) if returned else (96, 24, 96, 496))))",
         "shaft_count, fitting_count, port_count, role_count = "+repr(tuple(count[k] for k in ("shafts","fittings","ports","roles")))),
        ("from scripts.eoere_leg_header_revision import verify_attachment_axes", "from scripts.eoere_v10_analysis import verify_attachment_axes"),
        ("if name.startswith(('base_post_outer_', 'eoere_cleat_')) or returned:", "if True:  # refresh every own gross profile"),
        ("expected_added = {'eoere_cleat_left_outer', 'eoere_cleat_right_outer'} if paired else set()", "expected_added = added  # explicit current geometry census bound by receipt"),
        ("'model_port_id': ex.port_id(a['flange'], a['transverse']),", "'model_port_id': ROW_PORT(a['flange'], a['transverse'], a.get('row','far')), 'source_row': a.get('row','far'),"),
        ("holes = [] if three_pin else copy.deepcopy(old['all_factory_holes'])", "holes = []"),
        ("binding = [r for r in ports if r['angle_id'] == pose['id'] and\n                       r['source_flange'] == hole['flange'] and r['source_transverse'] == hole['transverse']]", "binding = [r for r in ports if r['angle_id'] == pose['id'] and\n                       r['source_flange'] == hole['flange'] and r['source_transverse'] == hole['transverse'] and r['source_row'] == hole['row']]"),
        ("binding[0]['axis_id'] if hole['row'] == 'far' and binding else None", "binding[0]['axis_id'] if binding else None"),
        ("'schema': SCHEMA", "'schema': V10_SCHEMA"),
    ]
    for before, after in replacements:
        source = replace_once(source, before, after)
    start = source.index("    shaft_function, edits = changed_function(ex, 'shafts'")
    end = source.index("    with patch.object(ex, 'role_rows'", start)
    source = source[:start]+"    shaft_function = V10_SHAFTS(ex, V10_COUNTS, {'role_rows': lambda a, method, volumes: response.spacer_roles(a, method, volumes, role_original), 'end_seats': lambda a, surfaces, method: response.spacer_ends(a, surfaces, method, ends_original)})\n"+source[end:]
    source = replace_once(source,
        "    else:\n        bodies, observations, import_proof = exporter.import_current(ex, report, panels, pins, q)",
        "    else:\n        importer, _ = changed_function(ex, 'import_cached', {28: "+str(count['wood']+6)+"})\n        with patch.object(ex, 'import_cached', importer):\n            bodies, observations, import_proof = exporter.import_current(ex, report, panels, pins, q)")
    return source


def floor_method(body_count):
    floor = v6.floor_method()
    # Recompile original reader with the actual v10 body census.
    original = (WORK / "owner_laminated_floor.py").read_text()
    tree = ast.parse(original)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "read")
    function = ast.unparse(node)
    function = replace_once(function, "closure['physical_body_count'] == 144", f"closure['physical_body_count'] == {body_count}")
    scope = {**vars(floor), "OWN": OWN}
    exec(compile(function, str(OWN), "exec"), scope)
    floor.read = scope["read"]
    floor.OUT = RUN
    floor.laminated.MATERIAL = MATERIAL
    return floor


def context(receipt_path, base):
    receipt_path = Path(receipt_path).resolve()
    require(receipt_path.is_relative_to(ROOT), "repository receipt required")
    receipt = json.loads(receipt_path.read_bytes())
    require(receipt.get("fabrication_released") is False and receipt.get("climbing_released") is False,
            "conditional geometry receipt required")
    physical_ref = receipt["checked_geometry"]
    require(sha(ROOT/physical_ref["path"]) == physical_ref["sha256"], "physical geometry bytes changed")
    geometry = json.loads((ROOT/physical_ref["path"]).read_bytes())
    global BASE, PHYSICAL, RECEIPT, GEOMETRY, MATERIAL, RUN, INPUTS, PHYSICAL_REVISION
    BASE, PHYSICAL, RECEIPT = Path(base).resolve(), ROOT/physical_ref["path"], receipt_path
    require(BASE.is_relative_to(WORK), "versioned ignored work area required")
    GEOMETRY, MATERIAL, RUN = BASE/"geometry/geometry.json", BASE/"material.json", BASE/"four-hosts"
    INPUTS = RUN/"preparation/inputs.json"
    PHYSICAL_REVISION = geometry["revision"]
    pins = dict(FROZEN_METHODS)
    for p,digest in pins.items():require(sha(ROOT/p) == digest,"frozen method changed: "+p)
    pins.update({ref(OWN)["path"]:sha(OWN), ref(receipt_path)["path"]:sha(receipt_path), **{physical_ref["path"]:physical_ref["sha256"]}})
    return {"receipt":ref(receipt_path),"physical_geometry":physical_ref,"source_sha256":pins,
            "count":inventory(geometry),"physical_clearance":receipt["checked_clearance"]}


def prepare(bindings):
    require(not BASE.exists(), "fresh attempt analysis directory required")
    count = bindings["count"]
    # Execute the unchanged union/material algorithm with explicit v10 identities
    # and the generalized preparation function above.
    source = inspect.getsource(v6.prepare)
    source = replace_once(source, '"d2849e0bb7e3751396854556fa0bb411d83f3cf94dec55ec157a582f4f5b6e80"', repr(bindings["receipt"]["sha256"]))
    source = replace_once(source, 'len(g["axes"]) == 96', f'len(g["axes"]) == {count["shafts"]}')
    source = replace_once(source, 'g["revision"] == "eoere-flat-cleats-principal-upper-pairs-v6"', 'g["revision"] == '+repr(PHYSICAL_REVISION))
    start = source.index('    source = inspect.getsource(mechanics.prepare)')
    end = source.index('    namespace = dict(vars(mechanics))', start)
    source = source[:start]+'    source = generalized_preparation_source(INVENTORY)\n'+source[end:]
    source = replace_once(source, 'namespace = dict(vars(mechanics))', 'namespace = {**vars(mechanics), "ROW_PORT":row_port,"V10_SHAFTS":generalized_shafts,"V10_COUNTS":INVENTORY,"V10_SCHEMA":SCHEMA}')
    source = replace_once(source, 'len(data["timber_rows"]) == 22 and len(data["shafts"]) == 96', f'len(data["timber_rows"]) == {count["wood"]-2} and len(data["shafts"]) == {count["shafts"]}')
    source = replace_once(source, 'len(data["finished_receiver_wall_queries"]) == 112', f'len(data["finished_receiver_wall_queries"]) == {count["walls"]-sum("eoere_cleat_" in r for a in json.loads(PHYSICAL.read_bytes())["axes"] for r in a["receivers"] if r.endswith("_outer"))}')
    source = replace_once(source, 'floor = floor_method()', 'floor = floor_method(INVENTORY["bodies"])')
    source = replace_once(source, 'data = parameterize_inputs(data, LoadParameters(weight=250, unit="lb"))', 'data = parameterize_inputs(data, LoadParameters(weight=250, unit="lb"))\n    data["source_sha256"].update(SOURCE_PINS)')
    source = replace_once(source, 'pins = {ref(OWN)["path"]: sha(OWN)}', 'pins = dict(SOURCE_PINS)')
    # Analysis plywood unions reduce two physical leaf hosts; use that census.
    analysis_count = dict(count)
    analysis_count["wood"] -= 2
    analysis_count["bodies"] -= 2
    physical = json.loads(PHYSICAL.read_bytes())
    analysis_count["walls"] -= sum(r.endswith("_outer") and r.startswith("eoere_cleat_") for a in physical["axes"] for r in a["receivers"])
    scope={**vars(v6), **globals(), "INVENTORY":analysis_count,"SOURCE_PINS":bindings["source_sha256"]}
    # Source's post-union assertions should use the analysis rather than physical census.
    source = source.replace(f'{count["wood"]-2} and len(data["shafts"])', f'{analysis_count["wood"]} and len(data["shafts"])')
    exec(compile(source,str(OWN),"exec"),scope)
    scope["prepare"]()
    data=json.loads(INPUTS.read_bytes())
    require(data["schema"] == SCHEMA, "own v10 schema required")
    snapshots={}
    for name in bindings["source_sha256"]:
        p=ROOT/name
        if p.suffix == ".py":
            target=BASE/(p.stem+"-method-snapshot.py")
            if not target.exists():target.write_bytes(p.read_bytes())
            snapshots[name]=ref(target)
    mechanics.write(BASE/"adapter-readiness.json",{**bindings,"analysis_revision":REVISION,
        "analysis_geometry":ref(GEOMETRY),"inputs":ref(INPUTS),"material":ref(MATERIAL),
        "analysis_inventory":analysis_count,"frozen_method_snapshots":snapshots,
        "load_contract":{"weight_lb":250,"downward_multiplier":2,"horizontal_force_N":300,"accessory_mass_kg":25,"duration_factor_CD":1},
        "producer":ref(OWN),"structural_acceptance":False,"fabrication_released":False,"climbing_released":False})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare",*CASES))
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    with (ROOT/"docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        bindings=context(args.receipt,args.out)
        if args.action=="prepare":prepare(bindings)
        else:raise NotImplementedError("eight-port execution binding pending independently verified operator")


if __name__=="__main__":main()
