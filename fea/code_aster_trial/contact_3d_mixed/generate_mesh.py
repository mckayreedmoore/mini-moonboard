#!/usr/bin/env python3
"""Generate a small conforming PENTA15/TRIA6 contact-output coupon."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TRIANGLES = (("A", "B", "C"), ("A", "C", "D"))
POINTS = {"A": (0.0, 0.0), "B": (100.0, 0.0),
          "C": (100.0, 100.0), "D": (0.0, 100.0)}
EDGE_PAIRS = (("A", "B"), ("B", "C"), ("C", "A"),
              ("A", "C"), ("C", "D"), ("D", "A"))
GAP_MM = 0.02
THICKNESS_MM = 20.0
E_MPA = 1000.0
NU = 0.25
C11_MPA = E_MPA * (1.0 - NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))
TOTAL_SOLID_COMPRESSION_MM = 0.01
AREA_MM2 = 10000.0
EXPECTED_PRESSURE_MPA = C11_MPA * TOTAL_SOLID_COMPRESSION_MM / (2.0 * THICKNESS_MM)
EXPECTED_FORCE_N = EXPECTED_PRESSURE_MPA * AREA_MM2


def edge(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


class Mesh:
    def __init__(self, rise_mm: float, slave_order: str = "active-open"):
        self.rise_mm = rise_mm
        if slave_order not in {"active-open", "open-active"}:
            raise ValueError(f"unsupported slave surface order {slave_order!r}")
        self.slave_order = slave_order
        self.nodes: dict[tuple[float, float, float], str] = {}
        self.coordinates: dict[str, tuple[float, float, float]] = {}
        self.next_node = 1
        self.solids: list[tuple[str, list[str], str]] = []
        self.skins: list[tuple[str, list[str], str]] = []
        self.master_cut: list[str] = []
        self.slave_cut: list[str] = []
        self.slave_surface: list[str] = []

    def node(self, xyz: tuple[float, float, float]) -> str:
        key = tuple(round(value, 10) for value in xyz)
        if key not in self.nodes:
            label = f"N{self.next_node:06d}"
            self.next_node += 1
            self.nodes[key] = label
            self.coordinates[label] = xyz
        return self.nodes[key]

    def z_master(self, x: float, y: float, upper: bool) -> float:
        return 0.0 if upper else -THICKNESS_MM

    def z_slave(self, x: float, y: float, rear: bool) -> float:
        rise = self.rise_mm * max(0.0, (y - x) / 100.0)
        return GAP_MM + rise + (THICKNESS_MM if rear else 0.0)

    def body(self, body: str) -> None:
        is_master = body == "M"
        for triangle_index, tri in enumerate(TRIANGLES):
            # Each prism has the CCW planform orientation A-B-C or A-C-D.
            base_names = [self.node((POINTS[name][0], POINTS[name][1],
                                     self.z_master(*POINTS[name], False) if is_master
                                     else self.z_slave(*POINTS[name], False)))
                          for name in tri]
            top_names = [self.node((POINTS[name][0], POINTS[name][1],
                                    self.z_master(*POINTS[name], True) if is_master
                                    else self.z_slave(*POINTS[name], True)))
                         for name in tri]

            def midpoint(a: str, b: str) -> str:
                xa, ya, za = self.coordinates[a]
                xb, yb, zb = self.coordinates[b]
                return self.node(((xa + xb) / 2.0, (ya + yb) / 2.0,
                                  (za + zb) / 2.0))

            base_mid = [midpoint(base_names[0], base_names[1]),
                        midpoint(base_names[1], base_names[2]),
                        midpoint(base_names[2], base_names[0])]
            long_mid = [midpoint(base_names[i], top_names[i]) for i in range(3)]
            top_mid = [midpoint(top_names[0], top_names[1]),
                       midpoint(top_names[1], top_names[2]),
                       midpoint(top_names[2], top_names[0])]

            label = f"{body}P{triangle_index + 1:05d}"
            conn = (base_names + top_names + base_mid + long_mid + top_mid)
            self.solids.append((label, conn, f"{body}_SOLID"))

            # Contact skins follow the top cap for the fixed master and the
            # first cap for the slave. The diagnostic can reverse slave group
            # order without changing the geometry or element connectivity.
            edge_names = {edge(tri[0], tri[1]): 0,
                          edge(tri[1], tri[2]): 1,
                          edge(tri[2], tri[0]): 2}
            if is_master:
                surf_conn = top_names + top_mid
                surf_label = f"MT{triangle_index + 1:05d}"
                group = "MASTER"
            else:
                # Outward bottom skin reverses corners A-C-B / A-D-C;
                # TRI6 midsides are ordered 12, 23, 31 after reversal.
                rev = (tri[0], tri[2], tri[1])
                corner_map = {tri[i]: base_names[i] for i in range(3)}
                mid_map = {edge(tri[0], tri[1]): base_mid[0],
                           edge(tri[1], tri[2]): base_mid[1],
                           edge(tri[2], tri[0]): base_mid[2]}
                surf_conn = [corner_map[name] for name in rev]
                surf_conn += [mid_map[edge(rev[0], rev[1])],
                              mid_map[edge(rev[1], rev[2])],
                              mid_map[edge(rev[2], rev[0])]]
                surf_label = f"ST{triangle_index + 1:05d}"
                group = "SLAVE"
                self.slave_surface.extend(base_names + base_mid)
            self.skins.append((surf_label, surf_conn, group))

            if triangle_index == 0:
                if is_master:
                    self.master_cut.extend(base_names + base_mid)
                else:
                    self.slave_cut.extend(top_names + top_mid)
            else:
                if is_master:
                    self.master_cut.extend(base_names + base_mid)
                else:
                    self.slave_cut.extend(top_names + top_mid)

    @staticmethod
    def unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    def write(self, output: Path) -> dict:
        self.body("M")
        self.body("S")
        self.master_cut = self.unique(self.master_cut)
        self.slave_cut = self.unique(self.slave_cut)
        self.slave_surface = self.unique(self.slave_surface)
        lines = ["TITRE", "PENTA15/TRIA6 3-D contact output known-answer coupon", "FINSF",
                 "COOR_3D"]
        for label, xyz in self.coordinates.items():
            lines.append(label + " " + " ".join(f"{v:.12g}" for v in xyz))
        lines.append("FINSF")
        lines.append("PENTA15")
        for label, conn, _group in self.solids:
            first = [label] + conn[:8]
            second = conn[8:]
            lines.append(" ".join(first))
            lines.append(" ".join(second))
        lines.append("FINSF")
        lines.append("TRIA6")
        for label, conn, _group in self.skins:
            lines.append(" ".join([label] + conn))
        lines.append("FINSF")
        slave_labels = [r[0] for r in self.skins if r[2] == "SLAVE"]
        if self.slave_order == "open-active":
            slave_labels.reverse()
        for group, labels in (("M_SOLID", [r[0] for r in self.solids if r[2] == "M_SOLID"]),
                              ("S_SOLID", [r[0] for r in self.solids if r[2] == "S_SOLID"]),
                              ("MASTER", [r[0] for r in self.skins if r[2] == "MASTER"]),
                              ("SLAVE", slave_labels)):
            lines.extend(["GROUP_MA", group + " " + " ".join(labels), "FINSF"])
        for group, labels in (("MCUT", self.master_cut), ("SCUT", self.slave_cut),
                              ("SLNOD", self.slave_surface)):
            lines.extend(["GROUP_NO", group + " " + " ".join(labels), "FINSF"])
        lines.append("FIN")
        if any(len(line) > 80 for line in lines):
            raise ValueError("ASTER mesh has a physical line longer than 80 columns")
        output.write_text("\n".join(lines) + "\n")
        return {
            "variant": "flat-full-contact" if self.rise_mm == 0.0 else "mixed-active-open",
            "rise_mm": self.rise_mm,
            "node_count": len(self.coordinates),
            "penta15_count": len(self.solids),
            "tria6_count": len(self.skins),
            "groups": {"M_SOLID": 2, "S_SOLID": 2, "MASTER": 2,
                       "SLAVE": 2, "MCUT": len(self.master_cut),
                       "SCUT": len(self.slave_cut), "SLNOD": len(self.slave_surface)},
            "contact_element_order": slave_labels,
            "contact_group_order": slave_labels,
            "active_slave_face_label": "ST00001",
            "open_slave_face_label": "ST00002",
            "penta15_nodes": "1-3 first cap; 4-6 second cap; 7-9 first-cap edges; 10-12 longitudinal edges; 13-15 second-cap edges",
            "units": {"length": "mm", "force": "N", "stress": "MPa"},
            "material": {"E_MPa": E_MPA, "nu": NU, "uniaxial_strain_modulus_MPa": C11_MPA},
            "flat_full_contact_oracle": {
                "initial_gap_mm": GAP_MM,
                "imposed_cut_closure_mm": 0.03,
                "solid_compression_mm": TOTAL_SOLID_COMPRESSION_MM,
                "interface_area_mm2": AREA_MM2,
                "pressure_magnitude_MPa": EXPECTED_PRESSURE_MPA,
                "contact_force_magnitude_N": EXPECTED_FORCE_N,
                "contact_force_direction_on_slave_N": [0.0, 0.0, EXPECTED_FORCE_N],
                "RN_and_SCUT_signed_table_convention": "expected RN sum is [0, 0, -3000] N; expected SCUT REAC_NODA is [0, 0, -3000] N and MCUT REAC_NODA is [0, 0, +3000] N; the two cut reactions must balance",
            },
            "mixed_active_open_oracle": ({
                "active_slave_face": "ST00001 (A-B-C)",
                "active_slave_face_label": "ST00001",
                "open_slave_face": "ST00002 (A-C-D)",
                "open_slave_face_label": "ST00002",
                "shared_nodes": ["A", "C", "midpoint(A,C)"],
                "initial_open_face_min_AUTO_sample_gap_mm": GAP_MM + self.rise_mm * 0.091576213509771,
                "hypothetical_uniform_closure_margin_mm": self.rise_mm * 0.091576213509771 - 0.03,
                "purpose": "compare shared-node CONT_NOEU/RN output when an active and an open TRIA6 share nodes and their contact-group order is reversed; no force-capacity or joint acceptance claim",
                "later_contact_face_label": slave_labels[-1],
            } if self.rise_mm > 0.0 else None),
            "frozen_limits": {
                "full_contact_force_absolute_error_N": 0.1,
                "full_contact_pressure_absolute_error_MPa": 0.003,
                "full_contact_stress_absolute_error_MPa": 0.003,
                "contact_gap_absolute_limit_mm": 0.01,
                "cut_pair_z_resultant_residual_N": 0.1,
                "flat_full_contact_RN_to_slave_cut_vector_residual_N": 0.1,
                "mixed_variant_RN_discrepancy": "diagnostic only; compare with frozen 0.1 N numerical floor, no analytic force or acceptance claim",
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--rise-mm", type=float, required=True)
    parser.add_argument("--slave-order", choices=("active-open", "open-active"), default="active-open")
    args = parser.parse_args()
    if args.rise_mm not in (0.0, 5.0):
        parser.error("frozen variants are rise-mm 0 or 5")
    mesh = Mesh(args.rise_mm, args.slave_order)
    readiness = mesh.write(args.output)
    readiness["input_mesh_sha256"] = __import__("hashlib").sha256(args.output.read_bytes()).hexdigest()
    readiness["test_only"] = True
    readiness["native_lane_authorization"] = "owner-approved bounded known-answer/method checks only"
    args.readiness.write_text(json.dumps(readiness, indent=2) + "\n")
    print(json.dumps(readiness, indent=2))


if __name__ == "__main__":
    main()
