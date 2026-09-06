"""Freeze both the rejected input-format trial and corrected bounded contrast."""
import hashlib
import json
import tarfile
from pathlib import Path


def summarize(record):
    """Keep full immutable mesh/load contexts in the raw archive, not twice."""
    return {key: value for key, value in record.items()
            if key not in {"nodes", "elements", "fixed", "loads", "surfaces"}}


def main():
    destination = Path(__file__).parent
    if any((destination/name).exists() for name in ("report.json", "evidence.tar.gz")):
        raise ValueError("Published evidence must not be overwritten")
    trials = {"unsafe-original": "section-force-tet-t_m4rvur", "corrected": "section-force-tet-sk65nd4e"}
    contents, records = {}, {}
    archive_path = destination/"evidence.tar.gz"
    with tarfile.open(archive_path, "x:gz") as archive:
        for trial, folder in trials.items():
            source = Path("fea/generated")/folder
            names = [f"tet{n}.{suffix}" for n in (2, 4) for suffix in ("inp", "json", "dat", "log", "sta", "cvg")]
            names += [str(path.relative_to(source)) for path in sorted((source/"launch_sources").glob("*.py"))]
            for name in names:
                raw = (source/name).read_bytes()
                key = trial+"/"+name
                contents[key] = hashlib.sha256(raw).hexdigest()
                archive.add(source/name, arcname=key)
            records[trial] = {str(n): summarize(json.loads((source/f"tet{n}.json").read_text())) for n in (2, 4)}
    report = {
        "status": "STRAIGHT HOMOGENEOUS C3D10 MIDMEMBER DIAGNOSTIC ONLY; NO CURVED FRAME OR JOINT VALIDATION",
        "solver": "CalculiX 2.21, mini-moonboard-fea:box-v1, OMP_NUM_THREADS=2; 60 seconds maximum per job",
        "assumptions": "10x10x100mm beam, E7000MPa, nu0; straight quadratic tetrahedra; all Z0 nodes clamped; independent consistent120N axial/1200Nmm bending end tractions; opposed planar Z50 cuts; no gravity/contact.",
        "limitations": "Native extrapolated/averaged stresses, not interface traction or bolt force. Two structured straight meshes do not establish general convergence or qualify curved frame elements. Original trial retained as rejected load-serialization evidence.",
        "source_directories": trials,
        "archive": archive_path.name,
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "archive_contents": contents,
        "records": records,
    }
    with (destination/"report.json").open("x") as handle:
        handle.write(json.dumps(report, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
