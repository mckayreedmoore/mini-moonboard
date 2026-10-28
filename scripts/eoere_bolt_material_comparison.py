"""Compare specified bolt families on two frozen V11 fields.

Only material comparison inputs change. The existing Mp/4 helper, full signed
steel demands, bearing fields and body/root profiles are reused. No candidate
forces, geometry, supplier selection or physical acceptance are changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
PUBLIC = ROOT / "docs/bolted-frame-development/owner-frame-v11/bolt-material-comparison.json"
RAW = ROOT / "fea/generated/v11-zero-spacer-eight-bolt-v1/hardware/material-scope/owner-comparison-v1"
PINS = {
    "docs/bolted-frame-development/owner-frame-v11/owner-material-purchase-decisions.json": "6f437911a9603ee4310eb284938479050049f6e54afd80792733d77f9d6b1da3",
    "docs/bolted-frame-development/owner-frame-v11/owner-four-bolt-outer-top-evaluation.json": "9f7a52fa675826cd7ec71ef950dfd1e3a549767be8e72740342a952eee435493",
    "docs/bolted-frame-development/owner-frame-v11/shorter-bolts/response-bank.json": "0ac9bb41342279c536e955e30bc2b5588e07c235843186820982e7a60455c35c",
    "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/response-bank.json": "a87f9edfa6006c206e883dd28108c8fa78369dbc8e40a256f141405fcfa5d092",
    "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/geometry-receipt.json": "b52265bcb0d9ff4cdf8215794a00df7b8f13bca285da9a7db532072c18147882",
    "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/planning/grouped-hardware.csv": "c82ff566e1ef0b541f08226cada83a11c5f1293326fb1e906634e5e920e97a4f",
    "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/hardware-profile-contract.json": "abcc49a6f59e4183b8b522e5fa064157f7107cf290a3043fac76d4927a508f8f",
    "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/hardware-option-twelve-grade5.json": "cb699292fa1e9a71e197bc7b12c31530ab1b6932a730ac49b0cc40f902373df0",
    "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/error-audit.json": "b79069db91fea439b5c21aac344495f0186cf189364f9d8499e3f75a47bcee47",
    "fea/generated/v11-shorter-bolts-v1/connections/method-closure/generalized-wrench/common-work-contracted-ellipse-v1/mixed-Mp4-projection-v1.json": "d44dd0e078d2164fa2bba170b6e28c2be45d21829f897a11dc20f2bbdd65b885",
    "fea/generated/v11-shorter-bolts-v1/connections/method-closure/generalized-wrench/common-work-contracted-ellipse-v1/project_mixed_mp4_v1.py": "fef047fcdc90f4cd6f6a232dc866000cce6e1f580621ae69769a9a257caa65de",
    "fea/generated/v11-zero-spacer-eight-bolt-v1/references/mixed-common-work-v1/runs/reference-v2/mixed-common-work-Mp4-rows-v1.json": "9883ecc2ce52ba9a54e849f88132b54d33305c85b2d8b32ec7135a774ab27ba3",
    "fea/generated/v11-relocated-rear-pair-v1/references/connection-closeout-v1/a574/decision-v1.json": "4150ae57d6c6afd8e46e9ee0a1948c62ee90bf15ebce6c5b3daf0101b0edcf3c",
    "fea/generated/v11-shorter-bolts-v1/connections/method-closure/A574-property/source-cache/a574-17.pdf": "7e2784c14e655862f0c22da437c200394702f31c7a1b23bb4130930b6e033c6a",
    "fea/generated/v11-shorter-bolts-v1/connections/method-closure/A574-property/source-cache/a574-17-page-2.png": "c4428d00c1eeec535f6f17b80daae0ee63bc17e14f646ef72071ed53537d8864",
    "fea/generated/v11-zero-spacer-eight-bolt-v1/hardware/material-scope/A574-proof-permanent-set-inference-v1.json": "e68f8782d5541054bb29fdb0d664c0c827acda933f3ba24452aae12afb93870b"
}
MPA_PER_KSI = 6.894757293168361
BASE = "fea/generated/v11-shorter-bolts-v1/connections/method-closure/generalized-wrench/"
HELPER = BASE + "common-work-contracted-ellipse-v1/project_mixed_mp4_v1.py"
INPUTS = {
    "selected112": {
        "revision": "v11-shorter-bolts-v1",
        "rows": BASE + "common-work-contracted-ellipse-v1/mixed-Mp4-projection-v1.json",
        "bank": "docs/bolted-frame-development/owner-frame-v11/shorter-bolts/response-bank.json",
        "generic_flag_count": 5,
    },
    "zero_spacer114": {
        "revision": "v11-zero-spacer-eight-bolt-v1",
        "rows": "fea/generated/v11-zero-spacer-eight-bolt-v1/references/mixed-common-work-v1/runs/reference-v2/mixed-common-work-Mp4-rows-v1.json",
        "bank": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/response-bank.json",
        "generic_flag_count": 3,
    },
}
CASES = {"a12-forward", "a12-left", "a12-rear", "k12-right", "k12-rear", "a1-rear"}


def read(name):
    return json.loads((ROOT / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(name):
    path = ROOT / name
    return {"path": name, "sha256": digest(path)}


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def verify_sources():
    for name, expected in PINS.items():
        if digest(ROOT / name) != expected:
            raise ValueError("Frozen source changed: " + name)


def maximum(rows, key):
    row = max(rows, key=lambda r: r[key])
    return {"value": row[key], "axis_id": row["axis_id"], "case_id": row["case_id"]}


def build():
    verify_sources()
    spec = importlib.util.spec_from_file_location("frozen_mp4_comparison_helper", ROOT / HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    all_rows, summaries, field_pins = {}, {}, {}
    # Existing proven section envelope for the review-only Grade 5 head/profile.
    root_ratio = 7.31774 / 7.3787
    profile_stress_bound = root_ratio ** -3
    decimal_error = 0.0
    for label, setup in INPUTS.items():
        source = read(setup["rows"])
        rows = []
        identities = {(r["axis_id"], r["case_id"]) for r in source["rows"]}
        assert len(identities) == len(source["rows"]) == 144
        assert {case for _, case in identities} == CASES
        assert len({axis for axis, _ in identities}) == 24
        for row in source["rows"]:
            if label == "selected112":
                fyb = row["conditional_Fyb_reference_psi_unchanged"]
                hinge_source = row["source_hinge_Mp5_preserved"]
                bearing = row["contracted_bearing_index_unchanged"]
                steel = row["preserved_independent_steel_and_legacy_thresholds_MPa"]
            else:
                fyb = row["conditional_Fyb_reference_psi"]
                hinge_source = row["own_Mp5_hinge_source_preserved"]
                bearing = row["contracted_bearing_index"]
                steel = row["own_full_N_V_T_M_reference"]["criterion_thresholds_MPa"]
            assert fyb in (45000.0, 92000.0)
            is_a574 = fyb == 45000.0
            assert math.isclose(
                helper.project_hinge(hinge_source)["required_Fyb_MPa"],
                row["Mp4_required_Fyb_MPa"], rel_tol=1e-12,
            )
            required_fyb = row["Mp4_required_Fyb_ksi"]
            required_fy = steel["Fy_required_from_independent_Fy_over_2_VM"] / MPA_PER_KSI
            comparison = 60.0 if is_a574 else 92.0
            ratio = root_ratio if is_a574 else 1.0
            stress_bound = profile_stress_bound if is_a574 else 1.0
            item = {
                "axis_id": row["axis_id"], "case_id": row["case_id"],
                "current_material": "ASTM A574" if is_a574 else "SAE J429 Grade 5",
                "required_Fyb_ksi": required_fyb,
                "required_Fy_ksi_under_separate_Fy_over2": required_fy,
                "unchanged_bearing_index": bearing,
                "preserved_generic45_or_Grade5_index": row["combined_common_work_Mp4_index"],
                "engineering_assumed60_A574_combined_index": max(bearing, required_fyb / comparison),
                "engineering_assumed60_separate_elastic_index": required_fy / comparison,
                "Grade5_profile_fixed_field_combined_upper_bound": max(
                    bearing / ratio, required_fyb * stress_bound / 92.0,
                ),
                "Grade5_profile_fixed_field_elastic_upper_bound": required_fy * stress_bound / 92.0,
                "A574_note153_bending_only_sensitivity": max(
                    bearing, required_fyb / (153.0 if is_a574 else 92.0),
                ),
                "A574_note153_conventional_elastic_index": None,
            }
            with localcontext() as ctx:
                ctx.prec = 50
                independent = Decimal(str(required_fyb)) / Decimal(str(comparison))
                decimal_error = max(decimal_error, abs(float(independent) - required_fyb / comparison))
            field = row["source_field"]
            prior = field_pins.setdefault(field["path"], field["sha256"])
            assert prior == field["sha256"]
            rows.append(item)
        assert Counter(r["current_material"] for r in rows) == {
            "ASTM A574": 72, "SAE J429 Grade 5": 72,
        }
        assert sum(r["preserved_generic45_or_Grade5_index"] > 1 for r in rows) == setup["generic_flag_count"]
        assert all(r["engineering_assumed60_A574_combined_index"] <= 1 for r in rows)
        assert all(r["engineering_assumed60_separate_elastic_index"] <= 1 for r in rows)
        summaries[label] = {
            "revision": setup["revision"], "response_bank": reference(setup["bank"]),
            "source_rows": reference(setup["rows"]), "states": 144,
            "A574_states": 72, "Grade5_states": 72,
            "unchanged_max_required_Fyb_ksi": maximum(rows, "required_Fyb_ksi"),
            "unchanged_max_required_Fy_ksi": maximum(rows, "required_Fy_ksi_under_separate_Fy_over2"),
            "preserved_generic45_maximum": maximum(rows, "preserved_generic45_or_Grade5_index"),
            "preserved_generic45_flags": setup["generic_flag_count"],
            "engineering_assumed60_A574_combined": maximum(rows, "engineering_assumed60_A574_combined_index"),
            "engineering_assumed60_separate_elastic": maximum(rows, "engineering_assumed60_separate_elastic_index"),
            "engineering_assumed60_flags": 0,
            "Grade5_profile_fixed_field_combined_upper_bound": maximum(rows, "Grade5_profile_fixed_field_combined_upper_bound"),
            "Grade5_profile_fixed_field_elastic_upper_bound": maximum(rows, "Grade5_profile_fixed_field_elastic_upper_bound"),
            "A574_note153_bending_only_sensitivity": maximum(rows, "A574_note153_bending_only_sensitivity"),
            "complete_joint_capacity": None,
        }
        all_rows[label] = rows
    for name, expected in field_pins.items():
        assert digest(ROOT / name) == expected, "Current field changed: " + name

    grouped_name = "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/planning/grouped-hardware.csv"
    with (ROOT / grouped_name).open(newline="") as stream:
        inventory = [
            {k: row[k] for k in (
                "sku", "required_quantity_each", "nominal_description",
                "grade_or_material", "historical_product_link", "conditional_bolt_type_id",
            )}
            for row in csv.DictReader(stream) if row["category"] == "bolt"
        ]
    assert sum(int(row["required_quantity_each"]) for row in inventory) == 114
    assert sum(int(row["required_quantity_each"]) for row in inventory if row["sku"] in ("8092", "8093")) == 16
    assert sum(int(row["required_quantity_each"]) for row in inventory if not row["sku"]) == 4
    detail = {
        "schema": "v11_owner_bolt_material_comparison_rows/v1",
        "rows": all_rows,
        "unchanged_source_fields": field_pins,
    }
    detail_bytes = encode(detail)
    detail_ref = {
        "path": str((RAW / "comparison-rows.json").relative_to(ROOT)),
        "sha256": hashlib.sha256(detail_bytes).hexdigest(),
    }
    report = {
        "schema": "v11_owner_bolt_material_comparison/v1",
        "question": "Which current exceedances need a different cleat, and which change under a reasonable explicitly assumed material comparison?",
        "owner_direction": "Look at the actual scheduled bolts and use reasonable available comparisons when exact product comparisons are absent; compare cleat and general exceedance alternatives.",
        "producer": reference(str(SELF.relative_to(ROOT))),
        "reproduce": "uv run python scripts/eoere_bolt_material_comparison.py --check",
        "recorded_inventory_scope": "Scheduled zero-spacer 114-bolt hardware, not an observation of delivered parts. Owner's saved record says nuts/bolts unpurchased.",
        "scheduled_bolt_families": {
            "A574_socket_screws": 16, "Grade5_hex_cap_screws_including_four_conditional_types": 98,
            "bolt_sku_8093_quantity": 12, "bolt_sku_8092_quantity": 4,
            "four_shorter_Grade5_supplier_SKUs_selected": False,
        },
        "scheduled_bolt_inventory": inventory,
        "comparison_basis": {
            "engineering_assumed60": {
                "A574_Fyb_ksi": 60.0, "A574_conventional_Fy_ksi": 60.0,
                "Grade5_Fyb_ksi": 92.0, "Grade5_conventional_Fy_ksi": 92.0,
                "status": "Owner-authorized conditional engineering comparison; additional conventional-yield assumption, not a supplier guarantee, actual measured property, or adopted NDS joint capacity.",
                "reason_for_use": "Reuses the already documented reduced 60-ksi material specification as a practical sensitivity on both current frozen banks. It is intentionally separate from generic 45-ksi bookkeeping and A574's much higher tensile/proof/design-note figures.",
                "proven_by_A574_label_or_proof": False,
                "comparison_only": True,
                "required_before_claiming_product_conformity": "An applicable material/product specification supporting conventional tensile yield at least60ksi; no blanket new physical test or external sign-off gate is imposed.",
            },
            "A574_primary_source": {
                "edition": "ASTM A574-17 Table1 and Note1, pinned original",
                "size_band": "Current 3/8-inch screws",
                "full_size_minimum_tensile_ksi": 180.0, "full_size_proof_stress_ksi": 140.0,
                "design_note_yield_ksi": 153.0, "design_note_offset_percent": 2.0,
                "Table1_machined_0_2percent_yield_applies_to_this_size": False,
                "proof_is_not_yield": True,
                "use_153_as_conventional_elastic_Fy": False,
                "why_not_automatically_use_153": "The retained original explicitly uses2% offset for the small-size design note. The machined0.2% row is not applicable at3/8in; neither is silently relabeled. The153 bending sensitivity is not a qualified F606/Fyb property route.",
            },
            "Grade5_alternative": {
                "scope": "Review-only substitution of twelve8093 cleat stacks; current Grade5 stacks unchanged.",
                "specified_Fyb_ksi": 92.0, "specified_Fy_ksi": 92.0,
                "existing_source_route": "Pinned J429_201405/F606-F606M21 and NDS2024_12.3.6.2 conditional tensile-yield route.",
                "current_root_mm": 7.3787, "alternative_root_mm": 7.31774,
                "uniform_root_ratio": root_ratio,
                "conservative_stress_bound_multiplier": profile_stress_bound,
                "changed_head_profile_requires_matched_geometry_mass_contact_and_forces": True,
                "supplier_selected": False, "implemented": False,
            },
        },
        "comparisons": summaries,
        "beyond_material": [
            "Current114 plywood-cleat perimeter reference0.415393 is below its conditional component limit; this is separate from individual bolt, end-distance, bond and complete-joint checks.",
            "Material assumptions do not remove the four cleat-post near-end comparisons, top TableD6.35mm shortfall, optional rear-foot scenarios, or complete splitting/contact/bond requirements.",
            "The separately authorized106-bolt outer-top trial keeps eight bolts per cleat and restores eight planned top bores. Its own force bank and comparisons are pending; neither current bank is transferred.",
        ],
        "remedy_order": [
            {"route": "Retain current plywood outlines and current socket heads; use the declared reduced60ksi comparison.",
             "benefit": "No geometry or force change for the material-only comparison; both current mixed atlases have zero rows above this material reference.",
             "limit": "An explicitly assumed comparison does not establish actual material conformity or clear end/row/splitting details."},
            {"route": "Substitute twelve same-diameter partially threaded Grade5 hex-cap cleat bolts.",
             "benefit": "Known conditional tensile-yield route; current conservative profile bounds stay below one without changing cleat outlines or hole stations.",
             "limit": "Exact6.5in product/profile, head seats/tool access, selfweight and matching mechanics require disposition before adoption."},
            {"route": "Finish the separately authorized four-bolt outer-top comparison, retaining eight per cleat.",
             "benefit": "Uses owned fittings and far rows to address the top pattern without changing cleat outlines.",
             "limit": "Changed top connection forces, local geometry and complete checks require its own bank; not a current pass."},
            {"route": "Revise the cleat-post bolt group or its supporting end detail if its end-distance hold persists.",
             "benefit": "Targets the actual hole-to-timber-end limitation while preserving the climbing surface.",
             "limit": "Thicker plywood or a stronger bolt alone does not add timber beyond the hole; new marks, access, net sections and forces must be checked."},
            {"route": "Larger gusset with an independently arranged bolt group or a new bearing-seat connection.",
             "benefit": "Possible broader fallback if local detailing cannot satisfy the complete joint.",
             "limit": "Unmodeled alternative, not a selected design; requires clearance, timber-end support, bond/load-path and complete matched evaluation. Existing shortfalls do not prove this redesign is necessary."},
        ],
        "source_verification": {
            "supplier_lookup": "Stripe Directory CLI unavailable; public primary product pages checked. No outreach, order, account change or purchase.",
            "primary_product_pages_checked": [
                {"url": "https://boltdepot.com/Product-Details?product=8093",
                 "facts": "3/8-16x6.5in partial-thread ASME B18.3, ASTM A574, minimum body4.69in."},
                {"url": "https://boltdepot.com/Product-Details?product=8092",
                 "facts": "3/8-16x6in partial-thread ASME B18.3, ASTM A574, minimum body4.19in."},
                {"url": "https://boltdepot.com/Product-Details?product=363",
                 "facts": "3/8-16x2.5in partial-thread ASME B18.2.1, SAE J429 Grade5."},
                {"url": "https://boltdepot.com/Product-Details?product=365",
                 "facts": "3/8-16x3in partial-thread ASME B18.2.1, SAE J429 Grade5."},
            ],
            "standard_design_methods": "Pinned original A574 image and existing NDS/F606 method chain, plus https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf; no new proof-to-yield conversion.",
        },
        "controls": {
            "states_replayed": 288, "material_families_per_bank": 2, "case_count_per_bank": 6,
            "existing_Mp4_helper_reused": True,
            "Grade5_states_unchanged_per_bank": 72,
            "signed_forces_moments_profiles_and_bearing_fields_unchanged": True,
            "all12_force_field_hashes_verified": len(field_pins) == 12,
            "decimal50_maximum_scaling_error": decimal_error,
            "explicit_two_percent_note_not_relabeled": True,
            "old_flags_and_banks_unchanged": True,
        },
        "source_bindings": PINS, "detailed_rows": detail_ref,
        "next106_force_result_transferred": False,
        "actual_Fy": None, "actual_Fyb": None, "actual_Cg": None, "actual_Cdelta": None,
        "complete_joint_capacity": None, "structural_acceptance": False,
        "complete_joint_qualified": False, "geometry_changed": False,
        "hardware_substitution_selected": False, "purchase_authorized": False,
        "fabrication_released": False, "climbing_released": False,
    }
    assert len(field_pins) == 12
    assert decimal_error <= 1e-15
    verify_sources()
    return report, detail_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Reproduce and compare existing owned outputs without writing")
    args = parser.parse_args()
    report, detail_bytes = build()
    public_bytes = encode(report)
    detail_path = RAW / "comparison-rows.json"
    if args.check:
        assert PUBLIC.read_bytes() == public_bytes, "Published comparison differs"
        assert detail_path.read_bytes() == detail_bytes, "Detailed comparison differs"
    else:
        assert not PUBLIC.exists() and not detail_path.exists(), "Use a fresh revision; preserve existing evidence"
        RAW.mkdir(parents=True, exist_ok=True)
        detail_path.write_bytes(detail_bytes)
        PUBLIC.write_bytes(public_bytes)
    print(json.dumps({
        "checked": args.check, "public_bytes": len(public_bytes),
        "raw_bytes": len(detail_bytes), "record": str(PUBLIC.relative_to(ROOT)),
        "sha256": hashlib.sha256(public_bytes).hexdigest(),
        "comparisons": {k: {name: v[name] for name in (
            "engineering_assumed60_A574_combined",
            "engineering_assumed60_separate_elastic",
            "Grade5_profile_fixed_field_combined_upper_bound",
        )} for k, v in report["comparisons"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()

