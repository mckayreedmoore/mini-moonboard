"""Package one accepted A1-rear 10k diagnostic for source-bound review."""

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from scripts.bolted_center_candidate_extract import extract_files

DEFAULT_SOURCE = Path(
    "fea/results/diagnostics/kerf-right-center/ab205-a1-rear-bore2-contact4-10k"
)
REQUIRED_SOURCES = (
    "fea/current_response_run.py",
    "fea/current_response_model.py",
    "scripts/bolted_center_native_diagnostic.py",
    "scripts/bolted_center_joint_model.py",
    "scripts/clear_space_batch.py",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv",
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(data):
    return (json.dumps(data, indent=2) + "\n").encode()


def _selection(report):
    if (
        report.get("diagnostic_scope", {}).get("case") != "a1-rear"
        or report["diagnostic_scope"].get("spring_n_per_mm") != 10000.0
    ):
        raise ValueError("Expected A1-rear 10k diagnostic")
    final = report["contact_cycles"][-1]["directory"]
    if Path(final).name != final or final in (".", ".."):
        raise ValueError("Unsafe final cycle")
    return ("diagnostic-scope.json", f"{final}/input.json") + tuple(
        f"source_snapshots/{name}" for name in REQUIRED_SOURCES
    )


def _replay_report(report, selected):
    replay = dict(report)
    replay["artifact_sha256"] = {
        name: report["artifact_sha256"][name] for name in selected
    }
    replay["source_sha256"] = {
        name: report["source_sha256"][name] for name in REQUIRED_SOURCES
    }
    return replay


def build(source=DEFAULT_SOURCE, output=Path("/tmp/bolted-center-a1-rear-10k.zip")):
    """Validate the complete local source, then package only replay inputs."""
    source, output = Path(source), Path(output)
    original = (source / "report.json").read_bytes()
    report = json.loads(original)
    selected = _selection(report)
    for name in selected:
        data = (source / name).read_bytes()
        if _sha(data) != report["artifact_sha256"].get(name):
            raise ValueError(f"Source artifact digest mismatch: {name}")
    actions = extract_files(source / "report.json")
    replay_bytes = _json(_replay_report(report, selected))
    actions["source"]["report_sha256"] = _sha(replay_bytes)
    members = {
        "original-report.json": original,
        "report.json": replay_bytes,
        "actions.json": _json(actions),
    }
    members.update({name: (source / name).read_bytes() for name in selected})
    manifest = {name: _sha(data) for name, data in sorted(members.items())}
    members["bundle-manifest.json"] = _json(
        {
            "format": "bolted-center-evidence-v1",
            "case": "a1-rear",
            "spring_n_per_mm": 10000,
            "members_sha256": manifest,
        }
    )
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as bundle:
        for name, data in sorted(members.items()):
            bundle.writestr(name, data)
    verify(output)
    return output


def verify(archive):
    """Check member hashes and replay same-case actions with the existing extractor."""
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or "bundle-manifest.json" not in names:
            raise ValueError("Invalid bundle member list")
        manifest = json.loads(bundle.read("bundle-manifest.json"))
        expected = manifest["members_sha256"]
        if manifest.get("format") != "bolted-center-evidence-v1" or set(names) != set(
            expected
        ) | {"bundle-manifest.json"}:
            raise ValueError("Unexpected bundle members")
        original = json.loads(bundle.read("original-report.json"))
        selected = _selection(original)
        if set(expected) != {
            "original-report.json",
            "report.json",
            "actions.json",
            *selected,
        }:
            raise ValueError("Bundle selection differs from source report")
        if json.loads(bundle.read("report.json")) != _replay_report(original, selected):
            raise ValueError("Replay report differs from source report")
        for name, digest in expected.items():
            if _sha(bundle.read(name)) != digest:
                raise ValueError(f"Bundle digest mismatch: {name}")
            if name in selected and digest != original["artifact_sha256"].get(name):
                raise ValueError(f"Source digest mismatch: {name}")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in selected + ("report.json",):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bundle.read(name))
            replayed = extract_files(root / "report.json")
        if replayed != json.loads(bundle.read("actions.json")):
            raise ValueError("Extracted same-case actions differ")
        return replayed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument(
        "path", type=Path, help="Output archive for build; archive for verify"
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    if args.command == "build":
        build(args.source, args.path)
    else:
        verify(args.path)
    print(f"Verified {args.path} ({args.path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
