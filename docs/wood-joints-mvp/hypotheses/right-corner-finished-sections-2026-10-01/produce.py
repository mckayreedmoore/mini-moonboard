#!/usr/bin/env python3
"""Join frozen right-corner source actions to exact saved-solid grain sections."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = Path("docs/wood-joints-mvp/hypotheses")
FEATURES = PACKETS / "current-finished-feature-register-2026-10-01"
ENVELOPES = PACKETS / "current-stock-envelope-reconciliation-2026-10-01"
UPPER = PACKETS / "upper-outer-finished-sections-2026-10-01"
ATTEMPT = HERE.relative_to(ROOT)
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
METHOD_HASHES = {
    "right-corner-whole-boundary-2026-10-01/produce.py": "c4547fd3186aff6a59bac032428c42bbbc2e8e8e6f8a144559ad7bc2ffa422b7",
    "right-corner-signed-load-path-2026-10-01/produce.py": "13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea",
    "remaining-candidate-washer-demands-2026-10-01/produce.py": "0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9",
    "remaining-candidate-washer-seats-2026-10-01/check_support.py": "a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967",
    "corner-washer-support-2026-10-01/check_support.py": "9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57",
    "corner-washer-eccentric-support-2026-10-01/check_eccentric_support.py": "97b6426cdc84364bfe8967d491906189b153d8805bbd53290f08dc5f730ce035",
    "mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/produce.py": "3f68d54de9aee14cec66b1d45283a678ef7517b5a0790c0eab9fba267e012565",
    "mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py": "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8",
    "upper-outer-finished-sections-2026-10-01/produce.py": "e5803f153c55ff622789cb24b4aed99cb9b70c5a593b63c0b14d129b7250b566",
    "upper-outer-finished-sections-2026-10-01/section_geometry.py": "8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3",
}
PIN_DOCUMENTS = (
    FEATURES / "source-pins.json",
    FEATURES / "axis-source-pins.json",
    ENVELOPES / "source-pins.json",
    PACKETS
    / "mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/source-pins.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    def reject(value):
        raise ValueError(f"nonfinite JSON constant: {value}")

    return json.loads(path.read_text(), parse_constant=reject)


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"unavailable method: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(
        Path(module.__file__).resolve() == path.resolve(), "runtime method path differs"
    )
    return module


def verify_pin(root: Path, record: dict) -> dict:
    path = (root / record["path"]).resolve()
    require(root.resolve() in path.parents, f"pin escapes root: {record['path']}")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == record["sha256"], f"pinned source changed: {record['path']}")
    if "size_bytes" in record:
        require(
            len(raw) == record["size_bytes"], f"pinned size changed: {record['path']}"
        )
    return {"path": record["path"], "sha256": digest, "size_bytes": len(raw)}


def merge_pins(*groups) -> list[dict]:
    result = {}
    for group in groups:
        for record in group:
            entry = {key: record[key] for key in ("path", "sha256", "size_bytes")}
            prior = result.setdefault(entry["path"], entry)
            require(prior == entry, f"conflicting source pin: {entry['path']}")
    return [result[path] for path in sorted(result)]


def load_inputs():
    method_pins = [
        verify_pin(ROOT, {"path": (PACKETS / relative).as_posix(), "sha256": expected})
        for relative, expected in METHOD_HASHES.items()
    ]
    upper = import_module(ROOT / UPPER / "produce.py", "right_sections_upper_method")
    documents = {
        "finished_surfaces": FEATURES / "surfaces.json",
        "axis_features": FEATURES / "axis-features.json",
        "stock_envelopes": ENVELOPES / "envelopes.json",
        "finished_surfaces_producer": FEATURES / "surfaces.py",
        "axis_features_producer": FEATURES / "axis_features.py",
        "stock_envelopes_producer": ENVELOPES / "envelopes.py",
    }
    local_code = {
        name: ATTEMPT / name
        for name in (
            "produce.py",
            "plan.py",
            "test_produce.py",
            "test_plan.py",
        )
    }
    local_code.update(
        {
            "section_kernel": UPPER / "section_geometry.py",
            "section_kernel_tests": UPPER / "test_section_geometry.py",
            "section_polygon_oracle": UPPER / "test_polygon_oracle.py",
        }
    )
    closure = upper.collect_pin_closure(ROOT, PIN_DOCUMENTS, documents, local_code)
    register_binding = read_json(ROOT / PIN_DOCUMENTS[-1])["source_response_register"]
    extra_pins = [
        verify_pin(
            ROOT,
            {
                "path": register_binding["producer_path"],
                "sha256": register_binding["producer_sha256"],
            },
        )
    ]
    base = import_module(
        ROOT / PACKETS / "corner-washer-support-2026-10-01/check_support.py",
        "right_sections_geometry_input_method",
    )
    # Preserve the reused source join's exact geometry/hardware input closure,
    # including records whose pin dictionaries use descriptive role keys.
    extra_pins.extend(
        verify_pin(ROOT, row) for row in base.checked_inputs()[4].values()
    )
    surfaces = read_json(ROOT / documents["finished_surfaces"])
    axes = read_json(ROOT / documents["axis_features"])
    envelopes = read_json(ROOT / documents["stock_envelopes"])
    require(
        surfaces["source_pins_sha256"] == sha(ROOT / FEATURES / "source-pins.json"),
        "surface pins differ",
    )
    require(
        envelopes["source_pins_sha256"] == sha(ROOT / ENVELOPES / "source-pins.json"),
        "stock pins differ",
    )
    require(
        surfaces["reviewed_stock_envelopes_sha256"]
        == sha(ROOT / documents["stock_envelopes"]),
        "surface stock source differs",
    )
    require(
        surfaces["reviewed_stock_source_pins_sha256"]
        == sha(ROOT / ENVELOPES / "source-pins.json"),
        "surface stock pins differ",
    )
    require(
        axes["source_hashes"]["surfaces_report_sha256"]
        == sha(ROOT / documents["finished_surfaces"]),
        "axis surface source differs",
    )
    for label, report in (
        ("finished_surfaces", surfaces),
        ("stock_envelopes", envelopes),
    ):
        require(
            report["producer_sha256"] == sha(ROOT / documents[label + "_producer"]),
            f"{label} producer differs",
        )
    # The existing join reads frozen records and creates vector datums; it does
    # not import STEP solids or execute section/washer geometry queries. Its
    # floor-group set iteration affects the last floating-point summation bits;
    # preserve its bytes and bind a stable interpreter hash seed for replay.
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / PACKETS / "right-corner-whole-boundary-2026-10-01/produce.py"),
            "--check",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONHASHSEED": "0"},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    require(
        completed.returncode == 0,
        f"frozen boundary source join refused: {completed.stderr[:1000]}",
    )
    boundary = json.loads(completed.stdout)
    require(
        boundary["candidate"] == CANDIDATE and boundary["revision"] == REVISION,
        "boundary candidate differs",
    )
    models = {}
    native_pins = []
    for case, record in sorted(boundary["cases"].items()):
        for source in record["source_files"].values():
            native_pins.append(verify_pin(ROOT, source))
        model = read_json(ROOT / record["source_files"]["model"]["path"])
        require(
            model["candidate"] == CANDIDATE
            and model["geometry_revision_id"] == REVISION
            and model["case_id"] == case,
            "native model identity differs",
        )
        for path, digest in sorted(model["source_geometry_hashes"].items()):
            native_pins.append(verify_pin(ROOT, {"path": path, "sha256": digest}))
        models[case] = model
    pins = merge_pins(closure, method_pins, extra_pins, native_pins)
    return surfaces, axes, envelopes, boundary, models, pins


def build_source_plan():
    surfaces, axes, envelopes, boundary, models, pins = load_inputs()
    method = import_module(HERE / "plan.py", "right_finished_section_plan")
    plan = method.build_plan(surfaces, axes, envelopes, boundary, models)
    plan["source_boundary_report_sha256"] = hashlib.sha256(
        canonical(boundary)
    ).hexdigest()
    plan["source_boundary_replay_python_hash_seed"] = "0"
    return plan, boundary, models, pins


def zero_area_witness(kernel, shape, plane: dict) -> dict | None:
    """Classify a completed exact common with no faces, preserving its topology."""
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

    p, g, _, _ = kernel._validate_frame(
        plane["plane_origin_global_xyz_mm"],
        plane["grain_axis_global_xyz"],
        plane["section_u_global_xyz"],
        plane["section_v_global_xyz"],
    )
    solid = shape.Solids()[0]
    box = solid.BoundingBox()
    margin = max(1e-4, max(box.xlen, box.ylen, box.zlen) * 1e-6, 1e-6)
    surface = gp_Pln(gp_Pnt(*p), gp_Dir(*g))
    bounds = kernel._projection_bounds(solid, surface, p, margin)
    maker = BRepBuilderAPI_MakeFace(surface, *bounds)
    if not maker.IsDone():
        return None
    operation = BRepAlgoAPI_Common(solid.wrapped, maker.Face())
    operation.Build()
    if not operation.IsDone():
        return None
    result = cq.Shape(operation.Shape())
    if result.isNull():
        return {
            "status": "EXACT_EMPTY_FINISHED_SECTION",
            "common_completed": True,
            "null_result": True,
            "face_count": 0,
            "edge_count": 0,
            "vertex_count": 0,
        }
    if (
        not BRepCheck_Analyzer(result.wrapped).IsValid()
        or result.Faces()
        or result.Solids()
    ):
        return None
    edges, vertices = len(result.Edges()), len(result.Vertices())
    return {
        "status": "LOWER_DIMENSIONAL_FINISHED_SECTION"
        if edges or vertices
        else "EXACT_EMPTY_FINISHED_SECTION",
        "common_completed": True,
        "null_result": False,
        "face_count": 0,
        "edge_count": edges,
        "vertex_count": vertices,
    }


def query_section(kernel, shape, plane: dict) -> dict:
    try:
        properties = kernel.section_properties(
            shape,
            plane["plane_origin_global_xyz_mm"],
            plane["grain_axis_global_xyz"],
            plane["section_u_global_xyz"],
            plane["section_v_global_xyz"],
            tolerance_mm=1e-5,
        )
    except kernel.SectionGeometryError as exc:
        witness = None
        if str(exc) in {
            "requested plane is outside the solid or has no positive-area section",
            "OCC returned an invalid section topology",
        }:
            witness = zero_area_witness(kernel, shape, plane)
        return {
            **plane,
            "status": witness["status"]
            if witness
            else "REFUSED_FINISHED_SECTION_QUERY",
            "properties": None,
            "kernel_refusal_reason": str(exc),
            "zero_area_topology_witness": witness,
        }
    return {
        **plane,
        "status": "POSITIVE_AREA_FINISHED_SECTION",
        "properties": properties,
    }


def compute_sections(plan: dict) -> list[dict]:
    kernel = import_module(
        ROOT / UPPER / "section_geometry.py", "right_finished_section_kernel"
    )
    import cadquery as cq

    solids = {}
    for frame in plan["member_frames_and_step_bindings"]:
        verify_pin(
            ROOT,
            {
                "path": frame["step_path"],
                "sha256": frame["step_sha256"],
                "size_bytes": frame["step_size_bytes"],
            },
        )
        shape = cq.importers.importStep(str(ROOT / frame["step_path"])).val()
        require(
            len(shape.Solids()) == 1 and shape.isValid(),
            f"invalid saved solid: {frame['member_id']}",
        )
        solids[frame["member_id"]] = shape
    sections = []
    for plane in plan["section_planes"]:
        sections.append(query_section(kernel, solids[plane["member_id"]], plane))
    return sections


def produce():
    plan, boundary, models, pins = build_source_plan()
    actions = import_module(HERE / "actions.py", "right_finished_section_actions")
    action_report = actions.build_actions(plan, boundary, models)
    sections = compute_sections(plan)
    refused = [row["plane_id"] for row in sections if row["properties"] is None]
    pins = merge_pins(
        pins,
        [
            verify_pin(
                ROOT, {"path": (ATTEMPT / name).as_posix(), "sha256": sha(HERE / name)}
            )
            for name in ("actions.py", "test_actions.py")
        ],
    )
    pin_document = {
        "schema": "right_corner_finished_sections_source_pins/v1",
        "sources": pins,
    }
    return {
        "schema": "right_corner_finished_sections/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "status": "PARTIAL_FINISHED_GEOMETRY_WITH_SOURCE_ACTIONS"
        if refused
        else "FROZEN_SOURCE_ACTIONS_AND_FINISHED_GEOMETRY_ONLY",
        "refused_section_plane_ids": refused,
        "source_plan": plan,
        "source_plan_sha256": hashlib.sha256(canonical(plan)).hexdigest(),
        "source_pins_sha256": hashlib.sha256(canonical(pin_document)).hexdigest(),
        "section_properties": sections,
        "actions": action_report,
        "claim_boundary": {
            "native_solve": False,
            "geometry_changed": False,
            "section_tractions_recovered": False,
            "regional_force_sharing": False,
            "common_strain": False,
            "resistance": False,
            "criterion_adoption": False,
            "joint_acceptance": False,
            "six_case_envelope": False,
            "fabrication_or_climbing_release": False,
        },
    }, pin_document


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.plan_only:
            plan, _, _, pins = build_source_plan()
            print(
                json.dumps(
                    {
                        "source_counts": plan["counts"],
                        "source_plan_sha256": hashlib.sha256(
                            canonical(plan)
                        ).hexdigest(),
                        "verified_input_pin_count": len(pins),
                        "geometry_executed": False,
                    },
                    sort_keys=True,
                )
            )
            return 0
        report, pins = produce()
        for name, value in (("sections.json", report), ("source-pins.json", pins)):
            raw = canonical(value)
            if args.verify:
                require(
                    (HERE / name).read_bytes() == raw, f"saved output differs: {name}"
                )
            else:
                (HERE / name).write_bytes(raw)
        print(
            json.dumps(
                {
                    "source_counts": report["source_plan"]["counts"],
                    "section_count": len(report["section_properties"]),
                    "refused_section_count": len(report["refused_section_plane_ids"]),
                    "source_pin_count": len(pins["sources"]),
                    "status": report["status"],
                },
                sort_keys=True,
            )
        )
    except (
        OSError,
        ValueError,
        KeyError,
        ImportError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"right finished-section source join refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
