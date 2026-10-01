"""Read-only architecture probes against exact attempt06 source files.

Compile only the standalone review sink harness in a temporary directory.
No source patching, Docker, CalculiX build, solver, or native coupon occurs.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKET = HERE.with_name("implicit-bounded-contact-capture-attempt06")
sha = lambda value: hashlib.sha256(value).hexdigest()
spec = importlib.util.spec_from_file_location("arch_capture_reader", PACKET / "capture_reader.py")
reader = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(reader)


def result_for(data: bytes, expected: dict) -> dict:
    try:
        result = reader.validate_capture(data, expected)
        return {"status": result["status"], "generation_count": result["generation_count"],
                "trial_summaries": result["trial_summaries"]}
    except reader.CaptureError as exc:
        return {"status": "REJECTED", "reason": str(exc)}


def mutate(data: bytes, record: str, fields: dict[int, str]) -> bytes:
    rows = [line.split("\t") for line in data.decode().splitlines()]
    row = next(row for row in rows if row[0] == record)
    for field, value in fields.items():
        row[field] = value
    body = "".join("\t".join(row) + "\n" for row in rows[:-1])
    rows[-1][6] = str(len(body.encode()))
    return (body + "\t".join(rows[-1]) + "\n").encode()


def main() -> None:
    compiler = shutil.which("cc") or shutil.which("gcc")
    if compiler is None:
        raise RuntimeError("standalone C compiler unavailable")
    results = {"scope": "standalone sink / offline reader only",
               "sink_sha256": sha((PACKET / "capture-sink.inc").read_bytes()),
               "reader_sha256": sha((PACKET / "capture_reader.py").read_bytes()),
               "probes": {}}
    with tempfile.TemporaryDirectory(prefix="attempt06-architecture-") as tmp:
        temp = Path(tmp)
        binary = temp / "review-harness"
        compilation = subprocess.run(
            [compiler, "-std=c11", "-O2", str(HERE / "reproduce.c"), "-lm", "-o", str(binary)],
            check=True, capture_output=True, text=True)
        results["compiler_stderr"] = compilation.stderr
        bindings = {
            "input_sha256": sha(b"architecture offline synthetic input"),
            "include_closure_sha256": sha(b""),
            "source_archive_sha256": sha((PACKET / "build/context/source.tar.bz2").read_bytes()),
            "patch_sha256": sha((PACKET / "build/context/capture.patch").read_bytes()),
            "binary_sha256": sha(binary.read_bytes()),
            "pair_roster_sha256": sha(b"architecture synthetic pair roster"),
            "face_roster_sha256": sha(b"architecture synthetic face roster"),
        }
        for mode in ("control", "native-iteration-advance", "temporary-collision", "original-positive"):
            count = 2 if mode == "original-positive" else 1
            output = temp / f"{mode}.tsv"
            env = dict(os.environ)
            env.update({
                "CCX_CONTACT_CAPTURE_PATH": str(output),
                "CCX_CAPTURE_INPUT_SHA256": bindings["input_sha256"],
                "CCX_CAPTURE_INCLUDE_SHA256": bindings["include_closure_sha256"],
                "CCX_CAPTURE_SOURCE_SHA256": bindings["source_archive_sha256"],
                "CCX_CAPTURE_PATCH_SHA256": bindings["patch_sha256"],
                "CCX_CAPTURE_BINARY_SHA256": bindings["binary_sha256"],
                "CCX_CAPTURE_PAIR_SHA256": bindings["pair_roster_sha256"],
                "CCX_CAPTURE_FACE_SHA256": bindings["face_roster_sha256"],
                "CCX_CAPTURE_EXPECTED_FACES": str(count), "CCX_CAPTURE_EXPECTED_TIES": "1",
            })
            expected = {
                "tie_count": 1, "face_count_by_tie": {"1": count},
                "face_ids_by_tie": {"1": [101 + i for i in range(count)]},
                "minimum_accepted_links": 1, "require_linear_law": True, "require_force": True,
                "capture_byte_cap": reader.CAPTURE_CAP, "run_bindings": bindings,
            }
            execution = subprocess.run([str(binary), mode], env=env, check=True,
                                       capture_output=True, text=True)
            probe = {"stdout": execution.stdout, "stderr": execution.stderr,
                     "configured_path_published": output.exists()}
            results["probes"][mode] = probe
            if output.exists():
                data = output.read_bytes()
                probe["reader"] = result_for(data, expected)
                probe["run_end"] = data.decode().splitlines()[-1]
                probe["capture_sha256"] = sha(data)
                (HERE / f"{mode}.tsv").write_bytes(data)
                if mode == "original-positive":
                    map_mutated = mutate(data, "MAP_SUMMARY", {2: "99", 3: "99", 4: "99", 5: "99"})
                    (HERE / "map-identity-mutated.tsv").write_bytes(map_mutated)
                    results["probes"]["map-identity-mismatch"] = {
                        "changes": "first MAP_SUMMARY step/increment/attempt/iteration changed from 1 to 99",
                        "reader": result_for(map_mutated, expected)}
                    force_mutated = mutate(data, "TRIAL_SUMMARY", {11: "0", 13: "NA", 14: "NA", 15: "NA", 16: "NA"})
                    (HERE / "missing-force-mutated.tsv").write_bytes(force_mutated)
                    results["probes"]["missing-force"] = {
                        "changes": "first generated trial force row removed; complete force aggregate replaced with NA",
                        "strict_reader": result_for(force_mutated, expected),
                        "require_force_false_reader": result_for(force_mutated, {**expected, "require_force": False})}
        (HERE / "probe-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
