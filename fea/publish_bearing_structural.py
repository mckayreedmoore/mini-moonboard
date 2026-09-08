"""Archive replayable stiffness evidence without publishing bulky visualization files."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea.floor_contact import mesh
from fea.solve_bearing_frame import straight_mesh_volume
from fea.solve_easy_frame import audit, digest

OUTPUT = Path("fea/results/bearing-frame")


def validate_metadata(row, deck, context):
    if any(row.get(key) != value for key, value in context.items()):
        raise ValueError("Archived context and result metadata differ")
    lines = deck.splitlines()
    elastic = [lines[i+1] for i, line in enumerate(lines[:-1]) if line.upper() == "*ELASTIC"]
    if len(elastic) != 1 or [float(v) for v in elastic[0].split(",")] != [row["modulus_mpa"], .3]:
        raise ValueError("Deck elastic properties differ from result")
    nodes, elements = mesh(deck)
    volume, midpoint_error = straight_mesh_volume(nodes, elements)
    if (len(nodes) != row["nodes"] or len(elements) != row["elements"]
            or not math.isclose(volume, row["mesh_volume_mm3"], rel_tol=1e-12)
            or not math.isclose(midpoint_error, row["maximum_midpoint_error_mm"], abs_tol=1e-12)
            or not math.isclose(abs(volume-row["cad_volume_mm3"])/row["cad_volume_mm3"],
                                row["volume_relative_error"], abs_tol=1e-12)):
        raise ValueError("Archived mesh and result metadata differ")


def publish(results):
    records = [json.loads(path.read_text()) for path in results]
    if sorted(row["mesh_size_mm"] for row in records) != [40., 60.]:
        raise ValueError("Require one 40mm and one 60mm result")
    if (records[0]["frozen_geometry"] != records[1]["frozen_geometry"]
            or records[0]["modulus_mpa"] != records[1]["modulus_mpa"]):
        raise ValueError("Mesh comparison inputs differ")
    pending = {}
    for path, row in zip(results, records, strict=True):
        if row["candidate"] != "bearing-lean-frame":
            raise ValueError("Unexpected candidate")
        if any(digest(name) != sha for name, sha in row["source_sha256"].items()):
            raise ValueError("Source differs from solver evidence")
        for name, sha in row["evidence_sha256"].items():
            if digest(path.parent/name) != sha:
                raise ValueError(f"Solver artifact differs: {name}")
        prefix = path.with_suffix("")
        deck = prefix.with_suffix(".inp").read_text()
        context = json.loads(Path(str(prefix)+".context.json").read_text())
        validate_metadata(row, deck, context)
        replay = audit(deck,
                       prefix.with_suffix(".dat").read_text(), row["frozen_geometry"])
        if any(json.loads(json.dumps(value)) != row[key] for key, value in replay.items()):
            raise ValueError("Independent result replay differs")
        stem = f"mesh{row['mesh_size_mm']:g}"
        archives = {}
        for suffix in (".inp", ".dat", ".context.json", ".log", ".sta"):
            original = Path(str(prefix)+suffix)
            name = stem+suffix+".gz"
            data = original.read_bytes()
            data_sha = hashlib.sha256(data).hexdigest()
            if data_sha != row["evidence_sha256"][original.name]:
                raise ValueError("Artifact changed during archival")
            payload = gzip.compress(data, mtime=0)
            archives[name] = {"gzip_sha256": hashlib.sha256(payload).hexdigest(),
                              "uncompressed_sha256": data_sha, "original_name": original.name}
            pending[OUTPUT/name] = payload
        row.update(replay_archives=archives,
                   publisher_source_sha256={"fea/publish_bearing_structural.py": digest(__file__)})
        pending[OUTPUT/(stem+".json")] = (json.dumps(row, indent=2, allow_nan=False)+"\n").encode()
    if any(path.exists() for path in pending):
        raise FileExistsError("Refusing to overwrite published stiffness evidence")
    for row in records:
        if any(digest(name) != sha for name, sha in row["source_sha256"].items()):
            raise ValueError("Source changed during archival")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path, data in pending.items():
        with path.open("xb") as stream:
            stream.write(data)
    print(f"Archived {len(pending)} replay files; no strength qualification")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, nargs=2)
    publish(parser.parse_args().results)
