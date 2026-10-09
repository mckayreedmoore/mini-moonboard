"""Three bounded evidence fixes; reuse all original mechanics and v1 validation."""

import hashlib
import json
import math
import os
import stat
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
V1_MAP_SHA256 = "ace9ab9d51c7f6320fb87be5f88329299f38b4bde5e7f1a9f2f0d77e98d2d371"
if "EXECUTED_BODY_SHA256" not in globals() or "LOADED_LAUNCHER_SHA256" not in globals():
    raise ValueError("Use run.py: executed body bytes must be captured before loading")
EXECUTED_BODY_SHA256 = globals()["EXECUTED_BODY_SHA256"]
LOADED_LAUNCHER_SHA256 = globals()["LOADED_LAUNCHER_SHA256"]
INPUT_BYTES_AT_LOAD = (HERE / "inputs.json").read_bytes()
CHECK_BYTES_AT_LOAD = (HERE / "check.py").read_bytes()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lexical_snapshot(paths):
    """Reject symlink components and retain lexical file/ancestor identities."""
    identities, hashes = {}, {}
    for supplied in paths:
        path = Path(os.path.abspath(supplied))
        for component in (path, *path.parents):
            observed = component.lstat()
            need(
                not stat.S_ISLNK(observed.st_mode),
                f"Symlink evidence path: {component}",
            )
            identity = (observed.st_dev, observed.st_ino, observed.st_mode)
            need(
                component not in identities or identities[component] == identity,
                "Evidence identity changed during capture",
            )
            identities[component] = identity
        need(path.is_file(), "Evidence must be a regular file")
        hashes[path] = sha(path.read_bytes())
    check_lexical((identities, hashes))
    return identities, hashes


def check_lexical(snapshot):
    identities, hashes = snapshot
    for path, expected in identities.items():
        observed = path.lstat()
        need(not stat.S_ISLNK(observed.st_mode), f"Symlink evidence path: {path}")
        need(
            (observed.st_dev, observed.st_ino, observed.st_mode) == expected,
            f"Lexical evidence identity changed: {path}",
        )
    for path, expected in hashes.items():
        need(
            sha(path.read_bytes()) == expected,
            f"Lexical evidence bytes changed: {path}",
        )


def raw_feasibility(result, details, state, analysis):
    """Reconstruct raw fields and bound the numerical repair by frozen tolerances."""
    inputs = state["inputs"]
    epsilon = inputs["limits"]["scaled_LP_residual_tolerance"]
    cut = inputs["limits"]["moment_cut_tolerance"]
    margin = inputs["limits"]["numerical_feasible_scale_margin"]
    for case, row in zip(
        inputs["published_cases"] + inputs["synthetic_cases"], result["cases"]
    ):
        length = case["main_length_in"] + case["side_length_in"] + case["gap_in"]
        force = min(
            case["main_length_in"] * case["main_bearing_lb_in"],
            case["side_length_in"] * case["side_bearing_lb_in"],
        )
        cap = case["yield_moment_lb_in"] / (force * length)
        minimum_scale = min(1 / (1 + epsilon), cap / (cap + cut)) * (1 - margin)
        for grid in row["grids"]:
            scale = grid["numerical_feasibility_scale"]
            need(
                scale >= minimum_scale - margin,
                "Numerical repair exceeds frozen LP/cut tolerances",
            )
            raw_load = grid["raw_LP_load_lbf"]
            need(
                raw_load <= force * (1 + 2 * epsilon + margin),
                "Raw load exceeds frozen bearing/equilibrium tolerance",
            )
            n = grid["cells_per_member"]
            field = details[f"{case['id']}/{n}"]
            raw_q = [q / scale for q in field["bearing_density_lb_in"]]
            need(
                all(
                    abs(q) <= bound * (1 + epsilon + margin)
                    for q, bound in zip(raw_q, field["bearing_bounds_lb_in"])
                ),
                "Raw bearing field exceeds frozen tolerance",
            )
            cells = list(zip(field["a_in"], field["b_in"], raw_q))
            side = math.fsum(q * (b - a) for a, b, q in cells[:n])
            main = math.fsum(q * (b - a) for a, b, q in cells[n:])
            need(
                max(abs(side - raw_load), abs(main + raw_load)) / force
                <= epsilon + margin,
                "Raw member equilibrium exceeds frozen tolerance",
            )
            first = math.fsum(q * (b * b - a * a) / 2 for a, b, q in cells)
            need(
                abs(first) / (force * length) <= epsilon + margin,
                "Raw shaft moment equilibrium exceeds frozen tolerance",
            )
            points, _, _ = analysis.integrate(field["a_in"], field["b_in"], raw_q)
            peak = max(abs(moment) for _, moment in points) / (force * length)
            need(
                peak <= cap + cut + margin * max(1, cap),
                "Raw moment field exceeds frozen cut tolerance",
            )


def prepare(evidence_paths=()):
    """Load captured v1 bytes and install only the three bounded checks."""
    bound = {
        HERE / "body.py": EXECUTED_BODY_SHA256,
        HERE / "run.py": LOADED_LAUNCHER_SHA256,
        HERE / "inputs.json": sha(INPUT_BYTES_AT_LOAD),
        HERE / "check.py": sha(CHECK_BYTES_AT_LOAD),
    }

    def loaded_sources_unchanged():
        for path, expected in bound.items():
            need(
                sha(path.read_bytes()) == expected,
                f"Loaded executable/source changed before use: {path}",
            )

    loaded_sources_unchanged()
    metadata = json.loads(INPUT_BYTES_AT_LOAD)
    need(
        metadata["schema"] == "synthetic_limit_evidence_review_fix_inputs/v2"
        and metadata["candidate_inputs_used"] is False
        and metadata["capacity_or_pass_claim"] is False,
        "Wrong synthetic review-fix inputs",
    )
    files = metadata["frozen_v1_files"]
    canonical = (
        json.dumps(files, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    need(sha(canonical) == V1_MAP_SHA256, "Unrecognized frozen v1 five-file map")
    captured = {}
    for relative, pin in files.items():
        path = ROOT / relative
        need(path == V1 / path.name, "Unexpected frozen v1 path")
        data = path.read_bytes()
        need(
            sha(data) == pin["sha256"] and len(data) == pin["bytes"],
            "Changed frozen v1 file",
        )
        bound[path], captured[relative] = pin["sha256"], data
    for pin in metadata["review_receipts"]:
        path = ROOT / pin["path"]
        data = path.read_bytes()
        need(sha(data) == pin["sha256"], "Changed review receipt")
        bound[path], captured[pin["path"]] = pin["sha256"], data
    legacy = types.ModuleType("captured_v1_synthetic_evidence_correction")
    legacy.__file__ = str(V1 / "correction.py")
    code = captured[str((V1 / "correction.py").relative_to(ROOT))]
    # V1 code is bound by the frozen map and executes from these captured bytes.
    exec(compile(code, legacy.__file__, "exec"), legacy.__dict__)  # noqa: S102
    loaded_sources_unchanged()
    paths = lexical_snapshot(evidence_paths)
    original_snapshot = legacy.snapshot
    original_unchanged = legacy.unchanged
    original_validate = legacy.validate_compact
    original_verify = legacy.verify

    def guarded_unchanged(pins):
        loaded_sources_unchanged()
        original_unchanged(pins)
        check_lexical(paths)

    def guarded_snapshot():
        loaded_sources_unchanged()
        state = original_snapshot()
        for path, expected in bound.items():
            relative = str(path.relative_to(ROOT))
            need(
                relative not in state["pins"] or state["pins"][relative] == expected,
                "Loaded source snapshot mismatch",
            )
            state["pins"][relative] = expected
            state["contents"][relative] = path.read_bytes()
        guarded_unchanged(state["pins"])
        return state

    def guarded_validate(result, details, state, analysis):
        claims = original_validate(result, details, state, analysis)
        raw_feasibility(result, details, state, analysis)
        return claims

    def guarded_verify(run, replay, output):
        nonlocal paths
        need(
            not Path(output).exists() and not Path(output).is_symlink(),
            "Verification output must be new",
        )
        files = [
            Path(directory) / name
            for directory in (run, replay)
            for name in ("result.json", "details.json", "run-provenance.json")
        ]
        paths = lexical_snapshot(files)
        return original_verify(run, replay, output)

    legacy.unchanged = guarded_unchanged
    legacy.snapshot = guarded_snapshot
    legacy.validate_compact = guarded_validate
    legacy.verify = guarded_verify
    return legacy


def main():
    prepare().main()
