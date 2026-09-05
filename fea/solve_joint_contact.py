"""Actual CalculiX frictionless pin/bore coupon, displacement controlled."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import gmsh
from joint_contact_results import job_name, number


def nset(name, tags):
    return [f'*NSET,NSET={name}', *(','.join(map(str, tags[i:i+16])) for i in range(0, len(tags), 16))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=float, default=8)
    parser.add_argument('--penalty', type=float, default=100000)
    parser.add_argument('--clearance', type=float, default=.2375)
    parser.add_argument('--direction', choices=('S', 'N'), default='S')
    args = parser.parse_args()
    if not (math.isfinite(args.size) and 0 < args.size <= 20 and math.isfinite(args.penalty)
            and args.penalty > 0 and math.isfinite(args.clearance) and 0 <= args.clearance < 1):
        parser.error('Invalid mesh, penalty or radial clearance')
    directory = Path('fea/generated/joint_contact')
    info = json.loads((directory/'geometry.json').read_text())
    if hashlib.sha256((directory/'leg.step').read_bytes()).hexdigest() != info['step_sha256']:
        raise ValueError('Changed frozen coupon')
    name = job_name(args.direction, args.size, args.penalty, args.clearance)
    prefix = directory/name
    gmsh.initialize()
    gmsh.option.setNumber('General.Verbosity', 2)
    gmsh.model.add(name)
    wood = gmsh.model.occ.importShapes(str(directory/'leg.step'))
    pins = [gmsh.model.occ.addCylinder(-2, y, 0, 42.1, 0, 0, 5-args.clearance)
            for y in info['stations_mm']]
    gmsh.model.occ.synchronize()
    gmsh.model.addPhysicalGroup(3, [tag for dim, tag in wood], 1)
    gmsh.model.setPhysicalName(3, 1, 'WOOD')
    for i, pin in enumerate(pins, 1):
        gmsh.model.addPhysicalGroup(3, [pin], i+1)
        gmsh.model.setPhysicalName(3, i+1, f'PIN{i}')
    gmsh.option.setNumber('Mesh.MeshSizeMax', args.size)
    gmsh.option.setNumber('Mesh.MeshSizeMin', args.size/4)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 32)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary', 0)
    gmsh.option.setNumber('Mesh.ElementOrder', 2)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize('HighOrder')
    types, tags3, conn3 = gmsh.model.mesh.getElements(3)
    if list(types) != [11]:
        raise ValueError('Expected quadratic tetrahedra')
    jacobian = min(float(v) for v in gmsh.model.mesh.getElementQualities(tags3[0], 'minDetJac'))
    if jacobian <= 0:
        raise ValueError('Nonpositive final Jacobian')
    tags, coords, _ = gmsh.model.mesh.getNodes()
    nodes = {int(t): tuple(float(v) for v in coords[i*3:i*3+3]) for i, t in enumerate(tags)}
    # Abaqus/CalculiX tetrahedron face IDs; corner triples identify each face.
    corners = ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0))
    faces = {}
    for i, tag in enumerate(tags3[0]):
        row = conn3[0][10*i:10*i+10]
        for face, inds in enumerate(corners, 1):
            key = tuple(sorted(int(row[j]) for j in inds))
            faces.setdefault(key, []).append((int(tag), face))
    surface = {}
    for label, volumes in [('WOOD', wood), *[(f'PIN{i}', [(3, pin)]) for i, pin in enumerate(pins, 1)]]:
        pairs = []
        for _, face in gmsh.model.getBoundary(volumes, oriented=False):
            if gmsh.model.getType(2, face) != 'Cylinder':
                continue
            types2, _, conn2 = gmsh.model.mesh.getElements(2, face)
            for kind, flat in zip(types2, conn2, strict=True):
                if kind != 9:
                    raise ValueError('Expected quadratic surface triangles')
                for i in range(0, len(flat), 6):
                    match = faces[tuple(sorted(int(t) for t in flat[i:i+3]))]
                    if len(match) != 1:
                        raise ValueError('Contact face is not external')
                    pairs.extend(match)
        surface[label] = pairs
    pin_nodes = {f'PIN{i}': [int(t) for t in gmsh.model.mesh.getNodes(3, pin, includeBoundary=True)[0]]
                 for i, pin in enumerate(pins, 1)}
    wood_nodes = [int(t) for dim, tag in wood for t in gmsh.model.mesh.getNodes(3, tag, includeBoundary=True)[0]]
    driven = [t for t in wood_nodes if abs(nodes[t][1]) < 1e-5]
    if not driven or not all(surface.values()) or not all(pin_nodes.values()):
        raise ValueError('Missing contact/support entities')
    gmsh.write(str(prefix.with_suffix('.inp')))
    gmsh.finalize()
    lines = [prefix.with_suffix('.inp').read_text(), *nset('DRIVE', driven), *nset('ALLN', list(nodes)),
             '*MATERIAL,NAME=WOOD_SCREEN', '*ELASTIC', '7000,0.3',
             '*SOLID SECTION,ELSET=WOOD,MATERIAL=WOOD_SCREEN',
             '*MATERIAL,NAME=FIXED_PIN', '*ELASTIC', '210000,0.3']
    for label, members in pin_nodes.items():
        lines += [*nset(label+'_N', members), f'*SOLID SECTION,ELSET={label},MATERIAL=FIXED_PIN']
    for label, pairs in surface.items():
        lines += [f'*SURFACE,NAME={label}_SURF,TYPE=ELEMENT', *[f'{t},S{face}' for t, face in pairs]]
    lines += ['*SURFACE INTERACTION,NAME=FRICTIONLESS', '*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR',
              number(args.penalty)]
    for label in pin_nodes:
        lines += ['*CONTACT PAIR,INTERACTION=FRICTIONLESS,TYPE=SURFACE TO SURFACE', f'WOOD_SURF,{label}_SURF']
    # Each case begins unstressed and approaches all four fixed pins. No force
    # sharing is prescribed. Every drive-face translation is explicitly guided.
    displacement = args.clearance+.03
    lines += ['*STEP,NLGEOM,INC=1000', '*STATIC', '1,1,1e-6,1', '*BOUNDARY',
              'DRIVE,1,1,0', f'DRIVE,2,2,{number(displacement if args.direction == "S" else 0)}',
              f'DRIVE,3,3,{number(displacement if args.direction == "N" else 0)}']
    lines += [f'{label}_N,1,3,0' for label in pin_nodes]
    lines += ['*NODE PRINT,NSET=ALLN,FREQUENCY=999999', 'U', '*NODE PRINT,NSET=DRIVE,TOTALS=YES', 'RF']
    for label in pin_nodes:
        lines += [f'*NODE PRINT,NSET={label}_N,TOTALS=YES', 'RF',
                  f'*CONTACT PRINT,SLAVE=WOOD_SURF,MASTER={label}_SURF', 'CF']
    lines += ['*CONTACT PRINT', 'CDIS,CSTR,CNUM', '*NODE FILE', 'U', '*END STEP']
    prefix.with_suffix('.inp').write_text('\n'.join(lines)+'\n')
    context = {'name': name, 'args': vars(args), 'imposed_displacement_mm': displacement, 'nodes': nodes,
                   'driven': driven, 'pins': pin_nodes, 'min_jacobian': jacobian, 'geometry': info,
                   'solver_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    prefix.with_suffix('.context.json').write_text(json.dumps(context)+'\n')
    # Capture input identity BEFORE invoking CalculiX; publication separately
    # reparses the actual deck and outputs rather than trusting these digests.
    prefix.with_suffix('.run.json').write_text(json.dumps({
        'input_sha256': hashlib.sha256(prefix.with_suffix('.inp').read_bytes()).hexdigest(),
        'context_sha256': hashlib.sha256(prefix.with_suffix('.context.json').read_bytes()).hexdigest(),
        'provenance': 'Input and context digests frozen immediately before ccx launch'}, indent=2)+'\n')
    run = subprocess.run(['ccx', '-i', name], cwd=directory, text=True, capture_output=True, check=False)
    prefix.with_suffix('.log').write_text(run.stdout+run.stderr)
    if run.returncode or '*ERROR' in (run.stdout+run.stderr).upper():
        raise RuntimeError(f'Contact solve failed: {prefix}.log')
    print(prefix, flush=True)


if __name__ == '__main__':
    main()
