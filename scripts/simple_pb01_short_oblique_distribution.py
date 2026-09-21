"""Source-bound PB01 bolt-pair force algebra; no connection capacity claim."""

import json
import math

from scripts.simple_pb01_short_tension_component_comparison import compare


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def unit(vector):
    length = math.sqrt(dot(vector, vector))
    if not math.isfinite(length) or length <= 0:
        raise ValueError("Invalid bolt-pair axis")
    return [value / length for value in vector], length


def decompose(first, second, pitch_mm):
    """Resolve two signed in-plane bolt forces into resultant and couple."""
    if not math.isfinite(pitch_mm) or pitch_mm <= 0:
        raise ValueError("Invalid bolt-pair pitch")
    if (
        len(first) != 2
        or len(second) != 2
        or not all(math.isfinite(value) for value in (*first, *second))
    ):
        raise ValueError("Invalid bolt-pair forces")
    resultant = [a + b for a, b in zip(first, second, strict=True)]
    half_difference = [(b - a) / 2 for a, b in zip(first, second, strict=True)]
    reconstructed = [
        [r / 2 - h for r, h in zip(resultant, half_difference, strict=True)],
        [r / 2 + h for r, h in zip(resultant, half_difference, strict=True)],
    ]
    return {
        "resultant_along_across_n": resultant,
        "half_difference_along_across_n": half_difference,
        "bolt_couple_nmm": pitch_mm * half_difference[1],
        "reconstructed_bolts_along_across_n": reconstructed,
        "sum_lateral_magnitudes_n": math.hypot(*first) + math.hypot(*second),
    }


def screen():
    """Re-read both authenticated archives and keep their cases separate."""
    source = compare()
    cases = {}
    for case, case_data in source["cases"].items():
        interfaces = case_data["interfaces"]
        upright = interfaces["upright"]["bolts"]
        rail = interfaces["rail"]["bolts"]
        upright_row, upright_pitch = unit(
            [
                b - a
                for a, b in zip(
                    upright[0]["point_xyz_mm"], upright[1]["point_xyz_mm"], strict=True
                )
            ]
        )
        rail_row, rail_pitch = unit(
            [
                b - a
                for a, b in zip(
                    rail[0]["point_xyz_mm"], rail[1]["point_xyz_mm"], strict=True
                )
            ]
        )
        raw_across, _ = unit(rail[0]["installation_axis_host_to_cleat_xyz"])
        upright_across, _ = unit(
            [
                a - dot(raw_across, upright_row) * r
                for a, r in zip(raw_across, upright_row, strict=True)
            ]
        )
        rail_across, _ = unit(
            [
                r - dot(upright_row, raw_across) * a
                for r, a in zip(upright_row, raw_across, strict=True)
            ]
        )
        if (
            not math.isclose(upright_pitch, 45.0, abs_tol=0.003)
            or not math.isclose(rail_pitch, 40.0, abs_tol=0.003)
            or abs(dot(upright_row, raw_across)) > 1e-4
            or abs(dot(rail_row, rail_across)) > 1e-6
        ):
            raise ValueError("PB01 short pair geometry changed")
        faces = {}
        for family, bolts, row_axis, across_axis, pitch in (
            ("upright", upright, upright_row, upright_across, upright_pitch),
            ("rail", rail, rail_row, rail_across, rail_pitch),
        ):
            projected = []
            out_of_plane = []
            for bolt in bolts:
                lateral = bolt["lateral_on_host_xyz_n"]
                components = [dot(lateral, row_axis), dot(lateral, across_axis)]
                projected.append(components)
                out_of_plane.append(
                    math.sqrt(
                        sum(
                            (v - components[0] * r - components[1] * t) ** 2
                            for v, r, t in zip(
                                lateral, row_axis, across_axis, strict=True
                            )
                        )
                    )
                )
            algebra = decompose(*projected, pitch)
            error = max(
                abs(a - b)
                for original, reconstructed in zip(
                    projected,
                    algebra["reconstructed_bolts_along_across_n"],
                    strict=True,
                )
                for a, b in zip(original, reconstructed, strict=True)
            )
            if max(out_of_plane) > 1e-6 or error > 1e-10:
                raise ValueError("PB01 signed force reconstruction failed")
            faces[family] = {
                "pitch_mm": pitch,
                "row_axis_xyz": row_axis,
                "across_axis_xyz": across_axis,
                "bolts": [
                    {
                        "name": bolt["name"],
                        "lateral_on_host_along_across_n": components,
                        "lateral_magnitude_n": bolt["lateral_on_host_magnitude_n"],
                        "axial_on_host_n": bolt["axial_on_host_n"],
                    }
                    for bolt, components in zip(bolts, projected, strict=True)
                ],
                **algebra,
                "max_reconstruction_error_n": error,
                "max_out_of_plane_lateral_n": max(out_of_plane),
                "bolt_couple_scope": "lateral bolt forces about pair midpoint; excludes face contact and other interface actions",
                "adjusted_resistance_n": None,
                "group_utilization": None,
            }
        cases[case] = faces
    return {
        "candidate": source["candidate"],
        "block_length_mm": source["block_length_mm"],
        "legacy_proxy_stations_per_case": source["proxy_station_count_per_case"],
        "retained_comparison_sha256": source["retained_comparison_sha256"],
        "cases": cases,
        "scope": "signed forces from numerically accepted provisional tension-only hybrid archives; not full V4 demands",
        "joint_utilization": None,
        "design_pass": None,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
