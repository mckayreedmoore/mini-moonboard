"""Evaluate the common-shaft normal-v opening bound at both knee spines.

This bounded twelve-state diagnostic reuses saved common receiver fields and
fresh same-state actions. It checks field recovery and the complete radial
support intervals for the unchanged four-bore geometry. It establishes no
timber resistance, physical failure, or complete-joint acceptance.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import struct
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
RESUME = UPPER.parent
ROOT = next(path for path in HERE.parents if (path / "current-candidate.json").is_file())
COMMON = UPPER / "rawlocal/knee-common-shafts/attempt01"
SPINES = UPPER / "rawlocal/knee-spine-net-sections/attempt02/checks.json"
GRAVITY = UPPER / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = UPPER / "rawlocal/knee-bridge-frame/attempt02/response"
MEMBER = RESUME / "member-screen-attempt02/knee-bridge-gravity01"
RAW = HERE / "rawlocal/common-spine-opening"

CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
SIDES = ("left", "right")
ARITHMETIC_TOL = 1e-6
FORCE_CLOSURE_TOL_N = 1e-6
MOMENT_CLOSURE_TOL_NMM = 215.9e-6
SOURCE_BODY_FORCE_CLOSURE_TOL_N = 1e-6
SOURCE_BODY_MOMENT_CLOSURE_TOL_NMM = 215.9e-6
SAVED_MEMBER_FORCE_BALANCE_LIMIT_N = 0.1
SAVED_MEMBER_MOMENT_BALANCE_LIMIT_NMM = 2.0

COMMON_REPORT = COMMON / "report.json"
COMMON_RECEIPT = COMMON / "receipt.json"
COMMON_CONTRACT = COMMON / "input-contract.json"
COMMON_REFERENCE = COMMON / "engineering-reference.json"
FRESH_ASSESSMENT = GRAVITY / "operator-assessment.json"
FRESH_MODEL = GRAVITY / "model.json"
FRESH_OPERATORS = GRAVITY / "operators.npz"
FRESH_ROWS = GRAVITY / "row-identities.json"
FRAME_COMPARISON = FRAME / "comparison.json"
FRAME_RESPONSE = FRAME / "response.npz"
RESPONSE_SUMMARY = UPPER / "rawlocal/knee-bridge-response/attempt02/summary.json"
RESPONSE_RECEIPT = UPPER / "rawlocal/knee-bridge-response/attempt02/receipt.json"
RESPONSE_DEMANDS = UPPER / "rawlocal/knee-bridge-response/attempt02/global-demands.jsonl"
JOINT_REGISTER = UPPER / "rawlocal/working-joint-register/attempt03/register.json"
MEMBER_RESULTS = MEMBER / "member-results.json"
MEMBER_INPUTS = MEMBER / "inputs.json"
MEMBER_GEOMETRY = MEMBER / "geometry.json"
MEMBER_ACTIONS = MEMBER / "action-section-arrays.npz"

STATE_SHA256 = {
    "state-00.json": "073a42216510eb9338d1512e278dfa82753b1639a93ed6e18d87d88792299b10",
    "state-01.json": "9f506732b6592bf96412af7ae4a65457ea3d16c3c9293fb043269b30588ade79",
    "state-02.json": "024ca9345a3ffb60122d1d64b21b8cd07c61ad9ab1063459b728ceec92a7c5a4",
    "state-03.json": "e817ad753fec4764ef9ee01817c5981bbba8a657814f544e4e1fd349ab90974c",
    "state-04.json": "53cce46683db1d49d964d466b88535cfac79d9ded318a8451dc2fde505228f38",
    "state-05.json": "78f955b6be7a69756fee79fcc2d747e71fd4e6a9647c448cc1763409aee038ef",
    "state-06.json": "df5588a2fd0f6b9c543626e06a56b6935aab2425ccdc08cc91bca61340011088",
    "state-07.json": "e691027bf78db84a3da6fe81b23fd4d3b17a65267294debed9a5bd6a46eada0d",
    "state-08.json": "043b3c5937c8dc22615ac735e292ae9680a0b37f3713b3e9cefabb37b157422d",
    "state-09.json": "e081cd4e55b48d9677950206edf304180e9d5cb6615a2b3beb49d39d511b34c2",
    "state-10.json": "c67b0948a1d100240df2afd4f4b9b52073d8952732e0879b5c3656c053747ebc",
    "state-11.json": "d577df15f50a6948c3f9fca047c392d8709f802e73d6b8b22f2df403a992738d",
}

PINS = {
    COMMON_REPORT: "dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0",
    COMMON_RECEIPT: "7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda",
    COMMON_CONTRACT: "7a38255a5e4bfcc49e7e2fd74b12117de7673dca769c6b17611a29cd0aa0f3a6",
    COMMON_REFERENCE: "24b3eb2e865b00cf02fb448bbfb533cf37a11b56a37b8cce127cb928c0c34183",
    SPINES: "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
    FRESH_ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    FRESH_MODEL: "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    FRESH_OPERATORS: "7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f",
    FRESH_ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    FRAME_COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME_RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    RESPONSE_SUMMARY: "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    RESPONSE_RECEIPT: "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    RESPONSE_DEMANDS: "f0d9bb8a8a25775a2571692183860b209708111b089f16538f7eab5d9adbe4c3",
    JOINT_REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    MEMBER_RESULTS: "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    MEMBER_INPUTS: "34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457",
    MEMBER_GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER_ACTIONS: "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_spine.step": "081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0",
    ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_right_spine.step": "f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa",
}
PINS.update({COMMON / name: digest for name, digest in STATE_SHA256.items()})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def write_json(path: Path, value: dict) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def root_key(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def bind(pins: dict[Path, str], path: Path, expected: str) -> None:
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source leaves repository: " + str(path))
    require(path not in pins or pins[path] == expected, "conflicting source pin: " + str(path))
    require(sha(path) == expected, "changed source: " + str(path))
    pins[path] = expected


def authenticate(pins: dict[Path, str]) -> None:
    for path, expected in pins.items():
        require(sha(path) == expected, "source changed during build: " + str(path))


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def subtract(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def norm(vector: list[float]) -> float:
    return math.sqrt(dot(vector, vector))


def maximum_absolute(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def wrench_about(actions: list[dict], datum: list[float]) -> list[float]:
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    for action in actions:
        action_force = action["force_xyz_n"]
        free_couple = action["free_couple_xyz_nmm"]
        force = add(force, action_force)
        moment = add(moment, add(cross(subtract(action["point_xyz_mm"], datum), action_force), free_couple))
    return [*force, *moment]


def wrench_vector(record: dict) -> list[float]:
    return [*record["force_xyz_n"], *record["moment_xyz_nmm"]]


def translate_wrench(wrench: list[float], source_datum: list[float], target_datum: list[float]) -> list[float]:
    force = wrench[:3]
    moment = add(wrench[3:], cross(subtract(source_datum, target_datum), force))
    return [*force, *moment]


def wrench_vector_residual(actual: list[float], expected: list[float], label: str) -> list[float]:
    require(len(actual) == len(expected) == 6, label + " wrench dimension differs")
    residual = subtract(actual, expected)
    require(maximum_absolute(residual[:3]) <= SOURCE_BODY_FORCE_CLOSURE_TOL_N,
            label + " force wrench does not close")
    require(maximum_absolute(residual[3:]) <= SOURCE_BODY_MOMENT_CLOSURE_TOL_NMM,
            label + " moment wrench does not close")
    return residual


def wrench_record_residual(actual: list[float], expected: dict, label: str) -> list[float]:
    return wrench_vector_residual(actual, wrench_vector(expected), label)


def mean_body_node(model: dict, body: str) -> list[float]:
    node_ids = model["body_nodes"][body]
    require(node_ids, "fresh frame model has no physical nodes for spine")
    points = [model["physical_node_coordinates_mm"][str(node_id)] for node_id in node_ids]
    require(all(len(point) == 3 and all(math.isfinite(value) for value in point) for point in points),
            "fresh body node coordinates are invalid")
    return [sum(point[index] for point in points) / len(points) for index in range(3)]


def high_force(supports: list[list[float]], forces: list[float], cut: float) -> float:
    """Sum whole supported forces above cut; refuse any intersected support."""
    require(len(supports) == len(forces), "support/resultant count differs")
    result = 0.0
    for (lo, hi), force in zip(supports, forces, strict=True):
        require(lo <= hi, "reversed support interval")
        require(hi < cut or lo > cut, "cut intersects a radial force support")
        if lo > cut:
            result += force
    return float(result)


def npy_array(archive: zipfile.ZipFile, key: str, dtype: str, shape: tuple[int, ...]) -> list[float] | list[int]:
    with archive.open(key + ".npy") as stream:
        prefix = stream.read(8)
        require(prefix[:6] == b"\x93NUMPY" and prefix[6] in (1, 2, 3), "unsupported NPY header: " + key)
        header_length = int.from_bytes(stream.read(2 if prefix[6] == 1 else 4), "little")
        require(0 < header_length < 10000, "invalid NPY header: " + key)
        header = ast.literal_eval(stream.read(header_length).decode("utf-8"))
        require(header["descr"] == dtype and header["fortran_order"] is False, "array representation differs: " + key)
        require(tuple(header["shape"]) == shape, "array shape differs: " + key)
        count = math.prod(shape)
        width, code = (8, "d") if dtype == "<f8" else (8, "q") if dtype == "<i8" else (0, "")
        require(width > 0, "unsupported array dtype: " + dtype)
        payload = stream.read(width * count)
        require(len(payload) == width * count and stream.read(1) == b"", "array payload size differs: " + key)
        return list(struct.unpack("<" + str(count) + code, payload))


def array_rows(archive: zipfile.ZipFile, key: str, dtype: str, shape: tuple[int, int]) -> list[list[float]]:
    values = npy_array(archive, key, dtype, shape)
    width = shape[1]
    return [values[index : index + width] for index in range(0, len(values), width)]


def merge_manifest_sources(pins: dict[Path, str], source_sha256: dict[str, str]) -> None:
    for relative, digest in source_sha256.items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT), "manifest source leaves repository")
        bind(pins, path, digest)


def verify_common(pins: dict[Path, str]) -> tuple[dict, dict, dict, dict[str, dict]]:
    report = read_json(COMMON_REPORT)
    receipt = read_json(COMMON_RECEIPT)
    saved_contract = read_json(COMMON_CONTRACT)
    contract = saved_contract["contract"]
    require(report["schema"] == "knee_common_shafts/v1", "common report schema differs")
    require(report["status"] == "COMPLETE_12_CONDITIONAL_COMMON_RECEIVER_EQUILIBRIA", "common report is not complete")
    require(receipt["schema"] == "knee_common_shafts_receipt/v1", "common receipt schema differs")
    require(receipt["status"] == report["status"] and receipt["sources_unchanged_before_and_after"], "common receipt status differs")
    require(saved_contract["schema"] == "knee_common_shafts_contract/v1", "common input contract schema differs")
    require(contract["schema"] == "knee_bridge_continuous_shaft_fresh_contract/v1", "nested common contract schema differs")
    require(saved_contract["source_sha256"] == receipt["source_sha256"], "common source manifests disagree")
    merge_manifest_sources(pins, receipt["source_sha256"])
    flags = (
        "global_frame_feedback",
        "saved_global_pose_or_port_motion_replaced",
        "isolated_states_fitted_or_used_as_initial_iterates",
        "internal_v_ties_passive_field_qualified",
        "elastic_timber_field_qualified",
        "hardware_capacity_qualified",
        "complete_joint_acceptance",
        "proposal_adopted",
        "physical_release",
        "physical_failure_claimed",
        "native_or_CAD_execution",
    )
    require(all(report.get(flag) is False for flag in flags), "common report scope flags differ")
    require(all(receipt.get(flag) is False for flag in flags), "common receipt scope flags differ")
    require(all(saved_contract.get(flag) is False for flag in flags), "common contract scope flags differ")

    output_hashes = receipt["output_sha256"]
    expected_outputs = {"report.json", "input-contract.json", "engineering-reference.json", *STATE_SHA256}
    require(expected_outputs <= set(output_hashes), "common receipt omits required outputs")
    for name, digest in output_hashes.items():
        path = (COMMON / name).resolve()
        require(path.parent == COMMON.resolve(), "common output leaves frozen attempt")
        bind(pins, path, digest)
    require(len(report["states"]) == len(STATE_SHA256) == 12, "common report must contain twelve states")
    states = {}
    for row in report["states"]:
        path_name = row["path"]
        require(path_name in STATE_SHA256 and row["sha256"] == STATE_SHA256[path_name], "common state digest differs")
        state = read_json(COMMON / path_name)
        require(state["schema"] == "knee_common_two_shafts_state/v1", "common state schema differs")
        require(state["side"] == row["side"] and state["case_id"] == row["case_id"], "common state identity differs")
        require(state["status"] == "CONDITIONAL_COMMON_RECEIVER_EQUILIBRIUM" and state["combined_full_wrenches_closed"], "common state is not closed")
        require((state["side"], state["case_id"]) not in states, "duplicate common state")
        require(state["case_id"] in CASES and state["side"] in SIDES, "unexpected common state identity")
        require(all(state.get(flag) is False for flag in flags), "common state scope flags differ")
        states[state["side"], state["case_id"]] = state
    require(set(states) == {(side, case) for side in SIDES for case in CASES}, "common state coverage differs")
    require(set(contract["geometry"]) == {
        f"knee_outer_{side}_side_{number}" for side in SIDES for number in (1, 2)
    }, "common axes differ from the four existing side shafts")
    require(len(contract["boundaries"]) == 24 and len(saved_contract["packets"]) == 12, "common boundary count differs")
    fresh_sources = contract["fresh_load_sources"]
    for path in (FRESH_ASSESSMENT, FRAME_COMPARISON, FRAME_RESPONSE, RESPONSE_SUMMARY, RESPONSE_RECEIPT, RESPONSE_DEMANDS):
        require(fresh_sources.get(root_key(path)) == PINS[path], "common fresh-load authority binding differs")
    return report, saved_contract, contract, states


def verify_fresh_inputs(pins: dict[Path, str]) -> tuple[dict, dict, dict, dict, dict, dict]:
    assessment = read_json(FRESH_ASSESSMENT)
    model = read_json(FRESH_MODEL)
    frame = read_json(FRAME_COMPARISON)
    member_result = read_json(MEMBER_RESULTS)
    member_input = read_json(MEMBER_INPUTS)
    geometry = read_json(MEMBER_GEOMETRY)
    joint_register = read_json(JOINT_REGISTER)
    require(assessment["schema"] == "knee-bridge-gravity-operators/v1", "fresh gravity assessment schema differs")
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS", "fresh gravity operators are not current")
    require(assessment["case_ids"] == list(CASES), "fresh gravity case order differs")
    require(model["schema"] == "simple_corrected_frame_model/v1", "fresh gravity model schema differs")
    require(set(model["body_nodes"]) == set(model["body_names"]), "fresh model physical node ownership differs")
    require("knee_outer_left_spine" in model["body_nodes"] and "knee_outer_right_spine" in model["body_nodes"],
            "fresh gravity model omits a knee spine node set")
    require(frame["schema"] == "coupled_two_receiver_frame_clearance/v1", "fresh frame response schema differs")
    require(frame["response_sha256"] == PINS[FRAME_RESPONSE], "fresh frame response binding differs")
    require(member_result["schema"] == "same_state_six_case_timber_member_screen/v1", "fresh action source schema differs")
    require(member_result["status"] == "COMPLETE_CONDITIONAL_ELEMENTARY_MEMBER_SCREENS_NOT_QUALIFICATION", "fresh action source is incomplete")
    require(member_result["clearance_input_directory"] == root_key(FRAME), "member actions use another frame response")
    require(member_result["frame_operator_directory"] == root_key(GRAVITY), "member actions use another gravity operator")
    require(member_result["same_state_dead_load_factor"] == assessment["dead_load_factor"] == frame["dead_load_factor"], "fresh dead-load factor differs")
    require(member_input["selected_force_keys"] == [case + "_gap_raw_force_n" for case in CASES], "member action force keys differ")
    require(joint_register["schema"] == "working_six_case_joint_force_register/v1", "reviewed joint register schema differs")
    require(joint_register["status"] == "COMPLETE_SAVED_FORCE_INTEGRATION", "reviewed joint register is incomplete")
    require(joint_register["case_ids"] == list(CASES), "reviewed joint register case order differs")
    accounting = joint_register["accounting"]
    require(accounting["total_unique_frame_bolt_axes"] == 104, "reviewed global axis census differs")
    require(accounting["corrected_continuous_knee_shafts"] == 4, "reviewed shared knee shaft census differs")
    require(set(accounting["shared_physical_axes"]) == {
        f"knee_outer_{side}_side_{number}" for side in SIDES for number in (1, 2)
    }, "reviewed shared knee shaft identities differ")
    require(member_result["source_sha256"] == member_input["source_sha256"], "member action source manifests disagree")
    require(geometry["members"]["knee_outer_left_spine"]["member_kind"] == "timber"
            and geometry["members"]["knee_outer_right_spine"]["member_kind"] == "timber", "fresh spine actions lack timber bodies")
    required_source_paths = (
        FRESH_ASSESSMENT,
        FRESH_MODEL,
        FRESH_OPERATORS,
        FRESH_ROWS,
        FRAME_COMPARISON,
        FRAME_RESPONSE,
    )
    for path in required_source_paths:
        require(member_result["source_sha256"].get(root_key(path)) == PINS[path], "fresh member actions do not bind " + str(path))
    for manifest in (assessment,):
        for name, digest in manifest["output_sha256"].items():
            path = (GRAVITY / name).resolve()
            require(path.parent == GRAVITY.resolve(), "fresh gravity output leaves attempt")
            bind(pins, path, digest)
    for name, digest in member_result["output_sha256"].items():
        path = (MEMBER / name).resolve()
        require(path.parent == MEMBER.resolve(), "fresh member output leaves attempt")
        bind(pins, path, digest)
    merge_manifest_sources(pins, member_result["source_sha256"])
    return assessment, frame, member_result, member_input, geometry, model


def local_frame(geometry: dict) -> tuple[list[float], list[float]]:
    rows = geometry["grain_frame_rows_xyz"]
    require(len(rows) == 3 and all(len(row) == 3 for row in rows), "spine grain frame shape differs")
    for i in range(3):
        for j in range(3):
            expected = 1.0 if i == j else 0.0
            require(abs(dot(rows[i], rows[j]) - expected) <= 1e-8, "spine grain frame is not orthonormal")
    return rows[0], rows[2]


def line_distance(point: list[float], origin: list[float], direction: list[float]) -> tuple[float, float]:
    delta = subtract(point, origin)
    projection = dot(delta, direction)
    perpendicular = subtract(delta, [projection * value for value in direction])
    return norm(perpendicular), projection


def find_bore_for_axis(axis: dict, bores: list[dict]) -> dict:
    datum = axis["datum_mm"]
    direction = axis["bolt_axis_xyz"]
    matches = []
    for bore in bores:
        bore_direction = bore["axis_unit_global_xyz"]
        require(abs(abs(dot(direction, bore_direction)) - 1.0) <= 1e-8, "common shaft axis is not parallel to a saved spine bore")
        distance, _ = line_distance(datum, bore["axis_origin_global_xyz_mm"], bore_direction)
        if distance <= ARITHMETIC_TOL:
            matches.append(bore)
    require(len(matches) == 1, "common shaft does not map to one unchanged spine bore")
    return matches[0]


def find_bore_for_point(point: list[float], bores: list[dict]) -> dict:
    matches = []
    for bore in bores:
        direction = bore["axis_unit_global_xyz"]
        distance, axial = line_distance(point, bore["axis_origin_global_xyz_mm"], direction)
        interval = bore["saved_axis_parameter_interval_mm"]
        if distance <= ARITHMETIC_TOL and interval[0] - ARITHMETIC_TOL <= axial <= interval[1] + ARITHMETIC_TOL:
            matches.append(bore)
    require(len(matches) == 1, "fresh bolt point does not map to one saved spine bore support")
    return matches[0]


def fresh_spine_actions(
    archive: zipfile.ZipFile,
    member: dict,
    model: dict,
    body: str,
    spine_geometry: dict,
    case: str,
    common_bore_ids: set[str],
    common_axis_geometry: dict[str, dict],
    cut_v_mm: float,
) -> dict:
    action_ids = member["point_action_ids"]
    roles = member["point_action_roles"]
    require(len(action_ids) == len(roles), "fresh action identity/role counts differ")
    count = len(action_ids)
    points = array_rows(archive, body + "__point_xyz_mm", "<f8", (count, 3))
    point_rows = npy_array(archive, body + "__point_rows", "<i8", (count,))
    values = array_rows(archive, case + "__" + body + "__point_force_free_couple_xyz", "<f8", (count, 6))
    require(all(math.isfinite(value) for row in (*points, *values) for value in row), "fresh spine action array is nonfinite")
    _, local_v = local_frame(spine_geometry)
    body_datum = mean_body_node(model, body)
    require(
        [role == "discrete_body_load" for role in roles] == [row == -1 for row in point_rows],
        "fresh physical gravity row ownership differs",
    )
    bores = spine_geometry["bores"]
    expected_bores = {bore["axis_id"] for bore in bores}
    bore_forces = {bore_id: 0.0 for bore_id in expected_bores - common_bore_ids}
    source_axis_forces: dict[str, float] = {}
    source_axis_bores: dict[str, str] = {}
    axis_counts: dict[str, int] = {}
    common_axis_counts = {
        axis_id: {"candidate_bolt_lateral_plane": 0, "physical_bolt_outer_seat_tension": 0}
        for axis_id in common_axis_geometry
    }
    common_axis_wrenches = {axis_id: [0.0] * 6 for axis_id in common_axis_geometry}
    common_axis_actions = {axis_id: [] for axis_id in common_axis_geometry}
    all_actions = []
    fixed_actions = []
    nonbore_actions = []
    body_load_actions = []
    for index, (point, value, role, action_id) in enumerate(zip(points, values, roles, action_ids, strict=True)):
        require(
            role in (
                "candidate_bolt_lateral_plane",
                "physical_bolt_outer_seat_tension",
                "timber_or_panel_contact",
                "discrete_body_load",
            ),
            "unhandled fresh spine action role: " + role,
        )
        force = value[:3]
        free_couple = value[3:]
        force_v = dot(force, local_v)
        v_station = dot(subtract(point, spine_geometry["start_xyz_mm"]), local_v)
        action = {
            "source_row": int(point_rows[index]),
            "action_id": action_id,
            "role": role,
            "point_xyz_mm": point,
            "force_xyz_n": force,
            "free_couple_xyz_nmm": free_couple,
            "local_v_station_mm": v_station,
            "local_v_force_n": force_v,
            "above_cut": v_station > cut_v_mm,
        }
        all_actions.append(action)
        common_axis_id = None
        if role in ("candidate_bolt_lateral_plane", "physical_bolt_outer_seat_tension"):
            require("/" in action_id, "fresh bolt action id lacks an axis prefix")
            candidate_axis_id = action_id.rsplit("/", 1)[0]
            if candidate_axis_id in common_axis_geometry:
                common_axis_id = candidate_axis_id
                common_axis_counts[candidate_axis_id][role] += 1
                datum = common_axis_geometry[candidate_axis_id]["datum_mm"]
                point_wrench = [*force, *add(cross(subtract(point, datum), force), free_couple)]
                common_axis_wrenches[candidate_axis_id] = add(common_axis_wrenches[candidate_axis_id], point_wrench)
                common_axis_actions[candidate_axis_id].append(action)
        if role == "candidate_bolt_lateral_plane":
            axis_id = action_id.rsplit("/", 1)[0]
            bore = find_bore_for_point(point, bores)
            source_axis_bores[axis_id] = bore["axis_id"]
            axis_counts[axis_id] = axis_counts.get(axis_id, 0) + 1
            source_axis_forces[axis_id] = source_axis_forces.get(axis_id, 0.0) + force_v
            if common_axis_id is None:
                fixed_actions.append(action)
                bore_forces[bore["axis_id"]] += force_v
        elif common_axis_id is None:
            fixed_actions.append(action)
            nonbore_actions.append(action)
            if role == "discrete_body_load":
                body_load_actions.append(action)
    side = body.split("_")[2]
    expected_axes = {
        f"knee_outer_{side}_post_1",
        f"knee_outer_{side}_post_2",
        f"knee_outer_{side}_side_1",
        f"knee_outer_{side}_side_2",
    }
    require(set(axis_counts) == expected_axes and all(count == 2 for count in axis_counts.values()), "fresh spine bore action census differs")
    require(set(source_axis_bores.values()) == expected_bores, "fresh bolt actions do not cover the four saved bore axes")
    require({source_axis_bores[axis] for axis in source_axis_bores if axis.endswith(("_side_1", "_side_2"))} == common_bore_ids,
            "common side actions do not map to the two shared bores")
    require({source_axis_bores[axis] for axis in source_axis_bores if axis.endswith(("_post_1", "_post_2"))} == expected_bores - common_bore_ids,
            "retained post actions do not map to the lower bores")
    require(set(common_axis_geometry) == {
        f"knee_outer_{side}_side_{number}" for number in (1, 2)
    }, "common axis action census differs")
    require(all(counts == {"candidate_bolt_lateral_plane": 2, "physical_bolt_outer_seat_tension": 1}
                for counts in common_axis_counts.values()), "common axis source action role census differs")
    require(all(abs(action["local_v_station_mm"] - cut_v_mm) > ARITHMETIC_TOL for action in fixed_actions),
            "fresh fixed point action lies on the local-v cut")
    source_body_wrench = wrench_about(all_actions, body_datum)
    fixed_body_wrench = wrench_about(fixed_actions, body_datum)
    body_load_wrench = wrench_about(body_load_actions, body_datum)
    nonbore_above = sum(action["local_v_force_n"] for action in nonbore_actions if action["above_cut"])
    body_load_above = sum(action["local_v_force_n"] for action in body_load_actions if action["above_cut"])
    fixed_above = sum(action["local_v_force_n"] for action in fixed_actions if action["above_cut"])
    fixed_below = sum(action["local_v_force_n"] for action in fixed_actions if not action["above_cut"])
    return {
        "retained_lower_bore_force_v_n_by_bore": bore_forces,
        "fresh_source_force_v_n_by_axis": source_axis_forces,
        "fresh_common_side_axis_actions_replaced_by_common_fields": True,
        "fresh_source_axis_to_bore": source_axis_bores,
        "common_axis_source_action_counts": common_axis_counts,
        "common_axis_source_actions": common_axis_actions,
        "common_axis_source_wrench_about_axis_datum": common_axis_wrenches,
        "fresh_nonbore_actions": nonbore_actions,
        "fresh_nonbore_action_count": len(nonbore_actions),
        "fresh_nonbore_actions_retained_at_source_points": True,
        "fresh_body_load_actions": body_load_actions,
        "fresh_body_load_action_count": len(body_load_actions),
        "fresh_body_load_wrench_about_node_mean": body_load_wrench,
        "fresh_body_load_above_cut_local_v_force_n": body_load_above,
        "fresh_nonbore_above_cut_local_v_force_n": nonbore_above,
        "fixed_source_actions_above_cut_local_v_force_n": fixed_above,
        "fixed_source_actions_below_cut_local_v_force_n": fixed_below,
        "source_body_datum_xyz_mm": body_datum,
        "source_body_wrench_about_node_mean": source_body_wrench,
        "fixed_source_body_wrench_about_node_mean": fixed_body_wrench,
        "fresh_point_actions_reused": count,
    }


def validate_spine_bore_sample(
    field: dict,
    bore: dict,
    spine_geometry: dict,
    local_v: list[float],
    shaft_interval: list[float],
) -> None:
    point = field["reference_point_mm"]
    direction = bore["axis_unit_global_xyz"]
    distance, axial = line_distance(point, bore["axis_origin_global_xyz_mm"], direction)
    bore_interval = bore["saved_axis_parameter_interval_mm"]
    require(
        bore_interval[0] - ARITHMETIC_TOL <= axial <= bore_interval[1] + ARITHMETIC_TOL,
        "common bore field point leaves the mapped finite bore-axis interval",
    )
    require(distance <= bore["radius_mm"] + ARITHMETIC_TOL, "common bore field point leaves its radial support")
    grain_axis, _ = local_frame(spine_geometry)
    relative = subtract(point, spine_geometry["start_xyz_mm"])
    grain_station = dot(relative, grain_axis)
    saved_grain_interval = bore["saved_grain_interval_mm"]
    require(
        saved_grain_interval[0] - ARITHMETIC_TOL <= grain_station <= saved_grain_interval[1] + ARITHMETIC_TOL,
        "common bore field point leaves the mapped axial grain interval",
    )
    support = [
        bore["transverse_center_mm"] - bore["radius_mm"],
        bore["transverse_center_mm"] + bore["radius_mm"],
    ]
    local_v_station = dot(relative, local_v)
    require(
        support[0] - ARITHMETIC_TOL <= local_v_station <= support[1] + ARITHMETIC_TOL,
        "common bore field point leaves the full local-v radial support",
    )
    require(
        shaft_interval[0] - ARITHMETIC_TOL <= field["x_mm"] <= shaft_interval[1] + ARITHMETIC_TOL,
        "common bore field station leaves the physical shaft receiver interval",
    )


def receiver_field_recovery(
    shaft: dict,
    receiver: str,
    datum: list[float],
    local_v: list[float],
    spine_support: tuple[dict, dict, list[float]] | None = None,
) -> dict:
    force_sum = [0.0, 0.0, 0.0]
    moment_sum = [0.0, 0.0, 0.0]
    bore_count = 0
    seat_point_count = 0
    bore_v_sum = 0.0
    for field in shaft["bore_fields"]:
        if field["receiver"] != receiver:
            continue
        point = field["reference_point_mm"]
        force = field["force_on_wood_xyz_n"]
        require(len(point) == len(force) == 3, "common bore field dimensions differ")
        require(all(math.isfinite(value) for value in (*point, *force)), "common bore field is nonfinite")
        if spine_support is not None:
            spine_geometry, bore, shaft_interval = spine_support
            validate_spine_bore_sample(field, bore, spine_geometry, local_v, shaft_interval)
        force_sum = add(force_sum, force)
        moment_sum = add(moment_sum, cross(subtract(point, datum), force))
        bore_v_sum += dot(force, local_v)
        bore_count += 1
    for seat in shaft["outer_seat_fields"]:
        if seat["receiver"] != receiver:
            continue
        traction = seat["point_tractions"]["wood_contact"]
        require(traction["on"] == "receiver", "outer-seat closure selected the wrong contact side")
        points = traction["reference_points_mm"]
        forces = traction["point_forces_xyz_n"]
        require(len(points) == len(forces) > 0, "outer-seat force point count differs")
        for point, force in zip(points, forces, strict=True):
            require(len(point) == len(force) == 3, "outer-seat point dimensions differ")
            require(all(math.isfinite(value) for value in (*point, *force)), "outer-seat point field is nonfinite")
            force_sum = add(force_sum, force)
            moment_sum = add(moment_sum, cross(subtract(point, datum), force))
            seat_point_count += 1
            require(abs(dot(force, local_v)) <= ARITHMETIC_TOL, "common outer-seat traction has local-v force")
    target_record = next(record for record in shaft["receivers"] if record["receiver"] == receiver)
    target = target_record["independently_recovered_connector_wrench"]
    original = target_record["original_isolated_source_wrench"]
    updated = target_record["independently_recovered_connector_wrench"]
    redistribution = target_record["redistribution_from_original_source"]
    force_residual = subtract(force_sum, target["force_xyz_n"])
    moment_residual = subtract(moment_sum, target["moment_xyz_nmm"])
    require(bore_count > 0 or seat_point_count > 0, "receiver has no physical saved point field")
    require(maximum_absolute(force_residual) <= FORCE_CLOSURE_TOL_N, "common receiver point forces do not close")
    require(maximum_absolute(moment_residual) <= MOMENT_CLOSURE_TOL_NMM, "common receiver point moments do not close")
    delta_force = subtract(updated["force_xyz_n"], original["force_xyz_n"])
    delta_moment = subtract(updated["moment_xyz_nmm"], original["moment_xyz_nmm"])
    require(maximum_absolute(subtract(delta_force, redistribution["force_xyz_n"])) <= FORCE_CLOSURE_TOL_N,
            "common updated/original force difference differs")
    require(maximum_absolute(subtract(delta_moment, redistribution["moment_xyz_nmm"])) <= MOMENT_CLOSURE_TOL_NMM,
            "common updated/original moment difference differs")
    return {
        "axis_id": shaft["axis_id"],
        "receiver": receiver,
        "wrench_datum_mm": datum,
        "original_isolated_source_wrench": original,
        "independently_recovered_connector_wrench": updated,
        "redistribution_from_original_source": redistribution,
        "saved_point_field_wrench_about_axis_datum": {
            "force_xyz_n": force_sum,
            "moment_xyz_nmm": moment_sum,
        },
        "point_field_closure_residual": {
            "force_xyz_n": force_residual,
            "moment_xyz_nmm": moment_residual,
        },
        "bore_samples": bore_count,
        "outer_seat_wood_contact_points": seat_point_count,
        "bore_resultant_v_force_n": bore_v_sum,
    }


def prepare_geometry(spines: dict, contract: dict) -> dict:
    geometry = spines["geometry"]
    require(set(geometry) == {f"knee_outer_{side}_spine" for side in SIDES}, "saved spine geometry census differs")
    output = {}
    for side in SIDES:
        body = f"knee_outer_{side}_spine"
        item = geometry[body]
        _, local_v = local_frame(item)
        bores = item["bores"]
        require(len(bores) == 4 and all(abs(bore["radius_mm"] - 3.75) <= ARITHMETIC_TOL for bore in bores),
                "expected the unchanged four 7.5 mm spine bores")
        ordered = sorted(bores, key=lambda bore: bore["transverse_center_mm"])
        high, second_high = ordered[-1], ordered[-2]
        require(high["axis_id"].endswith("facet006") and second_high["axis_id"].endswith("facet007"),
                "high-v bore ordering differs from the saved four-bore geometry")
        lower, upper = second_high["transverse_center_mm"] + second_high["radius_mm"], high["transverse_center_mm"] - high["radius_mm"]
        require(upper > lower + ARITHMETIC_TOL, "no clear gap between complete high-v bore supports")
        cut = (lower + upper) / 2
        supports = [
            [bore["transverse_center_mm"] - bore["radius_mm"], bore["transverse_center_mm"] + bore["radius_mm"]]
            for bore in ordered
        ]
        common_bore_ids = set()
        axis_bore = {}
        for number in (1, 2):
            axis_id = f"knee_outer_{side}_side_{number}"
            axis = contract["geometry"][axis_id]
            matched = find_bore_for_axis(axis, bores)
            expected_facet = "facet007" if number == 1 else "facet006"
            require(matched["axis_id"].endswith(expected_facet), "common side axis maps to an unexpected spine bore")
            spine_receiver = next(record for record in axis["receivers"] if record["member"] == body)
            require(abs(spine_receiver["bore_diameter_mm"] / 2 - matched["radius_mm"]) <= ARITHMETIC_TOL,
                    "common shaft and unchanged spine bore radii differ")
            axis_bore[axis_id] = matched["axis_id"]
            common_bore_ids.add(matched["axis_id"])
        output[side] = {
            "body": body,
            "local_v_xyz": local_v,
            "bores_low_to_high_v": ordered,
            "supports_low_to_high_v_mm": supports,
            "clear_cut_interval_mm": [lower, upper],
            "cut_v_mm": cut,
            "high_bore_id": high["axis_id"],
            "second_high_bore_id": second_high["axis_id"],
            "common_axis_to_bore": axis_bore,
            "common_bore_ids": common_bore_ids,
        }
    return output


def verify_spine_step_identity(spines: dict, member_geometry: dict) -> dict[str, dict[str, str]]:
    """Bind saved four-bore references to the unchanged fresh member STEP files."""
    output = {}
    for side in SIDES:
        body = f"knee_outer_{side}_spine"
        reference = spines["geometry"][body]["finished_step_binding"]
        member = member_geometry["members"][body]
        path = reference["path"]
        digest = reference["file_sha256"]
        require(path == member["current_finished_step"], "spine section and fresh member STEP paths differ")
        require(digest == member["current_finished_step_sha256"], "spine section and fresh member STEP hashes differ")
        require(digest == member["original_finished_step_sha256"], "fresh member STEP is not the reviewed original solid")
        require(member["replaced_original_bore_features"] == [], "fresh member geometry replaces a reviewed spine bore")
        require(PINS[(ROOT / path).resolve()] == digest, "spine STEP identity lacks its exact direct pin")
        output[body] = {"path": path, "sha256": digest}
    return output


def build(output: Path) -> dict:
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate rawlocal/common-spine-opening child")
    pins: dict[Path, str] = {}
    for path, digest in PINS.items():
        bind(pins, path, digest)
    producer = Path(__file__).resolve()
    bind(pins, producer, sha(producer))
    common_report, _saved_contract, contract, common_states = verify_common(pins)
    _assessment, _frame, member_results, _member_inputs, member_geometry, model = verify_fresh_inputs(pins)
    spine_checks = read_json(SPINES)
    require(spine_checks["schema"] == "knee-spine-two-body-nominal-opening-section-references-v1", "spine geometry schema differs")
    step_identities = verify_spine_step_identity(spine_checks, member_geometry)
    geometry = prepare_geometry(spine_checks, contract)
    member_records = member_geometry["members"]
    results = []
    with zipfile.ZipFile(MEMBER_ACTIONS) as archive:
        for side in SIDES:
            geom = geometry[side]
            body = geom["body"]
            member = member_records[body]
            for case in CASES:
                state = common_states[side, case]
                common_axis_geometry = {
                    axis_id: contract["geometry"][axis_id] for axis_id in geom["common_axis_to_bore"]
                }
                fresh = fresh_spine_actions(
                    archive,
                    member,
                    model,
                    body,
                    spine_checks["geometry"][body],
                    case,
                    geom["common_bore_ids"],
                    common_axis_geometry,
                    geom["cut_v_mm"],
                )
                bore_force_by_id = dict(fresh["retained_lower_bore_force_v_n_by_bore"])
                shaft_records = {shaft["axis_id"]: shaft for shaft in state["shafts"]}
                require(set(shaft_records) == set(geom["common_axis_to_bore"]), "common state axes differ from reviewed side shafts")
                member_case = next(record for record in member_results["cases"] if record["case_id"] == case)
                member_summary = next(record for record in member_case["members"] if record["member"] == body)
                source_body_residual = wrench_record_residual(
                    fresh["source_body_wrench_about_node_mean"],
                    member_summary["whole_member_balance"],
                    "fresh source spine body",
                )
                source_body_report = wrench_vector(member_summary["whole_member_balance"])
                require(maximum_absolute(source_body_report[:3]) <= SAVED_MEMBER_FORCE_BALANCE_LIMIT_N,
                        "fresh source spine force balance exceeds its saved member-screen limit")
                require(maximum_absolute(source_body_report[3:]) <= SAVED_MEMBER_MOMENT_BALANCE_LIMIT_NMM,
                        "fresh source spine moment balance exceeds its saved member-screen limit")
                body_load_residual = wrench_record_residual(
                    fresh["fresh_body_load_wrench_about_node_mean"],
                    member_summary["mapped_body_load_wrench_about_node_mean"],
                    "fresh mapped body-load",
                )
                receiver_closures = []
                spine_receiver_closures = {}
                source_common_wrench_body_datum = [0.0] * 6
                updated_common_wrench_body_datum = [0.0] * 6
                common_axis_body_audits = []
                for axis_id, bore_id in geom["common_axis_to_bore"].items():
                    shaft = shaft_records[axis_id]
                    axis = contract["geometry"][axis_id]
                    receiver_names = axis["receiver_order"]
                    require(len(receiver_names) == 3, "common shaft receiver census differs")
                    for receiver in receiver_names:
                        spine_support = None
                        if receiver == body:
                            bore = next(item for item in geom["bores_low_to_high_v"] if item["axis_id"] == bore_id)
                            shaft_interval = next(
                                item["interval_from_head_wood_face_mm"]
                                for item in axis["receivers"]
                                if item["member"] == body
                            )
                            spine_support = (spine_checks["geometry"][body], bore, shaft_interval)
                        closure = receiver_field_recovery(
                            shaft, receiver, axis["datum_mm"], geom["local_v_xyz"], spine_support
                        )
                        receiver_closures.append(closure)
                        if receiver == body:
                            spine_receiver_closures[axis_id] = closure
                    spine_closure = spine_receiver_closures[axis_id]
                    original_action_wrench = fresh["common_axis_source_wrench_about_axis_datum"][axis_id]
                    original_connector_wrench = spine_closure["original_isolated_source_wrench"]
                    original_source_residual = wrench_record_residual(
                        original_action_wrench,
                        original_connector_wrench,
                        "fresh common-axis original source " + axis_id,
                    )
                    updated_field_wrench = spine_closure["saved_point_field_wrench_about_axis_datum"]
                    original_at_body_datum = translate_wrench(
                        original_action_wrench, axis["datum_mm"], fresh["source_body_datum_xyz_mm"]
                    )
                    updated_at_body_datum = translate_wrench(
                        wrench_vector(updated_field_wrench), axis["datum_mm"], fresh["source_body_datum_xyz_mm"]
                    )
                    source_common_wrench_body_datum = add(source_common_wrench_body_datum, original_at_body_datum)
                    updated_common_wrench_body_datum = add(updated_common_wrench_body_datum, updated_at_body_datum)
                    common_axis_body_audits.append(
                        {
                            "axis_id": axis_id,
                            "source_axis_actions_about_axis_datum": original_action_wrench,
                            "original_isolated_source_wrench": original_connector_wrench,
                            "original_source_action_closure_residual": original_source_residual,
                            "updated_saved_bore_plus_wood_seat_field_wrench_about_axis_datum": updated_field_wrench,
                            "original_source_wrench_about_body_datum": original_at_body_datum,
                            "updated_field_wrench_about_body_datum": updated_at_body_datum,
                        }
                    )
                    spine_v_force = spine_closure["bore_resultant_v_force_n"]
                    require(bore_id not in bore_force_by_id, "updated common bore would double-count a fresh source force")
                    bore_force_by_id[bore_id] = spine_v_force
                source_body_wrench = fresh["source_body_wrench_about_node_mean"]
                fixed_body_wrench = fresh["fixed_source_body_wrench_about_node_mean"]
                source_body_rebuild_residual = wrench_vector_residual(
                    add(fixed_body_wrench, source_common_wrench_body_datum),
                    source_body_wrench,
                    "fresh source fixed plus common-axis body",
                )
                updated_body_wrench = add(fixed_body_wrench, updated_common_wrench_body_datum)
                updated_body_expected = add(
                    subtract(source_body_wrench, source_common_wrench_body_datum),
                    updated_common_wrench_body_datum,
                )
                updated_body_accounting_residual = wrench_vector_residual(
                    updated_body_wrench,
                    updated_body_expected,
                    "updated spine body point-field accounting",
                )
                body_wrench_accounting = {
                    "datum_xyz_mm": fresh["source_body_datum_xyz_mm"],
                    "source_action_wrench_about_node_mean": source_body_wrench,
                    "source_screen_wrench_about_node_mean": source_body_report,
                    "source_action_to_screen_residual": source_body_residual,
                    "fresh_body_load_wrench_about_node_mean": fresh["fresh_body_load_wrench_about_node_mean"],
                    "fresh_body_load_screen_wrench_about_node_mean": member_summary["mapped_body_load_wrench_about_node_mean"],
                    "fresh_body_load_to_screen_residual": body_load_residual,
                    "fixed_source_action_wrench_about_node_mean": fixed_body_wrench,
                    "removed_common_source_wrenches_about_node_mean": source_common_wrench_body_datum,
                    "source_fixed_plus_common_rebuild_residual": source_body_rebuild_residual,
                    "updated_common_field_wrenches_about_node_mean": updated_common_wrench_body_datum,
                    "updated_body_wrench_about_node_mean": updated_body_wrench,
                    "updated_body_expected_from_source_replacement": updated_body_expected,
                    "updated_body_accounting_residual": updated_body_accounting_residual,
                    "common_axis_replacements": common_axis_body_audits,
                    "updated_body_local_v_resultant_n": dot(updated_body_wrench[:3], geom["local_v_xyz"]),
                }
                ordered_ids = [bore["axis_id"] for bore in geom["bores_low_to_high_v"]]
                require(set(bore_force_by_id) == set(ordered_ids), "four-bore signed v force census incomplete")
                bore_forces = [bore_force_by_id[bore_id] for bore_id in ordered_ids]
                bore_signed_above = high_force(geom["supports_low_to_high_v_mm"], bore_forces, geom["cut_v_mm"])
                require(all(math.isfinite(value) for value in bore_forces), "nonfinite bore resultant")
                require(len(receiver_closures) == 6, "each common state must recover both shafts and three receivers")
                support_by_bore = dict(zip(ordered_ids, geom["supports_low_to_high_v_mm"], strict=True))
                common_field_v_by_bore = {
                    geom["common_axis_to_bore"][axis_id]: spine_receiver_closures[axis_id]["bore_resultant_v_force_n"]
                    for axis_id in geom["common_axis_to_bore"]
                }
                common_above = sum(
                    force_v for bore_id, force_v in common_field_v_by_bore.items()
                    if support_by_bore[bore_id][0] > geom["cut_v_mm"]
                )
                common_below = sum(
                    force_v for bore_id, force_v in common_field_v_by_bore.items()
                    if support_by_bore[bore_id][1] < geom["cut_v_mm"]
                )
                fixed_nonbore_above = fresh["fresh_nonbore_above_cut_local_v_force_n"]
                signed = bore_signed_above + fixed_nonbore_above
                direct_updated_above = fresh["fixed_source_actions_above_cut_local_v_force_n"] + common_above
                direct_updated_below = fresh["fixed_source_actions_below_cut_local_v_force_n"] + common_below
                require(abs(signed - direct_updated_above) <= SOURCE_BODY_FORCE_CLOSURE_TOL_N,
                        "necessary normal resultant differs from direct updated pointfield above the cut")
                updated_body_v_force = dot(updated_body_wrench[:3], geom["local_v_xyz"])
                half_sum_residual = direct_updated_above + direct_updated_below - updated_body_v_force
                require(abs(half_sum_residual) <= SOURCE_BODY_FORCE_CLOSURE_TOL_N,
                        "updated above/below force halves do not match the complete body resultant")
                cut_half_accounting = {
                    "signed_updated_pointfield_above_cut_v_force_n": direct_updated_above,
                    "signed_updated_pointfield_below_cut_v_force_n": direct_updated_below,
                    "above_plus_below_v_force_n": direct_updated_above + direct_updated_below,
                    "complete_updated_body_v_force_n": updated_body_v_force,
                    "above_below_to_body_resultant_residual_n": half_sum_residual,
                    "above_below_sum_matches_updated_body_resultant": True,
                }
                results.append(
                    {
                        "side": side,
                        "body": body,
                        "case_id": case,
                        "common_state_path": next(row["path"] for row in common_report["states"] if row["side"] == side and row["case_id"] == case),
                        "cut_local_v_mm": geom["cut_v_mm"],
                        "clear_cut_interval_local_v_mm": geom["clear_cut_interval_mm"],
                        "complete_radial_support_intervals_local_v_mm": {
                            bore_id: support for bore_id, support in zip(ordered_ids, geom["supports_low_to_high_v_mm"], strict=True)
                        },
                        "signed_bore_v_resultants_n_low_to_high_v": {
                            bore_id: bore_force_by_id[bore_id] for bore_id in ordered_ids
                        },
                        "signed_bore_opening_resultant_above_cut_n": bore_signed_above,
                        "fixed_fresh_nonbore_resultant_above_cut_n": fixed_nonbore_above,
                        "signed_required_normal_v_resultant_n": signed,
                        "direct_updated_pointfield_above_cut_v_resultant_n": direct_updated_above,
                        "direct_cut_pointfield_above_matches_necessary_resultant": True,
                        "cut_half_accounting": cut_half_accounting,
                        "minimum_required_timber_tension_n": max(0.0, signed),
                        "zero_perpendicular_tension_necessary_condition_pass": signed <= ARITHMETIC_TOL,
                        "fresh_action_audit": fresh,
                        "source_and_updated_body_wrench_accounting": body_wrench_accounting,
                        "common_axis_records": [
                            {
                                "axis_id": axis_id,
                                "spine_bore_id": geom["common_axis_to_bore"][axis_id],
                                "source_tension_n": shaft_records[axis_id]["source_tension_n"],
                                "redistributed_tension_n": shaft_records[axis_id]["redistributed_tension_n"],
                                "receiver_wrench_recovery": [
                                    record for record in receiver_closures if record["axis_id"] == axis_id
                                ],
                            }
                            for axis_id in sorted(shaft_records)
                        ],
                    }
                )
    require(len(results) == 12, "expected both spines and all six nominal cases")
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n!.gitignore\n")
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    maximum = max(result["minimum_required_timber_tension_n"] for result in results)
    peak = max(results, key=lambda result: result["minimum_required_timber_tension_n"])
    checks = {
        "schema": "common-spine-bore-spreading-invariant-opening/v2",
        "authority": {
            "common_report_sha256": PINS[COMMON_REPORT],
            "common_receipt_sha256": PINS[COMMON_RECEIPT],
            "common_input_contract_sha256": PINS[COMMON_CONTRACT],
            "fresh_gravity_assessment_sha256": PINS[FRESH_ASSESSMENT],
            "fresh_frame_comparison_sha256": PINS[FRAME_COMPARISON],
            "fresh_frame_response_sha256": PINS[FRAME_RESPONSE],
            "fresh_spine_action_arrays_sha256": PINS[MEMBER_ACTIONS],
            "unchanged_four_bore_geometry_sha256": PINS[SPINES],
            "reviewed_global_reaction_axis_basis": 104,
            "planning_inventory_axis_count": 108,
            "proposed_internal_v_ties_absent_from_global_rows": 4,
            "proposed_internal_v_ties_separately_allocated_or_transferred": False,
            "fully_coupled_108_axis_response": False,
            "reviewed_spine_step_identities": step_identities,
            "common_states": 12,
            "permanent_only_states_included": False,
            "same_state_cases": list(CASES),
        },
        "method": {
            "criterion": "Complete bore radial supports lie on one side of a clear local-v cut. Add their signed force resultants above the cut to all other saved fresh point forces above the cut, kept at source locations. The bound is invariant only to force spreading within each bore support.",
            "wrench_recovery": "Sum saved on-wood bore forces and saved wood-side outer-seat point tractions about each shaft geometry datum; no per-point free couple is present in these traction fields.",
            "bore_field_forces_are_already_quadrature_weighted": True,
            "fresh_nonbore_forces_and_free_couples_retained": True,
            "fresh_nonbore_actions_kept_at_source_points": True,
            "free_couples_retained_in_complete_body_wrenches": True,
            "common_source_actions_replaced_once_by_actual_bore_and_wood_seat_fields": True,
            "source_and_updated_body_wrenches_accounted_at_node_mean": True,
            "cut_half_sum_checked_against_updated_body_resultant": True,
            "fresh_action_source": root_key(MEMBER_ACTIONS),
            "fresh_force_scope": "104 reviewed global connector rows under 108-axis planning inventory gravity mass; four proposed internal-v ties are absent from the global rows and are not transferred here.",
            "fresh_old_actions_on_common_side_bores_replaced_by_common_fields": True,
            "fresh_post_bore_actions_retained_below_cut": True,
            "force_closure_tolerance_n": FORCE_CLOSURE_TOL_N,
            "moment_closure_tolerance_nmm": MOMENT_CLOSURE_TOL_NMM,
            "source_body_force_closure_tolerance_n": SOURCE_BODY_FORCE_CLOSURE_TOL_N,
            "source_body_moment_closure_tolerance_nmm": SOURCE_BODY_MOMENT_CLOSURE_TOL_NMM,
            "saved_member_source_balance_limit_n": SAVED_MEMBER_FORCE_BALANCE_LIMIT_N,
            "saved_member_source_balance_limit_nmm": SAVED_MEMBER_MOMENT_BALANCE_LIMIT_NMM,
            "arithmetic_tolerance_n_mm": ARITHMETIC_TOL,
        },
        "states": results,
        "maximum_necessary_timber_tension_lower_bound_n": maximum,
        "maximum_witness": {key: peak[key] for key in ("side", "body", "case_id", "signed_required_normal_v_resultant_n", "minimum_required_timber_tension_n", "cut_local_v_mm")},
        "full_receiver_wrench_recovery_checks": 72,
        "all_fresh_nonbore_actions_retained": True,
        "fresh_nonbore_v_force_in_opening_resultant": True,
        "all_other_fresh_actions_fixed_at_source_points": True,
        "opening_bound_invariant_only_to_bore_force_spreading": True,
        "source_and_updated_body_wrench_accounting_closed": True,
        "cut_half_sum_checked_against_complete_updated_body_v_resultant": True,
        "all_four_bore_supports_clear_of_each_cut": True,
        "splitting_resistance_established": False,
        "complete_joint_acceptance": False,
        "permanent_load_state_qualified": False,
        "global_frame_feedback": False,
        "complete_physical_boundary_claimed": False,
        "updated_body_equilibrium_claimed": False,
        "reviewed_global_reaction_axis_basis": 104,
        "planning_inventory_axis_count": 108,
        "proposed_internal_v_ties_absent_from_global_rows": 4,
        "fully_coupled_108_axis_response": False,
        "internal_v_ties_included_or_transferred": False,
        "proposal_adopted": False,
        "physical_release": False,
        "native_or_cad_run": False,
        "new_solver_or_capacity_model_added": False,
        "source_sha256": {root_key(path): digest for path, digest in sorted(pins.items())},
    }
    require(sha(producer) == pins[producer], "producer changed during build")
    write_json(output / "checks.json", checks)
    authenticate(pins)
    write_json(
        output / "receipt.json",
        {
            "schema": "common-spine-invariant-opening-receipt/v1",
            "producer_sha256": pins[producer],
            "source_sha256": {root_key(path): digest for path, digest in sorted(pins.items())},
            "output_sha256": {
                name: sha(output / name) for name in ("producer.py.snapshot", "checks.json")
            },
            "sources_unchanged_before_and_after": True,
            "splitting_resistance_established": False,
            "complete_joint_acceptance": False,
            "permanent_load_state_qualified": False,
            "global_frame_feedback": False,
            "internal_v_ties_included_or_transferred": False,
            "proposal_adopted": False,
            "physical_release": False,
        },
    )
    print(json.dumps({"states": len(results), "maximum_necessary_timber_tension_lower_bound_n": maximum, "witness": checks["maximum_witness"]}))
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
