#!/usr/bin/env python3
"""Derive fixed-one-increment decks from the pinned three-step coupon."""

import hashlib
import json
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EVAL = REPO / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SOURCE = EVAL / "contact-mortar-c3d10-known-answer-attempt01"
SOURCE_EXPECTED_SHA256 = "7013bb5fd9f0aa6c30b1d93bee9741dc757a5a3fcba473804741eb89f2824da1"
SOURCE_INPUTS = {
    "mortar_c3d10.inp": "618197036e03a565a9c9e1be763aea9137f2edbeb6bc4209ea3cd1d0656e6566",
    "penalty_c3d10.inp": "95eef006c0e54786e172dbfd501ec0c5935981a133ab6e64ebeabb85a5ee425b",
}
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02/source.tar.bz2"
)
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/statics.f": "d5add12845e7dc6e7a19043fa6114012b9f36ed0723590308d60f4b09eee4599",
    "CalculiX/ccx_2.23/src/gencontelem_f2f.f": "853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe",
    "CalculiX/ccx_2.23/src/slavintmortar.f": "a993c9a84202b7ce642073e52994269697eb487afbc51c86ff61c303b4f6e808",
}
STATIC_OLD = b"*STATIC\n0.1,1.0,1e-8,0.1\n"
STATIC_NEW = b"*STATIC,DIRECT\n1,1\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_source() -> None:
    if sha(SOURCE_ARCHIVE.read_bytes()) != SOURCE_ARCHIVE_SHA256:
        raise SystemExit("pinned CalculiX source archive hash mismatch")
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for path, expected in SOURCE_MEMBERS.items():
            member = archive.getmember("./" + path)
            actual = sha(archive.extractfile(member).read())
            if actual != expected:
                raise SystemExit(f"pinned source member hash mismatch: {path}")


def derive(name: str) -> bytes:
    raw = (SOURCE / "input" / name).read_bytes()
    if sha(raw) != SOURCE_INPUTS[name]:
        raise SystemExit(f"pinned source deck hash mismatch: {name}")
    if raw.count(STATIC_OLD) != 3:
        raise SystemExit(f"expected three original automatic STATIC schedules in {name}")
    return raw.replace(STATIC_OLD, STATIC_NEW)


def main() -> None:
    for evidence in (HERE / "input-freeze.json", HERE / "execution.json", HERE / "output"):
        if evidence.exists():
            raise SystemExit(f"refusing to regenerate frozen/executed packet: {evidence}")
    source_expected = (SOURCE / "expected.json").read_bytes()
    if sha(source_expected) != SOURCE_EXPECTED_SHA256:
        raise SystemExit("pinned source expected.json hash mismatch")
    verify_source()

    names = ("mortar_c3d10.inp", "penalty_c3d10.inp")
    decks = {name: derive(name) for name in names}
    if decks[names[0]].replace(b"TYPE=MORTAR", b"TYPE=CONTACT") != decks[names[1]].replace(
        b"TYPE=SURFACE TO SURFACE", b"TYPE=CONTACT"
    ):
        raise SystemExit("derived decks differ outside the contact TYPE value")
    (HERE / "input").mkdir(exist_ok=True)
    for name, data in decks.items():
        (HERE / "input" / name).write_bytes(data)

    expected = json.loads(source_expected)
    expected["schema"] = "calculix_mortar_c3d10_fullstep_known_answer/v1"
    expected["status"] = "PREPARED_FOR_PARENT_REVIEW_NO_NATIVE_EXECUTION"
    expected["acceptance"].update({
        "require_exactly_one_accepted_increment_per_step": True,
        "require_no_cutbacks_or_rejected_attempts": True,
        "direct_is_fixed_increment_not_alternate_linear_solver": True,
    })
    expected["steps"] = [
        {
            "step": 1, "name": "OPEN", "top_u3_mm": 0.001,
            "nominal_increments": 1, "static_direct": True,
            "static_data_line": "1,1",
        },
        {
            "step": 2, "name": "COMPRESSION", "top_u3_mm": -0.005,
            "nominal_increments": 1, "static_direct": True,
            "static_data_line": "1,1",
        },
        {
            "step": 3, "name": "REOPEN", "top_u3_mm": 0.001,
            "nominal_increments": 1, "static_direct": True,
            "static_data_line": "1,1",
        },
    ]
    expected["cases"] = {
        "mortar_c3d10": {
            "input": "input/mortar_c3d10.inp",
            "input_sha256": sha(decks[names[0]]),
            "contact_type": "MORTAR",
        },
        "penalty_c3d10": {
            "input": "input/penalty_c3d10.inp",
            "input_sha256": sha(decks[names[1]]),
            "contact_type": "SURFACE TO SURFACE",
            "role": "separate law-matched method comparison; never mixed in one deck",
        },
    }
    expected["source"]["source_members_sha256"].update(SOURCE_MEMBERS)
    expected["source"]["notes"].extend([
        "statics.f parses *STATIC,DIRECT into idrct=1; manual §7.122 specifies a fixed increment",
        "gencontelem_f2f.f:570-585 and slavintmortar.f:90-93 govern static gap-shrink paths",
    ])
    expected["direct_schedule"] = {
        "meaning": "Fixed step increment, not a direct matrix solver or dynamic procedure",
        "manual": {
            "version": "2.23",
            "section": "§7.122 *STATIC",
            "path": "fea/generated/ccx_2.23.pdf",
            "sha256": "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330",
        },
        "source_file": "CalculiX/ccx_2.23/src/statics.f",
        "source_sha256": SOURCE_MEMBERS["CalculiX/ccx_2.23/src/statics.f"],
        "source_lines": [95, 97],
        "effect": "Each successful step has one full-step increment; convergence failure stops the run.",
        "cutback_is_acceptance": False,
    }
    expected["schedule_discriminator"] = {
        "prior_monotonic_result": (
            "Both formulations failed an intermediate accepted-state gate; "
            "penalty reached the expected compression endpoint."
        ),
        "question": (
            "Does the same opening/compression/reopening endpoint sequence recover "
            "its analytical endpoint response when every step has one full increment?"
        ),
        "limit": (
            "This tests three endpoint states and the schedule only; it does not validate "
            "subincrement response or full-joint behavior."
        ),
    }
    expected["requested_outputs"]["trace_contract"].update({
        "accepted_increment_count_by_step": {"1": 1, "2": 1, "3": 1},
        "no_rejected_attempts_or_cutbacks": True,
    })
    expected_bytes = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    (HERE / "expected.json").write_bytes(expected_bytes)

    readiness = {
        "schema": "calculix_mortar_c3d10_fullstep_readiness/v1",
        "status": "READY_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "parent_owns": ["input freeze", "bounded serial native execution", "result audit"],
        "source_expected_sha256": SOURCE_EXPECTED_SHA256,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "manual_sha256": expected["direct_schedule"]["manual"]["sha256"],
        "derived_files_sha256": {
            "input/mortar_c3d10.inp": sha(decks[names[0]]),
            "input/penalty_c3d10.inp": sha(decks[names[1]]),
            "expected.json": sha(expected_bytes),
        },
        "checks": {
            "source_deck_hashes_verified": True,
            "source_archive_and_member_hashes_verified": True,
            "only_static_schedule_cards_changed": True,
            "contact_type_is_only_deck_difference": True,
            "three_original_targets_preserved": True,
            "one_fixed_increment_per_step": True,
            "linear_known_answer_and_tolerances_inherited_unchanged": True,
        },
    }
    (HERE / "readiness.json").write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "cases": expected["cases"],
        "readiness": readiness["status"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
