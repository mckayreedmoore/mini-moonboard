#!/usr/bin/env python3
"""Read-only comparison of pinned DAT parsing before/after exact-zero U handling."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
PACKET = SERIES / "current-springa-zero-u-token-response-audit-attempt01"
UPSTREAM = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "implicit-bounded-contact-capture-attempt02/build/context/source.tar.bz2"
)
MANIFEST = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "calculix-2.23-upgrade-attempt01/build_manifest.json"
)
MANUAL = Path("fea/generated/ccx_2.23.pdf")
PROFILE = Path("fea/calculix_223/solver-profile.json")
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
SOURCE_FILE_SHA256 = {
    "printoutnode.f": "ed77454fbf771c38ebbb32f0785013dae3585eca50e5cc7b28c646dec0ce4b94",
}
E13_6 = re.compile(r"^[+-]?\d\.\d{6}E[+-]\d{2}$")
ZERO_E13_6 = re.compile(r"^[+-]?0\.000000E\+00$")
HEADER = re.compile(
    r"^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

BASELINE_AUDIT = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
BASELINE_CASE_BOUND = SERIES / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
BASELINE_STABLE_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"
BASELINE_CASE_BOUND_SHA256 = "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479"

COUPONS = [
    {
        "name": "current-exact-floor-mpc-fixture-attempt02",
        "model": SERIES / "current-exact-floor-mpc-fixture-attempt02/model.json",
        "deck": SERIES / "current-exact-floor-mpc-fixture-attempt02/model.inp",
        "dat": SERIES / "current-exact-floor-mpc-fixture-attempt02/native/model.dat",
        "check": SERIES / "current-exact-floor-mpc-fixture-attempt02/parent-all-increment-check.json",
        "expected_status": "PASS_PARENT_ALL_PRINTED_INCREMENT_CHECK",
        "pins": {
            "model": "94368165d50627350f1e92b0396e35e07ad794c60161d22016d1444faf54af5f",
            "deck": "09689c00090008eccc955f5cf6fa020c73836b4460a38c0f10ae56493f1ce5b7",
            "dat": "6b7fce5cfbb6230bca951931917f146a299da75d71f2a5a9fce756d4e6cf3bdc",
            "check": "e06c476ac0ef83e248f725e7adcb8bbffe3f310497ccc5ab018a211de4fac64f",
        },
    },
    {
        "name": "nonlinear-springa-known-answer-attempt01",
        "model": SERIES / "nonlinear-springa-known-answer-attempt01/native/model.json",
        "deck": SERIES / "nonlinear-springa-known-answer-attempt01/native/model.inp",
        "dat": SERIES / "nonlinear-springa-known-answer-attempt01/native/model.dat",
        "check": SERIES / "nonlinear-springa-known-answer-attempt01/parent-all-increment-check.json",
        "expected_status": "PASS_PARENT_ALL_PRINTED_INCREMENT_CHECK",
        "pins": {
            "model": "e8d20960545fb2371212533e90358b67d220f5cec2eb9f6378868a3b66d6843c",
            "deck": "29648efb81b2cc6ad44788a107f7138bab3fdc5148171d68c46cca1b7d6bdbfe",
            "dat": "0767d6d2687fda99a949cb2e1cdac3b672f01a0eac1e92b0290932131c5ddaa8",
            "check": "3a051a1b36768b383c6be68b3884cc58ab264a488e139467c6879c797e5c470c",
        },
    },
    {
        "name": "contact-mortar-c3d10-fullstep-attempt01/penalty_c3d10",
        "model": None,
        "deck": Path(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "contact-mortar-c3d10-fullstep-attempt01/output/penalty_c3d10/coupon.inp"
        ),
        "dat": Path(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "contact-mortar-c3d10-fullstep-attempt01/output/penalty_c3d10/coupon.dat"
        ),
        "execution": Path(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "contact-mortar-c3d10-fullstep-attempt01/output/penalty_c3d10/execution.json"
        ),
        "verifier": Path(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "contact-mortar-c3d10-fullstep-attempt01/verifier.json"
        ),
        "expected_status": "PASS_METHOD_FIXTURE",
        "pins": {
            "deck": "27bdc3140b31e40d0ad61f896578b1c95f543e87e9871c1c479213000e3dbd7e",
            "dat": "e793edb0413c5ecc838cc7e12a21cd391e7cb80624f776b8efb1149993ac9f4f",
            "execution": "29ce67670ea234468f43fa310fb42aa275a4db3d43a429c58452829ff6f4cbb0",
            "verifier": "813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14",
        },
    },
]

ZERO_E_MINUS_78_DAT = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "contact-mortar-c3d10-known-answer-attempt01/output/penalty_c3d10/coupon.dat"
)
ZERO_E_MINUS_78_EXECUTION = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "contact-mortar-c3d10-known-answer-attempt01/output/penalty_c3d10/execution.json"
)
ZERO_E_MINUS_78_DECK = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "contact-mortar-c3d10-known-answer-attempt01/output/penalty_c3d10/coupon.inp"
)
ZERO_E_MINUS_78_PINS = {
    ZERO_E_MINUS_78_DAT: "eb568867db71057ed92acd80ce7ab8eae745164e574df32749ca4da5ba8b5434",
    ZERO_E_MINUS_78_EXECUTION: "759b5331c2eca3def253396dcfb2a218634722d6d8b732af19ec1a47ed141972",
    ZERO_E_MINUS_78_DECK: "95eef006c0e54786e172dbfd501ec0c5935981a133ab6e64ebeabb85a5ee425b",
}


def sha(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text())


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    require(spec is not None and spec.loader is not None, f"cannot load module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_raw_blocks(data: str) -> dict[tuple[str, float], dict[int, list[str]]]:
    result: dict[tuple[str, float], dict[int, list[str]]] = {}
    for match in HEADER.finditer(data):
        kind = "u" if match.group(1).lower() == "displacements" else "rf"
        time = float(match.group(2).replace("D", "E").replace("d", "e"))
        key = kind, time
        require(key not in result, f"duplicate {kind} block at {time}")
        rows: dict[int, list[str]] = {}
        started = False
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                require(node not in rows, f"duplicate node {node} at {time}")
                rows[node] = fields[1:]
                started = True
            elif started:
                break
        require(rows, f"empty {kind} block at {time}")
        result[key] = rows
    return result


def radius(token: str) -> float:
    mantissa, exponent = token.split("E", 1)
    decimal_places = len(mantissa.split(".", 1)[1])
    return 0.5 * 10.0 ** (int(exponent) - decimal_places)


def evidence_pins() -> dict[str, Any]:
    expected = {
        BASELINE_AUDIT: BASELINE_STABLE_SHA256,
        BASELINE_CASE_BOUND: BASELINE_CASE_BOUND_SHA256,
        MANUAL: "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330",
        PROFILE: "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c",
        MANIFEST: "496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66",
        UPSTREAM: SOURCE_ARCHIVE_SHA256,
    }
    observed = {str(path): sha(path) for path in expected}
    for path, digest in expected.items():
        require(sha(path) == digest, f"source/document pin mismatch: {path}")
    manifest = load(MANIFEST)
    require(manifest["upstream_source_archive_sha256"] == SOURCE_ARCHIVE_SHA256,
            "build manifest does not bind the source archive")
    require("GNU Fortran (Ubuntu 13.3.0" in manifest["compiler_versions"]["gfortran"],
            "pinned compiler is not GNU Fortran 13.3.0")
    archived: dict[str, str] = {}
    excerpts: list[str] = []
    with tarfile.open(ROOT / UPSTREAM, "r:bz2") as archive:
        member = "./CalculiX/ccx_2.23/src/printoutnode.f"
        stream = archive.extractfile(member)
        require(stream is not None, "pinned printoutnode.f is absent from upstream archive")
        source = stream.read()
        actual = hashlib.sha256(source).hexdigest()
        require(actual == SOURCE_FILE_SHA256["printoutnode.f"], "printoutnode.f hash mismatch")
        require(manifest["upstream_files_sha256"].get(member) == actual,
                "build manifest does not bind printoutnode.f")
        archived["printoutnode.f"] = actual
        decoded = source.decode("ascii")
        excerpts = [line.strip() for line in decoded.splitlines()
                    if "real*8 v(" in line or "write(5,'(i10,1p,6(1x,e13.6))') node," in line]
        require(any("real*8 v(" in line for line in excerpts),
                "source no longer shows the U print value as real*8")
        require(any("1p,6(1x,e13.6)" in line.lower() for line in excerpts),
                "source no longer shows the pinned E13.6 U writer")
    profile = load(PROFILE)
    require(profile["version"] == "2.23"
            and profile["binary_sha256"] == "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
            and profile["image_id"] == "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38",
            "solver profile does not identify the pinned CCX 2.23 binary/image")
    return {
        "source_and_document_sha256": observed,
        "upstream_member_sha256": archived,
        "compiler": manifest["compiler_versions"]["gfortran"].splitlines()[0],
        "solver_profile": {
            "version": profile["version"],
            "image_id": profile["image_id"],
            "binary_sha256": profile["binary_sha256"],
        },
        "printoutnode_f_relevant_lines": excerpts,
        "fortran_standard_reference": {
            "document": "WG5 N1191, working draft, Fortran 2003, §10.5.1.2.2 (E and D editing)",
            "url": "https://wg5-fortran.org/N1151-N1200/N1191.pdf",
            "rule_used": "E editing writes rounded significant digits with a decimal exponent; with the pinned 1P scale factor, nonzero values remain exponent-scaled rather than sharing an absolute zero bin.",
        },
    }


def compare_coupon(coupon: dict[str, Any], baseline: Any, refined: Any) -> dict[str, Any]:
    for role, expected in coupon["pins"].items():
        path = coupon[role]
        require(sha(path) == expected, f"coupon pin mismatch: {coupon['name']} {role}")
    dat = (ROOT / coupon["dat"]).read_text()
    deck = (ROOT / coupon["deck"]).read_text()
    require(not re.search(r"^\s*\*TRANSFORM\b", deck, re.MULTILINE | re.IGNORECASE),
            f"coupon output uses a transformed coordinate system: {coupon['name']}")
    raw = extract_raw_blocks(dat)
    old = baseline.parse_native_blocks(dat)
    new = refined.parse_native_blocks(dat)
    check_status: str
    if coupon.get("check"):
        check = load(coupon["check"])
        check_status = check.get("status", "missing")
        require(check_status == coupon["expected_status"],
                f"all-increment coupon status changed: {coupon['name']}")
        expected_count = int(check.get("printed_increment_count", check.get("increment_count", -1)))
        observed_count = len([kind_time for kind_time in raw if kind_time[0] == "u"])
        require(observed_count == expected_count, f"coupon increment count mismatch: {coupon['name']}")
    else:
        execution = load(coupon["execution"])
        verifier = load(coupon["verifier"])
        check_status = verifier.get("status", "missing")
        require(check_status == coupon["expected_status"],
                f"contact method fixture status changed: {coupon['name']}")
        require(execution.get("status") == "completed"
                and execution.get("docker_cli_exit_code") == 0
                and execution.get("container_state", {}).get("ExitCode") == 0,
                "contact coupon native execution is not completed/zero-exit")
        require(execution.get("outputs_sha256", {}).get("coupon.dat") == sha(coupon["dat"])
                and execution.get("outputs_sha256", {}).get("coupon.inp") == sha(coupon["deck"]),
                "contact coupon output/input hash does not match its execution record")

    zero_u = 0
    nonzero_u = 0
    zero_rf = 0
    tiny_nonzero: list[dict[str, Any]] = []
    smallest_nonzero: dict[str, Any] | None = None
    for (kind, time), rows in raw.items():
        require(time in old and time in new, f"parsed time missing from auditor: {coupon['name']} {time}")
        for node, tokens in rows.items():
            old_value = old[time][kind][node]
            new_value = new[time][kind][node]
            old_radius = old[time][kind + "_radius"][node]
            new_radius = new[time][kind + "_radius"][node]
            for dof, token in enumerate(tokens):
                require(E13_6.fullmatch(token), f"unexpected token grammar in coupon {coupon['name']}: {token!r}")
                value = float(token)
                require(math.isfinite(value), f"non-finite coupon token {coupon['name']}: {token!r}")
                require(old_value[dof] == value == new_value[dof],
                        f"parsed value changed: {coupon['name']} {kind} {time} node {node} dof {dof+1}")
                if kind == "rf":
                    require(new_radius[dof] == old_radius[dof],
                            f"RF radius changed: {coupon['name']} {time} node {node} dof {dof+1}")
                    zero_rf += int(value == 0.0)
                elif value == 0.0:
                    require(ZERO_E13_6.fullmatch(token),
                            f"zero U token is not canonical: {coupon['name']} {token!r}")
                    require(new_radius[dof] == 0.0,
                            f"exact-zero U token retained a rounding radius: {coupon['name']} {token!r}")
                    require(old_radius[dof] == 0.5e-6,
                            f"baseline zero-token radius differs from 5e-7: {coupon['name']} {token!r}")
                    zero_u += 1
                else:
                    require(new_radius[dof] == old_radius[dof],
                            f"nonzero U radius changed: {coupon['name']} {token!r}")
                    nonzero_u += 1
                    if smallest_nonzero is None or abs(value) < abs(float(smallest_nonzero["value"])):
                        smallest_nonzero = {
                            "time": time,
                            "node": node,
                            "dof_1based": dof + 1,
                            "token": token,
                            "value": value,
                            "unchanged_half_last_place_radius": new_radius[dof],
                        }
                    if abs(value) < 5e-7 and len(tiny_nonzero) < 8:
                        tiny_nonzero.append({
                            "time": time,
                            "node": node,
                            "dof_1based": dof + 1,
                            "token": token,
                            "unchanged_half_last_place_radius": new_radius[dof],
                        })
    return {
        "name": coupon["name"],
        "verification_status": check_status,
        "no_transform_cards_for_direct_u_output": True,
        "native_increment_count": len([key for key in raw if key[0] == "u"]),
        "exact_zero_u_tokens": zero_u,
        "nonzero_u_tokens_unchanged": nonzero_u,
        "zero_rf_tokens_with_unchanged_radius": zero_rf,
        "first_tiny_nonzero_u_tokens": tiny_nonzero,
        "smallest_magnitude_nonzero_u_token": smallest_nonzero,
        "all_parsed_u_and_rf_values_unchanged": True,
        "all_rf_radii_unchanged": True,
        "all_nonzero_u_radii_unchanged": True,
    }


def format_only_e_minus_78_observation() -> dict[str, Any]:
    for path, expected in ZERO_E_MINUS_78_PINS.items():
        require(sha(path) == expected, f"E-78 observation pin mismatch: {path}")
    data = (ROOT / ZERO_E_MINUS_78_DAT).read_text()
    deck = (ROOT / ZERO_E_MINUS_78_DECK).read_text()
    require(not re.search(r"^\s*\*TRANSFORM\b", deck, re.MULTILINE | re.IGNORECASE),
            "E-78 format observation contains a coordinate transform card")
    # This separate completed stream contains larger exponents without an E marker;
    # it is evidence of normalized small scientific values, not an accepted input
    # to the deliberately narrow E13.6 replay parser below.
    execution = load(ZERO_E_MINUS_78_EXECUTION)
    require(execution.get("status") == "completed"
            and execution.get("docker_cli_exit_code") == 0
            and execution.get("container_state", {}).get("ExitCode") == 0
            and execution.get("outputs_sha256", {}).get("coupon.dat") == sha(ZERO_E_MINUS_78_DAT),
            "E-78 format observation lacks a matching completed native output record")
    pattern = re.compile(
        r"^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    kind, time = "", ""
    sample = None
    for line in data.splitlines():
        match = pattern.match(line)
        if match:
            kind, time = match.group(1).lower(), match.group(2)
            continue
        fields = line.split()
        if kind == "displacements" and len(fields) == 4 and fields[0].isdigit():
            for dof, token in enumerate(fields[1:], 1):
                if token == "-1.619282E-78":
                    sample = {"time": time, "node": int(fields[0]), "dof_1based": dof, "token": token}
                    break
        if sample:
            break
    require(sample is not None, "pinned E-78 sample token is absent")
    return {
        "input_path": str(ZERO_E_MINUS_78_DAT),
        "dat_sha256": sha(ZERO_E_MINUS_78_DAT),
        "deck_sha256": sha(ZERO_E_MINUS_78_DECK),
        "completed_native_exit_code": execution["docker_cli_exit_code"],
        "verifier_status": "FAIL; this observation is only for output formatting",
        "observed_nonzero_displacement": sample,
        "nonzero_token_half_last_place": 5.0e-85,
        "parser_replay": "not used; this older stream also contains three-digit exponents without E, which the narrow parser intentionally rejects as unrecognized",
    }


def negative_controls(refined: Any) -> dict[str, Any]:
    def data(u_tokens: list[str]) -> str:
        return (
            "displacements (vx,vy,vz) for set NALL and time 0.1000000E+00\n"
            f" 1 {u_tokens[0]} {u_tokens[1]} {u_tokens[2]}\n\n"
            "forces (fx,fy,fz) for set NALL and time 0.1000000E+00\n"
            " 1 0.000000E+00 1.000000E+00 -1.000000E+00\n\n"
        )

    sample = refined.parse_native_blocks(data(["0.000000E+00", "1.000000E-08", "-1.000000E-08"]))
    state = sample[0.1]
    require(state["u_radius"][1] == [0.0, 5.0e-15, 5.0e-15],
            "zero and nonzero synthetic control radii are wrong")
    require(state["rf_radius"][1] == [5.0e-7, 5.0e-7, 5.0e-7],
            "RF synthetic control radii changed")
    rejected: dict[str, bool] = {}
    for label, tokens in {
        "nonfinite": ["NaN", "1.000000E+00", "1.000000E+00"],
        "unmarked_three_digit_exponent": ["1.000000-103", "1.000000E+00", "1.000000E+00"],
        "noncanonical_zero_exponent": ["0.000000E-01", "1.000000E+00", "1.000000E+00"],
    }.items():
        try:
            refined.parse_native_blocks(data(tokens))
        except refined.ResponseAuditError:
            rejected[label] = True
        else:
            rejected[label] = False
            raise ValueError(f"strict parser accepted negative-control form: {label}")
    return {
        "zero_component_radius_mm": state["u_radius"][1][0],
        "nonzero_1e_minus_8_component_radius_mm": state["u_radius"][1][1],
        "rf_radii_remain_original_half_last_place": state["rf_radius"][1],
        "rejected_controls": rejected,
        "note": "Synthetic parser-only controls; no native model was generated or run.",
    }


def replay() -> dict[str, Any]:
    pins = evidence_pins()
    baseline = load_module(BASELINE_AUDIT, "baseline_springa_audit")
    refined = load_module(PACKET / "stable_response_audit.py", "zero_u_token_springa_audit")
    wrapper_path = PACKET / "response_audit.py"
    wrapper = load_module(wrapper_path, "zero_u_token_case_bound_audit")
    require(wrapper._stable.parse_native_blocks is wrapper.parse_native_blocks,
            "case-bound wrapper did not import the refined parser")

    baseline_wrapper = (ROOT / BASELINE_CASE_BOUND).read_text()
    refined_wrapper = (ROOT / wrapper_path).read_text()
    path_edits = (
        'STABLE_PACKET = SERIES / "current-springa-frame-response-audit-attempt01"\n'
        'STABLE_AUDIT = STABLE_PACKET / "response_audit.py"\n'
        'STABLE_AUDIT_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"'
    )
    replacement = (
        "STABLE_PACKET = HERE\n"
        'STABLE_AUDIT = STABLE_PACKET / "stable_response_audit.py"\n'
        'STABLE_AUDIT_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"'
    )
    require(path_edits in baseline_wrapper, "baseline wrapper pin lines changed")
    require(refined_wrapper == baseline_wrapper.replace(path_edits, replacement),
            "case-bound wrapper copy has changes beyond the refined stable-parser binding")

    method_replays = [compare_coupon(coupon, baseline, refined) for coupon in COUPONS]
    k12 = SERIES / "current-springa-frame-k12-rear-all-bearing-attempt01"
    k12_pins = {
        k12 / "model.json": "72cc39411bb92d3ee739a9b9aa9b025fe466f2b818f29feaa76a26c284366424",
        k12 / "model.inp": "0cdcee16de7be40e8a7a511c26f6cbf67f116d2475f76eab294fa661ee6fac68",
        k12 / "model.dat": "8c3c7590e11df6c8bce52e814ece2aba2f05ff24eb261517e95e74db41528807",
        k12 / "freeze.json": "161e9b8bfecb7ef4d5060db4d6fb25aeeb38df5fa4332a3ba47fbd92df70ac92",
        k12 / "execution.json": "4e10033ba2a12952122ac790ae6c4dcf4a9585b936d239e86d73465be6db6ccc",
    }
    for path, expected in k12_pins.items():
        require(sha(path) == expected, f"K12 read-only screen evidence pin mismatch: {path}")
    execution = load(k12 / "execution.json")
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "K12 existing native evidence is not successful and terminal")

    return {
        "schema": "ccx223_zero_u_token_format_replay/v1",
        "status": "SUPPORTED_NARROW_ZERO_TOKEN_REPRESENTATION_RULE",
        "interpretation": {
            "zero_u_token": "For the pinned CCX 2.23 direct E13.6 U output path, a canonical all-zero scientific field records a computed output datum of exactly zero; it is not a ±0.5e-7 absolute interval.",
            "nonzero_u_token": "Retain the existing half-last-place radius using that token's printed exponent.",
            "rf_tokens": "All reaction values and radii remain on the original parser path.",
            "limit": "This corrects serialization-rounding treatment only. It does not bound solver convergence/residual error, arithmetic before the write, binary underflow, transformations, or the exact continuum solution.",
        },
        "evidence_pins": pins,
        "new_auditor": {
            "source_file_sha256": {
                str(PACKET / "stable_response_audit.py"): sha(PACKET / "stable_response_audit.py"),
                str(wrapper_path): sha(wrapper_path),
            },
            "base_stable_auditor_sha256": BASELINE_STABLE_SHA256,
            "base_case_bound_wrapper_sha256": BASELINE_CASE_BOUND_SHA256,
            "wrapper_copy_diff_scope": "Only STABLE_PACKET, STABLE_AUDIT filename, and pinned refined stable-source SHA were changed from df1ed source.",
        },
        "three_method_coupon_replays": method_replays,
        "extra_e_minus_78_format_observation": format_only_e_minus_78_observation(),
        "strict_parser_negative_controls": negative_controls(refined),
        "k12_existing_native_evidence_sha256": {str(path): sha(path) for path in k12_pins},
        "native_run_performed_by_this_replay": False,
        "freeze_or_ledger_changed": False,
        "physical_or_design_acceptance": False,
    }


if __name__ == "__main__":
    print(json.dumps(replay(), indent=2, sort_keys=True, allow_nan=False))
