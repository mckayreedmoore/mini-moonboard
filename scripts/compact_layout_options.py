"""Bounded compact-two layout options; conditional comparisons, not qualification."""

import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from fea.current_response_resistance import VALIDITY

LEG = np.array([0.0, -0.26015745792854417, 0.9655662054381139])
RIM = np.array([0.0, 0.6427876096865427, 0.7660444431189752])



def capacity(f, d, fyb=45000., *, leg=LEG, rim=RIM):
    demand2 = np.sum(f[..., 1:] ** 2, axis=-1)
    qs = []
    angles = []
    for g in (rim, leg):
        co = np.minimum(1, (f @ g) ** 2 / np.maximum(demand2, 1e-20))
        angles.append(np.degrees(np.arccos(np.sqrt(co))))
        per = 6100 * 0.5**1.45 / math.sqrt(d)
        qs.append(5600 * per / (5600 * (1 - co) + per * co) * d)
    qm, qs = qs
    my = fyb * d**3 / 6
    vs = [qm * 3.5 / 5, qs * 3.5 / 5]
    for a, b, c, rd in (
        (1 / (4 * qs) + 1 / (4 * qm), 3.5, -qs * 3.5**2 / 4 - qm * 3.5**2 / 4, 4.5),
        (1 / (2 * qs) + 1 / (4 * qm), 1.75, -my - qm * 3.5**2 / 4, 4),
        (1 / (4 * qs) + 1 / (2 * qm), 1.75, -qs * 3.5**2 / 4 - my, 4),
        (1 / (2 * qs) + 1 / (2 * qm), 0, -2 * my, 4),
    ):
        vs.append(-2 * c / (b + np.sqrt(b * b - 4 * a * c)) / rd)
    # Historical constants 5/4.5/4 equal base Rd 4/3.6/3.2 times 1.25.
    ktheta = 1 + np.maximum.reduce(angles)/360
    values = np.array(vs)*1.25/ktheta*4.4482216152605
    return values.min(axis=0), values.argmin(axis=0)



def build(report_path, geometry_path, *, expected_candidate="compact-two-development"):
    """Use symmetric actual grain/stock geometry and both saved joint wrenches."""
    p = json.loads(gzip.decompress(report_path.read_bytes()) if report_path.suffix == ".gz" else report_path.read_bytes())
    geometry = json.loads(geometry_path.read_text())
    if geometry.get('candidate') != p.get('candidate'):
        raise ValueError('Geometry and native response must identify the same candidate')
    geo = geometry['members']
    if any(not np.isclose(geo[name][key], value, atol=1e-6)
           for name in ('base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right')
           for key, value in (('depth_mm', 139.7), ('width_mm', 88.9))):
        raise ValueError('Require the actual 88.9 by 139.7 mm compact stock')
    leg = np.array(geo['lumber_leg_left']['grain'], dtype=float)
    rim = np.array(geo['base_side_left']['grain'], dtype=float)
    for grain in (leg, rim):
        if not np.isclose(np.linalg.norm(grain), 1.) or abs(grain[0]) > 1e-10:
            raise ValueError('Require unit grain axes in the side-frame plane')
    for role in ('lumber_leg', 'base_side'):
        left, right = geo[role+'_left'], geo[role+'_right']
        if any(not np.allclose(left[key], right[key], atol=1e-8)
               for key in ('grain', 'end_stations_mm')) or not np.allclose(
                   left['centre_mm'][1:], right['centre_mm'][1:], atol=1e-8):
            raise ValueError('This bounded screen requires mirrored side geometry')
    LN = np.array([0, leg[2], -leg[1]])
    RN = np.array([0, rim[2], -rim[1]])
    A = np.array([LN[1:], RN[1:]])
    if p.get("candidate") != expected_candidate or not all(
        p.get(k) is True for k in VALIDITY
    ):
        raise ValueError("Require accepted actual compact native response")
    base = np.r_[
        0,
        np.linalg.solve(
            A,
            [
                np.array(geo["lumber_leg_left"]["centre_mm"]) @ LN,
                np.array(geo["base_side_left"]["centre_mm"]) @ RN,
            ],
        ),
    ]
    shifts = np.array(
        [
            np.r_[0, np.linalg.solve(A, [a, b])]
            for a, b in itertools.product(range(-40, 41, 5), repeat=2)
        ]
    )
    loads = []
    for side in ("left", "right"):
        rows = [
            r
            for k, r in p["physical_connection_forces"].items()
            if k.startswith("lumber_leg_bolt_" + side)
        ]
        pts = np.array([r["point"] for r in rows])
        f = np.array(
            [
                r["force_on_first_xyz_n"]
                if r["first"].startswith("lumber_leg")
                else r["force_on_second_xyz_n"]
                for r in rows
            ]
        )
        c = pts.mean(0)
        loads.append((f.sum(0), np.cross(pts - c, f).sum(0)[0], c))

    def check(q, d):
        q = q - q.mean(0)
        D = 25.4 * d
        n = len(q)
        polar = np.sum(q[:, 1:] ** 2)
        if (
            min(np.linalg.norm(v - w) for i, v in enumerate(q) for w in q[i + 1 :])
            < 4 * D
        ):
            return None
        if any(np.ptp(q @ normal) > 139.7 - 3*D - 6 for normal in (LN, RN)):
            return None
        margins = np.full(len(shifts), 1e9)
        peak = np.zeros(len(shifts))
        peak90 = np.zeros(len(shifts))
        pts = base[None, None, :] + shifts[:, None, :] + q[None, :, :]
        for F, M, C in loads:
            mx = M - np.cross(base + shifts - C, F)[:, 0]
            f = np.broadcast_to(F / n, (len(shifts), n, 3)).copy()
            f[:, :, 1] -= mx[:, None] * q[None, :, 2] / polar
            f[:, :, 2] += mx[:, None] * q[None, :, 1] / polar
            peak = np.maximum(
                peak, (np.linalg.norm(f[:, :, 1:], axis=-1) / capacity(f, d, leg=leg, rim=rim)[0]).max(1)
            )
            peak90 = np.maximum(peak90, (np.linalg.norm(f[:, :, 1:], axis=-1) /
                capacity(f, d, 90000., leg=leg, rim=rim)[0]).max(1))
            for normal, sgn, name, g in (
                (LN, 1, "lumber_leg_left", leg),
                (RN, -1, "base_side_left", rim),
            ):
                coord = (q[None, :, :] + shifts[:, None, :]) @ normal
                nf = sgn * (f @ normal)
                for sign in (-1, 1):
                    margins = np.minimum(
                        margins,
                        (
                            69.85 - sign * coord - np.where(sign * nf > 0, 4, 1.5) * D
                        ).min(1),
                    )
                s = (pts - np.array(geo[name]["centre_mm"])) @ g
                ends = geo[name]["end_stations_mm"]
                margins = np.minimum(
                    margins, np.minimum(s - ends[0] - 7 * D, ends[1] - s - 7 * D).min(1)
                )
        eligible = np.flatnonzero(margins >= 3)
        if not len(eligible):
            return None
        def summarize(i, selected_peak, selected_fyb):
            modes = set()
            for F, M, C in loads:
                mx = M - np.cross(base + shifts[i] - C, F)[0]
                f = np.broadcast_to(F/n, (n, 3)).copy()
                f[:, 1] -= mx*q[:, 2]/polar
                f[:, 2] += mx*q[:, 1]/polar
                modes.update(("Im", "Is", "II", "IIIm", "IIIs", "IV")[int(m)] for m in capacity(f, d, leg=leg, rim=rim)[1])
            return {
                "ratio": float(selected_peak[i]),
                "selected_fyb_psi": selected_fyb,
                "same_layout_fyb_45ksi_ratio_cd_1_0": float(peak[i]),
                "ratio_cd_1_0": float(selected_peak[i]),
                "hypothetical_ratio_cd_1_6": float(selected_peak[i]/1.6),
                "same_layout_hypothetical_fyb_90ksi_ratio_cd_1_0": float(peak90[i]),
                "same_layout_hypothetical_fyb_90ksi_ratio_cd_1_6": float(peak90[i])/1.6,
                "same_layout_modes_at_45ksi": sorted(modes),
                "left_axes_xyz_mm": (base + q + shifts[i] + [loads[0][2][0], 0, 0]).tolist(),
                "right_axes_xyz_mm": (base + q + shifts[i] + [loads[1][2][0], 0, 0]).tolist(),
                "margin": float(margins[i]),
                "shift_LN_RN": (shifts[i] @ np.array([LN, RN]).T).tolist(),
                "points_relative_depth_center": (q + shifts[i]).tolist(),
            }

        return (summarize(eligible[np.argmin(peak[eligible])], peak, 45000.),
                summarize(eligible[np.argmin(peak90[eligible])], peak90, 90000.))

    results = []
    for n in (4, 2, 3):
        for d in (0.375, 0.5, 0.625, 0.75, 0.875, 1.):
            best = None
            best90 = None
            count = 0
            if n == 2:
                layouts = (
                    (
                        np.array([0, math.cos(t), math.sin(t)])[None, :]
                        * np.array([-a / 2, a / 2])[:, None],
                        (a, t),
                    )
                    for a in range(math.ceil(4 * d * 25.4), 221, 5)
                    for t in np.arange(0, math.pi, math.pi / 18)
                )
            else:

                def layoutsgen(n=n, d=d):
                    for a, b in itertools.product(
                        range(math.ceil(4 * d * 25.4), 151, 5), repeat=2
                    ):
                        corners = np.array(
                            [
                                s * a / 2 * leg + t * b / 2 * rim
                                for s, t in itertools.product((-1, 1), repeat=2)
                            ]
                        )
                        for omit in range(4) if n == 3 else [None]:
                            yield (
                                (
                                    corners
                                    if omit is None
                                    else np.delete(corners, omit, 0)
                                ),
                                (a, b, omit),
                            )

                layouts = layoutsgen()
            for q, params in layouts:
                r = check(q, d)
                if r:
                    count += 1
                    ordinary, stronger = r
                    if best is None or ordinary["ratio"] < best["ratio"]:
                        best = {**ordinary, "parameters": params}
                    if best90 is None or stronger["ratio"] < best90["ratio"]:
                        best90 = {**stronger, "parameters": params}
            results.append(
                {
                    "bolt_count_per_leg": n,
                    "diameter_in": d,
                    "layouts_with_at_least_one_eligible_shift": count,
                    "best": best,
                    "best_hypothetical_fyb_90ksi": best90,
                }
            )

    return {
        "candidate": p["candidate"],
        "actual_grain_axes": {"leg":leg.tolist(), "rim":rim.tolist()},
        "source_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (report_path, geometry_path, Path(__file__))
        },
        "source_resultants_on_legs": [
            {
                "side": side,
                "force_xyz_n": f.tolist(),
                "moment_x_nmm": float(m),
                "centroid_xyz_mm": c.tolist(),
            }
            for side, (f, m, c) in zip(("left", "right"), loads, strict=True)
        ],
        "bounds": {
            "diameters_in": [0.375, 0.5, 0.625, 0.75, 0.875, 1.],
            "bearing_lengths_mm": [88.9, 88.9],
            "two_bolt_lengths_mm": "ceil(4D) through220 in5mm steps",
            "two_bolt_angle_degrees": "0 through170 in10degree steps, measuredfrom+worldY toward+Z",
            "three_four_bolt_layouts": "LEG/RIM parallelogram a,b=ceil(4D) through150 in5mm steps;3bolts useeach of4 possible omittedcorners",
            "centroid_depth_offsets_mm": "−40 through40 in5mm steps independentlyalongLEGnormal andRIMnormal",
            "minimum_pair_distance_mm": "4D",
            "minimum_edge_end_reserve_mm": 3.0,
            "directional_edges": "4D loaded and1.5D unloaded usingeach predictedsamecaseboltforce; conservativeoblique interpretation",
            "end_distance": "7D fromconservativefull-depth CADendinterval",
            "yield_bending_psi": 45000.0,
            "specific_gravity": 0.5,
            "parallel_bearing_psi": 5600.0,
            "ktheta": "1 + max acute force-to-grain angle in degrees / 360; Rd bases 4, 3.6, 3.2",
            "ktheta_primary_source": "https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf",
            "extra_group_reduction_applied": False,
            "full_root_penalty_applied": False,
        },
        "results": results,
        "any_fixed_resultant_pass": any(
            r["best"] and r["best"]["ratio"] <= 1 for r in results
        ),
        "scope": "Bounded fixed-resultant planar elastic redistribution of current assembled wrenches. No frame reanalysis, no out-of-plane moment/axial interaction, no fastener-row qualification or construction release. A failed bound is not proof that every connection is impossible.",
        "hypothetical_duration_ranking": "Cd1.6 is shown only as arithmetic ranking; current adopted Cd remains1.0. No load-duration acceptance transfers.",
        "higher_grade_comparison": "90ksi bending yield is hypothetical, not a verified bolt product or tensile-to-bending conversion. Optimized independently within the same bounded placement family; same-layout comparisons are also retained. Modes Im,Is,II are independent of Fyb.",
        "qualified_for_design": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("fea/results/compact-two-study/report.json.gz"),
    )
    parser.add_argument(
        "--geometry",
        type=Path,
        default=Path("fea/results/compact-two-study/geometry.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("fea/results/compact-options-study/layouts.json"),
    )
    parser.add_argument("--expected-candidate", default="compact-two-development")
    args = parser.parse_args()
    result = build(args.report, args.geometry, expected_candidate=args.expected_candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        {
            "any_fixed_resultant_pass": result["any_fixed_resultant_pass"],
            "families": len(result["results"]),
        }
    )


if __name__ == "__main__":
    main()
