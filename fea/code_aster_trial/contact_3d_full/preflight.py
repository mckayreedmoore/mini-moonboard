#!/usr/bin/env python3
"""Offline geometry and frozen-oracle preflight; does not run Code_Aster."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


AUTO_TRI6 = (
    (0.091576213509771, 0.091576213509771),
    (1.0 - 2.0 * 0.091576213509771, 0.091576213509771),
    (0.091576213509771, 1.0 - 2.0 * 0.091576213509771),
    (0.445948490915965, 0.108103018168070),
    (0.445948490915965, 0.445948490915965),
    (0.108103018168070, 0.445948490915965),
)


def parse_mesh(path: Path):
    lines = path.read_text().splitlines()
    if max(map(len, lines), default=0) > 80:
        raise ValueError("ASTER mesh contains a physical line longer than 80 columns")
    coords = {}
    sections = {}
    i = 0
    while i < len(lines):
        section = lines[i].strip()
        if section in {"COOR_3D", "PENTA15", "TRIA6", "GROUP_MA", "GROUP_NO"}:
            i += 1
            records = []
            while i < len(lines) and lines[i].strip() != "FINSF":
                records.append(lines[i].split())
                i += 1
            sections.setdefault(section, []).extend(records)
        i += 1
    for row in sections["COOR_3D"]:
        if len(row) != 4:
            raise ValueError(f"bad coordinate record {row}")
        coords[row[0]] = np.asarray([float(v) for v in row[1:]], dtype=float)

    penta = {}
    pending = []
    for row in sections["PENTA15"]:
        if not row:
            continue
        if not pending:
            pending = row
        else:
            pending.extend(row)
        if len(pending) == 16:
            penta[pending[0]] = pending[1:]
            pending = []
        elif len(pending) > 16:
            raise ValueError(f"bad wrapped PENTA15 connectivity: {pending}")
    if pending:
        raise ValueError(f"incomplete PENTA15 connectivity: {pending}")

    tria = {}
    for row in sections["TRIA6"]:
        if len(row) != 7:
            raise ValueError(f"bad TRIA6 record {row}")
        tria[row[0]] = row[1:]

    groups_ma = {}
    for row in sections["GROUP_MA"]:
        if len(row) < 2:
            raise ValueError(f"bad GROUP_MA record {row}")
        groups_ma[row[0]] = row[1:]
    groups_no = {}
    for row in sections["GROUP_NO"]:
        if len(row) < 2:
            raise ValueError(f"bad GROUP_NO record {row}")
        groups_no[row[0]] = row[1:]
    return lines, coords, penta, tria, groups_ma, groups_no


def shape(u, v):
    l1 = 1.0 - u - v
    return np.asarray((l1 * (2 * l1 - 1), u * (2 * u - 1), v * (2 * v - 1),
                       4 * l1 * u, 4 * u * v, 4 * v * l1))


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(source: Path) -> dict:
    mail = source / "contact_coupon.mail"
    _lines, coords, penta, tria, gm, gn = parse_mesh(mail)
    readiness = json.loads((source / "readiness.json").read_text())
    if len(penta) != 4 or len(tria) != 4:
        raise ValueError(f"expected 4 PENTA15 + 4 TRIA6; got {len(penta)} + {len(tria)}")
    if set(gm["M_SOLID"]) != {"MP00001", "MP00002"}:
        raise ValueError(f"wrong master volume group: {gm['M_SOLID']}")
    if set(gm["S_SOLID"]) != {"SP00001", "SP00002"}:
        raise ValueError(f"wrong slave volume group: {gm['S_SOLID']}")
    if gm["MASTER"] != ["MT00001", "MT00002"]:
        raise ValueError(f"master TRIA6 order changed: {gm['MASTER']}")
    expected_slave_order = readiness.get("contact_group_order", ["ST00001", "ST00002"])
    if gm["SLAVE"] != expected_slave_order:
        raise ValueError(f"slave TRIA6 order differs from readiness: {gm['SLAVE']} != {expected_slave_order}")
    if (len(gn["MCUT"]) != 9 or len(gn["SCUT"]) != 9 or len(gn["SLNOD"]) != 9):
        raise ValueError(f"unexpected node groups: { {k: len(v) for k,v in gn.items()} }")

    signed_penta = {}
    for label, conn in penta.items():
        p = [coords[name] for name in conn]
        signed = float(np.dot(np.cross(p[1] - p[0], p[2] - p[0]), p[3] - p[0]))
        signed_penta[label] = signed
        if signed <= 0.0:
            raise ValueError(f"nonpositive PENTA15 orientation at {label}: {signed:g}")
        if max(np.linalg.norm(p[i] - (p[j] + p[k]) / 2.0)
               for i, (j, k) in zip((6, 7, 8), ((0, 1), (1, 2), (2, 0)))) > 1.0e-10:
            raise ValueError(f"first-cap midside is not at edge midpoint: {label}")

    master_normals = {}
    for label in gm["MASTER"]:
        conn = tria[label]
        pts = [coords[name] for name in conn[:3]]
        normal = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        master_normals[label] = [float(v) for v in normal]
        if normal[2] <= 0.0:
            raise ValueError(f"master surface {label} is not oriented toward +Z")
    slave_normals = {}
    for label in gm["SLAVE"]:
        conn = tria[label]
        pts = [coords[name] for name in conn[:3]]
        normal = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        slave_normals[label] = [float(v) for v in normal]
        if normal[2] >= 0.0:
            raise ValueError(f"slave surface {label} is not outward-oriented toward -Z")

    active_label = readiness.get("active_slave_face_label", "ST00001")
    open_label = readiness.get("open_slave_face_label", "ST00002")
    shared = sorted(set(tria[active_label]) & set(tria[open_label]))
    if len(shared) != 3:
        raise ValueError(f"expected three shared edge nodes, found {shared}")
    open_samples = []
    for u, v in AUTO_TRI6:
        xyz = shape(u, v) @ np.asarray([coords[node] for node in tria[open_label]])
        open_samples.append(float(xyz[2]))
    min_open_gap = min(open_samples)
    mesh_variant = readiness["variant"]
    if mesh_variant == "mixed-active-open" and min_open_gap <= 0.40:
        raise ValueError(f"mixed open-face quadrature margin too small: {min_open_gap:g} mm")
    if mesh_variant == "flat-full-contact" and max(abs(v - 0.02) for v in open_samples) > 1.0e-10:
        raise ValueError("full-contact variant is not flat at the frozen 0.02 mm gap")

    return {
        "status": "PASS",
        "scope": "offline geometry and source-input preflight only; no native solve",
        "variant": mesh_variant,
        "input_sha256": digest(mail),
        "counts": {"nodes": len(coords), "PENTA15": len(penta), "TRIA6": len(tria)},
        "physical_line_max_columns": max(map(len, _lines), default=0),
        "groups": {"M_SOLID": len(gm["M_SOLID"]), "S_SOLID": len(gm["S_SOLID"]),
                   "MASTER": len(gm["MASTER"]), "SLAVE": len(gm["SLAVE"]),
                   "MCUT": len(gn["MCUT"]), "SCUT": len(gn["SCUT"]),
                   "SLNOD": len(gn["SLNOD"])},
        "signed_penta_determinants_mm3": signed_penta,
        "master_surface_area_vectors_mm2": master_normals,
        "slave_surface_area_vectors_mm2": slave_normals,
        "slave_contact_order": gm["SLAVE"],
        "active_slave_face": active_label,
        "open_slave_face": open_label,
        "shared_slave_nodes": shared,
        "open_face_AUTO_sample_initial_gap_mm": open_samples,
        "open_face_minimum_AUTO_sample_gap_mm": min_open_gap,
        "mixed_open_face_margin_after_uniform_0p03mm_cut_motion_mm": min_open_gap - 0.03,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.source.resolve())
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
