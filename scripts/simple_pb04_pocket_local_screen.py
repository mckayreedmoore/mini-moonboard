"""PB04 outer-upright pocket local screen for authenticated a12-forward only."""

import json
import math

from mini_moonboard.bolted_timber_checks import (
    dfl_net_parallel_tension_reference_lbf,
    dfl_parallel_row_tear_out_reference_lbf,
)
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts import simple_pb04_first_case_demand as demand
from scripts import simple_pb04_native as pb04
from scripts.simple_pb03_first_case_demand import _cross, _dot, _norm, _sha256
from scripts.simple_pb03_quarter_inch_resistance import MM_PER_IN, N_PER_LBF


def _section(depth):
    """Exact grain-normal area at either pocket axis; adjacent axes are 45 mm apart."""
    length = pocket.lower.BLOCK_X_MM
    width = pocket.lower.BLOCK_T_MM
    bore = pocket.lower.BORE_DIAMETER_MM
    diameter = pocket.FORSTNER_DIAMETER_MM
    if not 0 < depth < length or diameter >= width:
        raise ValueError("unsupported pocket section")
    gross = length * width
    bore_only = gross - length * bore
    net = gross - (length - depth) * bore - depth * diameter
    # The helper supplies the actual-bore DF-L reference; the area ratio
    # applies the additional exact rectangular pocket opening on this plane.
    bore_reference = dfl_net_parallel_tension_reference_lbf(
        length / MM_PER_IN, width / MM_PER_IN, (bore / MM_PER_IN,)
    )
    return {
        "pocket_depth_mm": depth,
        "gross_area_mm2": gross,
        "bore_only_area_mm2": bore_only,
        "exact_net_area_mm2": net,
        "net_tension_reference_n": bore_reference * net / bore_only * N_PER_LBF,
        "section_scope": "each upright pocket-axis plane; gross block plus that bore and pocket",
    }


def _authenticated_report():
    path = demand.DEFAULT_REPORT
    if _sha256(path) != demand.REPORT_SHA256:
        raise ValueError("PB04 a12-forward report changed")
    report = json.loads(path.read_text())
    if (
        report.get("candidate") != pb04.SOURCE_ID
        or report.get("diagnostic_scope", {}).get("case") != "a12-forward"
    ):
        raise ValueError("PB04 case identity changed")
    if any(
        report.get(key) is not True
        for key in (
            "numerically_accepted",
            "global_equilibrium_passed",
            "member_equilibrium_passed",
            "contact_active_set_converged",
            "axial_tension_active_set_converged",
        )
    ):
        raise ValueError("PB04 case acceptance changed")
    for name, digest in demand.SOURCE_SHA256.items():
        if (
            _sha256(demand.ROOT / name) != digest
            or report["source_sha256"][name] != digest
        ):
            raise ValueError(f"PB04 source changed: {name}")
    return report


def _bolt_action(report, bolt, grain):
    source = report["physical_connection_forces"][bolt.name]
    force = tuple(source["force_on_second_xyz_n"])
    point = tuple(source["point"])
    if any(not math.isfinite(value) for value in (*force, *point)):
        raise ValueError(f"{bolt.name}: nonfinite action")
    if (
        _norm(tuple(a + b for a, b in zip(force, source["force_on_first_xyz_n"])))
        > 1e-7
    ):
        raise ValueError(f"{bolt.name}: action/reaction mismatch")
    parallel = _dot(force, grain)
    transverse = math.sqrt(max(0, _dot(force, force) - parallel * parallel))
    return {
        "name": bolt.name,
        "point_xyz_mm": point,
        "force_on_block_xyz_n": force,
        "signed_grain_force_n": parallel,
        "transverse_force_n": transverse,
    }


def _net_reference_gate(force_n, sections):
    ratios = {
        key: force_n / section["net_tension_reference_n"]
        for key, section in sections.items()
    }
    return {
        "absolute_grain_force_n": force_n,
        "ratios_by_depth": ratios,
        "exceeds_reference": any(ratio > 1 for ratio in ratios.values()),
        "scope": "isolated axial force/reference comparison; moment and joint interaction open",
    }


def _development_decision(stations):
    return (
        "REJECT_POCKETED_NET_REFERENCE"
        if any(row["net_reference_gate"]["exceeds_reference"] for row in stations)
        else "REVISE_LOCAL_CHECKS"
    )


def screen():
    """Report local reference screens; no single mode qualifies the joint."""
    report = _authenticated_report()
    module = pb04.PB04Native()
    if pb04._source_fingerprint(module) != demand.GEOMETRY_FINGERPRINT:
        raise ValueError("PB04 cut geometry identity changed")
    geometries = module.pb03_geometries()
    original_pockets, original_blocks = pocket.build_counterbored_blocks(geometries)
    installed = {part.name: part.shape for part in module.wood_parts()}
    depth = pocket._required_depth_mm()
    if not math.isclose(depth, 36.9824, abs_tol=1e-6):
        raise ValueError("PB04 pocket depth changed")
    sections = {f"{value:.4f}": _section(value) for value in (depth, depth + 1)}
    stations = []
    for station in pocket.TARGET_STATIONS:
        geometry = geometries[station]
        grain = tuple(
            report["member_section_demands"][geometry.block_name]["member"]["axis"]
        )
        bolts = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
        ]
        if len(bolts) != 2 or not math.isclose(_norm(grain), 1, abs_tol=1e-8):
            raise ValueError(f"{station}: pair identity changed")
        centers = [_dot(bolt.start.toTuple(), grain) for bolt in bolts]
        rail_bolts = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
        ]
        if abs(centers[0] - centers[1]) <= pocket.FORSTNER_DIAMETER_MM:
            raise ValueError(f"{station}: pocket sections overlap")
        if (
            len(rail_bolts) != 2
            or abs(rail_bolts[0].start.x - rail_bolts[1].start.x)
            <= pocket.lower.BORE_DIAMETER_MM
        ):
            raise ValueError(f"{station}: rail-bore section changed")
        if any(
            abs(_dot(rail.start.toTuple(), grain) - center)
            <= (pocket.FORSTNER_DIAMETER_MM + pocket.lower.BORE_DIAMETER_MM) / 2
            for rail in rail_bolts
            for center in centers
        ):
            raise ValueError(f"{station}: rail bore reaches pocket section")
        actions = [_bolt_action(report, bolt, grain) for bolt in bolts]
        if not math.isclose(
            installed[geometry.block_name].Volume(),
            original_blocks[station].Volume(),
            abs_tol=1e-5,
        ):
            raise ValueError(f"{station}: installed cut block changed")
        trial_block = geometry.block
        for bolt in bolts:
            direction = bolt.direction.normalized()
            outer_face = bolt.start + direction * (
                pocket.lower.END_ALLOWANCE_MM + bolt.grip
            )
            trial_cut = pocket._cylinder(
                outer_face.toTuple(),
                (-direction).toTuple(),
                depth + 1,
                pocket.FORSTNER_DIAMETER_MM,
            )
            key = f"{station}/{bolt.name}"
            if original_pockets[key].cut(trial_cut).Volume() > pocket.lower.TOL_MM3:
                raise ValueError(f"{key}: trial does not contain installed pocket")
            trial_block = trial_block.cut(trial_cut)
        center = tuple(
            math.fsum(row["point_xyz_mm"][i] for row in actions) / 2 for i in range(3)
        )
        moment = tuple(
            math.fsum(
                _cross(
                    tuple(row["point_xyz_mm"][j] - center[j] for j in range(3)),
                    row["force_on_block_xyz_n"],
                )[i]
                for row in actions
            )
            for i in range(3)
        )
        pair = {
            "signed_force_on_block_xyz_n": tuple(
                math.fsum(row["force_on_block_xyz_n"][i] for row in actions)
                for i in range(3)
            ),
            "signed_grain_force_n": math.fsum(
                row["signed_grain_force_n"] for row in actions
            ),
            "absolute_grain_force_n": math.fsum(
                abs(row["signed_grain_force_n"]) for row in actions
            ),
            "absolute_transverse_force_n": math.fsum(
                row["transverse_force_n"] for row in actions
            ),
            "moment_about_pair_midpoint_nmm": moment,
            "moment_magnitude_nmm": _norm(moment),
        }
        net_gate = _net_reference_gate(pair["absolute_grain_force_n"], sections)
        # Each end-directed component is retained separately. The helper's
        # parallel-grain reference is a sensitivity under oblique pair loading.
        bounds = demand._extent(geometry.block, grain)
        row_refs = []
        for row in actions:
            signed = row["signed_grain_force_n"]
            coordinate = _dot(row["point_xyz_mm"], grain)
            loaded_end = (
                bounds[1] - coordinate if signed > 0 else coordinate - bounds[0]
            )
            row_refs.append(
                {
                    "bolt": row["name"],
                    "signed_grain_force_n": signed,
                    "loaded_end_distance_mm": loaded_end,
                    "reference_n": dfl_parallel_row_tear_out_reference_lbf(
                        (pocket.lower.BLOCK_X_MM - depth) / MM_PER_IN,
                        1,
                        loaded_end / MM_PER_IN,
                    )
                    * N_PER_LBF,
                    "rated": False,
                }
            )
        stations.append(
            {
                "station": station,
                "block": geometry.block_name,
                "gross_block_volume_mm3": geometry.block.Volume(),
                "cut_block_volume_mm3": original_blocks[station].Volume(),
                "detached_37_9824_cut_block_volume_mm3": trial_block.Volume(),
                "pocket_keys": [f"{station}/{bolt.name}" for bolt in bolts],
                "bolts": actions,
                "pair": pair,
                "sections": sections,
                "net_reference_gate": net_gate,
                "intervening_rail_bore_section": {
                    "exact_net_area_mm2": pocket.lower.BLOCK_T_MM
                    * (pocket.lower.BLOCK_X_MM - 2 * pocket.lower.BORE_DIAMETER_MM),
                    "net_tension_reference_n": dfl_net_parallel_tension_reference_lbf(
                        pocket.lower.BLOCK_T_MM / MM_PER_IN,
                        pocket.lower.BLOCK_X_MM / MM_PER_IN,
                        (pocket.lower.BORE_DIAMETER_MM / MM_PER_IN,) * 2,
                    )
                    * N_PER_LBF,
                },
                "row_tear_out_references": row_refs,
                "net_section_fully_rated": False,
                "block_shear_rated": False,
                "near_hole_splitting_rated": False,
            }
        )
        if any(key not in original_pockets for key in stations[-1]["pocket_keys"]):
            raise ValueError(f"{station}: pocket inventory changed")
    return {
        "schema": "simple_pb04_pocket_local_screen/v1",
        "case": "a12-forward",
        "candidate": pb04.SOURCE_ID,
        "report_sha256": demand.REPORT_SHA256,
        "geometry_fingerprint_sha256": demand.GEOMETRY_FINGERPRINT,
        "stations": stations,
        "development_decision": _development_decision(stations),
        "physical_revision_selected": False,
        "next_calculation": "For both pocket depths, derive the exact centroid and second moments of each bored pocket-axis section; resolve the authenticated bolt-plus-contact signed section force and moment, then check combined parallel-grain tension/bending without cancelling pair actions. Keep group tear-out, splitting, torsion, and other cases separate.",
        "unqualified_modes": [
            "pair moment on pocketed net section and bending interaction",
            "block shear and group tear-out around both holes",
            "near-hole splitting and cross-grain fracture",
            "torsion",
            "group action, washer seat, preload, and local bearing",
            "contact force and moment transfer into the block section",
            "other five cases",
        ],
        "qualified_for_design": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
