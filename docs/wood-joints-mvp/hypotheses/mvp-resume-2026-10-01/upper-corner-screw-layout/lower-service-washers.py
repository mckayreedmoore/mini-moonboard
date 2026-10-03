"""Compare eight frozen lower-service washer seats with current signed ties.

The parent runs this stdlib-only arithmetic. Saved geometry and signed service
states are reused; no force array, CAD model, or mechanics helper is executed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
HYPOTHESES = HERE.parents[1]
RAW = HERE / "rawlocal/lower-service-washers"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PREFIX = "left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/"
AXES = tuple(
    PREFIX + name
    for name in ("lower_rail_1", "lower_rail_2", "lower_side_1", "lower_side_2")
)
MEMBERS = {
    "left_service_outer_lower_cleat",
    "base_rail_service_lower_left",
    "base_side_left",
}
PSI_MPA = 0.006894757293168361
FIELDS = (
    "case_id",
    "axis_id",
    "member",
    "outer_tie_signed_n",
    "axis_grain_absolute_dot",
    "wood_reference_route",
    "wood_reference_mpa",
    "ideal_full_annulus_area_mm2",
    "ideal_annulus_pressure_mpa",
    "ideal_pressure_over_wood_reference",
    "known_partial_support",
    "full_annulus_reference_applicable",
    "actual_supported_pressure_mpa",
    "washer_metal_resistance_n",
)
FROZEN = {
    "model": (
        HERE / "operators-attempt02/model.json",
        "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ),
    "inputs": (
        HERE / "operators-attempt02/model-inputs.json",
        "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    ),
    "rows": (
        HERE / "operators-attempt02/row-identities.json",
        "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    ),
    "comparison": (
        HERE / "frame-250-attempt02/comparison.json",
        "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    ),
    "response": (
        HERE / "frame-250-attempt02/response.npz",
        "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    ),
    "service": (
        HERE.parent
        / "service-joint-current-attempt03/four-screw-250-attempt03/result.json",
        "850a31de41efc8e710cb45660f9822852469303e0e391fb70ed325977558293c",
    ),
    "geometry": (
        HYPOTHESES
        / "lower-left-service-joint/results/attempt01/geometry-evidence.json",
        "5692b6620fffe0c36f729f4d0cac607c3012c9a9a112659d12a521432bed6c24",
    ),
    "old_inputs": (
        HYPOTHESES
        / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json",
        "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    ),
    "support": (
        Path("/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json"),
        "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3",
    ),
    "materials": (
        HYPOTHESES / "hardware-material-specification-2026-09-30/material-inputs.json",
        "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    ),
    "fasteners": (
        HYPOTHESES / "hardware-material-specification-2026-09-30/fastener-inputs.json",
        "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    ),
    "annuli": (
        HYPOTHESES / "upper-block-strength-2026-10-01/seats.json",
        "4463f581490842095224afefd0b355428f82668f039b2e6035dfe4ec879c96c1",
    ),
    "remaining": (
        HERE / "bolted-replay-results/remaining-attempt02/screen.json",
        "abe988897087ad9d07f94c5def6a7427cfeb9c493a26ef50d3d13b8baac94d45",
    ),
    "csv_schema": (
        HERE / "bolted-replay-results/remaining-attempt02/washer-reference-states.csv",
        "43da5dab2bc0ed8761959767aecec466a645a3832509c7162e494cc4da17f35b",
    ),
    "method_snapshot": (
        HERE / "bolted-replay-results/remaining-attempt02/producer.py.snapshot",
        "4d9ea0e03ab98ba4bc8c9e4641a85d5e54603c59cf2ab1d17385de4c16dc964f",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def location(path: Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def encoded(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def unit(vector: list) -> list[float]:
    require(
        len(vector) == 3 and all(math.isfinite(v) for v in vector), "Invalid direction"
    )
    length = math.hypot(*vector)
    require(length > 0, "Zero direction")
    return [v / length for v in vector]


def close_vectors(first: list, second: list, tolerance: float = 1e-6) -> bool:
    return len(first) == len(second) == 3 and all(
        math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance
        for a, b in zip(first, second, strict=True)
    )


def build() -> tuple[dict, dict[Path, str]]:
    """Return the 48 reference states and direct source pins for parent use."""
    pins: dict[Path, str] = {}

    def pin(path: Path, expected: str) -> None:
        path = path.resolve()
        actual = digest(path)
        require(actual == expected, f"Frozen source differs: {path}")
        require(path not in pins or pins[path] == actual, f"Conflicting pin: {path}")
        pins[path] = actual

    for path, expected in FROZEN.values():
        pin(path, expected)
    pin(Path(__file__), digest(Path(__file__)))
    source = {
        key: json.loads(path.read_text())
        for key, (path, _) in FROZEN.items()
        if path.suffix == ".json"
    }
    model, inputs, old = source["model"], source["inputs"], source["old_inputs"]
    service, comparison = source["service"], source["comparison"]
    geometry, support = source["geometry"], source["support"]
    require(
        model["candidate"]
        == inputs["candidate"]
        == old["candidate"]
        == support["candidate"],
        "Candidate binding differs",
    )
    require(
        model["source_revision"] == inputs["revision_id"] == old["revision_id"],
        "Geometry revision differs",
    )
    require(
        service["schema"] == "current_lower_service_individual_reference/v1",
        "Service schema differs",
    )
    require(
        service["frame_directory"] == location(HERE / "operators-attempt02"),
        "Service operator directory differs",
    )
    require(
        service["force_source"] == location(FROZEN["response"][0]),
        "Service force source differs",
    )
    require(
        service["force_key"] == "case_id + '_gap_raw_force_n'"
        and service["gap_scale"] == 1.0,
        "Service force selection differs",
    )
    require(
        service["case_ids"] == list(CASES)
        and service["axis_count"] == 4
        and service["state_count"] == 24,
        "Service census differs",
    )
    require(
        not service["complete_joint_acceptance"] and not service["physical_release"],
        "Service authority differs",
    )
    require(
        comparison["response_sha256"] == FROZEN["response"][1],
        "Comparison response binding differs",
    )
    for key in ("model", "inputs", "rows", "comparison", "response"):
        path, expected = FROZEN[key]
        require(
            service["source_sha256"].get(location(path)) == expected,
            f"Service source binding differs: {key}",
        )
    nominal = [s for s in comparison["states"] if s["gap_scale"] == 1.0]
    require(
        [s["case_id"] for s in nominal] == list(CASES), "Nominal case order differs"
    )
    require(
        service["force_state_scope"]["bounded_nominal_cases"] == list(CASES),
        "Source force scope differs",
    )

    reader = csv.DictReader(
        io.StringIO(FROZEN["csv_schema"][0].read_text(), newline="")
    )
    require(
        tuple(reader.fieldnames or ()) == FIELDS, "Existing washer CSV schema differs"
    )
    require(
        not any(r["axis_id"] in AXES for r in reader),
        "Lower service already present in remaining washer rows",
    )
    require(
        source["remaining"]["output_sha256"]["washer-reference-states.csv"]
        == FROZEN["csv_schema"][1],
        "Remaining CSV binding differs",
    )

    for entry in geometry["washer_source_input_pins"].values():
        pin(ROOT / entry["path"], entry["sha256"])
    require(
        geometry["source_sha256"]["/tmp/remaining-washer-seats.json"]
        == FROZEN["support"][1],
        "Historical support bytes differ",
    )
    require(
        geometry["washer_source_input_pins"] == support["input_pins"],
        "Support input bindings differ",
    )
    seats = geometry["target_nominal_seats"]
    require(
        len(seats) == 8
        and {(s["axis_id"], s["role"]) for s in seats}
        == {(a, r) for a in AXES for r in ("head", "nut")},
        "Eight-endpoint support census differs",
    )
    require(
        [s for s in support["seats"] if s["axis_id"] in AXES] == seats,
        "Saved service support records differ",
    )
    require({s["member"] for s in seats} == MEMBERS, "Support receiver census differs")
    require(
        not geometry["release"] and geometry["stock_grains_observed"] is False,
        "Geometry authority differs",
    )
    connections = {
        c["axis_id"]: c for c in inputs["connections"] if c.get("axis_id") in AXES
    }
    old_connections = {
        c["axis_id"]: c for c in old["connections"] if c.get("axis_id") in AXES
    }
    require(
        len(connections) == len(old_connections) == 4
        and connections == old_connections,
        "Service geometry/axes changed",
    )
    members = {
        m["member_id"]: m for m in inputs["members"] if m["member_id"] in MEMBERS
    }
    old_members = {
        m["member_id"]: m for m in old["members"] if m["member_id"] in MEMBERS
    }
    require(
        len(members) == len(old_members) == 3 and members == old_members,
        "Service receivers changed",
    )
    for name, member in members.items():
        descriptor = member["reduced_geometry_descriptor"]
        finished = member["current_finished_step_binding"]
        require(
            support["finished_step_pins"][name]
            == {"path": finished["path"], "sha256": finished["file_sha256"]},
            f"Finished support source differs: {name}",
        )
        require(
            descriptor["step_sha256"] == finished["file_sha256"],
            f"Descriptor STEP differs: {name}",
        )
        pin(ROOT / finished["path"], finished["file_sha256"])
        pin(
            ROOT / descriptor["material_frame_map"],
            descriptor["material_frame_map_sha256"],
        )
        bound_grain = model["material_binding"]["orientation_overrides"][name][
            "material_axes_global_xyz"
        ]["L"]
        require(
            close_vectors(unit(descriptor["axis"]), unit(bound_grain), 1e-8),
            f"Current grain binding differs: {name}",
        )

    material = source["materials"]["conditional_DF_L_No2_base_row"]
    require(
        material["base_properties"]["units"]["stress"] == "psi", "Material units differ"
    )
    require(
        material["base_properties"]["Fc_perpendicular"] == 625
        and material["base_properties"]["Fc_parallel"] == 1350,
        "Original base references differ",
    )
    fc = {
        k: material["base_properties"][k] * PSI_MPA
        for k in ("Fc_perpendicular", "Fc_parallel")
    }
    require(
        fc == source["remaining"]["wood_reference_mpa"],
        "Material references differ from current helper",
    )
    washer = source["fasteners"]["dimension_inputs"]["washer"]
    od_mm, id_mm = washer["od_in"][0] * 25.4, washer["id_in"][1] * 25.4
    require(od_mm > id_mm > 7.5, "Catalog annulus or bore dimensions differ")
    area = math.pi / 4 * 25.4**2 * (washer["od_in"][0] ** 2 - washer["id_in"][1] ** 2)
    annuli = [
        a
        for a in source["annuli"]["washer_annulus_scenarios"]
        if a["scenario_id"] == "catalog_minimum_area"
    ]
    require(len(annuli) == 1, "Catalog annulus census differs")
    annulus = annuli[0]
    require(
        math.isclose(area, annulus["annulus_area_mm2"], rel_tol=1e-12),
        "Catalog annulus area differs",
    )
    require(
        math.isclose(od_mm, annulus["od_mm"], abs_tol=1e-12)
        and math.isclose(id_mm, annulus["id_mm"], abs_tol=1e-12),
        "Catalog dimensions differ",
    )

    rows = source["rows"]
    ties = {
        a: [r for r in rows if r["row_id"] == a + "/outer-seat-axial-tie"] for a in AXES
    }
    require(
        len(rows) == 1888 and all(len(r) == 1 for r in ties.values()),
        "Current tie row census differs",
    )
    endpoints = []
    for axis_id in AXES:
        connection = connections[axis_id]
        axis = unit(connection["axis_xyz"])
        geom = connection["source_record"]["geometry"]
        tie = ties[axis_id][0]
        require(
            tie["ownership"]["role"] == "physical_bolt_outer_seat_tension"
            and tie["law"]["intended_law"] == "tension_only",
            "Tie role/law differs",
        )
        require(
            close_vectors(unit(tie["ownership"]["direction_global_xyz"]), axis, 1e-8),
            "Tie direction differs",
        )
        require(
            math.isclose(geom["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8),
            "Service diameter differs",
        )
        intervals = geom["wood_receiver_intervals"]
        require(
            len(intervals) == 2
            and all(
                len(r["current_shaft_intersection_solid_intervals_from_underhead_mm"])
                == 1
                for r in intervals
            ),
            "Service receiver intervals differ",
        )
        ordered = sorted(
            intervals,
            key=lambda r: r[
                "current_shaft_intersection_solid_intervals_from_underhead_mm"
            ][0][0],
        )
        require(
            {r["receiver_id"] for r in ordered}
            == set(connection["receiver_member_ids"]),
            "Connection receiver census differs",
        )
        underhead = [
            v - d * geom["modeled_underhead_to_tip_mm"] / 2
            for v, d in zip(geom["shaft_center_global_xyz_mm"], axis, strict=True)
        ]
        for role, interval in zip(
            ("head", "nut"), (ordered[0], ordered[-1]), strict=True
        ):
            matches = [
                (i, s)
                for i, s in enumerate(seats)
                if s["axis_id"] == axis_id and s["role"] == role
            ]
            require(len(matches) == 1, "Duplicate endpoint support")
            seat_index, seat = matches[0]
            name = seat["member"]
            require(
                name
                == interval["receiver_id"]
                == tie["ownership"]["first_body" if role == "head" else "second_body"],
                "Endpoint owner differs",
            )
            distance = interval[
                "current_shaft_intersection_solid_intervals_from_underhead_mm"
            ][0][0 if role == "head" else 1]
            point = [v + distance * d for v, d in zip(underhead, axis, strict=True)]
            require(
                close_vectors(point, seat["point_xyz_mm"]), "Endpoint position differs"
            )
            if role == "head":
                require(
                    close_vectors(point, tie["ownership"]["point_mm"]),
                    "Tie datum differs",
                )
            require(
                seat["geometry_screen_pass"]
                and seat["receiver_count"] == 2
                and seat["bore_radius_mm"] == 3.75,
                "Endpoint support applicability differs",
            )
            nominal_support = [
                s for s in seat["nominal"] if s["scenario"] == "plain_minimum_area"
            ]
            require(
                len(nominal_support) == 1, "Nominal support scenario census differs"
            )
            witness = nominal_support[0]
            require(
                witness["supported"]
                and witness["inward_min"] >= 1 - 1e-6
                and witness["outward_max"] <= 1e-6,
                "Catalog annulus lacks full nominal support",
            )
            measurements = witness["inward_measurements"]
            require(
                [m["depth_mm"] for m in measurements] == [0.01, 0.05, 0.1]
                and all(
                    m["support_fraction"] >= 1 - 1e-6
                    and math.isclose(m["supported_area_mm2"], area, rel_tol=1e-12)
                    for m in measurements
                ),
                "Annulus support probes differ",
            )
            grain = unit(members[name]["reduced_geometry_descriptor"]["axis"])
            alignment = abs(sum(a * g for a, g in zip(axis, grain, strict=True)))
            require(alignment < 1e-8, "Lower-service perpendicular grain route changed")
            endpoints.append(
                {
                    "axis_id": axis_id,
                    "role": role,
                    "member": name,
                    "axis_global_xyz": axis,
                    "grain_global_xyz": grain,
                    "axis_grain_absolute_dot": alignment,
                    "point_xyz_mm": seat["point_xyz_mm"],
                    "tie_row_zero_based": tie["row"],
                    "tie_row_id": tie["row_id"],
                    "support_source": location(FROZEN["geometry"][0]),
                    "support_pointer": f"/target_nominal_seats/{seat_index}",
                    "support_scenario": "plain_minimum_area",
                    "full_nominal_annulus_supported": True,
                    "current_finished_step_binding": members[name][
                        "current_finished_step_binding"
                    ],
                    "current_material_orientation": model["material_binding"][
                        "orientation_overrides"
                    ][name],
                    "material_reference_source": location(FROZEN["materials"][0]),
                    "material_reference_pointer": "/conditional_DF_L_No2_base_row/base_properties/Fc_perpendicular",
                }
            )

    states = service["states"]
    require(
        len(states) == 24
        and {(s["case_id"], s["axis_id"]) for s in states}
        == {(c, a) for c in CASES for a in AXES},
        "Signed service state census differs",
    )
    by_state = {(s["case_id"], s["axis_id"]): (i, s) for i, s in enumerate(states)}
    references, force_census = [], []
    for case in CASES:
        for axis_id in AXES:
            index, state = by_state[(case, axis_id)]
            tension = state["simultaneous_tension_n"]
            require(
                math.isfinite(tension) and tension >= -1e-8,
                "Invalid signed tensile-tie force",
            )
            require(
                set(state["receiver_ids"])
                == set(connections[axis_id]["receiver_member_ids"])
                and len(state["receiver_ids"]) == 2,
                "Signed-state receiver census differs",
            )
            force_census.append(
                {
                    "case_id": case,
                    "axis_id": axis_id,
                    "outer_tie_signed_n": tension,
                    "source": location(FROZEN["service"][0]),
                    "pointer": f"/states/{index}/simultaneous_tension_n",
                    "tie_row_zero_based": ties[axis_id][0]["row"],
                }
            )
            for endpoint in (e for e in endpoints if e["axis_id"] == axis_id):
                pressure = max(0.0, tension) / area
                references.append(
                    {
                        "case_id": case,
                        "axis_id": axis_id,
                        "member": endpoint["member"],
                        "outer_tie_signed_n": tension,
                        "axis_grain_absolute_dot": endpoint["axis_grain_absolute_dot"],
                        "wood_reference_route": "PERPENDICULAR_BASE_REFERENCE",
                        "wood_reference_mpa": fc["Fc_perpendicular"],
                        "ideal_full_annulus_area_mm2": area,
                        "ideal_annulus_pressure_mpa": pressure,
                        "ideal_pressure_over_wood_reference": pressure
                        / fc["Fc_perpendicular"],
                        "known_partial_support": False,
                        "full_annulus_reference_applicable": True,
                        "actual_supported_pressure_mpa": None,
                        "washer_metal_resistance_n": None,
                    }
                )
    require(
        len(references)
        == len({(r["case_id"], r["axis_id"], r["member"]) for r in references})
        == 48,
        "Washer state census differs",
    )
    result = {
        "schema": "current_lower_service_annular_wood_bearing_reference/v1",
        "status": "CONDITIONAL_ANNULAR_WOOD_BEARING_REFERENCE_ONLY",
        "case_ids": list(CASES),
        "axis_ids": list(AXES),
        "counts": {
            "axes": 4,
            "endpoints": 8,
            "signed_axis_case_states": 24,
            "washer_reference_states": 48,
            "applicable_reference_states": 48,
        },
        "force_source": service["force_source"],
        "force_key": service["force_key"],
        "gap_scale": service["gap_scale"],
        "force_state_scope": service["force_state_scope"],
        "source_nominal_state_status": [
            {k: s[k] for k in ("case_id", "gap_scale", "status")} for s in nominal
        ],
        "source_sha256": {location(path): sha for path, sha in sorted(pins.items())},
        "csv_fields": list(FIELDS),
        "signed_force_census": force_census,
        "endpoints": endpoints,
        "catalog_annulus": {
            "od_min_mm": od_mm,
            "id_max_mm": id_mm,
            "area_mm2": area,
            "dimension_inputs": washer,
            "scenario": annulus,
            "observed_delivery": False,
        },
        "material_reference": material,
        "material_adjustment_inputs": source["materials"]["adjustment_factor_inputs"],
        "applied_factor_increase": False,
        "wood_reference_mpa": fc,
        "states": references,
        "peak_conditional_wood_bearing_reference": max(
            references, key=lambda r: r["ideal_pressure_over_wood_reference"]
        ),
        "limits": [
            "This adds eight endpoints and 48 conditional WOOD-BEARING comparisons to the excluded lower-service scope only.",
            "Signed Ti is copied from the authenticated current service result, separately for each simultaneous nominal case; no historical force, envelope maximum, preload or friction is substituted.",
            "Uniform pressure assumes the centered catalog minimum annulus is fully loaded. Frozen nominal support geometry does not qualify the installed washer/head/nut footprint, eccentricity, loaded spreading or contact.",
            "The original dry normal-duration DF-L No. 2 base reference is retained without an adjustment increase. Stock species, grade, moisture, grain and material properties are unobserved conditional inputs.",
            "Actual supported pressure and washer metal resistance remain null. No washer yield, steel/plate capacity or complete axial/lateral interaction is assigned.",
            "This is source reuse, not an independent force replay or profile claim. Source seating, formal47/all8, rank and strict stability dispositions are unchanged and no pass is transferred.",
        ],
        "reviewed_geometry_changed": service["reviewed_geometry_changed"],
        "geometry_changed_by_this_producer": False,
        "native_solve_run": False,
        "frame_solve_run": False,
        "CAD_rebuilt": False,
        "tests_run": False,
        "review_run": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    for path, expected in pins.items():
        require(digest(path) == expected, f"Source changed during arithmetic: {path}")
    return result, pins


def produce(output: Path = RAW / "attempt01") -> dict:
    """Publish into a fresh owned raw directory; leave all existing packets intact."""
    output = output.resolve()
    require(
        output.is_relative_to(RAW) and output != RAW,
        "Output must be a fresh child of rawlocal/lower-service-washers",
    )
    require(not output.exists(), f"Preserve existing output: {output}")
    result, pins = build()
    table = io.StringIO(newline="")
    writer = csv.DictWriter(table, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(result["states"])
    payload = encoded(result)
    snapshot = Path(__file__).read_bytes()
    for path, expected in pins.items():
        require(
            digest(path) == expected, f"Consumed source changed before write: {path}"
        )
    require(
        hashlib.sha256(snapshot).hexdigest() == pins[Path(__file__).resolve()],
        "Producer changed before snapshot",
    )
    output.mkdir(parents=True)
    (output / "result.json").write_text(payload)
    (output / "washer-reference-states.csv").write_bytes(
        table.getvalue().encode("utf-8")
    )
    (output / "producer.py.snapshot").write_bytes(snapshot)
    receipt = {
        "schema": "lower_service_washer_direct_source_receipt/v1",
        "source_sha256": result["source_sha256"],
        "source_unchanged_before_write": True,
        "output_sha256": {
            name: digest(output / name)
            for name in (
                "result.json",
                "washer-reference-states.csv",
                "producer.py.snapshot",
            )
        },
        "python_version": sys.version,
        "counts": result["counts"],
        "source_receipt_scope": "Direct saved artifacts, catalog/material inputs and exact unchanged axis/receiver/support sources. Inherited force/helper history remains provenance; no upstream producer is executed.",
        "force_state_scope": result["force_state_scope"],
        "native_or_frame_or_CAD_execution": False,
        "tests_run": False,
        "review_run": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    (output / "receipt.json").write_text(encoded(receipt))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RAW / "attempt01")
    args = parser.parse_args()
    receipt = produce(args.output)
    print(
        encoded(
            {"counts": receipt["counts"], "output_sha256": receipt["output_sha256"]}
        ),
        end="",
    )


if __name__ == "__main__":
    main()
