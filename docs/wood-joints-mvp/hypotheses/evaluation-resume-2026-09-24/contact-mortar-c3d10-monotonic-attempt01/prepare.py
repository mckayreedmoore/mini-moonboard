#!/usr/bin/env python3
"""Derive a one-step monotonic coupon from the pinned known-answer decks."""

import hashlib
import json
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
STEP_MARKER = "** STEP: OPEN; prescribed top-face U3=+0.001000 mm\n"
STEP = """** STEP: MONOTONIC_COMPRESSION; top U3 ramps from 0 to -0.005 mm
*STEP,NLGEOM,INC=100
*STATIC
0.1,1.0,1e-8,0.1
*BOUNDARY
TOP,3,3,-0.005000
*NODE PRINT,NSET=ALLNODES,FREQUENCY=1
U,RF
*NODE FILE,FREQUENCY=1
U,RF
*CONTACT FILE,FREQUENCY=1
CDIS,CSTR
*END STEP
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive(source_name: str, contact_type: str) -> bytes:
    source = (SOURCE / "input" / source_name).read_bytes()
    if sha(source) != SOURCE_INPUTS[source_name]:
        raise SystemExit(f"pinned source deck hash mismatch: {source_name}")
    text = source.decode("ascii")
    if text.count(STEP_MARKER) != 1:
        raise SystemExit(f"unexpected source step marker: {source_name}")
    prefix = text.split(STEP_MARKER, 1)[0]
    prefix = prefix.replace(
        "C3D10 compression/open/reopen method coupon; not a joint model",
        "C3D10 monotonic compression method coupon; not a joint model",
    )
    deck = (prefix + STEP).encode("ascii")
    if deck.count(f"TYPE={contact_type}".encode("ascii")) != 1:
        raise SystemExit(f"contact formulation changed unexpectedly: {source_name}")
    return deck


def main() -> None:
    for evidence in (HERE / "input-freeze.json", HERE / "execution.json", HERE / "output"):
        if evidence.exists():
            raise SystemExit(f"refusing to regenerate frozen/executed packet: {evidence}")
    if sha((SOURCE / "expected.json").read_bytes()) != SOURCE_EXPECTED_SHA256:
        raise SystemExit("pinned source expected.json hash mismatch")
    if sha(SOURCE_ARCHIVE.read_bytes()) != SOURCE_ARCHIVE_SHA256:
        raise SystemExit("pinned CalculiX source archive hash mismatch")

    names = ("mortar_c3d10.inp", "penalty_c3d10.inp")
    decks = {
        names[0]: derive(names[0], "MORTAR"),
        names[1]: derive(names[1], "SURFACE TO SURFACE"),
    }
    normalized = decks[names[0]].replace(b"TYPE=MORTAR", b"TYPE=CONTACT")
    if normalized != decks[names[1]].replace(b"TYPE=SURFACE TO SURFACE", b"TYPE=CONTACT"):
        raise SystemExit("derived decks differ outside the contact TYPE value")
    (HERE / "input").mkdir(exist_ok=True)
    for name, data in decks.items():
        (HERE / "input" / name).write_bytes(data)

    expected = json.loads((SOURCE / "expected.json").read_text())
    expected["schema"] = "calculix_mortar_c3d10_monotonic_known_answer/v1"
    expected["status"] = "PREPARED_FOR_PARENT_REVIEW_NO_NATIVE_EXECUTION"
    expected["acceptance"].update({
        "require_all_three_steps_accepted": False,
        "require_one_monotonic_compression_step_accepted": True,
        "require_open_compression_reopen_force_and_series_compliance": False,
        "claim_opening_or_reversal_validated": False,
    })
    expected["analytical_known_answer"].pop("open_and_reopen", None)
    expected["analytical_known_answer"]["all_accepted_increment_profile"] = {
        "step1_monotonic_compression": (
            "top U3=-0.005*t mm for step-relative t in [0,1]; "
            "pressure=max(-top_U3,0)/C, C=5e-5 mm3/N; "
            "apply the existing uniform axial series profile at each accepted increment"
        ),
        "interface_geometry_gap_sign": (
            "upper slave average U3 minus lower master average U3; "
            "positive is clearance and negative is overlap"
        ),
    }
    expected["steps"] = [{
        "step": 1,
        "name": "MONOTONIC_COMPRESSION",
        "initial_top_u3_mm": 0.0,
        "top_u3_mm": -0.005,
        "nominal_increments": 10,
        "requested_cards": ["*STEP,NLGEOM,INC=100", "*STATIC", "0.1,1.0,1e-8,0.1"],
        "requested_minimum_increment_note": (
            "The deck requests 1e-8; pinned solver raises the effective STATIC minimum to 1e-6. "
            "The declared .1 schedule should not require a cutback."
        ),
    }]
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
    expected["requested_outputs"]["steps"] = ["one monotonic compression step"]
    expected["history_discriminator"] = {
        "prior_fixture_execution_sha256": (
            "c09e9d37dff3f8702c5a651f78f7ab44f508265ea82c5f2ef3f0019cb209c49c"
        ),
        "interpretation": (
            "A MORTAR pass here would show the prior failure is not reproduced on direct "
            "monotonic compression, consistent with dependence on prior opening/reversal. "
            "A MORTAR failure here shows the defect is not limited to that prior history."
        ),
        "limit": "This one-step pair does not validate opening, reopening, or joint behavior.",
    }
    expected_bytes = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    (HERE / "expected.json").write_bytes(expected_bytes)
    readiness = {
        "schema": "calculix_mortar_c3d10_monotonic_readiness/v1",
        "status": "READY_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "parent_owns": ["input freeze", "bounded serial native execution", "result audit"],
        "source_fixture": "contact-mortar-c3d10-known-answer-attempt01",
        "source_expected_sha256": SOURCE_EXPECTED_SHA256,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "derived_files_sha256": {
            "input/mortar_c3d10.inp": sha(decks[names[0]]),
            "input/penalty_c3d10.inp": sha(decks[names[1]]),
            "expected.json": sha(expected_bytes),
        },
        "checks": {
            "source_deck_hashes_verified": True,
            "contact_type_is_only_deck_difference": True,
            "one_nlgeom_static_step_only": True,
            "initial_touch_then_monotonic_compression": True,
            "open_or_reopen_acceptance_claim": False,
            "known_answer_and_tolerances_inherited_unchanged": True,
        },
    }
    (HERE / "readiness.json").write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "cases": expected["cases"],
        "readiness": readiness["status"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
