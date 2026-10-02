"""Compare grain-aware rectangular panel placements; no geometry or response run."""

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").exists())
BASE = HERE.parent
ASSEMBLY = HERE / "rawlocal/catalog-labels-attempt01/reconciled-assembly.json"
PURCHASE = ROOT / "docs/purchased-materials.md"
MODEL = BASE / "upper-corner-screw-layout/operators-attempt02/model.json"
PINS = {
    ASSEMBLY: "d79bedb1edbc0d4cbde095e77fdebc99bbcb3348ee5cca1866eb80737a732590",
    PURCHASE: "3a1e09c02e223cdec91ad96e258046e73322a23c6417252453f818624c3b8bad",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
}
D = Decimal


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rectangle(body, strong_axis):
    x, t, _ = body["proposed_stock_box_mm"]
    x, t = D(str(x)), D(str(t))
    return (x, t) if strong_axis == "X" else (t, x)


def sheet(rows, dimensions, kerf):
    """Stack grain-aligned blanks along L; W is perpendicular to face grain."""
    length, width = dimensions
    placements, cursor = [], D(0)
    for body, axis in rows:
        along, across = rectangle(body, axis)
        placements.append({"body_id": body["body_id"], "strong_body_axis": axis,
                           "L_start_mm": cursor, "W_start_mm": D(0),
                           "L_size_mm": along, "W_size_mm": across})
        cursor += along + kerf
    used_length = cursor - kerf
    used_width = max(p["W_size_mm"] for p in placements)
    if used_length > length or used_width > width:
        raise ValueError("Placement exceeds the nominal sheet envelope")
    return {"placements": placements,
            "occupied_L_including_internal_kerfs_mm": used_length,
            "occupied_W_mm": used_width,
            "combined_end_trim_budget_L_mm": length - used_length,
            "combined_edge_trim_budget_W_mm": width - used_width}


def layout(main, kickers, dimensions, kerf, main_axis):
    length, _ = dimensions
    main_length, _ = rectangle(main[0], main_axis)
    pair_fits = 2 * main_length + kerf <= length
    if pair_fits:
        rows = [[(main[0], main_axis), (main[1], main_axis)],
                [(main[2], main_axis), (main[3], main_axis)],
                [(body, "T") for body in kickers]]
        proof = "Four mains require two sheets; each paired sheet has no remaining panel-sized region, so kickers require a third."
    else:
        rows = [[(body, main_axis)] for body in main]
        kicker_length, _ = rectangle(kickers[0], "T")
        if main_length + 2 * (kerf + kicker_length) <= length:
            rows[0].extend((body, "T") for body in kickers)
            proof = "At most one main fits each sheet; four mains require four sheets, and both kickers fit the first remainder."
        else:
            rows.append([(body, "T") for body in kickers])
            proof = "At most one main fits each sheet; its remainder cannot fit a kicker. Four main sheets plus one kicker sheet are required."
    return {"main_strong_axis": main_axis, "kicker_strong_axis": "T",
            "sheet_L_mm": length, "sheet_W_mm": dimensions[1], "kerf_mm": kerf,
            "sheet_count": len(rows), "sheets": [sheet(r, dimensions, kerf) for r in rows],
            "minimum_for_axis_aligned_rectangular_envelopes": True,
            "minimum_count_reason": proof,
            "main_axes_match_saved_model": main_axis == "T",
            "kicker_axes_match_saved_model": True,
            "two_main_L_deficit_mm": max(D(0), 2 * main_length + kerf - length)}


def run(output):
    if output.exists():
        raise ValueError("Use a fresh output child; preserve earlier arithmetic")
    for path, expected in PINS.items():
        if sha(path) != expected:
            raise ValueError(f"Changed source: {path.relative_to(ROOT)}")
    bodies = json.loads(ASSEMBLY.read_text())["bodies"]
    panels = [b for b in bodies if b["kind"] == "plywood panels"]
    main = sorted((b for b in panels if b["body_id"].startswith("main_")), key=lambda b: b["body_id"])
    kickers = sorted((b for b in panels if b["body_id"].startswith("kicker_")), key=lambda b: b["body_id"])
    if len(main) != 4 or len(kickers) != 2:
        raise ValueError("Require exactly four mains and two kickers")
    for body in panels:
        expected = [1217.6125, 277.0 if body in kickers else 1219.2, 18.25625]
        if any(abs(a - b) > 1e-8 for a, b in zip(body["proposed_stock_box_mm"], expected, strict=True)):
            raise ValueError(f"Changed rectangular envelope: {body['body_id']}")
    report = {"schema": "wood-joint-grain-aware-panel-placement/v1",
              "status": "CONDITIONAL_RECTANGULAR_OPTIONS_ONLY",
              "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
              "producer_sha256": sha(Path(__file__)),
              "sheet_coordinate_basis": "L follows declared factory face grain; W is perpendicular. For square 4x4 sheets this axis must be identified, not inferred from outline.",
              "scenarios": [layout(main, kickers, (D(length), D("1219.2")), D(kerf), axis)
                            for length in ("2438.4", "1219.2")
                            for kerf in ("3.175", "3.2") for axis in ("X", "T")],
              "limits": ["No sheet/product or cut option selected; no physical sheet or grain observation claimed.",
                         "Rectangular source stock envelopes only; no holes, profiling, sheet defects or cut mechanics evaluated.",
                         "Coordinates start at retained edges after trimming; trim budgets are combined losses at both ends/edges, not allowances per edge.",
                         "Kerf is charged between retained blanks. A final edge trim may place part of the blade outside the sheet; remaining margins are not a blade/tool-access qualification.",
                         "Nominal sheet dimensions are assumptions; actual usable sizes and face axes must agree with the chosen option.",
                         "These placements do not bound connection forces or establish panel strength, stiffness or screw capacity."],
              "physical_release": False}
    # Decimal arithmetic is serialized as exact decimal strings, avoiding fit-by-rounding.
    data = json.dumps(report, indent=2, default=str) + "\n"
    output.mkdir(parents=True)
    (output / "result.json").write_text(data)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    for s in report["scenarios"]:
        print(s["sheet_L_mm"], s["kerf_mm"], s["main_strong_axis"], s["sheet_count"])
    print("result_sha256", sha(output / "result.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output.resolve())
