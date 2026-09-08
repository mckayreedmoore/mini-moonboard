"""Archive two replayable timber stiffness screens, never strength approval."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea.publish_bearing_structural import validate_metadata
from fea.solve_easy_frame import audit, digest

OUTPUT = Path("fea/results/timber-base")
KEY = "timber-base-development"
PUBLISHER_SOURCES = (
    "fea/publish_timber_structural.py", "fea/publish_bearing_structural.py",
    "fea/solve_bearing_frame.py", "fea/solve_easy_frame.py", "fea/floor_contact.py",
    "fea/box_results.py", "fea/floor_contact_results.py", "fea/hybrid_results.py",
)


def publish(results):
    publisher_sources = {name: digest(name) for name in PUBLISHER_SOURCES}
    records = [json.loads(path.read_text()) for path in results]
    if sorted(row["mesh_size_mm"] for row in records) != [40., 60.]:
        raise ValueError("Require one 40mm and one 60mm result")
    if (records[0]["frozen_geometry"] != records[1]["frozen_geometry"]
            or records[0]["modulus_mpa"] != records[1]["modulus_mpa"]):
        raise ValueError("Mesh comparison inputs differ")
    pending = {}
    for path, row in zip(results, records, strict=True):
        info = row["frozen_geometry"]
        if row["candidate"] != KEY or info["candidate"] != KEY:
            raise ValueError("Unexpected candidate")
        geometry_sources = info["geometry_source_sha256"]
        if not geometry_sources or any(row["source_sha256"].get(name) != sha
                                       for name, sha in geometry_sources.items()):
            raise ValueError("Missing frozen geometry source closure")
        if any(digest(name) != sha for name, sha in row["source_sha256"].items()):
            raise ValueError("Source differs from solver evidence")
        info_path = path.parent/"box_frame_bulk.json"
        if (digest(info_path) != row["input_sha256"]
                or json.loads(info_path.read_text()) != info
                or digest(path.parent/"box_frame_bulk.step") != info["step_sha256"]):
            raise ValueError("Frozen input or STEP differs from solver evidence")
        if (row["size_mm"] != row["mesh_size_mm"]
                or not math.isfinite(row["modulus_mpa"]) or row["modulus_mpa"] <= 0
                or not math.isfinite(row["min_jacobian"]) or row["min_jacobian"] <= 0
                or not 0 <= row["volume_relative_error"] <= .005
                or row["mesh_settings"].get("Mesh.SecondOrderLinear") != 1):
            raise ValueError("Invalid mesh or material screening metadata")
        for name, sha in row["evidence_sha256"].items():
            if Path(name).name != name or digest(path.parent/name) != sha:
                raise ValueError(f"Solver artifact differs: {name}")
        prefix = path.with_suffix("")
        payloads = {}
        for suffix in (".inp", ".dat", ".context.json", ".log", ".sta"):
            original = Path(str(prefix)+suffix)
            data = original.read_bytes()
            if hashlib.sha256(data).hexdigest() != row["evidence_sha256"].get(original.name):
                raise ValueError("Missing or changed replay artifact")
            payloads[suffix] = data
        if hashlib.sha256(payloads[".inp"]).hexdigest() != row["deck_sha256"]:
            raise ValueError("Deck differs from solver context")
        deck = payloads[".inp"].decode()
        validate_metadata(row, deck, json.loads(payloads[".context.json"]))
        replay = audit(deck, payloads[".dat"].decode(), info)
        if any(json.loads(json.dumps(value)) != row[key] for key, value in replay.items()):
            raise ValueError("Independent result replay differs")
        if "*ERROR" in payloads[".log"].decode().upper():
            raise ValueError("Solver log contains an error")
        stem = f"mesh{row['mesh_size_mm']:g}"
        archives = {}
        for suffix, data in payloads.items():
            name = stem+suffix+".gz"
            payload = gzip.compress(data, mtime=0)
            archives[name] = {"gzip_sha256": hashlib.sha256(payload).hexdigest(),
                "uncompressed_sha256": hashlib.sha256(data).hexdigest(),
                "original_name": prefix.name+suffix}
            pending[OUTPUT/name] = payload
        row.update(replay_archives=archives, publisher_source_sha256=publisher_sources)
        pending[OUTPUT/(stem+".json")] = (json.dumps(row, indent=2, allow_nan=False)+"\n").encode()
    if any(path.exists() for path in pending):
        raise FileExistsError("Refusing to overwrite published stiffness evidence")
    for sources in [publisher_sources, *(row["source_sha256"] for row in records)]:
        if any(digest(name) != sha for name, sha in sources.items()):
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
