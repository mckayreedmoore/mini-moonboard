"""Read nodal MED fields with the pinned image's MEDCoupling; no native solve."""

import json
import sys

import medcoupling as mc


path = sys.argv[1]
meshes = mc.GetMeshNames(path)
assert len(meshes) == 1, meshes
fields = {}
coordinates = None
for name in mc.GetAllFieldNames(path):
    if not name.endswith(("DEPL", "VITE", "ACCE")):
        continue
    states = []
    for iteration, order, time in mc.GetAllFieldIterations(path, name):
        field = mc.ReadFieldNode(path, meshes[0], 0, name, iteration, order)
        array = field.getArray()
        xyz = field.getMesh().getCoords().toNumPyArray().tolist()
        if coordinates is None:
            coordinates = xyz
        assert coordinates == xyz
        states.append({"iteration": iteration, "order": order, "time": time,
                       "components": array.getInfoOnComponents(),
                       "values": array.toNumPyArray().tolist()})
    fields[name] = states
print(json.dumps({"mesh": meshes[0], "coordinates": coordinates, "fields": fields}, allow_nan=False))
