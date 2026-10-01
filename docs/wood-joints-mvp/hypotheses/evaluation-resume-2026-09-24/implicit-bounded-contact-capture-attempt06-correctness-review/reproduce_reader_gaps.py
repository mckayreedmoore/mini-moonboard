"""Two parent-authorized offline reader probes, using an unchanged temp copy."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / "implicit-bounded-contact-capture-attempt06"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def serialize(rows):
    # Recount only the pre-footer bytes, so length changes cannot mask a gap.
    body = "\n".join("\t".join(row) for row in rows[:-1]) + "\n"
    rows[-1][6] = str(len(body.encode()))
    return (body + "\t".join(rows[-1]) + "\n").encode()


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="attempt06-reader-probes-") as temp:
        copy = Path(temp) / "packet"
        shutil.copytree(PACKET, copy)
        spec = importlib.util.spec_from_file_location(
            "probe_capture_tests", copy / "tests/test_capture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = module.CaptureSinkTests
        cls.setUpClass()  # Existing standalone sink harnesses only.
        try:
            case = cls()
            valid = case.run_sink()
            expected = case.expected()
            baseline = module.reader.validate_capture(valid, expected)
            assert baseline["status"] == "PASS_CAPTURE_STRUCTURE"
            (HERE / "probe-positive.tsv").write_bytes(valid)
            (HERE / "probe-expected.json").write_text(
                json.dumps(expected, indent=2, sort_keys=True) + "\n"
            )
            results.append({"probe": "positive_control", "status": baseline["status"]})

            for field, name in ((2, "step"), (3, "increment"), (4, "attempt"), (5, "iteration")):
                rows = [line.split("\t") for line in valid.decode().splitlines()]
                target = next(row for row in rows if row[0] == "MAP_SUMMARY")
                original = target[field]
                target[field] = "9"
                changed = serialize(rows)
                result = module.reader.validate_capture(changed, expected)
                path = HERE / f"probe-map-wrong-{name}.tsv"
                path.write_bytes(changed)
                results.append({
                    "probe": f"map_summary_wrong_{name}", "field_index": field,
                    "original": original, "mutated": target[field],
                    "gen_begin_field": next(row for row in rows if row[0] == "GEN_BEGIN")[field],
                    "status": result["status"], "artifact": path.name,
                    "sha256": sha(changed),
                })

            rows = [line.split("\t") for line in valid.decode().splitlines()]
            target = next(row for row in rows if row[0] == "STATE_JOIN" and row[1] == "2")
            original = target[9:15].copy()
            target[9] = "-1"
            target[10] = "4"
            changed = serialize(rows)
            result = module.reader.validate_capture(changed, expected)
            path = HERE / "probe-join-negative.tsv"
            path.write_bytes(changed)
            results.append({
                "probe": "negative_state_join_counts", "field_indices": list(range(9, 15)),
                "original": original, "mutated": target[9:15],
                "status": result["status"], "artifact": path.name, "sha256": sha(changed),
                "old_and_new_conservation_total": 3,
            })
        finally:
            cls.tearDownClass()

    output = {
        "scope": "Two parent-authorized reader gaps only; unchanged packet in a temporary copy.",
        "reader_sha256": sha((PACKET / "capture_reader.py").read_bytes()),
        "source_pins_sha256": sha((PACKET / "source-pins.json").read_bytes()),
        "results": results,
        "production_solver_build": False, "solver_execution": False, "docker_invoked": False,
    }
    (HERE / "reader-probes.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
