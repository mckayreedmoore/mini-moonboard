"""Route the frozen current bolt-geometry checker to the selected latest analysis.

The v8 geometry checker remains the only numeric implementation. This small
adapter binds its globals to either the v8 or v9 intake, records the selected
method lineage, and never prepares or solves an analysis.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import inspect
import json
import types
from pathlib import Path
from typing import Any

from scripts import eoere_current_bolt_geometry_review as frozen_reader
from scripts.eoere_paired_frame_basis import ROOT, ref, sha

OWN = Path(__file__).resolve()
FROZEN_READER = Path(frozen_reader.__file__).resolve()
FROZEN_READER_SHA256 = "7910b5aa333b169d88bfe5c12c422aaef8e2df015ed43da72c4891c357324913"
ANALYSIS_MODULES = {
    "v8": "scripts.eoere_v8_analysis",
    "v9": "scripts.eoere_v9_analysis",
}
READINESS_SCHEMAS = {
    "v8": "eoere_v8_existing_response_method_readiness/v1",
    "v9": "eoere_v9_existing_response_method_readiness/v1",
}
PUBLIC_ROOT = ROOT / "docs/bolted-frame-development"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def readiness_schema(analysis_name: str) -> str:
    try:
        return READINESS_SCHEMAS[analysis_name]
    except KeyError as error:
        raise ValueError("analysis module must be v8 or v9") from error


def load_analysis_module(analysis_name: str) -> Any:
    readiness_schema(analysis_name)
    module_path = ANALYSIS_MODULES[analysis_name]
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as error:
        if error.name == module_path:
            raise ValueError(f"selected analysis module is not available yet: {module_path}") from error
        raise
    for name in ("OWN", "BASE", "REVISION", "PHYSICAL_REVISION", "context"):
        require(hasattr(module, name), f"{module_path} is missing required API member {name}")
    return module


def adapted_readiness_checker_source(analysis_name: str) -> str:
    """Return the frozen checker source with only the selected schema literal changed."""
    schema = readiness_schema(analysis_name)
    source = inspect.getsource(frozen_reader._checked_readiness)
    old = '"eoere_v8_existing_response_method_readiness/v1"'
    require(source.count(old) == 1, "frozen readiness schema guard changed")
    if analysis_name == "v8":
        return source
    return source.replace(old, json.dumps(schema), 1)


def method_blueprint(analysis_name: str, analysis_module: Any) -> dict[str, Any]:
    require(sha(FROZEN_READER) == FROZEN_READER_SHA256, "frozen current geometry reader changed")
    return {
        "schema": "eoere_latest_bolt_geometry_method_blueprint/v1",
        "selected_analysis_module": analysis_name,
        "analysis_module": ref(analysis_module.OWN),
        "analysis_revision": analysis_module.REVISION,
        "physical_geometry_revision": analysis_module.PHYSICAL_REVISION,
        "readiness_schema": readiness_schema(analysis_name),
        "frozen_geometry_reader": ref(FROZEN_READER),
        "frozen_geometry_reader_sha256": FROZEN_READER_SHA256,
        "latest_wrapper": ref(OWN),
        "numeric_method": "frozen current bolt geometry reader; no formulas or result values adapted",
    }


def bind_report_metadata(
    result: dict[str, Any], analysis_name: str, analysis_module: Any
) -> dict[str, Any]:
    """Bind selected revisions and remove the frozen reader's v8-only prose label."""
    blueprint = method_blueprint(analysis_name, analysis_module)
    limits = result.get("qualification_limits")
    require(isinstance(limits, list), "current reviewer qualification limits required")
    old_limit = "The admitted six fields are evaluated with their own v8 forces and geometry; no earlier frame metric or response is carried into this report."
    new_limit = f"The admitted six fields are evaluated with their own {analysis_name} forces and geometry; no earlier frame metric or response is carried into this report."
    if analysis_name == "v9":
        require(limits.count(old_limit) == 1, "frozen v8 qualification wording changed")
        result["qualification_limits"] = [new_limit if row == old_limit else row for row in limits]
    result["method_blueprint"] = copy.deepcopy(blueprint)
    result["source_bindings"]["latest_wrapper"] = ref(OWN)
    result["source_bindings"]["frozen_geometry_reader"] = ref(FROZEN_READER)
    result["source_bindings"]["analysis_module"] = ref(analysis_module.OWN)
    return blueprint


def make_reader_namespace(analysis_name: str, analysis_module: Any | None = None) -> dict[str, Any]:
    """Clone the frozen reader's functions against selected analysis globals."""
    analysis_module = analysis_module or load_analysis_module(analysis_name)
    readiness_schema(analysis_name)
    require(sha(FROZEN_READER) == FROZEN_READER_SHA256, "frozen current geometry reader changed")
    require(sha(OWN) == ref(OWN)["sha256"], "latest wrapper changed while loading")

    namespace = dict(vars(frozen_reader))
    namespace.update(
        OWN=OWN,
        analysis=analysis_module,
        READINESS=analysis_module.BASE / "adapter-readiness.json",
        OUT=analysis_module.BASE / "bolt-geometry-review-latest-v1",
        PUBLIC_ROOT=PUBLIC_ROOT,
        FROZEN_READER=FROZEN_READER,
        FROZEN_READER_SHA256=FROZEN_READER_SHA256,
    )
    for name, value in vars(frozen_reader).items():
        if isinstance(value, types.FunctionType) and value.__globals__ is frozen_reader.__dict__:
            cloned = types.FunctionType(
                value.__code__,
                namespace,
                name=value.__name__,
                argdefs=value.__defaults__,
                closure=value.__closure__,
            )
            cloned.__kwdefaults__ = value.__kwdefaults__
            namespace[name] = cloned

    # v9 shares the readiness contract but has its own declared schema. Adapt
    # exactly that one string guard; all intake and numeric functions remain
    # the frozen reader's unchanged function bodies.
    source = adapted_readiness_checker_source(analysis_name)
    exec(compile(source, str(FROZEN_READER), "exec"), namespace)  # noqa: S102 -- one guarded schema literal adapter
    raw_check = namespace["_checked_readiness"]

    def checked_readiness(
        readiness_path: Path,
        readiness_sha256: str,
        initial_pins: dict[str, str] | None = None,
    ):
        pins = {} if initial_pins is None else dict(initial_pins)
        binding = ref(FROZEN_READER)
        require(binding["sha256"] == FROZEN_READER_SHA256, "frozen reader binding changed")
        previous = pins.get(binding["path"])
        require(previous is None or previous == FROZEN_READER_SHA256, "conflicting frozen reader pin")
        pins[binding["path"]] = FROZEN_READER_SHA256
        return raw_check(readiness_path, readiness_sha256, pins)

    namespace["_checked_readiness"] = checked_readiness
    base_summary = namespace["public_summary"]
    blueprint = method_blueprint(analysis_name, analysis_module)
    base_write_new = namespace["_write_new"]

    def bound_write_new(path: Path, value: Any) -> None:
        if (
            path.name == "full-review.json"
            and isinstance(value, dict)
            and value.get("schema") == "eoere_current_bolt_geometry_review/v1"
            and "cases" in value
        ):
            bind_report_metadata(value, analysis_name, analysis_module)
        base_write_new(path, value)

    def bound_public_summary(result: dict[str, Any], full_path: Path) -> dict[str, Any]:
        # The frozen reader writes the raw report first. Metadata must already
        # be in those bytes before this hash-bound compact summary is formed.
        require(result.get("method_blueprint") == blueprint, "raw report method blueprint missing or changed")
        require(
            result.get("source_bindings", {}).get("frozen_geometry_reader") == ref(FROZEN_READER)
            and result.get("source_bindings", {}).get("latest_wrapper") == ref(OWN)
            and result.get("source_bindings", {}).get("analysis_module") == ref(analysis_module.OWN),
            "raw report latest/frozen source bindings changed",
        )
        summary = base_summary(result, full_path)
        summary["method_blueprint"] = copy.deepcopy(blueprint)
        return summary

    namespace["_write_new"] = bound_write_new
    namespace["public_summary"] = bound_public_summary
    return namespace


def review_latest(
    analysis_name: str,
    readiness_path: Path,
    readiness_sha256: str,
    out: Path | None = None,
    public_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the frozen current-field reducer against one selected analysis bank."""
    analysis_module = load_analysis_module(analysis_name)
    namespace = make_reader_namespace(analysis_name, analysis_module)
    output = (analysis_module.BASE / "bolt-geometry-review-latest-v1") if out is None else out
    return namespace["review"](readiness_path, readiness_sha256, output, public_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-module", choices=tuple(ANALYSIS_MODULES), required=True)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--readiness-sha256", required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--public", type=Path, help="optional fresh public output; no index is changed")
    args = parser.parse_args()
    result, summary = review_latest(
        args.analysis_module,
        args.readiness,
        args.readiness_sha256,
        args.out,
        args.public,
    )
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "analysis_revision": result["analysis_revision"],
                "case_pair_counts": [case["pair_census_counts"] for case in result["cases"]],
                "full_review": summary["full_review"],
                "complete_Cdelta": None,
                "complete_joint_qualified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
