"""Extract nodal histories and named node groups with pinned MEDCoupling."""

import argparse
import json
import re

import medcoupling as mc


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("med_file")
parser.add_argument("--node-group", action="append", default=[])
parser.add_argument("--all-singleton-groups", action="store_true",
                    help="Also extract every source-ID group named N followed by digits")
args = parser.parse_args()
meshes = mc.GetMeshNames(args.med_file)
assert len(meshes) == 1, meshes
mesh = mc.MEDFileUMesh(args.med_file)
groups = {}
available = mesh.getGroupsOnSpecifiedLev(1)
requested = list(args.node_group)
if args.all_singleton_groups:
    requested.extend(name for name in available if re.fullmatch(r"N\d+", name))
    requested.extend(name for name in ("PHYS_NODES", "CARRIER_NODES", "NREF", "NROT")
                     if name in available)
for name in dict.fromkeys(requested):
    assert name in available, (name, available)
    groups[name] = mesh.getGroupArr(1, name).toNumPyArray().tolist()
    if re.fullmatch(r"N\d+", name):
        assert len(groups[name]) == 1, (name, groups[name])
fields, coordinates = {}, None
for name in mc.GetAllFieldNames(args.med_file):
    if not name.endswith(("DEPL", "VITE", "ACCE")):
        continue
    states = []
    for iteration, order, time in mc.GetAllFieldIterations(args.med_file, name):
        field = mc.ReadFieldNode(args.med_file, meshes[0], 0, name, iteration, order)
        array = field.getArray()
        xyz = field.getMesh().getCoords().toNumPyArray().tolist()
        if coordinates is None:
            coordinates = xyz
        assert coordinates == xyz
        states.append({"iteration": iteration, "order": order, "time": time,
                       "components": array.getInfoOnComponents(),
                       "values": array.toNumPyArray().tolist()})
    fields[name] = states
assert coordinates is not None and fields
for name, indices in groups.items():
    assert len(indices) == len(set(indices))
    assert all(0 <= index < len(coordinates) for index in indices)
print(json.dumps({"mesh": meshes[0], "coordinates": coordinates,
                  "node_groups": groups, "fields": fields}, allow_nan=False))
