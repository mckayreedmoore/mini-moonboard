#!/usr/bin/env python3
"""Add two native SOF output requests to the passing full-step decks."""

import copy
import hashlib
import json
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EVAL = REPO / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
BASE = EVAL / "contact-mortar-c3d10-fullstep-attempt01"
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02/source.tar.bz2"
)
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
METHOD_SCREEN = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "mortar-output-method-screen.md"
)
METHOD_SCREEN_SHA256 = "1a9e89c94ab9a88a73132443aea11a6be5fbeb3ad58186929eb3b937746257a4"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
BASE_PINS = {
    "input-freeze.json": "978f8e49e79d6569dc033595ce565ce8587e36c4c5845c5615f120582634e8b0",
    "execution.json": "a485410aada87d2e149b39ee77b78d3efcada065c833a0c7e91acf1a60312574",
    "verifier.py": "d86d98494241657b1f8dda8ea42d747dac851c2319b914458f520008bc3a572b",
    "verifier.json": "813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14",
    "RESULTS.md": "ba1f3b4b7dea4840547bde6b44497fd71e4f3d5d4d9912bc4cb7ce6fb9de3e77",
}
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/sectionprints.f": "deee2931a7165184fc4d482ddfd1ab405da9ef4dcb870625374babf3e27c5446",
    "CalculiX/ccx_2.23/src/printoutface.f": "e39d508e431c5ad29556594f7bf82753a8729a836ecf67ebd24a872212f13cbc",
    "CalculiX/ccx_2.23/src/results.c": "9113a4984342355ff15bb16a609c5bdb034183c951719b064037b3858eac24dd",
}
SECTION_BLOCK = (
    b"*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1\nSOF\n"
    b"*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1\nSOF\n"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_pins() -> tuple[dict, dict]:
    for name, digest in BASE_PINS.items():
        if sha((BASE / name).read_bytes()) != digest:
            raise SystemExit(f"passing full-step artifact hash mismatch: {name}")
    freeze = json.loads((BASE / "input-freeze.json").read_text())
    for name, digest in freeze["files_sha256"].items():
        if sha((BASE / name).read_bytes()) != digest:
            raise SystemExit(f"frozen full-step file changed: {name}")
    execution = json.loads((BASE / "execution.json").read_text())
    prior = json.loads((BASE / "verifier.json").read_text())
    if (execution.get("status") != "completed_pending_audit"
            or execution.get("input_freeze_sha256") != BASE_PINS["input-freeze.json"]):
        raise SystemExit("full-step execution is incomplete or unbound to the pinned freeze")
    if prior.get("status") != "PASS_METHOD_FIXTURE":
        raise SystemExit("full-step baseline does not have a passing method audit")
    if sha((REPO / "fea/generated/ccx_2.23.pdf").read_bytes()) != MANUAL_SHA256:
        raise SystemExit("pinned CalculiX 2.23 manual hash mismatch")
    if sha(SOURCE_ARCHIVE.read_bytes()) != SOURCE_ARCHIVE_SHA256:
        raise SystemExit("pinned CalculiX source archive hash mismatch")
    if sha(METHOD_SCREEN.read_bytes()) != METHOD_SCREEN_SHA256:
        raise SystemExit("pinned MORTAR output-method screen hash mismatch")
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for path, digest in SOURCE_MEMBERS.items():
            data = archive.extractfile(archive.getmember("./" + path)).read()
            if sha(data) != digest:
                raise SystemExit(f"pinned SECTION PRINT source hash mismatch: {path}")
    return freeze, prior


def add_output_only_cards(raw: bytes, name: str) -> bytes:
    marker = b"*END STEP\n"
    if raw.count(marker) != 3:
        raise SystemExit(f"expected three full-step endpoints in {name}")
    result = raw.replace(marker, SECTION_BLOCK + marker)
    if result.count(SECTION_BLOCK) != 3 or result.replace(SECTION_BLOCK, b"") != raw:
        raise SystemExit(f"non-output input changes detected in input/{name}")
    return result


def main() -> None:
    for evidence in (HERE / "input-freeze.json", HERE / "execution.json", HERE / "output"):
        if evidence.exists():
            raise SystemExit(f"refusing to regenerate frozen/executed packet: {evidence}")
    freeze, prior_verifier = verify_pins()
    source_expected = (BASE / "expected.json").read_bytes()
    base_expected = json.loads(source_expected)
    input_names = ("mortar_c3d10.inp", "penalty_c3d10.inp")
    decks = {}
    for name in input_names:
        relative = "input/" + name
        original = (BASE / relative).read_bytes()
        if sha(original) != freeze["files_sha256"][relative]:
            raise SystemExit(f"full-step input differs from its immutable freeze: {relative}")
        decks[name] = add_output_only_cards(original, name)
    if decks[input_names[0]].replace(b"TYPE=MORTAR", b"TYPE=CONTACT") != decks[
        input_names[1]
    ].replace(b"TYPE=SURFACE TO SURFACE", b"TYPE=CONTACT"):
        raise SystemExit("section-output decks differ beyond their contact type")

    (HERE / "input").mkdir(exist_ok=True)
    for name, data in decks.items():
        (HERE / "input" / name).write_bytes(data)

    expected = copy.deepcopy(base_expected)
    expected["schema"] = "calculix_mortar_c3d10_section_force_known_answer/v1"
    expected["status"] = "PREPARED_FOR_PARENT_REVIEW_NO_NATIVE_EXECUTION"
    expected["cases"]["mortar_c3d10"]["input_sha256"] = sha(decks[input_names[0]])
    expected["cases"]["penalty_c3d10"]["input_sha256"] = sha(decks[input_names[1]])
    expected["source"]["source_members_sha256"].update(SOURCE_MEMBERS)
    expected["source"]["notes"].extend([
        "sectionprints.f parses SURFACE, NAME and FREQUENCYF; SOF requests all section resultants",
        "printoutface.f supports C3D10 six-node faces and integrates extrapolated/averaged stresses",
        "SOF at a material/contact stress jump is a bulk-stress proxy, not exact contact traction",
    ])
    expected["base_passing_fixture"] = {
        "path": str(BASE.relative_to(REPO)),
        "input_freeze_sha256": BASE_PINS["input-freeze.json"],
        "execution_sha256": BASE_PINS["execution.json"],
        "verifier_source_sha256": BASE_PINS["verifier.py"],
        "passing_verifier_result_sha256": BASE_PINS["verifier.json"],
        "results_summary_sha256": BASE_PINS["RESULTS.md"],
        "verifier_status": prior_verifier["status"],
        "base_input_sha256": {
            name: freeze["files_sha256"]["input/" + name] for name in input_names
        },
        "scope": "Previously passed output-freeze endpoints; mechanics gates are inherited unchanged",
    }
    section_gate = {
        "requested_cards_per_step": [
            "*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1 / SOF",
            "*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1 / SOF",
        ],
        "global_keyword_present": False,
        "no_new_stress_frd_requests": True,
        "reports_per_case": 6,
        "reports_per_step": 2,
        "step_times": [1.0, 2.0, 3.0],
        "surfaces": {
            "SLAVE": {"name": "SLAVE_IF", "elements_faces": "1,2 S1", "face_count": 2},
            "MASTER": {"name": "MASTER_IF", "elements_faces": "11,12 S3", "face_count": 2},
        },
        "expected_area_mm2_each_surface": 4.0,
        "area_abs_tolerance_mm2": 1e-5,
        "force_sign_and_tolerance": {
            "SLAVE_compression_vector_N": [0.0, 0.0, 400.0],
            "MASTER_compression_vector_N": [0.0, 0.0, -400.0],
            "compression_vector_norm_error_N": "<= 0.01*400 + 0.001 = 4.001",
            "open_reopen_section_force_norm_N": 0.001,
            "opposed_force_sum_norm_N": {"compression": 4.001, "open_reopen": 0.001},
        },
        "moment_sign_and_tolerance": {
            "compression_reference_point_mm": [1.0, 1.0, 0.0],
            "SLAVE_expected_origin_moment_Nmm": [400.0, -400.0, 0.0],
            "MASTER_expected_origin_moment_Nmm": [-400.0, 400.0, 0.0],
            "origin_moment_vector_error_Nmm": "<= 0.01*400 + 0.001 = 4.001",
            "centroid_moment_norm_Nmm": "<= 0.01*400 + 0.001 = 4.001 at compression",
            "opposed_origin_moment_sum_norm_Nmm": {"compression": 4.001, "open_reopen": 0.001},
            "centroid_rule": "SOF deformed centroid; z offset does not change the expected Fz moment",
        },
        "reported_components": [
            "global force vector",
            "origin moment vector",
            "deformed center of gravity and mean normal",
            "centroid moment vector",
            "area, normal force, shear, torque and bending moment",
        ],
        "result_interpretation": (
            "Bulk-stress extrapolated/averaged proxy, not exact contact force at stress jumps; "
            "no joint qualification"
        ),
        "parity_with_base_run": [
            "DAT nodal U/RF numeric row arrays must match exactly",
            "STA rows and token arrays must match exactly",
            "CVG rows and token arrays must match exactly",
        ],
    }
    expected["section_force_contract"] = section_gate
    expected["requested_outputs"]["section_print"] = section_gate
    expected["requested_outputs"]["source_method_screen"] = {
        "path": str(METHOD_SCREEN.relative_to(REPO)),
        "sha256": METHOD_SCREEN_SHA256,
        "interpretation": "SOF is extrapolated/averaged bulk stress output, not MORTAR contact force",
    }
    expected_bytes = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    (HERE / "expected.json").write_bytes(expected_bytes)

    readiness = {
        "schema": "calculix_mortar_c3d10_section_force_readiness/v1",
        "status": "READY_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "parent_owns": ["input freeze", "bounded serial native execution", "result audit"],
        "base_passing_fixture_pins": expected["base_passing_fixture"],
        "source_archive_sha256": expected["source"]["archive_sha256"],
        "source_screen_sha256": METHOD_SCREEN_SHA256,
        "source_members_sha256": SOURCE_MEMBERS,
        "derived_files_sha256": {
            "input/mortar_c3d10.inp": sha(decks[input_names[0]]),
            "input/penalty_c3d10.inp": sha(decks[input_names[1]]),
            "expected.json": sha(expected_bytes),
        },
        "checks": {
            "passed_fullstep_fixture_pins_verified": True,
            "source_archive_and_section_output_members_verified": True,
            "only_two_section_print_requests_per_step_added": True,
            "removing_section_requests_restores_base_inputs_byte_for_byte": True,
            "6_expected_reports_per_case": True,
            "global_option_not_requested": True,
            "mechanics_gates_inherited_unchanged": True,
        },
    }
    (HERE / "readiness.json").write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": readiness["status"],
        "cases": expected["cases"],
        "reports_per_case": section_gate["reports_per_case"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
