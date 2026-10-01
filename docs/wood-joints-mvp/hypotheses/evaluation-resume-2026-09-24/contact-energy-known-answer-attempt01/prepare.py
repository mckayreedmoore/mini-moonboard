#!/usr/bin/env python3
"""Prepare output-only energy requests from the passed section-force fixture."""

from __future__ import annotations

import copy
import hashlib
import json
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EVAL = HERE.parent
BASE = EVAL / "contact-section-force-known-answer-attempt02"
METHOD_NOTE = (
    EVAL / "contact-mortar-c3d10-fullstep-attempt01"
    / "energy-method-review-2026-09-27.md"
)
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02/source.tar.bz2"
)
MANUAL = REPO / "fea/generated/ccx_2.23.pdf"

BASE_PINS = {
    "input-freeze.json": "0603288af8a4385000d029eca0e31bda57fc63f39e474796033213026b5aa8f7",
    "execution.json": "2736908e0f59c73a43330021c6c3798e46fc3726b22a179ec3dcb1ee07b43435",
    "verifier.py": "c68a9fd998d8ed601d4223118af1699b343cc6688e37818e03131fd84321524b",
    "verifier.json": "4a0fe723f21686ffa6e0d41ca7724b5f901b6234db87a4ac7b3a376dd73da215",
    "RESULTS.md": "99a1768739ad988fa91a6eaf46e6561264d948bfc629095739d7f48b45c318ca",
    "expected.json": "9298fdce2f9e3e04d5cc12112361a06c6029ecfbbf0f1fa9fa329925d1f42bfd",
}
BASE_INPUTS = {
    "mortar_c3d10.inp": "1cbaabfaaa046e956c5515d6b3fca0c97489ed443aaa1f59d79489265a1fa46a",
    "penalty_c3d10.inp": "d307eae404de89826c9b05ceb531a4ee070905ed649c3d9d76a4576e4be0faf5",
}
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
METHOD_NOTE_SHA256 = "82493cbd62a39456bce855c31f44e8fee0bb79c3a33725dd2b7c1393421c7cbd"
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/contactpairs.f":
        "e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488",
    "CalculiX/ccx_2.23/src/contactprints.f":
        "88a2fc1a15caa2ab9b28de6ff6c4566f34e7f24c9db5c2c3ee4ef333439c717d",
    "CalculiX/ccx_2.23/src/elprints.f":
        "15d4ad6001e3ecb4eeaa05cba39333626b6c079cbe9d696879092dc2c73ff7b7",
    "CalculiX/ccx_2.23/src/getcontactparams.f":
        "03384b3d55deb22010f19a4521f3b10380caaf16441d270bf35f886ec0aadbaa",
    "CalculiX/ccx_2.23/src/printout.f":
        "ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32",
    "CalculiX/ccx_2.23/src/printoutelem.f":
        "e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544",
    "CalculiX/ccx_2.23/src/resultsmech.f":
        "15fccc9fb553f259af5d33bc78e8d3808f1f9f338ee266ce92192bae33026fa6",
    "CalculiX/ccx_2.23/src/springforc_f2f.f":
        "3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4",
}
OUTPUT_BLOCK = (
    b"*EL PRINT,ELSET=UPPER,TOTALS=ONLY,FREQUENCY=1\nELSE\n"
    b"*EL PRINT,ELSET=LOWER,TOTALS=ONLY,FREQUENCY=1\nELSE\n"
    b"*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1\nCELS\n"
)
CASE_FILES = ("mortar_c3d10.inp", "penalty_c3d10.inp")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def verify_source() -> None:
    require(sha(SOURCE_ARCHIVE.read_bytes()) == SOURCE_ARCHIVE_SHA256,
            "pinned CalculiX 2.23 source archive hash mismatch")
    require(sha(MANUAL.read_bytes()) == MANUAL_SHA256,
            "pinned CalculiX 2.23 manual hash mismatch")
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for relative, digest in SOURCE_MEMBERS.items():
            member = archive.extractfile(archive.getmember("./" + relative))
            require(member is not None and sha(member.read()) == digest,
                    f"pinned 2.23 source member hash mismatch: {relative}")


def verify_baseline() -> tuple[dict, dict]:
    for filename, digest in BASE_PINS.items():
        require(sha((BASE / filename).read_bytes()) == digest,
                f"passing section-force baseline changed: {filename}")
    freeze = read_json(BASE / "input-freeze.json")
    for filename, digest in freeze["files_sha256"].items():
        require(sha((BASE / filename).read_bytes()) == digest,
                f"baseline frozen file hash mismatch: {filename}")
    result = read_json(BASE / "verifier.json")
    execution = read_json(BASE / "execution.json")
    require(result.get("status") == "PASS_SECTION_STRESS_FIXTURE",
            "section-force attempt02 is not the pinned passing fixture")
    require(execution.get("status") == "completed_pending_audit",
            "section-force attempt02 execution status changed")
    verifier_result = result
    require(verifier_result.get("mechanical_acceptance") is False
            and verifier_result.get("joint_acceptance") is False,
            "section-force baseline claim boundary changed")
    expected = read_json(BASE / "expected.json")
    for name, digest in BASE_INPUTS.items():
        rel = "input/" + name
        data = (BASE / rel).read_bytes()
        require(sha(data) == digest, f"baseline input hash mismatch: {rel}")
        require(freeze["files_sha256"][rel] == digest,
                f"baseline freeze does not pin {rel}")
        case = "mortar_c3d10" if name.startswith("mortar") else "penalty_c3d10"
        require(expected["cases"][case]["input_sha256"] == digest,
                f"baseline expected.json does not pin {rel}")
    return freeze, expected


def add_output_requests(raw: bytes, filename: str) -> bytes:
    marker = b"*END STEP\n"
    require(raw.count(marker) == 3, f"expected three fixed steps in {filename}")
    require(raw.count(b"*EL FILE,FREQUENCY=1\nS\n") == 3,
            f"baseline STRESS requests changed in {filename}")
    require(raw.count(b"*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1\nSOF\n") == 3,
            f"baseline slave SOF requests changed in {filename}")
    require(raw.count(b"*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1\nSOF\n") == 3,
            f"baseline master SOF requests changed in {filename}")
    require(b"*EL PRINT" not in raw and b"CELS" not in raw,
            f"unexpected prior energy output request in {filename}")
    result = raw.replace(marker, OUTPUT_BLOCK + marker)
    require(result.count(OUTPUT_BLOCK) == 3,
            f"energy output request count mismatch in {filename}")
    require(result.replace(OUTPUT_BLOCK, b"") == raw,
            f"energy output packet changed more than the output requests: {filename}")
    return result


def make_expected(base_expected: dict, deck_hashes: dict[str, str]) -> dict:
    expected = copy.deepcopy(base_expected)
    expected.update({
        "schema": "calculix_mortar_c3d10_energy_known_answer/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NO_FREEZE_OR_NATIVE_EXECUTION",
        "native_execution_authorized": False,
        "energy_contract": {
            "only_added_output_cards_per_step": [
                "*EL PRINT,ELSET=UPPER,TOTALS=ONLY,FREQUENCY=1 / ELSE",
                "*EL PRINT,ELSET=LOWER,TOTALS=ONLY,FREQUENCY=1 / ELSE",
                "*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1 / CELS",
            ],
            "preserved_mechanics": (
                "All attempt02 U/RF/SOF/STRESS, endpoint mechanics, node coverage, "
                "STA/CVG/stdout trace, exact state-count, and MORTAR iteration-cap "
                "gates remain unchanged. The energy audit is additional and separate."
            ),
            "states": {
                "open": {"step": 1, "time": 1.0, "body_ELSE_each_N_mm": 0.0,
                         "contact_CELS_N_mm": 0.0},
                "compression": {"step": 2, "time": 2.0,
                                "body_ELSE_each_N_mm": 0.4,
                                "bulk_ELSE_pair_N_mm": 0.8,
                                "contact_CELS_N_mm": 0.2,
                                "combined_energy_N_mm": 1.0},
                "reopen": {"step": 3, "time": 3.0, "body_ELSE_each_N_mm": 0.0,
                           "contact_CELS_N_mm": 0.0},
            },
            "analytical_basis": {
                "units": "mm, N, MPa = N/mm2; energies N*mm",
                "youngs_modulus_N_per_mm2": 100000.0,
                "body_area_mm2": 4.0,
                "body_thickness_mm": 2.0,
                "body_shortening_compression_mm": 0.002,
                "body_energy_each_formula": "0.5*(E*A/L)*delta^2",
                "normal_slope_N_per_mm3": 100000.0,
                "interface_area_mm2": 4.0,
                "interface_overclosure_mm": 0.001,
                "contact_energy_formula": "0.5*K*A*g^2",
                "nonlinear_fixture_note": (
                    "The full-step coupon's observed compression force is about "
                    "399.5199 N versus the 400 N small-strain analytical force; "
                    "the energy oracle remains the frozen linear known answer."
                ),
            },
            "predeclared_energy_tolerances": {
                "nonzero_state_inequality": "abs(observed-reference) <= 0.01*reference + 1e-6 N*mm",
                "zero_state_inequality": "abs(observed) <= 1e-6 N*mm",
                "relative_component_tolerance": 0.01,
                "absolute_energy_tolerance_N_mm": 1e-6,
                "rationale": (
                    "The 1% relative term matches inherited force/compliance numerical "
                    "tolerances and covers the approximately 0.120% small-strain vs "
                    "nonlinear endpoint force difference. The 1e-6 N*mm term is one "
                    "last-place unit at 1 N*mm in the pinned 2.23 total-energy text format."
                ),
                "parent_review_required_before_freeze": True,
            },
            "availability_and_result_separation": {
                "mechanical_pass_independent_of_energy_output": True,
                "ELSE_status": (
                    "Separate body-energy status; missing, incomplete, nonfinite or "
                    "out-of-tolerance ELSE is an energy-output failure only."
                ),
                "penalty_CELS_status": (
                    "Separate penalty contact-energy status; missing/incomplete output "
                    "is UNAVAILABLE_UNVALIDATED, and a mismatch is an energy-channel "
                    "failure. Neither changes inherited mechanical status."
                ),
                "mortar_CELS_status": (
                    "If no MORTAR CELS records exist, report UNAVAILABLE_UNVALIDATED; "
                    "do not fill zero and do not fail inherited mechanics. If records "
                    "exist, preserve them and compare to the analytical oracle; source "
                    "semantics still require parent review before treating them as stored energy."
                ),
                "work_energy_gate": (
                    "Cannot pass from a missing/unsupported MORTAR channel or from an "
                    "energy value inferred solely as a work residual."
                ),
            },
        },
        "baseline_source": {
            "path": str(BASE.relative_to(REPO)),
            "input_freeze_sha256": BASE_PINS["input-freeze.json"],
            "execution_sha256": BASE_PINS["execution.json"],
            "verifier_source_sha256": BASE_PINS["verifier.py"],
            "passing_verifier_result_sha256": BASE_PINS["verifier.json"],
            "results_sha256": BASE_PINS["RESULTS.md"],
            "status": "PASS_SECTION_STRESS_FIXTURE",
            "input_sha256": BASE_INPUTS,
        },
        "cases": {
            "mortar_c3d10": {
                "input": "input/mortar_c3d10.inp",
                "input_sha256": deck_hashes["mortar_c3d10"],
                "contact_type": "MORTAR",
            },
            "penalty_c3d10": {
                "input": "input/penalty_c3d10.inp",
                "input_sha256": deck_hashes["penalty_c3d10"],
                "contact_type": "SURFACE TO SURFACE",
            },
        },
        "pinned_2_23_source": {
            "manual_path": "fea/generated/ccx_2.23.pdf",
            "manual_sha256": MANUAL_SHA256,
            "manual_keywords": ["*EL PRINT", "*CONTACT PRINT"],
            "archive_path": str(SOURCE_ARCHIVE.relative_to(REPO)),
            "archive_sha256": SOURCE_ARCHIVE_SHA256,
            "source_members_sha256": SOURCE_MEMBERS,
            "method_review_path": str(METHOD_NOTE.relative_to(REPO)),
            "method_review_sha256": METHOD_NOTE_SHA256,
            "source_interpretation": {
                "ELSE": "Per-body total internal energy output for selected solid element sets.",
                "CELS_penalty": "Source-supported for mortar modes 0/1; compare the matched penalty fixture to 0.2 N*mm.",
                "CELS_mortar": "TYPE=MORTAR maps to mode 2; audited storage/print paths do not establish mode-2 CELS energy.",
            },
        },
    })
    return expected


def main() -> None:
    for forbidden in ("input-freeze.json", "execution.json", "verifier.json", "output"):
        require(not (HERE / forbidden).exists(),
                f"refusing to overwrite/claim parent freeze or run artifact: {forbidden}")
    require(not (HERE / "preparation.json").exists(),
            "preparation already exists; review rather than regenerate it")
    require(sha(METHOD_NOTE.read_bytes()) == METHOD_NOTE_SHA256,
            "energy method review changed after parent confirmed it stable")
    baseline_freeze, baseline_expected = verify_baseline()
    verify_source()

    patched = {}
    for filename in CASE_FILES:
        relative = "input/" + filename
        raw = (BASE / relative).read_bytes()
        require(sha(raw) == BASE_INPUTS[filename], f"baseline input changed: {relative}")
        require(sha(raw) == baseline_freeze["files_sha256"][relative],
                f"baseline frozen input mismatch: {relative}")
        patched[filename] = add_output_requests(raw, filename)

    mortar = patched["mortar_c3d10.inp"]
    penalty = patched["penalty_c3d10.inp"]
    mortar_contact_neutral = mortar.replace(b"TYPE=MORTAR", b"TYPE=CONTACT")
    penalty_contact_neutral = penalty.replace(b"TYPE=SURFACE TO SURFACE", b"TYPE=CONTACT")
    require(mortar_contact_neutral == penalty_contact_neutral,
            "matched energy decks differ beyond the contact type")

    for filename, data in patched.items():
        out = HERE / "input" / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)

    deck_hashes = {name.replace(".inp", ""): sha(data)
                   for name, data in patched.items()}
    expected = make_expected(baseline_expected, deck_hashes)
    (HERE / "expected.json").write_text(
        json.dumps(expected, indent=2, sort_keys=True) + "\n"
    )
    preparation = {
        "schema": "calculix_mortar_c3d10_energy_preparation/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NO_FREEZE_OR_NATIVE_EXECUTION",
        "native_execution_authorized": False,
        "baseline_path": str(BASE.relative_to(REPO)),
        "baseline_input_freeze_sha256": BASE_PINS["input-freeze.json"],
        "baseline_execution_sha256": BASE_PINS["execution.json"],
        "baseline_verifier_result_sha256": BASE_PINS["verifier.json"],
        "output_only_addition": OUTPUT_BLOCK.decode("ascii").splitlines(),
        "baseline_deck_sha256": BASE_INPUTS,
        "prepared_deck_sha256": deck_hashes,
        "input_change_check": "Removing the three exact output blocks restores each passed attempt02 input byte-for-byte.",
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "manual_sha256": MANUAL_SHA256,
        "method_review_sha256": METHOD_NOTE_SHA256,
        "input_freeze_created": False,
        "native_run_performed": False,
    }
    (HERE / "preparation.json").write_text(
        json.dumps(preparation, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "status": preparation["status"],
        "input_sha256": deck_hashes,
        "input_freeze_created": False,
        "native_run_performed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
