"""Publish the existing selected 112 nominal stack inventory without a new audit.

Publication checks five pinned sources. Portable checks read the three public
context sources and the issued outputs; they do not recover ignored inventory
or geometry files. No prices, availability, delivered fit or release are added.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

REVISION = "v10-packer-free-flush-return-far-row-only-v1"
PREFIX = "docs/bolted-frame-development/owner-frame-v10/packer-free/"
PLAN = PREFIX + "hardware-planning.json"
CSV = PREFIX + "hardware-planning.csv"
PLAN_SHA = "4d8173d2dd1ce4f347301a769b56ce948adeb32e909866a22b990299697b6102"
SOURCES = {
    "nominal_inventory": {
        "path": "fea/generated/v10-packer-free-v1/connections/hardware-final/hardware-binding-v2.json",
        "sha256": "61dd844a17cbb335e1347807bea75a36015e3de1be26ddf6352372c6937f6ed4",
    },
    "resolved_spacers": {
        "path": PREFIX + "hardware-spacer-mapping.json",
        "sha256": "a8dafcde6e4b0a1b63b648537da594916254640abc6918beaf86887de805dcee",
    },
    "physical_geometry": {
        "path": "fea/generated/v10-packer-free-v1/geometry-v1/geometry.json",
        "sha256": "9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde",
    },
    "geometry_receipt": {
        "path": PREFIX + "geometry-receipt.json",
        "sha256": "73b097d9bcc364748ca08f897fca38cc2bdb7869cc04586e6706afb9b9d3d527",
    },
    "response_bank": {
        "path": PREFIX + "response-bank.json",
        "sha256": "976ee8d8ac593f978edf03d9eda028755751fd69b540fb8a01cdd073a242bdc3",
    },
}
TOTALS = {"bolt": 112, "nut": 112, "washer": 224, "spacer": 40}
FALSE_FLAGS = (
    "purchase_authorized",
    "fabrication_released",
    "structural_acceptance",
    "climbing_released",
    "delivered_parts_verified",
    "physical_fit_qualified",
)
FIELDS = (
    "category",
    "SKU",
    "nominal_quantity",
    "unit",
    "planning_status",
    "source_field",
    "Actual",
    "Disposition",
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encode(value: dict) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def bound(root: Path, reference: dict) -> bytes:
    path = (root / reference["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Source path leaves the repository")
    raw = path.read_bytes()
    if digest(raw) != reference["sha256"]:
        raise ValueError("Pinned source changed: " + reference["path"])
    return raw


def nominal_rows(inventory: dict, mapping: dict) -> list[dict]:
    """Reuse already-reconciled totals; the resolved map controls spacer SKUs."""
    if (
        inventory.get("stack_count") != 112
        or inventory["spacers"]["selected_spacer_piece_count"] != 40
    ):
        raise ValueError("The reconciled selected 112 inventory is required")
    quantities = [
        (
            "bolt",
            inventory["bolt_SKU_quantities"],
            "nominal_inventory#/nominal_candidate_bom/bolt_SKU_quantities",
        ),
        (
            "nut",
            inventory["nut_SKU_quantities"],
            "nominal_inventory#/nominal_candidate_bom/nut_SKU_quantities",
        ),
        (
            "washer",
            inventory["washer_SKU_quantities_two_per_stack"],
            "nominal_inventory#/nominal_candidate_bom/washer_SKU_quantities_two_per_stack",
        ),
        (
            "spacer",
            mapping["nominal_catalog_SKU_quantities"],
            "resolved_spacers#/nominal_catalog_SKU_quantities",
        ),
    ]
    rows = []
    for category, counts, source in quantities:
        if not isinstance(counts, dict) or not counts:
            raise ValueError("Empty nominal SKU inventory")
        for sku, quantity in sorted(counts.items()):
            if (
                not isinstance(sku, str)
                or not sku
                or type(quantity) is not int
                or quantity <= 0
            ):
                raise ValueError(
                    "Positive integer quantities and explicit SKUs required"
                )
            rows.append(
                dict(
                    zip(
                        FIELDS,
                        (
                            category,
                            sku,
                            quantity,
                            "pieces",
                            "NOMINAL_PLANNING_PHYSICAL_FIT_UNVERIFIED",
                            source,
                            "",
                            "",
                        ),
                        strict=True,
                    )
                )
            )
    if totals(rows) != TOTALS or mapping["nominal_catalog_SKU_quantities"] != {
        "13731": 20,
        "13733": 20,
    }:
        raise ValueError("Selected 112 or resolved 20/20 spacer totals differ")
    return rows


def totals(rows: list[dict]) -> dict[str, int]:
    return {
        category: sum(
            row["nominal_quantity"] for row in rows if row["category"] == category
        )
        for category in TOTALS
    }


def csv_bytes(rows: list[dict]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def public_context(root: Path) -> dict:
    sources = {
        name: json.loads(bound(root, SOURCES[name]))
        for name in ("resolved_spacers", "geometry_receipt", "response_bank")
    }
    mapping, receipt, bank = (
        sources[name]
        for name in ("resolved_spacers", "geometry_receipt", "response_bank")
    )
    if (
        mapping["revision"] != REVISION
        or mapping["current_spacer_pieces"] != 40
        or mapping["geometry_receipt"] != SOURCES["geometry_receipt"]
        or receipt["checked_geometry"]["sha256"]
        != SOURCES["physical_geometry"]["sha256"]
        or bank["geometry_revision"] != REVISION
        or bank["physical_geometry"]["sha256"] != SOURCES["geometry_receipt"]["sha256"]
        or bank["all_six_cases_admitted"] is not True
        or len(bank["cases"]) != 6
        or any(
            row["both_independent_replays_admitted"] is not True
            for row in bank["cases"]
        )
    ):
        raise ValueError("Current geometry, mapping and own admitted bank must match")
    return sources


def make_plan(rows: list[dict]) -> dict:
    return {
        "schema": "v10_current112_nominal_hardware_planning/v1",
        "revision": REVISION,
        "scope": "Nominal bolt/nut/washer/metal-spacer quantities from the completed selected 112 inventory. Not a purchase order, delivered-fit or capacity determination.",
        "source_bindings": {
            name: dict(reference) for name, reference in SOURCES.items()
        },
        "rows": [dict(row) for row in rows],
        "totals": dict(TOTALS),
        "retained_context_not_reselected": {
            "angles": 24,
            "Hillman_panel_kicker_axes": 66,
        },
        "spacer_resolution": "The source inventory preserves eight legacy blank short-spacer SKU cells. The resolved nominal map controls all 20 SKU 13731 and 20 SKU 13733 pieces; this publisher performs no new recipe/BRep audit.",
        "remaining_physical_inputs": [
            "Delivered type/grade/lot, body/root/thread/runout and underhead length.",
            "Actual nut/washer/spacer dimensions, free seating and complete working-thread engagement.",
            "Spacer material/compression and actual holding/turning tool access.",
            "Connection/fitting/material qualification remains governed by the current development evaluation.",
        ],
        "prices_or_availability_claimed": False,
        "new_quantity_audit_or_geometry_force_calculation": False,
        "all_six_cases_and_both_replays_recorded": True,
        "publication_raw_inventory_and_geometry_pins_checked": True,
        "portable_check_scope": "Checks issued JSON/CSV and 3 public context sources; does not recover or re-audit the ignored inventory, geometry, BReps or force fields.",
        "producer": "scripts/publish_current112_hardware_plan.py",
        "CSV": {"path": CSV, "sha256": digest(csv_bytes(rows))},
        **dict.fromkeys(FALSE_FLAGS, False),
    }


def prepare(root: Path) -> dict:
    context = public_context(root)
    inventory = json.loads(bound(root, SOURCES["nominal_inventory"]))
    geometry = json.loads(bound(root, SOURCES["physical_geometry"]))
    bindings = inventory["source_bindings"]
    if (
        inventory["physical_geometry_revision"] != REVISION
        or geometry["revision"] != REVISION
        or geometry["current_bolt_count"] != 112
        or geometry["current_angle_count"] != 24
        or geometry["current_Hillman_count"] != 66
        or inventory["current_stack_census"]["current_axis_and_stack_count"] != 112
        or any(
            bindings[key]["sha256"] != SOURCES[source]["sha256"]
            for key, source in (
                ("current_physical_geometry", "physical_geometry"),
                ("current_checked_receipt", "geometry_receipt"),
                ("current_response_bank", "response_bank"),
            )
        )
    ):
        raise ValueError(
            "Reconciled inventory must join the selected 112 geometry and bank"
        )
    return make_plan(
        nominal_rows(inventory["nominal_candidate_bom"], context["resolved_spacers"])
    )


def check(root: Path) -> dict:
    raw = (root / PLAN).read_bytes()
    if PLAN_SHA and digest(raw) != PLAN_SHA:
        raise ValueError("Published hardware plan fingerprint differs")
    plan = json.loads(raw)
    public_context(root)
    rows = plan["rows"]
    if (
        plan != make_plan(rows)
        or totals(rows) != TOTALS
        or len(rows) != 14
        or any(
            set(row) != set(FIELDS) or row["Actual"] != "" or row["Disposition"] != ""
            for row in rows
        )
        or (root / CSV).read_bytes() != csv_bytes(rows)
    ):
        raise ValueError("Issued nominal plan/CSV, counts or blank observations differ")
    return {
        "status": "current112_nominal_hardware_plan_verified",
        "SKU_rows": len(rows),
        "totals": TOTALS,
        "plan_sha256": digest(raw),
        "CSV_sha256": plan["CSV"]["sha256"],
        "public_source_pins_checked": 3,
        "ignored_inputs_reopened": False,
        "physical_fit_qualified": False,
        "purchase_authorized": False,
    }


def publish(root: Path) -> dict:
    plan = prepare(root)
    files = {PLAN: encode(plan), CSV: csv_bytes(plan["rows"])}
    if PLAN_SHA and digest(files[PLAN]) != PLAN_SHA:
        raise ValueError("Prepared plan differs from the issued fingerprint")
    for relative, raw in files.items():
        destination = root / relative
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError("Preserve existing differing output: " + relative)
    for relative, raw in files.items():
        destination = root / relative
        if not destination.exists():
            with destination.open("xb") as stream:
                stream.write(raw)
    return {**check(root), "publication_all_five_source_pins_checked": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(publish(args.root) if args.write else check(args.root), indent=2))
