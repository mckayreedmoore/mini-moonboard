"""Compact replay archive and conditional leg-to-board asymmetric actions."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from fea import timber_asymmetric as run
from fea.floor_contact import mesh
from fea.floor_contact_results import blocks
from fea.leg_joint_demand import local_components
from fea.timber_joint_demand import authenticated_inputs, resultant

OUTPUT = Path("fea/results/timber-asymmetric")
JOINTS = Path("fea/results/timber-joint-demand.json")


def compliance(basis):
    matrix = np.array([b["loaded_displacement_mm"] for b in basis], dtype=float).T / np.array([1000., 1000., -1000.])
    if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, rtol=1e-5, atol=1e-8):
        raise ValueError("Single-node compliance violates reciprocity")
    eigenvalues = np.linalg.eigvalsh((matrix+matrix.T)/2)
    if min(eigenvalues) <= 0:
        raise ValueError("Single-node compliance is not positive definite")
    return {"matrix_mm_per_n": matrix.tolist(), "maximum_symmetry_residual_mm_per_n": float(np.max(abs(matrix-matrix.T))),
            "symmetric_eigenvalues_mm_per_n": eigenvalues.tolist(),
            "limits": "Reciprocity and positive compliance diagnostic only, not strength or full-matrix proof"}


def publish():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite asymmetric publication")
    info_path = run.DIRECTORY/"input.json"
    info = json.loads(info_path.read_text())
    accepted, original, _, accepted_sources = authenticated_inputs()
    joint = json.loads(JOINTS.read_text())
    if (info["candidate"] != joint["candidate"] or joint["candidate"] != "timber-base-development"
            or info["accepted_mesh_deck_sha256"] != accepted["deck_sha256"]):
        raise ValueError("Accepted geometry identity differs")
    sources = dict(accepted_sources)
    for closure in (info["source_sha256"], joint["source_sha256"]):
        if any(p in sources and sources[p] != sha for p, sha in closure.items()):
            raise ValueError("Conflicting source identities")
        sources.update(closure)
    for path in (JOINTS, Path("fea/publish_timber_asymmetric.py"), Path("uv.lock")):
        sources[str(path)] = run.digest(path)
    run.unchanged(sources)
    nodes, elements = mesh(original)
    axes = joint["local_axes_world"]
    node = {h: info["mapping"][h]["node"] for h in run.HOLDS}
    if any(abs(nodes[n][0]) >= 1219.2 or abs(nodes[n][2]) < 1e-5 for n in node.values()):
        raise ValueError("Applied load could belong to leg/interface/floor")
    payloads = {"input.json": info_path.read_bytes()}
    omitted, basis_results, cases = {}, {}, []
    for hold in run.HOLDS:
        record_path = run.DIRECTORY/f"{hold}.json"
        record = json.loads(record_path.read_text())
        if record["hold"] != hold or record["input_sha256"] != run.digest(info_path):
            raise ValueError("Basis uses different inputs")
        required = {hold+s for s in (".inp", ".dat", ".log", ".sta", ".launch.json")}
        if not required <= record["artifacts"].keys() or any(Path(p).name != p for p in record["artifacts"]):
            raise ValueError("Missing or invalid basis replay artifacts")
        run.unchanged({str(run.DIRECTORY/p): sha for p, sha in record["artifacts"].items()})
        for name in required:
            payloads[name] = (run.DIRECTORY/name).read_bytes()
        payloads[record_path.name] = record_path.read_bytes()
        omitted.update({p: sha for p, sha in record["artifacts"].items() if p not in required})
        deck, dat = payloads[hold+".inp"].decode(), payloads[hold+".dat"].decode()
        launch = json.loads(payloads[hold+".launch.json"])
        if (mesh(deck) != (nodes, elements) or run.digest(run.DIRECTORY/f"{hold}.inp") != info["deck_sha256"][hold]
                or launch["deck_sha256"] != info["deck_sha256"][hold]
                or launch["input_sha256"] != run.digest(info_path)
                or launch["source_sha256"] != info["source_sha256"]
                or "*ERROR" in payloads[hold+".log"].decode().upper()):
            raise ValueError("Basis deck/launch differs from accepted mesh or run failed")
        basis = run.audit(deck, dat, node[hold])
        if json.loads(json.dumps(basis)) != record["basis"]:
            raise ValueError("Basis output replay differs")
        parsed, leg_basis = blocks(dat), {}
        for side in ("left", "right"):
            leg = joint["legs"][side]
            supports = leg["floor_nodes"]
            if not supports or len(set(supports)) != len(supports) or any(n not in nodes or abs(nodes[n][2]) > 1e-5 for n in supports):
                raise ValueError("Invalid leg support inventory")
            leg_basis[side] = [resultant({n: nodes[n] for n in supports},
                {n: parsed["forces", "FEET", float(i)][n] for n in supports}, leg["reference_world_mm"])
                for i in (1, 2, 3)]
        if set(joint["legs"]["left"]["floor_nodes"]) & set(joint["legs"]["right"]["floor_nodes"]):
            raise ValueError("Leg support overlap")
        basis_results[hold] = {"basis": basis, "compliance": compliance(basis), "leg_on_board_basis_world_n_nmm": leg_basis,
                               "solver_version_banner": record["solver_version_banner"]}
        for scenario in run.scenarios(basis, nodes[node[hold]]):
            actions = {}
            for side, values in leg_basis.items():
                world = [sum(c*v[i] for c, v in zip(scenario["basis_coefficients"], values, strict=True)) for i in range(6)]
                actions[side] = {"leg_on_board_world_n_nmm": world,
                    "board_on_leg_world_n_nmm": [-v for v in world],
                    "leg_on_board_local_xsn_n_nmm": local_components(world, axes)}
            cases.append({"hold": hold, **scenario, "legs": actions})
    maximum = {str(weight): max((c for c in cases if c["climber_lb"] == weight),
        key=lambda c: c["loaded_displacement_magnitude_mm"]) for weight in (150, 200, 250, 300)}
    run.unchanged(sources)
    run.unchanged({str(run.DIRECTORY/name): hashlib.sha256(data).hexdigest()
                   for name, data in payloads.items()})
    archives = {name+".gz": gzip.compress(data, mtime=0) for name, data in payloads.items()}
    report = {"candidate": info["candidate"], "limits": run.LIMITS,
        "source_sha256": sources, "input": info, "basis_solve_count": 9,
        "scenario_count": len(cases), "basis_results": basis_results, "cases": cases,
        "maximum_loaded_displacement_by_weight": maximum, "local_axes_world": axes,
        "leg_references_world_mm": {s: joint["legs"][s]["reference_world_mm"] for s in ("left", "right")},
        "omitted_diagnostic_artifacts_sha256": omitted,
        "replay_archives": {name+".gz": {"gzip_sha256": hashlib.sha256(archives[name+".gz"]).hexdigest(),
            "uncompressed_sha256": hashlib.sha256(data).hexdigest()} for name, data in payloads.items()}}
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, data in archives.items():
        with (OUTPUT/name).open("xb") as stream:
            stream.write(data)
    run.save(OUTPUT/"summary.json", report)


if __name__ == "__main__":
    publish()
