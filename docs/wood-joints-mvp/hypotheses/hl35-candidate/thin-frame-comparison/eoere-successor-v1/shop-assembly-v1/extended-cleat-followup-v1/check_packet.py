"""Check saved shop bytes and reject occupied outputs or disconnected sources."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(script, args):
    result = subprocess.run([sys.executable, "-B", str(script), *args], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("fresh output directory required")
    args.out.mkdir(parents=True)
    script = OWN / "export.py"
    before = {p.name: digest(p) for p in OWN.iterdir() if p.is_file()}
    code, stdout, stderr = run(script, ["--check"])
    if code:
        raise ValueError(stderr)
    checks = [{"name": "exact_issued_byte_replay", "passed": True, "stdout": stdout}]
    code, _, stderr = run(script, ["--out", str(OWN)])
    if not code or "output directory must be fresh/empty" not in stderr:
        raise ValueError("occupied-output rejection failed")
    checks.append({"name": "occupied_packet_unchanged", "passed": True})
    original = json.loads((OWN / "inputs.json").read_text())
    for control in ("source_hash", "current_axes", "datum_join"):
        directory = args.out / control
        directory.mkdir()
        copied_script = directory / "export.py"
        copied_script.write_bytes(script.read_bytes())
        spec = copy.deepcopy(original)
        if control == "source_hash":
            spec["sources"]["extension"]["sha256"] = "0" * 64
            expected = "source changed: extension"
        else:
            key = "extension" if control == "current_axes" else "members"
            ref = spec["sources"][key]
            bad = directory / ("bad.json" if key == "extension" else "bad.csv")
            source = (ROOT / ref["path"]).read_bytes()
            if key == "extension":
                geometry = json.loads(source)
                geometry["axes"][0]["point_xyz_mm"][0] += 1
                bad.write_text(json.dumps(geometry))
                expected = "extension axes differ from reviewed base"
            else:
                bad.write_bytes(source.replace(b"1815.6464830416933", b"1816.6464830416933", 1))
                if bad.read_bytes() == source:
                    raise ValueError("datum control did not modify the fixture")
                expected = "old datum result/table join differs: members.csv"
            spec["sources"][key] = {"path": str(bad.resolve().relative_to(ROOT)),
                                     "sha256": digest(bad), "bytes": bad.stat().st_size}
        (directory / "inputs.json").write_text(json.dumps(spec))
        output = directory / "rejected-output"
        code, _, stderr = run(copied_script, ["--out", str(output)])
        (directory / "stderr.txt").write_text(stderr)
        if not code or expected not in stderr or output.exists():
            raise ValueError(f"source rejection failed: {control}")
        checks.append({"name": control, "passed": True, "expected_rejection": expected})
    after = {p.name: digest(p) for p in OWN.iterdir() if p.is_file()}
    if before != after:
        raise ValueError("issued packet changed during checks")
    result = {"schema": "eoere_current_shop_packet_controls/v1", "passed": True,
              "checks": checks, "packet_sha256": before, "checker_sha256": digest(Path(__file__)),
              "python": sys.version, "execution": "stdlib source-only replay and three negative fixtures",
              "independent_agent_review": False, "geometry_or_mechanics_acceptance": False}
    (args.out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "checks": len(checks), "issued_bytes_unchanged": True}))


if __name__ == "__main__":
    main()
