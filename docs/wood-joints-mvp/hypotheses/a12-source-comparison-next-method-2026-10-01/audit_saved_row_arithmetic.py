"""Replay row 1586 endpoint arithmetic from retained summaries only.

This is not a stiffness reader or solver. It never opens model.sti; the
pure-solid export is cited only through its authenticated assessment metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tarfile
import time
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RECOVERY = ROOT / "docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-2026-10-01-attempt01"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
DIAG = BASE / "current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01"
RAW = BASE / "current-a12-fixed-active-raw-H-comparison-attempt01"
PROJECTION = BASE / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json"
DECK = BASE / "current-springa-selected-floor-a12-rear-attempt03/model.inp"
PURE_K_ASSESSMENT = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/assessment.json"
CCX_ARCHIVE = Path("/tmp/ccx_2.23.src.tar.bz2")

PINNED_FILES = {
    RECOVERY / "parent-result.json": "79b97a8191bcbdc5d9cbc3a806998fcdc741283717d9c3922b2330bd102bc908",
    RECOVERY / "parent-source-result.json": "560352a02ab4e01291f1c0d73db5f9001a71a38d8f9c3212962fb0cd586432b3",
    DIAG / "assessment.json": "7542ce827f79bcdfe93c018e6b6f869f6435e8190a5ca0d5d492158961412658",
    RAW / "response.npz": "2ada6877988c573fbfe89bb47b9945e774a8c373c250ad136e1124943ffa1a97",
    PROJECTION: "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3",
    DECK: "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    PURE_K_ASSESSMENT: "ba41b9c75815f7daf27b3517ac01afff109d5f3e3611aa985811e92c269e69ec",
}
ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
CCX_MEMBERS = {
    "./CalculiX/ccx_2.23/src/matrixstorage.c": "2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4",
    "./CalculiX/ccx_2.23/src/springforc_n2f.f": "706d066ef4b951c6382b754094bc576d98865b86f6272da535b588c7e7282d60",
    "./CalculiX/ccx_2.23/src/calcspringforc.f": "67d945c054f9e0584432a0f4aef5bd6d3373688530ceaafe4c96796c72b975aa",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pins() -> dict:
    actual = {}
    for path, expected in PINNED_FILES.items():
        digest = sha256(path)
        if digest != expected:
            raise RuntimeError(f"pinned input changed: {path}")
        actual[str(path.relative_to(ROOT))] = digest

    archive_digest = sha256(CCX_ARCHIVE)
    if archive_digest != ARCHIVE_SHA256:
        raise RuntimeError("pinned CalculiX source archive changed")
    members = {}
    with tarfile.open(CCX_ARCHIVE, "r:bz2") as archive:
        for name, expected in CCX_MEMBERS.items():
            member = archive.extractfile(name)
            if member is None:
                raise RuntimeError(f"missing pinned CalculiX source member: {name}")
            data = member.read()
            digest = hashlib.sha256(data).hexdigest()
            if digest != expected:
                raise RuntimeError(f"pinned CalculiX source member changed: {name}")
            members[name] = digest
            compact = b"".join(data.lower().split())
            if name.endswith("matrixstorage.c"):
                if b'%20.13e\\n",ai[i],aj[i],aa[i]' not in compact:
                    raise RuntimeError("matrixstorage source no longer has the pinned %.13e writer")
            elif name.endswith("springforc_n2f.f"):
                if b"pl(j,i)=xl(j,i)+vl(j,i)" not in compact or b"val=dd-dd0" not in compact:
                    raise RuntimeError("SPRINGA endpoint operation sequence changed")
            elif name.endswith("calcspringforc.f"):
                if b"xk=(yiso(id+1)-yiso(id))/(xiso(id+1)-xiso(id))" not in compact:
                    raise RuntimeError("SPRING table slope operation changed")
                if b"fk=yiso(id)+xk*(val-xiso(id))" not in compact:
                    raise RuntimeError("SPRING table force operation changed")

    return {
        "repository_inputs_sha256": actual,
        "calculix_source_archive_sha256": archive_digest,
        "calculix_source_members_sha256": members,
    }


def parse_deck_row() -> tuple[list[float], list[float], float, float]:
    lines = DECK.read_text(encoding="utf-8", errors="strict").splitlines()
    coordinates: dict[int, list[float]] = {}
    in_nodes = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("*"):
            in_nodes = stripped.upper().startswith("*NODE")
            continue
        if not in_nodes:
            continue
        fields = [field.strip() for field in stripped.split(",")]
        if len(fields) == 4 and fields[0] in {"21300", "21301"}:
            coordinates[int(fields[0])] = [float(value) for value in fields[1:]]

    if set(coordinates) != {21300, 21301}:
        raise RuntimeError("emitted deck is missing row 1586 endpoint coordinates")

    spring_line = "*SPRING,ELSET=SPR1787,NONLINEAR"
    try:
        index = next(i for i, line in enumerate(lines) if line.strip().upper() == spring_line)
    except StopIteration as error:
        raise RuntimeError("emitted row 1586 SPRING table not found") from error
    table = []
    for line in lines[index + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("*"):
            break
        pair = [float(value.strip()) for value in stripped.split(",")]
        if len(pair) != 2:
            raise RuntimeError("unexpected SPRING table row")
        table.append(pair)
    if len(table) != 3 or table[1] != [0.0, 0.0]:
        raise RuntimeError("unexpected row 1586 spring table")
    # CalculiX SPRING table columns are force, displacement; the source stores
    # displacement in xiso and force in yiso before evaluating calcspringforc.
    f0, x0 = table[1]
    f1, x1 = table[2]
    slope = (f1 - f0) / (x1 - x0)
    if slope <= 0 or x0 != 0.0:
        raise RuntimeError("row 1586 positive table branch is not the expected branch")
    return coordinates[21300], coordinates[21301], slope, float(table[2][0])


def decimal_norm(vector: list[Decimal]) -> Decimal:
    return sum(component * component for component in vector).sqrt()


def known_answer() -> dict:
    with localcontext() as context:
        context.prec = 100
        length0 = Decimal(100)
        transverse = Decimal("0.00001")
        length1 = (length0 * length0 + transverse * transverse).sqrt()
        direct = length1 - length0
        rationalized = transverse * transverse / (length1 + length0)
        error = abs(direct - rationalized)
        if error > Decimal("1e-95"):
            raise RuntimeError("rationalized length-difference known answer failed")
        return {
            "initial_axis_length_mm": str(length0),
            "transverse_delta_mm": str(transverse),
            "expected_length_change_mm": str(direct),
            "rationalized_length_change_mm": str(rationalized),
            "identity_error_mm": str(error),
            "status": "PASS_NEW_CANCELLATION_IDENTITY_KNOWN_ANSWER",
        }


def audit() -> dict:
    started = time.perf_counter()
    input_hashes = verify_pins()
    parent = load_json(RECOVERY / "parent-result.json")
    recovery = load_json(RECOVERY / "parent-source-result.json")
    diagnostic = load_json(DIAG / "assessment.json")
    projection = load_json(PROJECTION)
    pure_k = load_json(PURE_K_ASSESSMENT)

    source_row = next(
        row for row in projection["rows"]
        if row["source_group"] == "SPR1787" and row["source_element"] == 3690
    )
    if source_row["family"] != "unilateral_springa" or source_row["source_inventory_row_index"] != 1786:
        raise RuntimeError("projection-contract identity for row 1586 changed")
    if parent["source_comparison_status"] != "ROW1586_OUTSIDE_UNCHANGED_NATIVE_RF_INTERVAL":
        raise RuntimeError("the unchanged source-row stop status changed")
    if parent["method_status"] != "PASS_ELASTIC_QUOTIENT_SCREEN" or not parent["original_raw_H_STOP_retained"]:
        raise RuntimeError("the reviewed source recovery result changed")

    x1, x2, table_slope, table_force_at_10 = parse_deck_row()
    span = recovery["finite_span_and_table"]
    p1 = [float(value) for value in span["current_endpoint1_mm"]]
    p2 = [float(value) for value in span["current_endpoint2_mm"]]

    # Mirror the source expression order: point positions are already retained
    # binary64 values; form each relative coordinate, sum its square in order,
    # take sqrt, subtract dd0, then evaluate the positive table segment.
    d0 = [x2[i] - x1[i] for i in range(3)]
    d = [p2[i] - p1[i] for i in range(3)]
    dd0 = math.sqrt(d0[0] ** 2 + d0[1] ** 2 + d0[2] ** 2)
    dd = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    extension = dd - dd0
    source_order_force = 0.0 + table_slope * (extension - 0.0)
    source_force_upper = parent["unchanged_native_RF_interval_N"][1]
    source_force_center = recovery["native_RF_comparison"]["original_native_endpoint_RF_center_N"]
    interval_radius = recovery["native_RF_comparison"]["unchanged_native_endpoint_RF_rounding_radius_N"]

    with localcontext() as context:
        context.prec = 100
        to_decimal = lambda value: Decimal.from_float(float(value))
        d0_decimal = [to_decimal(x2[i]) - to_decimal(x1[i]) for i in range(3)]
        d_decimal = [to_decimal(p2[i]) - to_decimal(p1[i]) for i in range(3)]
        length0_decimal = decimal_norm(d0_decimal)
        length_decimal = decimal_norm(d_decimal)
        extension_decimal = length_decimal - length0_decimal
        rationalized_extension = sum(
            (d_decimal[i] - d0_decimal[i]) * (d_decimal[i] + d0_decimal[i])
            for i in range(3)
        ) / (length_decimal + length0_decimal)
        if abs(extension_decimal - rationalized_extension) > Decimal("1e-90"):
            raise RuntimeError("saved-row rationalized length identity failed")
        exact_slope_decimal = Decimal.from_float(table_slope)
        stable_force = exact_slope_decimal * rationalized_extension
        stable_force_float = float(stable_force)

    if source_order_force != span["table_force_N"]:
        raise RuntimeError("binary64 source-order re-evaluation differs from saved force")
    if abs(source_order_force - parent["computed_force_N"]) > 1e-15:
        raise RuntimeError("recovered source force differs from parent result")
    if parent["unchanged_native_RF_interval_N"][0] <= stable_force_float <= source_force_upper:
        raise RuntimeError("stable arithmetic unexpectedly enters the unchanged RF interval")

    raw_row = diagnostic["force_interval"]["worst_failed_normalized_difference"]
    if raw_row["source_position"] != 1586:
        raise RuntimeError("raw-H diagnostic no longer identifies row 1586 as worst normalized failure")
    recovered_force = span["table_force_N"]
    raw_scalar = raw_row["native_springa"]["raw_H_scalar_linear_force_N"]
    raw_force = raw_row["raw_H_force_N"]
    reduced_k = source_row["law"]["stiffness_N_per_mm"]
    linear_q = recovery["finite_span_and_table"]["linear_endpoint_axis_projection_mm"]

    if pure_k["stiffness"]["sha256"] != "7d22d2b013fcdc9fddfeab589b456615f0671db989a034e091bac855f3a93c01":
        raise RuntimeError("pure-solid stiffness export identity metadata changed")

    return {
        "schema": "a12_row1586_saved_row_arithmetic_discriminator/v1",
        "status": "PASS_ARITHMETIC_ONLY_RF_MISS_RETAINED",
        "scope": "saved endpoint arithmetic only; no source matrix parsing or recovery",
        "inputs_sha256": input_hashes,
        "source_metadata": {
            "pure_solid_stiffness_sha256_from_assessment_only": pure_k["stiffness"]["sha256"],
            "pure_solid_upper_pairs_from_assessment_only": pure_k["stiffness"]["triangle_pair_count"],
            "pure_solid_reconstructed_nonzeros_from_assessment_only": pure_k["stiffness"]["reconstructed_symmetric_nonzero_count"],
            "matrixstorage_format": "one-based upper triangle; fprintf `%20.13e` for each double; 14 significant decimal digits",
            "matrixstorage_member_sha256": CCX_MEMBERS["./CalculiX/ccx_2.23/src/matrixstorage.c"],
            "spring_source_member_sha256": {
                name: digest for name, digest in CCX_MEMBERS.items() if name.endswith(("springforc_n2f.f", "calcspringforc.f"))
            },
            "source_force_operation": "pl=xl+vl; dd0=norm(xl2-xl1); dd=norm(pl2-pl1); val=dd-dd0; fk=yiso(id)+xk*(val-xiso(id))",
            "source_compliance_projection_row_stiffness_N_per_mm": reduced_k,
            "emitted_table_positive_slope_N_per_mm": table_slope,
            "emitted_table_force_at_10mm_N": table_force_at_10,
            "table_minus_reduced_stiffness_N_per_mm": table_slope - reduced_k,
        },
        "row_1586_arithmetic": {
            "binary64_mirror_dd0_mm": dd0,
            "binary64_mirror_dd_mm": dd,
            "binary64_mirror_dd_minus_dd0_mm": extension,
            "binary64_mirror_table_force_N": source_order_force,
            "saved_recovered_table_force_N": recovered_force,
            "decimal_rationalized_table_force_from_same_binary64_endpoints_N": str(stable_force),
            "decimal_minus_binary64_force_N": stable_force_float - source_order_force,
            "final_norm_and_subtraction_half_ulp_scale_N": 0.5 * (math.ulp(dd0) + math.ulp(dd)) * table_slope,
            "native_rf_interval_N": parent["unchanged_native_RF_interval_N"],
            "native_rf_center_N": source_force_center,
            "native_rf_rounding_radius_N": interval_radius,
            "binary64_force_above_native_rf_upper_N": source_order_force - source_force_upper,
            "stable_force_above_native_rf_upper_N": stable_force_float - source_force_upper,
            "source_raw_H_force_N": raw_force,
            "raw_H_force_minus_recovered_table_force_N": raw_force - recovered_force,
            "raw_H_force_minus_raw_H_scalar_linear_force_N": raw_force - raw_scalar,
            "recovered_finite_geometry_minus_linear_projection_force_N": recovered_force - table_slope * linear_q,
            "measured_source_operator_interval_pass": False,
        },
        "known_answer": known_answer(),
        "claim_limit": "The high-precision identity tests only endpoint norm/difference arithmetic for this saved binary64 endpoint state. It does not estimate the influence of stiffness serialization, prove forward error, compare the saved matrix to an unrounded native matrix, explain the source/native force difference, or alter the original force interval or raw-H STOP.",
        "execution_counts": {
            "sti_bytes_read": False,
            "sti_triplets_parsed": 0,
            "source_K_factorizations": 0,
            "source_states_solved": 0,
            "native_runs": 0,
        },
        "elapsed_seconds": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=HERE / "arithmetic-result.json")
    args = parser.parse_args()
    report = audit()
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.report), "elapsed_seconds": report["elapsed_seconds"]}, sort_keys=True))


if __name__ == "__main__":
    main()
