"""N14 permanent saved-state postprocessor; only the parent executes run(output).

Import performs no I/O or numerical imports. prepare() authenticates sources,
joins identities and reads NPZ headers only. No solver or producer is launched.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/panel-permanent-completion"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
RESOLVER = HERE / "rawlocal/knee-bridge-permanent-resolve/attempt02"
N14_RAW = HERE / "rawlocal/panel-reference-completion/attempt01"
N14 = HERE / "panel-reference-completion.py"
RESPONSE = RESOLVER / "response.npz"
OPERATORS = GRAVITY / "operators.npz"
PROJECTION = GRAVITY / "B.npz"
BASE = PACKET.parent / "mvp-acceleration-2026-09-28"
DOF = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
ATTACHMENT = PACKET / "panel-attachment/attachment_screen.py"
LATERAL = PACKET / "panel-attachment/lateral_reference.py"
REFERENCE = PACKET / "panel-attachment/results/attempt08-all-two-receiver/comparison.json"
PANEL = ROOT / "fea/reinforced_panel_checks.py"
YIELD = ROOT / "fea/dowel_yield.py"
WRENCH = PACKET / "top_corner_actions.py"
CD = 0.9
AXIAL = "non_qualifying_parametric_screw_withdrawal"
SHEAR = "panel_screw_lateral_plane"
CONTACT = "timber_or_panel_contact"
PINS = {
    N14: "1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1",
    RESOLVER / "comparison.json": "3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a",
    RESPONSE: "605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    OPERATORS: "7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f",
    PROJECTION: "d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a",
    GRAVITY / "model.json": "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    GRAVITY / "model-inputs.json": "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    GRAVITY / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    N14_RAW / "receipt.json": "5b42272f49c1924546abab3bd4d036a0a95f7afb2700055fb2e769ab56a3db91",
    N14_RAW / "summary.json": "dfa8a93d686e82b5ee8099ad55fce66f436d1720ab5fb51b4cdf6c1b2761c6f5",
    DOF: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    ATTACHMENT: "c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc",
    LATERAL: "8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2",
    REFERENCE: "7146069ad3ecf913cbb354f3a37d1e6af6768fc3b577f574feb5a10bd483eb2f",
    PANEL: "1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d",
    YIELD: "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
}
FLAGS = dict.fromkeys((
    "N14_accepted", "Hillman_capacity_qualified", "complete_panel_acceptance",
    "complete_screw_acceptance", "complete_joint_acceptance", "full_frame_acceptance",
    "strict_frame_stability", "proposal_adopted", "formal_criteria_updated",
    "physical_release", "fabrication_release", "geometry_hardware_load_or_stiffness_changed",
    "SPAX_resistance_or_installation_transferred", "historical_acceptance_transferred",
    "second_duration_or_dynamic_credit", "native_CAD_frame_or_coupon_run",
    "original_producer_pipelines_executed", "new_contact_or_frame_sharing_solved",
    "tests_or_review_loop_run",
), False)


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def key(path):
    return str(Path(path).resolve().relative_to(ROOT))


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source hash differs: " + key(path))


def source_pins():
    """Close the consumed method and duration basis, excluding unrelated authority."""
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    cache = PACKET.parent / "upper-block-strength-2026-10-01/source-cache"
    for name, digest in {
        "chapter2-2024-awc.pdf": "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
        "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
        "chapter11-2024-awc-20260911.pdf": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
        "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    }.items():
        pins[cache / name] = digest
    authenticate(pins)
    return pins


def functions(path, names, namespace):
    """Compile only named pure function definitions, never top-level workflows."""
    tree = ast.parse(Path(path).read_text(), filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(nodes) == len(names) and all(not node.decorator_list for node in nodes), "pure definitions differ")
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**namespace)


def basis():
    namespace = dict(Path=Path, ast=ast, json=json, math=math, struct=struct,
                     SimpleNamespace=SimpleNamespace, ZipFile=ZipFile, require=require,
                     N_PER_LBF=4.4482216152605, ATTACHMENT=ATTACHMENT, LATERAL=LATERAL,
                     YIELD=YIELD, PANEL=PANEL, REFERENCE=REFERENCE, WRENCH=WRENCH,
                     OPERATORS=OPERATORS, RESPONSE=RESPONSE, PROJECTION=PROJECTION,
                     CASES=("permanent-only",), AXIAL=AXIAL, SHEAR=SHEAR, CONTACT=CONTACT)
    return functions(N14, ("definitions", "headers", "references", "nominal_receiver",
                           "comparison_row", "screw_references", "panel_sections"), namespace)


def inputs(pins):
    """Non-numerical joins; no geometry/reference arithmetic or array values."""
    helper = basis()
    report, model, manifest, rows = map(read, (RESOLVER / "comparison.json", GRAVITY / "model.json",
                                              GRAVITY / "model-inputs.json", GRAVITY / "row-identities.json"))
    require(report["status"] == "COMPLETED_BOUNDED_NUMERICAL_COMPARISON_WITH_EXPLICIT_GAPS"
            and report["post_execution_source_authentication"], "permanent source incomplete")
    require(report["load_case"] == "permanent-only" and report["selected_unfactored_gravity_column"] == 0
            and report["dead_load_factor"] == 1.1110134616260479
            and report["modeled_mass_kg"] == 225.19791414318078 and report["equipment_mass_kg"] == 25
            and report["equipment_multiplier_applied_once"] and report["additional_dead_load_multiplier"] == 1
            and all(report[k] == 0 for k in ("live_gravity_scale", "live_horizontal_scale", "live_moment_scale")),
            "permanent load contract differs")
    state = next(s for s in report["states"] if s["state"] == "permanent-only_gap")
    certificate = state["fixed_force_clearance_certificate"]
    require(state["gap_scale"] == 1 and state["status"] == "PASS_CONDITIONAL_WITH_BOUNDED_SEATING"
            and state["audit"]["force_bearing_rigid_rank"] == 296 and certificate["nullity"] == 4
            and certificate["bounded"] and not certificate["frame_state_accepted"]
            and not certificate["strict_active_tangent_stability_established"], "nominal limits differ")
    require(report["output_sha256"]["response.npz"] == pins[RESPONSE], "response binding differs")
    receipt = read(N14_RAW / "receipt.json")
    require(receipt["producer_sha256"] == pins[N14]
            and receipt["output_sha256"]["summary.json"] == pins[N14_RAW / "summary.json"], "N14 formula evidence differs")
    shared = (OPERATORS, PROJECTION, GRAVITY / "model.json", GRAVITY / "model-inputs.json", GRAVITY / "row-identities.json")
    require(all(report["source_sha256"][key(p)] == receipt["source_sha256"][key(p)] == pins[p] for p in shared),
            "permanent/N14 physical sources differ")
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "raw row order differs")
    require(model["material_binding"]["panel_group_factor"] == 1
            and model["material_binding"]["panel_targets"]["thickness_mm"] == 18.25625,
            "frozen panel material scenario differs")
    members = {m["member_id"]: m for m in manifest["members"]}
    connections = {c["axis_id"]: c for c in manifest["connections"] if c["kind"] == "panel_screw"}
    axial, lateral = {}, defaultdict(list)
    for row in rows:
        axis = row["row_id"].split("/")[0]
        if row["ownership"]["role"] == AXIAL:
            require(axis not in axial, "duplicate axial row")
            axial[axis] = row
        elif row["ownership"]["role"] == SHEAR:
            lateral[axis].append(row)
    require(len(connections) == len(axial) == 66 and set(connections) == set(axial) == set(lateral), "66-screw join differs")
    axes = []
    for axis, connection in sorted(connections.items()):
        source = connection["source_record"]
        panel, receiver = source["panel_member"], source["receiver_member"]
        components = [*lateral[axis], axial[axis]]
        require(len(components) == 3 and all({r["ownership"]["first_body"], r["ownership"]["second_body"]} == {panel, receiver}
                and r["ownership"]["point_mm"] == axial[axis]["ownership"]["point_mm"] for r in components), "screw components differ")
        require(members[panel]["member_kind"] == "panel" and members[receiver]["member_kind"] == "timber"
                and source["purchased_nominal_length_mm"] == 63.5, "existing receiver/product differs")
        axes.append(dict(axis_id=axis, panel=panel, receiver=receiver, rows=[r["row"] for r in components],
                         point_mm=axial[axis]["ownership"]["point_mm"], axis=connection["axis_xyz"],
                         source_axis_record=source, receiver_geometry=members[receiver]["reduced_geometry_descriptor"]))
    require(Counter(a["panel"] for a in axes) == {"main_upper_left": 12, "main_upper_right": 12,
            "main_lower_left": 12, "main_lower_right": 12, "kicker_left": 9, "kicker_right": 9}
            and len({(a["panel"], a["receiver"]) for a in axes}) == 22, "six-panel/22-group census differs")
    headers = {"operators": helper.headers(OPERATORS), "response": helper.headers(RESPONSE), "projection": helper.headers(PROJECTION)}
    for name, shape in {"H": [1888, 1888], "D": [1888, 300], "e": [1888, 12], "W": [300, 12], "F": [37647, 12]}.items():
        require(headers["operators"][name]["shape"] == shape, "operator header differs: " + name)
    for name, shape in {"raw_force_n": [1888], "lumped_q_mm": [1612], "rigid_coordinates": [300]}.items():
        require(headers["response"]["permanent-only_gap_" + name]["shape"] == shape, "response header differs: " + name)
    parser = helper.definitions(PARSER, ("parse_dof_lines", "parse_dof_file"),
                                {"Path": Path, "re": re, "AssessmentError": ValueError})
    labels = parser.parse_dof_file(DOF)
    require(len(labels) == 37647 and len(set(labels)) == 37647, "physical DOF join differs")
    authenticate(pins)
    return SimpleNamespace(pins=pins, helper=helper, comparison=report, source_state=state,
                           model=model, inputs=manifest, rows=rows, axes=axes, labels=labels, headers=headers)


def method(data):
    """Adapt four exact frozen expressions and summary census in a private AST."""
    helper = data.helper
    namespace = helper.panel_sections.__globals__
    replacements = {
        'data.comparison["dead_load_factor"]*W[:, 2*ci] + W[:, 2*ci+1]': 'data.comparison["dead_load_factor"]*W[:, 0]',
        'D @ rigid + data.comparison["dead_load_factor"]*e[:, 2*ci] + e[:, 2*ci+1] - H @ force':
            'D @ rigid + data.comparison["dead_load_factor"]*e[:, 0] - H @ force',
        'data.comparison["dead_load_factor"]*F[ids, 2*ci] + F[ids, 2*ci+1]': 'data.comparison["dead_load_factor"]*F[ids, 0]',
        'len(screws) == len({(s["case_id"], s["axis_id"]) for s in screws}) == 396 and len(panels) == 36':
            'len(screws) == len({(s["case_id"], s["axis_id"]) for s in screws}) == 66 and len(panels) == 6',
    }
    mappings = {ast.dump(ast.parse(old, mode="eval").body): ast.parse(new, mode="eval").body for old, new in replacements.items()}
    counts = Counter()

    class Adapt(ast.NodeTransformer):
        def visit(self, node):
            signature = ast.dump(node)
            if signature in mappings:
                counts[signature] += 1
                return ast.copy_location(copy.deepcopy(mappings[signature]), node)
            return super().visit(node)

    tree = ast.parse(N14.read_text(), filename=str(N14))
    assess = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "assess")
    assess = Adapt().visit(assess)
    require(all(counts[k] == 1 for k in mappings), "frozen recovery adapter pattern differs")
    summary = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "summarize")
    census = Counter()
    for node in ast.walk(summary):
        if isinstance(node, ast.Constant) and node.value in (396, 36):
            census[node.value] += 1
            node.value = {396: 66, 36: 6}[node.value]
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values, strict=True):
                if isinstance(k, ast.Constant) and k.value == "nominal_cases":
                    require(isinstance(v, ast.Constant) and v.value == 6, "summary case count differs")
                    v.value = 1
                    census["cases"] += 1
    require(census == {396: 3, 36: 1, "cases": 1}, "summary adapter patterns differ")
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    adapted = ast.fix_missing_locations(ast.Module(body=[future, assess, summary], type_ignores=[]))
    exec(compile(adapted, str(N14), "exec"), namespace)  # noqa: S102
    original_references, original_sections = namespace["references"], namespace["panel_sections"]

    def permanent_references():
        refs = original_references()
        saved = read(N14_RAW / "summary.json")["reference_catalog"]
        require(refs.heads == saved["heads"] and refs.withdrawal == saved["withdrawal"]
                and refs.lateral == saved["lateral"], "unchanged N14 unadjusted bases differ")
        refs.duration_factors = [CD]
        return refs

    def permanent_sections(*args):
        records = original_sections(*args)
        strength_keys = {"bending_nmm_per_mm", "tension_n_per_mm", "compression_n_per_mm", "transverse_shear_n_per_mm"}
        for record in records:
            require(record["CD"] == 1, "panel base duration differs")
            record["normal_duration_references"] = record["references"]
            record["references"] = {group: {k: value*CD if k in strength_keys else value for k, value in reference.items()}
                                    for group, reference in record["normal_duration_references"].items()}
            record["normal_duration_diagnostic_comparisons"] = record["comparisons"]
            record["comparisons"] = {group: {metric: helper.comparison_row(row["ratio"]/CD) for metric, row in metrics.items()}
                                     for group, metrics in record["normal_duration_diagnostic_comparisons"].items()}
            record["CD"] = CD
        return records

    namespace.update(references=permanent_references, panel_sections=permanent_sections)
    return SimpleNamespace(assess=namespace["assess"], summarize=namespace["summarize"])


def contract(data):
    return dict(schema="panel_permanent_completion/v1", status="PREPARED_NO_NUMERICAL_RECOVERY",
                source_state=data.source_state, source_headers=data.headers, wood_reference_CD=CD,
                source_response_sha256=PINS[RESPONSE], source_comparison_sha256=PINS[RESOLVER / "comparison.json"],
                load_basis={k: data.comparison[k] for k in ("modeled_mass_kg", "equipment_mass_kg", "dead_load_factor",
                            "selected_unfactored_gravity_column", "live_gravity_scale", "live_horizontal_scale", "live_moment_scale")},
                expected_counts={"screw_states": 66, "panel_states": 6, "screw_receiver_group_states": 22, "panel_cut_traces": 376},
                authority_scope={"reviewed_global_axes": 104, "unadopted_proposal_axes": 108, "Hillman_screws": 66},
                adapter_overrides=["one permanent-only nominal case", "gravity column zero only",
                                   "66/6 summary and recovery census", "CD0.9 once on unadjusted wood references"],
                known_answer_evidence={"N14_receipt": PINS[N14_RAW / "receipt.json"], "N14_summary": PINS[N14_RAW / "summary.json"],
                                       "new_tests_or_oracles": False},
                limits=["One saved nominal force/motion point; rank296/nullity4, no alternate-seating force envelope or strict stability acceptance.",
                        "Existing Hillman steel/profile, thread engagement, side-grain, pilot and contacting-face hypotheses remain unqualified.",
                        "Gross panel component means leave local rolling shear, hole/countersink ligaments, cutouts, plate interaction, buckling and serviceability unresolved.",
                        "Group4 is a reference sensitivity on saved Group1 elasticity; delivered plywood grade/layup/axis assumptions remain.",
                        "Absolute individual elastic motions and four internal static-bolt compatibility remain unavailable."],
                mechanics_evaluated=False, numerical_imports=False, **FLAGS)


def prepare(output=None):
    """Source-only manifest; optional fresh output receipt, no numerical imports."""
    if output is not None:
        return execute(output, False)
    data = inputs(source_pins())
    method(data)  # Compile and validate private source patterns; execute no arithmetic.
    authenticate(data.pins)
    return {**contract(data), "source_sha256": {key(p): h for p, h in sorted(data.pins.items())},
            "identities": data.axes, "API": {"prepare": "prepare(output=None)", "run": "run(output)"}}


def write(output, name, value, jsonl=False):
    with (output / name).open("x") as stream:
        if jsonl:
            for row in value:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        else:
            stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def execute(output, numerical):
    output = Path(output)
    require(not output.is_symlink() and not RAW.is_symlink(), "output/root symlink refused")
    output = output.resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned RAW child required")
    pins = source_pins()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    report = dict(schema="panel_permanent_completion/v1", status="STOP", mode="run" if numerical else "prepare", **FLAGS)
    error = None
    try:
        data = inputs(pins)
        report.update(contract(data))
        adapted = method(data)
        if numerical:
            require(platform.python_version() == "3.12.3" and importlib.metadata.version("numpy") == "2.5.2", "runtime differs from frozen response")
            result = adapted.assess(data)
            require((len(result["screws"]), len(result["panels"]), len(result["groups"]), len(result["cuts"])) == (66, 6, 22, 376),
                    "permanent census incomplete")
            for name, collection in (("screw-states.jsonl", "screws"), ("screw-groups.jsonl", "groups"),
                                     ("panel-balances.jsonl", "panels"), ("panel-cuts.jsonl", "cuts")):
                write(output, name, result[collection], True)
            report.update(adapted.summarize(result), status="COMPLETED_PERMANENT_REFERENCE_COMPARISON_WITH_EXPLICIT_GAPS",
                          mechanics_evaluated=True, numerical_imports=True)
        authenticate(pins)
    except Exception as caught:  # noqa: BLE001 -- retain a STOP receipt before re-raising.
        error = caught
        report.update(status="STOP", terminal_exception=f"{type(caught).__name__}: {caught}")
    sources = {key(p): h for p, h in sorted(pins.items())}
    write(output, "sources.json", sources)
    write(output, "summary.json", report)
    if error is not None:
        write(output, "stop.json", report)
    artifacts = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    write(output, "receipt.json", dict(schema="panel_permanent_completion_receipt/v1", status=report["status"],
          mode=report["mode"], producer_sha256=pins[Path(__file__).resolve()], source_sha256=sources,
          output_sha256=artifacts, sources_authenticated_before_and_after=error is None, **FLAGS))
    if error is not None:
        raise error
    return dict(status=report["status"], output=key(output), producer_sha256=pins[Path(__file__).resolve()],
                summary_sha256=sha(output / "summary.json"), receipt_sha256=sha(output / "receipt.json"), source_pin_count=len(pins))


def run(output):
    """Parent-only, one finite saved-state traversal; no equation system solve."""
    return execute(output, True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    print(json.dumps(prepare(args.output) if args.prepare else run(args.output), indent=2))
