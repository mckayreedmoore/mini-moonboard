"""Native all-prescribed C3D10 force-recovery control; not frame analysis."""
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from fea.floor_contact_results import blocks

IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))


def definition():
    corners = np.array([[0., 0., 0.], [10., 0., 0.], [0., 10., 0.], [0., 0., 10.]])
    points = np.vstack((corners, [(corners[a]+corners[b])/2 for a, b in EDGES]))
    displacement = points*np.array([.001, -.0003, -.0003])
    # Constant sigma_xx=E*epsilon=7 N/mm². Integral grad(N) is zero
    # for vertices, V*(grad(Li)+grad(Lj)) for each edge node.
    gradients = np.array([[-.1, -.1, -.1], [.1, 0., 0.], [0., .1, 0.], [0., 0., .1]])
    expected = np.zeros((10, 3))
    for index, (a, b) in enumerate(EDGES, 4):
        expected[index, 0] = 1000/6*7*(gradients[a, 0]+gradients[b, 0])
    lines = ["*NODE,NSET=ALLN"]
    lines += [f"{i},"+",".join(map(str, p)) for i, p in enumerate(points, 1)]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=BODY", "1,1,2,3,4,5,6,7,8,9,10",
              "*MATERIAL,NAME=MAT", "*ELASTIC", "7000,0.3",
              "*SOLID SECTION,ELSET=BODY,MATERIAL=MAT", "*STEP", "*STATIC", "*BOUNDARY"]
    lines += [f"{i},{j},{j},{v:.15g}" for i, row in enumerate(displacement, 1) for j, v in enumerate(row, 1)]
    lines += ["*NODE PRINT,NSET=ALLN", "U,RF", "*END STEP", ""]
    return "\n".join(lines), points, displacement, expected


def run():
    directory = Path(tempfile.mkdtemp(prefix="prescribed-tet-", dir="fea/generated")).resolve()
    deck, points, imposed, expected = definition()
    (directory/"control.inp").write_text(deck)
    command = ["docker", "run", "--rm", "--network=none", "--cpus=1", "--memory=1g",
               "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
               "--user", f"{os.getuid()}:{os.getgid()}", "-e", "OMP_NUM_THREADS=1",
               "-v", f"{directory}:/work", "-w", "/work", IMAGE, "ccx", "-i", "control"]
    with (directory/"run.log").open("w") as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=False)
    report = {"image": IMAGE, "returncode": completed.returncode, "scope": "All-prescribed linear tetrahedron control only",
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    path = directory/"control.dat"
    if path.exists():
        parsed = blocks(path.read_text())
        forces = parsed.get(("forces", "ALLN", 1.), {})
        displacements = parsed.get(("displacements", "ALLN", 1.), {})
        if set(forces) == set(displacements) == set(range(1, 11)):
            actual = np.array([forces[i] for i in range(1, 11)])
            u = np.array([displacements[i] for i in range(1, 11)])
            report.update(maximum_force_error_n=float(abs(actual-expected).max()),
                          maximum_displacement_error_mm=float(abs(u-imposed).max()),
                          force_residual_n=actual.sum(axis=0).tolist(),
                          moment_residual_nmm=np.cross(points, actual).sum(axis=0).tolist())
            report["passed"] = bool(completed.returncode == 0
                                    and "*ERROR" not in (directory/"run.log").read_text().upper()
                                    and abs(actual-expected).max() < .001
                                    and abs(u-imposed).max() < 1e-9)
    report.setdefault("passed", False)
    report["artifact_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in directory.iterdir() if p.is_file()}
    (directory/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(directory)
    print(json.dumps(report))


if __name__ == "__main__":
    run()
