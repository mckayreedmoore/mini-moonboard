from __future__ import annotations

import math
import sys
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "prepared"))

import prepare
import verify
from contact_pair_output import QUANTITIES


def _deck_set(deck: str, set_name: str, keyword: str):
    lines = deck.splitlines()
    header = f"*{keyword},NSET={set_name}" if keyword == "NSET" else None
    matching = [index for index, line in enumerate(lines)
                if header is not None and line.strip().upper() == header]
    if len(matching) != 1:
        raise ValueError(f"expected one {keyword} set {set_name}")
    members = []
    for raw in lines[matching[0] + 1:]:
        line = raw.strip()
        if line.startswith("*"):
            break
        if line:
            members.extend(int(field.strip()) for field in line.split(","))
    if not members or len(members) != len(set(members)):
        raise ValueError(f"empty or duplicate members in {set_name}")
    return set(members)


def _deck_upper_element_nodes(deck: str):
    lines = deck.splitlines()
    headers = [index for index, line in enumerate(lines)
               if line.strip().upper() == "*ELEMENT,TYPE=C3D10,ELSET=UPPER"]
    if len(headers) != 1:
        raise ValueError("expected one UPPER C3D10 element set")
    nodes = set()
    for raw in lines[headers[0] + 1:]:
        line = raw.strip()
        if line.startswith("*"):
            break
        if line:
            fields = [int(field.strip()) for field in line.split(",")]
            if len(fields) != 11:
                raise ValueError("malformed UPPER C3D10 connectivity")
            nodes.update(fields[1:])
    if not nodes:
        raise ValueError("empty UPPER element set")
    return nodes


def _parse_contact_deck_restraints(deck: str):
    lines = deck.splitlines()
    boundary_headers = [index for index, line in enumerate(lines)
                        if line.strip().upper() == "*BOUNDARY"]
    if len(boundary_headers) != 1:
        raise ValueError("expected exactly one emitted *BOUNDARY card")
    boundary_rows = []
    for raw in lines[boundary_headers[0] + 1:]:
        line = raw.strip()
        if line.startswith("*"):
            break
        if not line or line.startswith("**"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 4:
            raise ValueError("malformed *BOUNDARY row")
        node, first, last = (int(field) for field in fields[:3])
        value = float(fields[3])
        if first < 1 or last < first or last > 6 or value != 0.0:
            raise ValueError("unsupported *BOUNDARY DOF range or value")
        boundary_rows.extend((node, dof, value) for dof in range(first, last + 1))
    if not boundary_rows:
        raise ValueError("empty emitted *BOUNDARY card")

    ground_nodes = _deck_set(deck, "GROUND", "NSET")
    gauge_nodes = _deck_set(deck, "UPPER_GAUGES", "NSET")
    pressure_nodes = _deck_set(deck, "LOAD_PATCH_NODES", "NSET")
    upper_nodes = _deck_upper_element_nodes(deck)
    if gauge_nodes != {33, 45}:
        raise ValueError("upper gauges must be nodes 33 and 45")
    if ground_nodes & upper_nodes:
        raise ValueError("lower ground node set overlaps the upper body")
    if gauge_nodes - upper_nodes:
        raise ValueError("an upper gauge is outside the upper body")

    actual = Counter(boundary_rows)
    expected = Counter((node, dof, 0.0)
                      for node in ground_nodes for dof in (1, 2, 3))
    expected.update(((33, 1, 0.0), (33, 2, 0.0), (45, 2, 0.0)))
    if actual != expected:
        raise ValueError("emitted *BOUNDARY rows differ from exact ground and gauge DOFs")
    constrained_nodes = {node for node, _dof, _value in boundary_rows}
    if constrained_nodes & pressure_nodes:
        raise ValueError("a loaded pressure node has an additional constraint")
    if any(node in upper_nodes and dof == 3
           for node, dof, _value in boundary_rows):
        raise ValueError("an upper-body z DOF is grounded")
    return {"ground": ground_nodes, "gauges": gauge_nodes,
            "pressure_nodes": pressure_nodes, "upper_nodes": upper_nodes,
            "boundary_rows": actual}


def _node_block(quantity: str, set_name: str, rows: dict[int, tuple[float, float, float]]):
    lines = [f" {quantity} for set {set_name} and time  0.1000000E+01", ""]
    lines.extend(f" {node:8d} " + " ".join(f"{value: .12E}" for value in row)
                 for node, row in sorted(rows.items()))
    return "\n".join(lines) + "\n\n"


def _pair_block(quantity: str, wrench: tuple[float, ...]):
    label = next(key for key, value in QUANTITIES.items() if value == quantity)
    return (
        " statistics for slave set SLAVE, master set MASTER and time  0.1000000E+01\n\n"
        f"   {label}\n\n"
        + "   " + " ".join(f"{value:.12E}" for value in wrench) + "\n\n"
    )


def _affine_dat(expected, coordinates, displacements, reactions, stress_rows):
    oracle = expected["oracle"]
    lines = [
        _node_block("displacements (vx,vy,vz)", "ALLNODES", displacements),
        _node_block("forces (fx,fy,fz)", "ALLNODES", reactions),
        " stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set ANNULUS and time  0.1000000E+01\n",
    ]
    lines.extend(f" {element} {point} " + " ".join(f"{value:.12E}" for value in stress)
                 + "\n" for element, point, stress in stress_rows)
    lines.append("\n total internal energy for set ANNULUS and time  0.1000000E+01\n\n")
    lines.append(f" {oracle['total_elastic_energy_N_mm']:.12E}\n")
    return "".join(lines)


def _solve3(matrix, rhs):
    augmented = [list(row) + [value] for row, value in zip(matrix, rhs)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular support-wrench fixture")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [a - factor * b
                              for a, b in zip(augmented[row], augmented[column])]
    return [augmented[row][3] for row in range(3)]


def _support_rf(expected, coordinates, target_wrench):
    ids = expected["restraints"]["ground_node_set"]
    chosen = None
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            for c in range(b + 1, len(ids)):
                triple = [ids[a], ids[b], ids[c]]
                xyz = [coordinates[node] for node in triple]
                matrix = [[1.0, 1.0, 1.0],
                          [xyz[0][1], xyz[1][1], xyz[2][1]],
                          [-xyz[0][0], -xyz[1][0], -xyz[2][0]]]
                determinant = (
                    matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
                    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
                    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))
                if abs(determinant) > 1e-8:
                    chosen = (triple, xyz, matrix)
                    break
            if chosen:
                break
        if chosen:
            break
    if chosen is None:
        raise ValueError("no noncollinear support nodes for synthetic audit")
    triple, xyz, matrix = chosen
    fz = _solve3(matrix, [target_wrench[2], target_wrench[3], target_wrench[4]])
    rows = {node: (0.0, 0.0, 0.0) for node in ids}
    for node, value in zip(triple, fz):
        rows[node] = (0.0, 0.0, value)
    return rows


class PreparationContracts(unittest.TestCase):
    def test_affine_annulus_uses_actual_polygon_area_and_compressive_rf_sign(self):
        deck, expected, nodes = prepare.job_affine()
        mesh = expected["mesh"]
        oracle = expected["oracle"]
        self.assertEqual(mesh["nodes"], 800)
        self.assertEqual(mesh["elements"], 384)
        self.assertAlmostEqual(mesh["corner_tet_volume_sum_mm3"],
                               mesh["top_FE_area_mm2"] * prepare.HEIGHT, places=10)
        self.assertLess(mesh["top_FE_area_mm2"], mesh["ideal_circle_area_mm2"])
        self.assertAlmostEqual(oracle["sigma_zz_MPa"], -20.0)
        self.assertLess(oracle["top_RF3_N"], 0.0)
        self.assertGreater(oracle["bottom_RF3_N"], 0.0)
        self.assertAlmostEqual(oracle["top_RF3_N"],
                               oracle["sigma_zz_MPa"] * mesh["top_FE_area_mm2"])
        self.assertTrue(oracle["interior_nodes_free"])
        self.assertTrue(set(oracle["interior_nodes_free"]) <= set(nodes))
        self.assertIn("*EL PRINT,ELSET=ANNULUS,FREQUENCY=1\nS", deck)
        self.assertIn("*EL PRINT,ELSET=ANNULUS,TOTALS=ONLY,FREQUENCY=1\nELSE", deck)
        tol = expected["predeclared_tolerances"]
        self.assertEqual(tol["moment_absolute_N_mm"], 0.02)
        self.assertEqual(tol["global_moment_absolute_N_mm"], 0.05)

    def test_loaded_patch_integrates_finite_faces_and_declares_rf_dof_basis(self):
        deck, expected, nodes = prepare.job_contact()
        patch = expected["loaded_patch"]
        restraints = expected["restraints"]
        self.assertEqual(expected["mesh"]["total_nodes"], 1600)
        self.assertEqual(expected["mesh"]["total_elements"], 768)
        self.assertEqual(len(patch["tri6_face_kinematics"]), 16)
        self.assertTrue(set(patch["pressure_node_ids"]) <= set(nodes))
        self.assertFalse(set(restraints["upper_in_plane_gauge_nodes"])
                         & set(patch["pressure_node_ids"]))
        self.assertEqual(patch["initial_applied_force_N"][:2], [0.0, 0.0])
        self.assertAlmostEqual(patch["initial_applied_force_N"][2],
                               -patch["pressure_MPa"]
                               * patch["tri6_straight_sided_FE_area_mm2"])
        centroid = patch["FE_area_centroid_mm"]
        force = patch["initial_applied_force_N"]
        expected_moment = verify.cross(centroid, force)
        for actual, reference in zip(patch["initial_applied_moment_about_origin_N_mm"],
                                     expected_moment):
            self.assertAlmostEqual(actual, reference, places=10)
        self.assertTrue(restraints["gauge_nodes_receive_no_pressure_load"])
        self.assertIn("total external nodal force", restraints["gauge_rf_semantics"])
        self.assertIn("LOAD_PATCH_NODES", deck)
        self.assertIn("*DSLOAD\nLOAD_PATCH,P,2", deck)
        self.assertIn("*CONTACT PAIR,INTERACTION=DIAGNOSTIC_NORMAL,TYPE=SURFACE TO SURFACE", deck)
        self.assertNotIn("*TIE", deck)
        self.assertNotIn("*FRICTION", deck)

    def test_contact_deck_parser_enforces_exact_emitted_constraints(self):
        deck, expected, _nodes = prepare.job_contact()
        parsed = _parse_contact_deck_restraints(deck)
        restraints = expected["restraints"]
        self.assertEqual(parsed["ground"], set(restraints["ground_node_set"]))
        self.assertEqual(parsed["gauges"], {33, 45})
        self.assertEqual(restraints["gauge_dofs"], {"33": [1, 2], "45": [2]})
        self.assertEqual(parsed["pressure_nodes"],
                         set(expected["loaded_patch"]["pressure_node_ids"]))
        self.assertEqual(len(parsed["boundary_rows"]),
                         3 * len(parsed["ground"]) + 3)

        first_ground = min(parsed["ground"])
        corruptions = {
            "missing-ground-range": deck.replace(
                f"{first_ground},1,3,0.0\n", "", 1),
            "duplicate-gauge-row": deck.replace(
                "*BOUNDARY\n", "*BOUNDARY\n45,2,2,0.0\n", 1),
            "wrong-gauge-dof": deck.replace(
                "33,1,1,0.0\n", "33,1,2,0.0\n", 1),
            "pressure-node-constraint": deck.replace(
                "*BOUNDARY\n",
                f"*BOUNDARY\n{min(parsed['pressure_nodes'])},3,3,0.0\n", 1),
            "upper-z-ground": deck.replace(
                "*BOUNDARY\n", "*BOUNDARY\n33,3,3,0.0\n", 1),
            "missing-boundary-card": deck.replace("*BOUNDARY\n", "** omitted\n", 1),
            "duplicate-boundary-card": deck.replace(
                "*BOUNDARY\n", "*BOUNDARY\n*BOUNDARY\n", 1),
        }
        for label, corrupted in corruptions.items():
            with self.subTest(corruption=label), self.assertRaises(ValueError):
                _parse_contact_deck_restraints(corrupted)

    def test_tri6_follower_pressure_integrates_deformed_area_vector_and_moment(self):
        coords = {
            1: (0.0, 0.0, 0.0), 2: (2.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0),
            4: (1.0, 0.0, 0.0), 5: (1.0, 0.5, 0.0), 6: (0.0, 0.5, 0.0),
        }
        # z=0.1*x+0.2*y is an affine tilted plane; the surface vector is
        # exactly (-0.1,-0.2,1) mm^2 for this reference triangle.
        disp = {node: (0.0, 0.0, 0.1 * xyz[0] + 0.2 * xyz[1])
                for node, xyz in coords.items()}
        faces = [{"node_ids": [1, 2, 3, 4, 5, 6], "outward_sign": 1}]
        wrench, area, centroid = verify.tri6_pressure_wrench(faces, coords, disp, 2.0)
        self.assertAlmostEqual(wrench[0], 0.2, places=11)
        self.assertAlmostEqual(wrench[1], 0.4, places=11)
        self.assertAlmostEqual(wrench[2], -2.0, places=11)
        self.assertAlmostEqual(area, math.sqrt(1.05), places=11)
        reference_centroid = (2 / 3, 1 / 3, 0.1 * (2 / 3) + 0.2 * (1 / 3))
        expected_moment = verify.cross(reference_centroid, (0.2, 0.4, -2.0))
        for actual, reference in zip(wrench[3:], expected_moment):
            self.assertAlmostEqual(actual, reference, places=11)
        self.assertTrue(math.isfinite(centroid[2]))

    def test_ccx_223_three_point_and_continuous_tri6_curved_moment_known_answer(self):
        coords = {
            1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 1.0), 3: (0.0, 1.0, 0.0),
            4: (0.5, 0.0, 0.25), 5: (0.5, 0.5, 0.25), 6: (0.0, 0.5, 0.0),
        }
        zero = {node: (0.0, 0.0, 0.0) for node in coords}
        face = [{"node_ids": [1, 2, 3, 4, 5, 6], "outward_sign": 1}]
        continuous, _area6, _centroid6 = verify.tri6_pressure_wrench(
            face, coords, zero, 1.0)
        discrete, _area3, _centroid3 = verify.tri6_pressure_wrench_ccx_223(
            face, coords, zero, 1.0)
        self.assertAlmostEqual(continuous[0], 1 / 3, places=12)
        self.assertAlmostEqual(continuous[1], 0.0, places=12)
        self.assertAlmostEqual(continuous[2], -1 / 2, places=12)
        self.assertAlmostEqual(continuous[3], -1 / 6, places=12)
        self.assertAlmostEqual(continuous[4], 4 / 15, places=12)
        self.assertAlmostEqual(continuous[5], -1 / 12, places=12)
        self.assertAlmostEqual(discrete[0], 1 / 3, places=12)
        self.assertAlmostEqual(discrete[1], 0.0, places=12)
        self.assertAlmostEqual(discrete[2], -1 / 2, places=12)
        self.assertAlmostEqual(discrete[3], -1 / 6, places=12)
        self.assertAlmostEqual(discrete[4], 29 / 108, places=12)
        self.assertAlmostEqual(discrete[5], -1 / 12, places=12)
        self.assertAlmostEqual(discrete[4] - continuous[4], 1 / 540, places=12)

    def test_affine_audit_uses_manual_rf_sign_and_fixed_moment_tolerances(self):
        _deck, expected, coords = prepare.job_affine()
        oracle = expected["oracle"]
        top_ids = expected["top_node_ids"]
        bottom_ids = expected["bottom_node_ids"]
        boundary = set(expected["boundary_node_ids"])
        displacements = {node: (0.0, 0.0,
                                expected["kinematics"]["epsilon_zz"] * xyz[2])
                        for node, xyz in coords.items()}
        reactions = {node: (0.0, 0.0, 0.0) for node in coords}
        for node in top_ids:
            reactions[node] = (0.0, 0.0, oracle["top_RF3_N"] / len(top_ids))
        for node in bottom_ids:
            reactions[node] = (0.0, 0.0, oracle["bottom_RF3_N"] / len(bottom_ids))
        mesh = prepare.make_annulus(
            r_in=prepare.R_IN, r_out=prepare.R_OUT, z0=0.0, z1=prepare.HEIGHT,
            n_radial=prepare.N_RADIAL, n_angle=prepare.N_ANGLE, n_z=prepare.N_Z)
        stress_rows = [(element, ip, (0.0, 0.0, -20.0, 0.0, 0.0, 0.0))
                       for element, _conn in mesh.elements for ip in range(1, 5)]
        dat = _affine_dat(expected, coords, displacements, reactions, stress_rows)
        result = verify.audit_affine(expected, dat, coords)
        self.assertEqual(result["status"], "PASS_AFFINE_ELASTIC_METHOD_FIXTURE")
        self.assertLess(result["top_reaction_wrench"]["force"]["error_norm"], 1e-8)
        self.assertEqual(set(top_ids) | set(bottom_ids),
                         set(expected["top_node_ids"]) | set(expected["bottom_node_ids"]))
        self.assertTrue(boundary)
        interior = oracle["interior_nodes_free"][0]
        missing_u = dict(displacements)
        del missing_u[interior]
        with self.assertRaises(ValueError):
            verify.audit_affine(expected,
                                _affine_dat(expected, coords, missing_u, reactions, stress_rows),
                                coords)
        missing_rf = dict(reactions)
        del missing_rf[interior]
        with self.assertRaises(ValueError):
            verify.audit_affine(expected,
                                _affine_dat(expected, coords, displacements, missing_rf, stress_rows),
                                coords)
        wrong_interior = dict(displacements)
        wrong_interior[interior] = (0.0, 0.0, wrong_interior[interior][2] + 1e-4)
        with self.assertRaises(ValueError):
            verify.audit_affine(expected,
                                _affine_dat(expected, coords, wrong_interior, reactions, stress_rows),
                                coords)
        substituted_element = list(stress_rows)
        first_element, first_point, first_stress = substituted_element[0]
        substituted_element[0] = (expected["mesh"]["elements"] + 1,
                                  first_point, first_stress)
        with self.assertRaises(ValueError):
            verify.audit_affine(expected,
                                _affine_dat(expected, coords, displacements, reactions,
                                            substituted_element), coords)
        duplicate_integration_point = list(stress_rows)
        first_element, _first_point, first_stress = duplicate_integration_point[0]
        duplicate_integration_point[0] = (first_element, 2, first_stress)
        with self.assertRaises(ValueError):
            verify.audit_affine(expected,
                                _affine_dat(expected, coords, displacements, reactions,
                                            duplicate_integration_point), coords)

    def test_contact_audit_uses_deformed_pressure_surface_and_separate_gauges(self):
        _deck, expected, coords = prepare.job_contact()
        patch = expected["loaded_patch"]
        loaded = set(patch["pressure_node_ids"])
        displacements = {node: (0.01, 0.02, 0.0)
                         for node in coords if node in loaded}
        applied, _area, _centroid = verify.tri6_pressure_wrench_ccx_223(
            patch["tri6_face_kinematics"], coords, displacements,
            patch["pressure_MPa"])
        initial = (*patch["initial_applied_force_N"],
                   *patch["initial_applied_moment_about_origin_N_mm"])
        self.assertGreater(verify.norm(tuple(a - b for a, b in zip(applied, initial))), 0.1)
        ground = _support_rf(expected, coords, tuple(-value for value in applied))
        zeros = {node: (0.0, 0.0, 0.0) for node in expected["restraints"]["upper_in_plane_gauge_nodes"]}
        loaded_rows = {node: displacements[node] for node in loaded}
        ground_u = {node: (0.0, 0.0, 0.0) for node in ground}
        contact = tuple(-value for value in applied)
        dat = "".join((
            _node_block("displacements (vx,vy,vz)", "LOAD_PATCH_NODES", loaded_rows),
            _node_block("displacements (vx,vy,vz)", "UPPER_GAUGES", zeros),
            _node_block("forces (fx,fy,fz)", "UPPER_GAUGES", zeros),
            _node_block("displacements (vx,vy,vz)", "GROUND", ground_u),
            _node_block("forces (fx,fy,fz)", "GROUND", ground),
            _pair_block("CF", contact),
            _pair_block("CFN", contact),
            _pair_block("CFS", (0.0,) * 6),
        ))
        result = verify.audit_contact(expected, dat, coords)
        self.assertEqual(result["status"], "PASS_FINITE_CONTACT_RESULTANT_METHOD_FIXTURE")
        self.assertGreater(verify.norm(result["change_from_initial_pressure_wrench_N_Nmm"]), 0.1)
        self.assertIn("ccx_2_23_discrete_three_point_pressure_wrench_N_Nmm", result)
        self.assertIn("continuous_six_point_pressure_wrench_N_Nmm", result)
        self.assertTrue(result["pressure_quadrature_difference_gate"]["pass"])
        self.assertEqual(result["pressure_quadrature_difference_gate"]["moment"]["limit"],
                         expected["predeclared_tolerances"][
                             "quadrature_difference_moment_absolute_N_mm"])
        self.assertEqual(result["upper_gauge_in_plane_reaction_l1_N"], 0.0)
        self.assertEqual(result["upper_gauge_free_z_RF_N_by_node_not_treated_as_reaction"],
                         {str(node): 0.0 for node in zeros})
        self.assertLess(result["whole_model_force_balance"]["force"]["error_norm"], 1e-8)


if __name__ == "__main__":
    unittest.main()
