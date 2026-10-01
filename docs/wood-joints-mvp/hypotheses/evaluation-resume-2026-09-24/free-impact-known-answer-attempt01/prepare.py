#!/usr/bin/env python3
"""Reproduce the free-impact C3D10 coupon input and expected contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
E = HERE.parent
ROOT = HERE.parents[4]
INPUT = HERE / "input/coupon.inp"
EXPECTED = HERE / "expected.json"
DESIGN = HERE / "fixture-design.md"

GEOMETRY_SOURCE = E / "implicit-contact-point-trace-attempt01/input/implicit_point_trace.inp"
GEOMETRY_SOURCE_SHA256 = "e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b"
REFERENCE_PATH = E / "implicit-contact-free-impact-design-attempt01/parent-reference.json"
REFERENCE_SHA256 = "fc63b21a5c9947f04dd1326339ba0201a2c251a465f41350fd35c46874198d61"
ARCHIVE = E / "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2"
ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MANUAL = ROOT / "fea/generated/ccx_2.23.pdf"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"

SOURCE_FILES = {
    "contactpairs.f": {
        "sha256": "e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488",
        "lines": "111-118",
        "purpose": "Maps the surface-to-surface contact pair to internal mode 1.",
    },
    "dynamics.f": {
        "sha256": "d861c936c204853e84e7647b4164e78556c11b6eb0a532b623d4a75622f53e5e",
        "lines": "70-78, 98-119, 134-139, 248-270",
        "purpose": "Alpha defaults/clamp, implicit contact eligibility, and fixed DIRECT bounds.",
    },
    "initialconditionss.f": {
        "sha256": "25c721d40c071e31baea9c4e7cf8bcc226bbdd0e65cccb327981b31e0c174b2c",
        "lines": "474-501",
        "purpose": "TYPE=VELOCITY parses node/set, global DOF, and velocity magnitude.",
    },
    "nonlingeo.c": {
        "sha256": "8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f",
        "lines": "904-907",
        "purpose": "Computes implicit beta and gamma from alpha; alpha zero yields 1/4 and 1/2.",
    },
    "e_c3d.f": {
        "sha256": "d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc",
        "lines": "986-1005",
        "purpose": "Integrates the C3D10 consistent mass matrix.",
    },
    "mafillsm.f": {
        "sha256": "d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602",
        "lines": "285-300, 338-355, 406-430",
        "purpose": "Calls element mass and assembles mass terms through MPC coefficients.",
    },
    "mafillsmmatrix.f": {
        "sha256": "5790af603df9ba61699bb67aa6552d6e89057202dd0c3b50637cf478ec4899a3",
        "lines": "MPC matrix assembly",
        "purpose": "Applies MPC transformations to assembled element mass entries.",
    },
    "gencontelem_f2f.f": {
        "sha256": "853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe",
        "lines": "550-560, 617-629, 672-685",
        "purpose": "Dynamic positive-gap filter and contact spring generation for the face-to-face pair.",
    },
    "springforc_f2f.f": {
        "sha256": "3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4",
        "lines": "155-164, 186-201, 248-253",
        "purpose": "Signed clearance, linear overclosure pressure/energy, and native spring resultant convention.",
    },
    "checkimpacts.f": {
        "sha256": "30b2e0c7ca03f741852dfc93b67657291f91acfc3b3db8c1b36ec9589733fd66",
        "lines": "89-108, 118-177",
        "purpose": "Energy residual and face-to-face impact/rebound cutback criteria.",
    },
}

UPPER_NODES = (1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24,
               25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35)
LOWER_NODES = (37, 38, 39, 40, 41, 42, 43, 44, 53, 54, 55, 56, 57, 58,
               59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71)
PHYSICAL_NODES = UPPER_NODES + LOWER_NODES
CONTROLLER = 8001


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def nset_nodes(deck: str, name: str) -> tuple[int, ...]:
    marker = f"*NSET,NSET={name}\n"
    require(deck.count(marker) == 1, f"Expected one source node set {name}")
    start = deck.index(marker) + len(marker)
    end = deck.find("\n*", start)
    if end < 0:
        end = len(deck)
    values = []
    for line in deck[start:end].splitlines():
        for field in line.split(","):
            field = field.strip()
            if field:
                values.append(int(field))
    return tuple(values)


def render_input() -> str:
    require(sha_file(GEOMETRY_SOURCE) == GEOMETRY_SOURCE_SHA256,
            "Pinned contact geometry source changed")
    text = GEOMETRY_SOURCE.read_text()
    require(nset_nodes(text, "N_UPPER") == UPPER_NODES, "Upper mesh node identity changed")
    require(nset_nodes(text, "N_LOWER") == LOWER_NODES, "Lower mesh node identity changed")

    text = text.replace(
        "*HEADING\nC3D10 compression/open/reopen method coupon; not a joint model\n",
        "*HEADING\nFree one-coordinate C3D10 impact method coupon; not a joint model\n",
        1,
    )
    old_controller_nodes = (
        "*NODE\n8001,10,0,10\n8002,11,0,10\n8003,10,1,10\n8004,10,0,11\n"
    )
    require(text.count(old_controller_nodes) == 1, "Witness node block changed")
    text = text.replace(old_controller_nodes, "*NODE\n8001,1,1,1\n", 1)

    witness_element = "*ELEMENT,TYPE=C3D4,ELSET=WITNESS\n8001,8001,8002,8003,8004\n"
    require(text.count(witness_element) == 1, "Witness element block changed")
    text = text.replace(witness_element, "", 1)

    old_all = "*NSET,NSET=ALLNODES\n1,2,3,4,5,6,7,8,17,18,19,20\n21,22,23,24,25,26,27,28,29,30,31,32\n33,34,35,37,38,39,40,41,42,43,44,53\n54,55,56,57,58,59,60,61,62,63,64,65\n66,67,68,69,70,71\n"
    require(text.count(old_all) == 1, "Source all-node set changed")
    def list_lines(values: tuple[int, ...]) -> str:
        return "".join(",".join(map(str, values[i:i + 12])) + "\n"
                       for i in range(0, len(values), 12))
    set_block = (
        "*NSET,NSET=N_PHYSICAL\n" + list_lines(PHYSICAL_NODES) +
        "*NSET,NSET=N_ALL\n" + list_lines(PHYSICAL_NODES + (CONTROLLER,)) +
        "*NSET,NSET=Q_NODE\n8001\n"
    )
    text = text.replace(old_all, set_block, 1)

    witness_anchor = "*NSET,NSET=WITNESS_ANCHOR\n8001,8002,8003\n"
    require(text.count(witness_anchor) == 1, "Witness node set changed")
    text = text.replace(witness_anchor, "", 1)

    old_material = "*DENSITY\n1.e-9\n*ELASTIC\n100000.,0.\n"
    require(text.count(old_material) == 1, "Source material block changed")
    text = text.replace(old_material, "*DENSITY\n0.125\n*ELASTIC\n100000.,0.\n", 1)
    witness_section = "*SOLID SECTION,ELSET=WITNESS,MATERIAL=ELASTIC\n"
    require(text.count(witness_section) == 1, "Witness solid section changed")
    text = text.replace(witness_section, "", 1)

    step_start = "*AMPLITUDE,NAME=CONTACT_GAP_PATH\n"
    require(text.count(step_start) == 1, "Source amplitude block changed")
    text = text[:text.index(step_start)]

    equations = ["*EQUATION\n"]
    for node in UPPER_NODES:
        equations.extend(("2\n", f"{node},3,1.\n", f"{CONTROLLER},3,-1.\n"))
    equations.extend((
        "*INITIAL CONDITIONS,TYPE=VELOCITY\n",
        "N_UPPER,3,-0.1\n",
        f"{CONTROLLER},3,-0.1\n",
        "*STEP,NLGEOM,INC=70\n",
        "*DYNAMIC,DIRECT,ALPHA=0.\n",
        "0.0001,0.007\n",
        "*BOUNDARY\n",
        "N_LOWER,1,3,0.\n",
        "N_UPPER,1,2,0.\n",
        "Q_NODE,1,2,0.\n",
        "*NODE PRINT,NSET=N_ALL,FREQUENCY=1\n",
        "U,V\n",
        "*NODE FILE,NSET=N_PHYSICAL,FREQUENCY=1\n",
        "U,V\n",
        "*EL PRINT,ELSET=UPPER,TOTALS=ONLY,FREQUENCY=1\n",
        "ELSE,ELKE,EMAS,EVOL\n",
        "*EL PRINT,ELSET=LOWER,TOTALS=ONLY,FREQUENCY=1\n",
        "ELSE,ELKE,EMAS,EVOL\n",
        "*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1\n",
        "CELS\n",
        "*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER,FREQUENCY=1\n",
        "CFN\n",
        "*END STEP\n",
    ))
    text += "".join(equations)
    return text


def render_design(deck_sha: str, reference_sha: str) -> str:
    return f'''# Free-impact C3D10 method fixture design

Date: 2026-09-27. This packet prepares a bounded method fixture only. The
baseline and trace cases use the same input deck, in that order. No native job
or build is performed by this preparation.

## Model and known answer

The deck preserves the 54 physical node coordinates, twelve C3D10 tetrahedra,
and the two surface-to-surface contact faces from the reviewed point-trace
coupon. Upper nodes are `{len(UPPER_NODES)}` and lower nodes are
`{len(LOWER_NODES)}`; upper slave faces are elements 1–2 S1 and lower master
faces are elements 11–12 S3. Their planar interface area is 4 mm². The old
disconnected C3D4 witness is removed; node 8001 is instead a free U3
controller at `(1,1,1)` mm.

The lower block is fixed. Upper U1/U2 are fixed, and each of its 27 U3 DOFs is
related by its own homogeneous equation to the free controller U3. Initial
velocity is `−0.1 mm/s` for every upper physical U3 and the controller U3. No
load, motion amplitude, or damping is applied. With density `0.125 tonne/mm³`,
each 8 mm³ body has mass 1 tonne; the expected moving projected mass is the
upper 1 tonne and total element mass is 2 tonnes. This is specifically a
translation test, not the nut's eccentric pivot MPC.

The pressure-overclosure slope is `100000 N/mm³`, giving ideal scalar contact
stiffness `400000 N/mm` over the 4 mm² face. The discrete alpha-zero Newmark
oracle is copied from the pinned 70-state
[`parent-reference.json`](../implicit-contact-free-impact-design-attempt01/parent-reference.json)
(SHA-256 `{reference_sha}`). Initial energy is 0.005 N·mm. Maximum compression
is at increment 25; the endpoint unilateral switch opens at increment 50,
where the predicted energy increase is 4.28163131e−6 N·mm (0.0856326%). The
continuous event time is comparison only; the fixed-step recurrence is the
oracle.

The input hash is `{deck_sha}`. Output requests are 55-node U/V DAT, 54-node
physical U/V FRD, upper and lower `ELSE,ELKE,EMAS,EVOL` totals, contact-energy
`CELS` totals, and pair-specific `CFN`. The trace case additionally records
the existing coupon-only `CCXPT_MAP` and corrected `CCXPT_TRIAL` lines. Require
70 accepted increment identities and match actual STA/CVG and FRD state times.
There is no fixed contact-point-count gate. The positive-gap MAP removal
condition and active compressed trial fields are interpreted using the pinned
trace field definitions. Old-set positive-gap TRIAL rows are diagnostic; later
regeneration removes positive-gap points, and accepted open states must have
zero active contact.

## Limits

This is a contact/inertia/output method fixture only. It does not establish
general C3D10 free-MPC inertia, the current physical-pivot map, a joint response,
wood bearing, friction, a capacity, or solver convergence in the full model.
The mass projection, initial velocity through the MPC, impact-energy branch,
CFN sign, and contact energy remain to be checked from the native records.
The parent runner owns freezing and serialized execution; the reviewer owns
the verifier and acceptance thresholds. The proposed output budget is 16 MiB
per case. Preparation status remains non-acceptance.
'''


def source_contract() -> dict:
    return {
        "source_archive_path": "../ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2",
        "source_archive_sha256": ARCHIVE_SHA256,
        "manual_pdf_path": "../../../../../fea/generated/ccx_2.23.pdf",
        "manual_pdf_sha256": MANUAL_SHA256,
        "source_files": SOURCE_FILES,
    }


def render_expected(deck: str, design: str) -> dict:
    require(sha_file(ARCHIVE) == ARCHIVE_SHA256, "Pinned 2.23 source archive changed")
    require(sha_file(MANUAL) == MANUAL_SHA256, "Pinned 2.23 manual changed")
    require(sha_file(REFERENCE_PATH) == REFERENCE_SHA256, "Pinned scalar reference changed")
    ref = json.loads(REFERENCE_PATH.read_text())
    require(ref.get("schema") == "proposed_scalar_free_contact_reference/v1" and
            ref.get("native_execution") is False and len(ref["states"]) == 70,
            "Unexpected parent scalar reference")
    with tarfile.open(ARCHIVE, "r:bz2") as archive:
        for name, source in SOURCE_FILES.items():
            member = "./CalculiX/ccx_2.23/src/" + name
            content = archive.extractfile(member).read()
            require(sha_bytes(content) == source["sha256"], f"Pinned source member changed: {name}")

    source_input_sha = sha_file(GEOMETRY_SOURCE)
    deck_sha = sha_bytes(deck.encode())
    return {
        "schema": "ccx223_free_impact_expected/v1",
        "status": "PREPARED_SOURCE_ONLY_NO_NATIVE_EXECUTION",
        "case_order": ["baseline", "trace"],
        "input": {
            "path": "input/coupon.inp",
            "sha256": deck_sha,
            "geometry_source_path": "../implicit-contact-point-trace-attempt01/input/implicit_point_trace.inp",
            "geometry_source_sha256": source_input_sha,
            "preserved_mesh_contract": "54 physical nodes, 12 C3D10 elements, upper/lower face contact pair from the pinned point-trace deck; witness tetra removed",
        },
        "inputs": {
            case: {"path": "input/coupon.inp", "sha256": deck_sha}
            for case in ("baseline", "trace")
        },
        "dependencies": {
            "reference_path": "../implicit-contact-free-impact-design-attempt01/parent-reference.json",
            "reference_sha256": REFERENCE_SHA256,
            "design_sha256": sha_bytes(design.encode()),
        },
        "pinned_sources": source_contract(),
        "units": {
            "length": "mm", "force": "N", "stress": "N/mm^2 (MPa)",
            "time": "s", "mass": "tonne", "energy": "N mm",
        },
        "geometry": {
            "physical_node_count": 54,
            "c3d10_element_count": 12,
            "upper_node_count": 27,
            "lower_node_count": 27,
            "controller_node": CONTROLLER,
            "controller_coordinate_mm": [1.0, 1.0, 1.0],
            "upper_nodes": list(UPPER_NODES),
            "lower_nodes": list(LOWER_NODES),
            "physical_nodes": list(PHYSICAL_NODES),
            "all_output_nodes": list(PHYSICAL_NODES + (CONTROLLER,)),
            "upper_element_set": "UPPER",
            "lower_element_set": "LOWER",
            "upper_elements": [1, 2, 3, 4, 5, 6],
            "lower_elements": [8, 9, 10, 11, 12, 13],
            "upper_element_faces": [[1, "S1"], [2, "S1"]],
            "lower_element_faces": [[11, "S3"], [12, "S3"]],
            "nsets": {
                "N_UPPER": list(UPPER_NODES),
                "N_LOWER": list(LOWER_NODES),
                "N_PHYSICAL": list(PHYSICAL_NODES),
                "N_ALL": list(PHYSICAL_NODES + (CONTROLLER,)),
                "Q_NODE": [CONTROLLER],
            },
        },
        "material_and_mass": {
            "youngs_modulus_N_per_mm2": 100000.0,
            "poisson_ratio": 0.0,
            "density_tonne_per_mm3": 0.125,
            "upper_volume_mm3": 8.0,
            "lower_volume_mm3": 8.0,
            "upper_mass_tonne": 1.0,
            "lower_mass_tonne": 1.0,
            "total_element_mass_tonne": 2.0,
            "expected_free_coordinate_projected_mass_tonne": 1.0,
            "mass_statement_scope": "The material mass is an input oracle; native MPC mass projection must be independently checked.",
        },
        "contact": {
            "slave_surface": "SLAVE",
            "master_surface": "MASTER",
            "pair_type": "SURFACE TO SURFACE",
            "pinned_internal_mode": 1,
            "law": "frictionless linear pressure-overclosure penalty",
            "friction_card": False,
            "initial_interface_plane_z_mm": 0.0,
            "initial_clearance_mm": 0.0,
            "initial_face_area_mm2": 4.0,
            "master_normal": [0.0, 0.0, 1.0],
            "normal_slope_N_per_mm3": 100000.0,
            "aggregate_linear_stiffness_N_per_mm": 400000.0,
            "signed_gap": "u3_upper - u3_lower; negative is compression, positive is open",
            "force_oracle": "CFN pair output should be +Z during compression, per prior shared-edge output evidence; scalar magnitude is k*max(-u3,0)",
            "stored_contact_energy_oracle": "0.5*k*min(u3,0)^2; zero once generated contact springs are filtered in open states",
        },
        "procedure": {
            "step": "one implicit NLGEOM *DYNAMIC,DIRECT step",
            "nmethod": 4,
            "alpha": 0.0,
            "beta": 0.25,
            "gamma": 0.5,
            "time_increment_s": 0.0001,
            "total_time_s": 0.007,
            "accepted_state_count": 70,
            "input_increment_count": 70,
            "direct_fixed_increment": True,
            "initial_conditions": {
                "displacement_u3_mm": 0.0,
                "velocity_u3_mm_per_s": -0.1,
                "initial_acceleration_mm_per_s2": 0.0,
                "velocity_applied_to": ["N_UPPER global DOF 3", "Q_NODE global DOF 3"],
            },
            "external_loads": [],
            "amplitudes": [],
            "damping": False,
        },
        "outputs": {
            "dat": {
                "node_set": "N_ALL", "node_count": 55,
                "fields": ["U", "V"], "frequency": 1,
            },
            "frd": {
                "node_set": "N_PHYSICAL", "node_count": 54,
                "fields": ["U", "V"], "frequency": 1,
                "controller_in_frd": False,
            },
            "element_print": {
                "frequency": 1, "totals_only": True,
                "fields": ["ELSE", "ELKE", "EMAS", "EVOL"],
                "sets": {"UPPER": [1, 2, 3, 4, 5, 6], "LOWER": [8, 9, 10, 11, 12, 13]},
            },
            "contact_print_total": {"frequency": 1, "totals_only": True, "fields": ["CELS"]},
            "contact_print_pair": {
                "frequency": 1, "slave_surface": "SLAVE", "master_surface": "MASTER",
                "fields": ["CFN"],
            },
            "accepted_identity": {
                "sta": "one accepted row for every step=1, increment=1..70, attempt=1, time=increment*0.0001 s",
                "cvg": "iterations join by step/increment/attempt; last converged row must agree with STA accepted iteration and trace event identity",
                "frd": "1PSTEP/100CL gives actual step/increment/time; join DAT tables by reported time",
                "reject_cutbacks_or_extra_or_missing_states": True,
            },
        },
        "reference": {
            "path": "../implicit-contact-free-impact-design-attempt01/parent-reference.json",
            "sha256": REFERENCE_SHA256,
            "schema": ref["schema"],
            "method": ref["recurrence"],
            "release_energy_identity": ref["release_energy_identity"],
            "mass_tonne": ref["mass_tonne"],
            "stiffness_N_per_mm": ref["spring_stiffness_N_mm"],
            "initial_velocity_mm_per_s": ref["initial_velocity_mm_s"],
            "initial_energy_Nmm": ref["initial_energy_Nmm"],
            "max_relative_energy_change": ref["max_relative_energy_change"],
            "states": ref["states"],
        },
        "event_checks": {
            "max_compression_increment": 25,
            "first_open_increment": 50,
            "last_increment": 70,
            "maximum_compression_mm": 0.00015810626598070757,
            "first_open_time_s": 0.005,
            "first_open_displacement_mm": 3.1069244162852196e-06,
            "first_open_velocity_mm_per_s": 0.10004280715081149,
            "release_energy_increase_Nmm": 4.2816313072023434e-06,
            "release_relative_energy_increase": 0.0008563262614455847,
        },
        "tolerances": {
            "displacement_abs_mm": 2.0e-8,
            "velocity_abs_mm_per_s": 2.0e-6,
            "kinetic_energy_abs_Nmm": 2.0e-7,
            "contact_energy_abs_Nmm": 2.0e-7,
            "contact_force_vector_abs_N": 1.0e-2,
            "mass_abs_tonne": 1.0e-8,
            "volume_abs_mm3": 1.0e-8,
            "solid_strain_energy_abs_Nmm": 1.0e-8,
            "time_abs_s": 1.0e-9,
            "trace_gap_abs_mm": 1.0e-8,
            "trace_pressure_abs_N_per_mm2": 1.0e-3,
            "trace_energy_abs_Nmm": 2.0e-7,
        },
        "trace_contract": {
            "record_phase_separation": ["CCXPT_MAP", "CCXPT_TRIAL"],
            "map_filter": "Every MAP raw_signed_gap>0 must have native_isol=0; record observed generated identities/counts without a point-count gate.",
            "trial_contract": "For numeric TRIAL records require finite fields, energy_enabled=1 and kscale=1; compare pressure=-K*corrected_gap/kscale and energy=0.5*K*area*corrected_gap^2/kscale, joined to state by step/increment/attempt and relative_time*0.007.",
            "accepted_compression_trial": "During active compression, aggregate TRIAL spring area should cover the interface and per-point signed pressure/energy must match the scalar law; use observed point area, never a hard-coded count.",
            "no_stale_open_trial_requirement": "Old-set positive-gap TRIAL rows are diagnostic; later regeneration removes positive-gap points, and accepted open states must have zero active contact. Any observed tensile TRIAL is not accepted-state force.",
            "cvg_contact_count": "Require positive active contact count during compressed accepted states and zero count once the accepted scalar displacement is open; do not impose an exact integration-point count.",
        },
        "limits": {
            "native_execution": False,
            "joint_acceptance": False,
            "model_acceptance": False,
            "scope": "One-coordinate C3D10 free-translation penalty-contact method fixture only; no current physical-pivot, general C3D10 MPC, joint, wood-bearing, or capacity acceptance.",
            "output_budget_bytes_each_case": 16777216,
        },
    }


def render_all() -> dict[str, bytes]:
    deck = render_input()
    design = render_design(sha_bytes(deck.encode()), REFERENCE_SHA256)
    expected = render_expected(deck, design)
    return {
        "input/coupon.inp": deck.encode(),
        "fixture-design.md": design.encode(),
        "expected.json": (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = render_all()
    if args.write:
        (HERE / "input").mkdir(parents=True, exist_ok=True)
        for relative, content in files.items():
            path = HERE / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    else:
        for relative, content in files.items():
            path = HERE / relative
            require(path.is_file() and path.read_bytes() == content,
                    f"Prepared file differs from source: {relative}")
    expected = json.loads(files["expected.json"])
    print(json.dumps({
        "status": "PASS_PREPARED_SOURCE_ONLY" if args.check else "WROTE_PREPARED_SOURCE_ONLY",
        "input_sha256": expected["input"]["sha256"],
        "expected_schema": expected["schema"],
        "reference_state_count": len(expected["reference"]["states"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
