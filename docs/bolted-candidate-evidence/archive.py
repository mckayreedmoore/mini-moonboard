"""Copy and verify the frozen PB-01 quarter diagnostic evidence; no native solve."""

import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simple_pb01_hybrid_local_actions import (
    ARCHIVE as SOURCE,
)
from scripts.simple_pb01_hybrid_local_actions import (
    ARCHIVE_SHA256,
    REPORT_SHA256,
    extract,
)

DEST = HERE / "pb01-quarter-contact4-a12left-evidence.tar.gz"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def build():
    if not DEST.exists():
        if sha256(SOURCE) != ARCHIVE_SHA256:
            raise ValueError("Source archive changed")
        shutil.copyfile(SOURCE, DEST)
    if sha256(DEST) != ARCHIVE_SHA256:
        raise ValueError("Evidence archive changed")

    with tarfile.open(DEST, "r:gz") as bundle:
        members = {member.name for member in bundle.getmembers() if member.isfile()}
        report_bytes = bundle.extractfile("report.json").read()
        if hashlib.sha256(report_bytes).hexdigest() != REPORT_SHA256:
            raise ValueError("Report changed")
        report = json.loads(report_bytes)
        final_cycle = report["contact_cycles"][-1]["directory"]
        if (
            final_cycle != "cycle-13"
            or not report["contact_cycles"][-1]["contact_passed"]
        ):
            raise ValueError("Unexpected final cycle")
        required = {
            "diagnostic-scope.json",
            "report.json",
            *(
                f"{final_cycle}/{name}"
                for name in (
                    "input.json",
                    "report.json",
                    "frame.inp",
                    "frame.dat",
                    "frame.log",
                    "frame.sta",
                )
            ),
            *("source_snapshots/" + name for name in report["source_sha256"]),
        }
        if not required <= members:
            raise ValueError(f"Missing archive members: {sorted(required - members)}")
        for name in required - {"report.json"}:
            expected = (
                report["source_sha256"].get(name.removeprefix("source_snapshots/"))
                if name.startswith("source_snapshots/")
                else report["artifact_sha256"].get(name)
            )
            if expected is None:
                raise ValueError(f"Unmanifested member: {name}")
            if hashlib.sha256(bundle.extractfile(name).read()).hexdigest() != expected:
                raise ValueError(f"Digest mismatch: {name}")

    actions = extract(DEST)
    scope = report["diagnostic_scope"]
    seed = {
        "purpose": "replay seed only; do not run as part of archive verification",
        "source_commit": "4c60e46",
        "source_archive_sha256": ARCHIVE_SHA256,
        "report_sha256": REPORT_SHA256,
        "source_manifest_entries": len(report["source_sha256"]),
        "final_cycle": final_cycle,
        "case": scope["case"],
        "variant": scope["pb01_pose_variant"],
        "contact_update_strategy": report["contact_update_strategy"],
        "initial_contact_names": report["initial_contact_names"],
        "max_cycles_cli_default": 30,
        "trial_stiffness_n_per_mm": scope["trial_stiffness_n_per_mm"],
        "solver_image": report["solver_image"],
        "native_runner": "scripts.simple_pb01_hybrid_diagnostic_run",
        "native_runner_arguments": [
            "a12-left",
            "--variant",
            "quarter",
            "--output",
            "<new-output-directory>",
        ],
        "diagnostic_scope": scope,
    }
    write_json(HERE / "local-forces.json", actions)
    write_json(HERE / "replay-seed.json", seed)
    print(
        "Verified archive, 260 source snapshots, final-cycle files, and local actions"
    )


if __name__ == "__main__":
    build()
