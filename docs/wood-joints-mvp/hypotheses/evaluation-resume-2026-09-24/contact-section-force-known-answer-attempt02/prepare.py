#!/usr/bin/env python3
"""Add nodal element-stress FRD output to the frozen section coupon inputs."""

import copy
import hashlib
import json
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EVAL = REPO / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
PREVIOUS = EVAL / "contact-section-force-known-answer-attempt01"
BASE = EVAL / "contact-mortar-c3d10-fullstep-attempt01"
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02/source.tar.bz2"
)
MANUAL = REPO / "fea/generated/ccx_2.23.pdf"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/noelfiles.f":
        "ed85b45d6987882e484f11a0be3dc9c2d716afba07d59483d364e0709107a59f",
    "CalculiX/ccx_2.23/src/resultsprint.f":
        "623792be43fcd68270eac18ab87e79acd0acdcc0f66e9fc87012438be6dc91cd",
    "CalculiX/ccx_2.23/src/frd.c":
        "6439bca2ae53c813ab6887c3c560dd15db5947fd8cf9b9f01ada5753d5ed9915",
}
PREVIOUS_PINS = {
    "input-freeze.json": "eeced8a094e46672831a4d2236cb984f6217f47af8cf331bb106df03a5c063ec",
    "execution.json": "1dcf538de97cbd720e952facda23ad63e8989458411b2d3b7d1b3a9a86093703",
    "verifier.py": "f56c23a1e27f623ba6deb94529c08ee62d74ea7e3e3a0f849649e4f23514ca5b",
    "verifier.json": "394e410aea2171b81eacf624c1ea274392c8e70518098ae71c00d45fe3c6bebc",
    "expected.json": "61d1d3485839dee22f6aafbc83fc2f37028a393589a10d7b7de39927718f481a",
}
BASE_PINS = {
    "input-freeze.json": "978f8e49e79d6569dc033595ce565ce8587e36c4c5845c5615f120582634e8b0",
    "execution.json": "a485410aada87d2e149b39ee77b78d3efcada065c833a0c7e91acf1a60312574",
    "verifier.py": "d86d98494241657b1f8dda8ea42d747dac851c2319b914458f520008bc3a572b",
    "verifier.json": "813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14",
    "RESULTS.md": "ba1f3b4b7dea4840547bde6b44497fd71e4f3d5d4d9912bc4cb7ce6fb9de3e77",
}
SECTION_BLOCK = (
    b"*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1\nSOF\n"
    b"*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1\nSOF\n"
)
EL_FILE_BLOCK = b"*EL FILE,FREQUENCY=1\nS\n"
INPUT_NAMES = ("mortar_c3d10.inp", "penalty_c3d10.inp")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def verify_pins(directory: Path, pins: dict[str, str]) -> None:
    for name, digest in pins.items():
        if sha((directory / name).read_bytes()) != digest:
            raise SystemExit(f"pinned artifact changed: {directory / name}")


def verify_frozen_files(directory: Path) -> dict:
    freeze = read_json(directory / "input-freeze.json")
    for name, digest in freeze["files_sha256"].items():
        if sha((directory / name).read_bytes()) != digest:
            raise SystemExit(f"frozen artifact changed: {directory / name}")
    return freeze


def verify_source() -> None:
    if sha(SOURCE_ARCHIVE.read_bytes()) != SOURCE_ARCHIVE_SHA256:
        raise SystemExit("pinned CalculiX 2.23 source archive hash mismatch")
    if sha(MANUAL.read_bytes()) != MANUAL_SHA256:
        raise SystemExit("pinned CalculiX 2.23 manual hash mismatch")
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for relative, digest in SOURCE_MEMBERS.items():
            member = archive.extractfile(archive.getmember("./" + relative))
            if member is None or sha(member.read()) != digest:
                raise SystemExit(f"pinned element-output source hash mismatch: {relative}")


def verify_prior_attempt() -> tuple[dict, dict, dict]:
    verify_pins(PREVIOUS, PREVIOUS_PINS)
    freeze = verify_frozen_files(PREVIOUS)
    execution = read_json(PREVIOUS / "execution.json")
    result = read_json(PREVIOUS / "verifier.json")
    if execution.get("status") != "completed_pending_audit":
        raise SystemExit("prior section execution is not the completed pinned run")
    if result.get("status") != "FAIL":
        raise SystemExit("prior section verifier no longer records the pinned failure")
    if result.get("error") != "Baseline mechanical/provenance gates fail":
        raise SystemExit("prior section verifier failure reason changed")
    for case in ("mortar_c3d10", "penalty_c3d10"):
        run = read_json(PREVIOUS / "output" / case / "execution.json")
        if run.get("status") != "completed" or run.get("docker_cli_exit_code") != 0:
            raise SystemExit(f"prior case did not complete as pinned: {case}")
    return freeze, execution, result


def verify_passed_baseline() -> dict:
    verify_pins(BASE, BASE_PINS)
    freeze = verify_frozen_files(BASE)
    if read_json(BASE / "execution.json").get("status") != "completed_pending_audit":
        raise SystemExit("fullstep baseline execution is not complete")
    if read_json(BASE / "verifier.json").get("status") != "PASS_METHOD_FIXTURE":
        raise SystemExit("fullstep baseline is not the pinned pass")
    return freeze


def add_element_stress(raw: bytes, name: str) -> bytes:
    marker = b"*END STEP\n"
    if raw.count(marker) != 3 or raw.count(SECTION_BLOCK) != 3:
        raise SystemExit(f"expected three section-print endpoints in {name}")
    updated = raw.replace(marker, EL_FILE_BLOCK + marker)
    if updated.count(EL_FILE_BLOCK) != 3 or updated.replace(EL_FILE_BLOCK, b"") != raw:
        raise SystemExit(f"unexpected non-output change in input/{name}")
    return updated


def node_ids(deck: bytes) -> list[int]:
    lines = deck.decode("ascii").splitlines()
    in_nodes = False
    ids = []
    for line in lines:
        if line.upper() == "*NODE":
            in_nodes = True
            continue
        if line.startswith("*"):
            in_nodes = False
        elif in_nodes and line.strip():
            ids.append(int(line.split(",", 1)[0]))
    if len(ids) != 54 or len(set(ids)) != 54:
        raise SystemExit("source deck is not the pinned 54-node mesh")
    return sorted(ids)


def main() -> None:
    for evidence in (HERE / "input-freeze.json", HERE / "execution.json", HERE / "output"):
        if evidence.exists():
            raise SystemExit(f"refusing to overwrite parent execution evidence: {evidence}")
    previous_freeze, previous_execution, previous_result = verify_prior_attempt()
    base_freeze = verify_passed_baseline()
    verify_source()

    previous_expected = read_json(PREVIOUS / "expected.json")
    previous_decks = {}
    decks = {}
    for name in INPUT_NAMES:
        relative = "input/" + name
        source_deck = (PREVIOUS / relative).read_bytes()
        if sha(source_deck) != previous_freeze["files_sha256"][relative]:
            raise SystemExit(f"prior frozen input hash mismatch: {relative}")
        previous_decks[name] = source_deck
        decks[name] = add_element_stress(source_deck, name)
        base_deck = (BASE / relative).read_bytes()
        if source_deck.replace(SECTION_BLOCK, b"") != base_deck:
            raise SystemExit(f"prior section deck no longer restores baseline: {relative}")
        if decks[name].replace(EL_FILE_BLOCK, b"") != source_deck:
            raise SystemExit(f"new deck changed more than EL FILE/S output: {relative}")
        if decks[name].replace(EL_FILE_BLOCK, b"").replace(SECTION_BLOCK, b"") != base_deck:
            raise SystemExit(f"new deck does not restore fullstep baseline: {relative}")

    if decks[INPUT_NAMES[0]].replace(b"TYPE=MORTAR", b"TYPE=CONTACT") != decks[
        INPUT_NAMES[1]
    ].replace(b"TYPE=SURFACE TO SURFACE", b"TYPE=CONTACT"):
        raise SystemExit("new decks differ beyond the contact type")

    for name, data in decks.items():
        (HERE / "input" / name).write_bytes(data)

    stress_members = [
        "CalculiX/ccx_2.23/src/noelfiles.f",
        "CalculiX/ccx_2.23/src/resultsprint.f",
        "CalculiX/ccx_2.23/src/frd.c",
    ]
    expected = copy.deepcopy(previous_expected)
    expected["schema"] = "calculix_mortar_c3d10_section_force_known_answer/v2"
    expected["status"] = "PREPARED_FOR_PARENT_REVIEW_NO_NATIVE_EXECUTION"
    expected["cases"]["mortar_c3d10"]["input_sha256"] = sha(decks[INPUT_NAMES[0]])
    expected["cases"]["penalty_c3d10"]["input_sha256"] = sha(decks[INPUT_NAMES[1]])
    expected["acceptance"].update({
        "require_frd_stress_at_all_nodes_each_accepted_state": True,
        "require_exact_mesh_node_coverage_and_finite_six_component_stress": True,
    })
    expected["section_force_contract"].pop("no_new_stress_frd_requests", None)
    expected["requested_outputs"]["section_print"].pop("no_new_stress_frd_requests", None)
    expected["requested_outputs"]["element_stress"] = {
        "requested_cards_per_step": ["*EL FILE,FREQUENCY=1 / S"],
        "frequency": 1,
        "frd_dataset_name": "STRESS",
        "components": ["SXX", "SYY", "SZZ", "SXY", "SYZ", "SZX"],
        "required_state_keys": [
            {"step": 1, "increment": 1, "time": 1.0},
            {"step": 2, "increment": 1, "time": 2.0},
            {"step": 3, "increment": 1, "time": 3.0},
        ],
        "mesh_node_count": 54,
        "mesh_node_ids": node_ids(previous_decks[INPUT_NAMES[0]]),
        "per_state_record_count": 54,
        "hard_gate": (
            "Each of the three accepted step-end STRESS datasets must contain exactly "
            "the 54 model node IDs once, with six finite stress components per node."
        ),
        "known_2_23_side_effect": (
            "Requesting S also enables ERR in the pinned 2.23 parser; ERR is incidental, "
            "not an acceptance gate."
        ),
        "interpretation": (
            "Nodal bulk-stress field availability and completeness only; stress values "
            "are not used as contact traction or joint acceptance."
        ),
    }
    expected["source"]["source_members_sha256"].update(SOURCE_MEMBERS)
    expected["source"]["notes"].extend([
        "noelfiles.f maps FREQUENCY=1 and S; S also enables ERR",
        "resultsprint.f extrapolates element stress to nodes",
        "frd.c emits STRESS with SXX,SYY,SZZ,SXY,SYZ,SZX",
    ])
    expected["prior_section_attempt"] = {
        "path": str(PREVIOUS.relative_to(REPO)),
        "input_freeze_sha256": sha((PREVIOUS / "input-freeze.json").read_bytes()),
        "execution_sha256": sha((PREVIOUS / "execution.json").read_bytes()),
        "verifier_source_sha256": sha((PREVIOUS / "verifier.py").read_bytes()),
        "verifier_result_sha256": sha((PREVIOUS / "verifier.json").read_bytes()),
        "verifier_status": previous_result["status"],
        "verifier_error": previous_result["error"],
        "input_sha256": {
            name: previous_freeze["files_sha256"]["input/" + name] for name in INPUT_NAMES
        },
        "output_frd_sha256": {
            case: sha((PREVIOUS / "output" / case / "coupon.frd").read_bytes())
            for case in ("mortar_c3d10", "penalty_c3d10")
        },
        "observed_output_issue": (
            "The prior audit found incomplete penalty FRD stress coverage: no nodal "
            "stress rows at opening/reopening, and 14 of 54 nodes at compression."
        ),
        "scope_of_fix": "Only add EL FILE stress output; no mechanical card changes.",
    }
    expected["base_passing_fixture"]["attempt01_section_output_extension"] = {
        "path": str(PREVIOUS.relative_to(REPO)),
        "freeze_sha256": PREVIOUS_PINS["input-freeze.json"],
        "execution_sha256": PREVIOUS_PINS["execution.json"],
        "verifier_source_sha256": PREVIOUS_PINS["verifier.py"],
        "failed_verifier_result_sha256": PREVIOUS_PINS["verifier.json"],
        "failed_verifier_status": "FAIL",
        "role": "Preserved failed SOF/FRD output attempt; no input or result reused.",
    }
    expected["element_stress_output_source"] = {
        "archive_path": str(SOURCE_ARCHIVE.relative_to(REPO)),
        "archive_sha256": SOURCE_ARCHIVE_SHA256,
        "manual_path": str(MANUAL.relative_to(REPO)),
        "manual_sha256": MANUAL_SHA256,
        "manual_section": "§7 *EL FILE",
        "source_members_sha256": SOURCE_MEMBERS,
        "source_basis": {
            "noelfiles.f": "FREQUENCY= sets jout(1); S selects element stress and auto-adds ERR.",
            "resultsprint.f": "Nodal stress extrapolation is performed for S output.",
            "frd.c": "The STRESS dataset has six named stress components.",
        },
    }
    expected_bytes = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    (HERE / "expected.json").write_bytes(expected_bytes)

    readiness = {
        "schema": "calculix_mortar_c3d10_section_force_stress_readiness/v1",
        "status": "READY_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "parent_owns": ["input freeze", "bounded serial native execution", "result audit"],
        "fullstep_baseline_unchanged": {
            "path": str(BASE.relative_to(REPO)),
            "input_freeze_sha256": BASE_PINS["input-freeze.json"],
            "execution_sha256": BASE_PINS["execution.json"],
            "pass_verifier_sha256": BASE_PINS["verifier.json"],
            "mortar_input_sha256": base_freeze["files_sha256"]["input/mortar_c3d10.inp"],
            "penalty_input_sha256": base_freeze["files_sha256"]["input/penalty_c3d10.inp"],
        },
        "prior_section_failure_pins": {
            name: digest for name, digest in PREVIOUS_PINS.items()
        },
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "manual_sha256": MANUAL_SHA256,
        "source_members_sha256": SOURCE_MEMBERS,
        "packet_files_sha256": {
            "prepare.py": sha((HERE / "prepare.py").read_bytes()),
            "README.md": sha((HERE / "README.md").read_bytes()),
        },
        "derived_files_sha256": {
            "input/mortar_c3d10.inp": sha(decks[INPUT_NAMES[0]]),
            "input/penalty_c3d10.inp": sha(decks[INPUT_NAMES[1]]),
            "expected.json": sha(expected_bytes),
        },
        "checks": {
            "prior_attempt01_failure_pins_and_outputs_verified": True,
            "fullstep_pass_baseline_pins_and_inputs_verified": True,
            "only_three_EL_FILE_S_blocks_added_to_attempt01_inputs": True,
            "removing_EL_FILE_blocks_restores_attempt01_inputs_byte_for_byte": True,
            "removing_SECTION_and_EL_FILE_blocks_restores_fullstep_inputs": True,
            "source_archive_manual_and_output_member_hashes_verified": True,
            "stress_gate_is_54_nodes_times_three_accepted_states_per_case": True,
            "no_solver_or_container_launched": True,
        },
    }
    (HERE / "readiness.json").write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "status": readiness["status"],
        "inputs": expected["cases"],
        "stress_states_per_case": len(
            expected["requested_outputs"]["element_stress"]["required_state_keys"]
        ),
        "stress_nodes_per_state": (
            expected["requested_outputs"]["element_stress"]["per_state_record_count"]
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
