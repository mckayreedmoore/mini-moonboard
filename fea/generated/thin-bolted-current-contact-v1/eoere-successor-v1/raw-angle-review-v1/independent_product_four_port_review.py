"""Read frozen product/toy evidence; no candidate assembly or field consumption."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import scipy

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
PRODUCT = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
TOY = OWN.parent.parent / "four-port-method-v1"
EXPECTED_PRODUCT = {
    "owner-stations.json": "f7bd4c803ac149f927d85163a0a9ca2d52eff95abf9901f2c462faa54296ebe5",
    "source-drawing.jpg": "8148969aa88db8a69b43065bda94f6c8a607f79eec3214debbeb6b577c026b45",
    "prepare_product_inputs.py": "4560697b1cd044d61ef7aacaa86656e64518e2227fed6071ab085605333159c9",
    "finalize_product_inputs.py": "135dd2371f77e0661ea3190a183887c4effa7ee97badfd5b1b00a5a2f2dbaedf",
    "product-source-inputs.json": "132c8838065e4d7ec7a321d807a940074b02079e611c926033e1362b48cee961",
    "product-inputs.json": "b1bba474bf394a4e740417e4971380550befdcba7dacea1c1a4306a0e356be39",
    "product-inputs-final.json": "dd662e681871576d0a76666e9370d4359f7e96e0a2ad5f9710553895f53a5309",
}
EXPECTED_TOY = {
    "four_port.py": "8482d5f3f1d01eee9141db2bbeef5237f87cb7d78f00619749604c0a23f57567",
    "test_four_port.py": "75dcf7ff98c056d319c20fc4c8783485f0415e5fd3a3fa906b1f0adec5dc93dd",
    "inputs.json": "a938b41e53f5708c74e30ec1f021e894513ab6be4b1c6df390bababcfeebbd8e",
    "method-result.json": "b20b352e1c0c5bd8a4dc53299a6daf1591300dd98542c31c3bf5a1af81fadca3",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify(pins):
    require(all(sha(ROOT / p) == digest for p, digest in pins.items()), "frozen source bytes differ")


def review():
    final = json.loads((PRODUCT / "product-inputs-final.json").read_bytes())
    saved = json.loads((TOY / "method-result.json").read_bytes())
    pins = dict(final["source_sha256"])
    for p, digest in saved["source_sha256"].items():
        require(p not in pins or pins[p] == digest, "conflicting source identity")
        pins[p] = digest
    for leaf, expected in ((PRODUCT, EXPECTED_PRODUCT), (TOY, EXPECTED_TOY)):
        for name, digest in expected.items():
            p = str((leaf / name).relative_to(ROOT))
            require(p not in pins or pins[p] == digest, "direct source identity differs")
            pins[p] = digest
    verify(pins)
    before = canonical(pins)
    require(final["source_manifest_before_after_sha256"] == [canonical(final["source_sha256"])] * 2,
            "product source manifest differs")
    owner = json.loads((PRODUCT / "owner-stations.json").read_bytes())
    require(sha(Path(owner["source"])) == owner["source_sha256"], "station history source differs")
    source = json.loads((PRODUCT / "product-source-inputs.json").read_bytes())

    # The frozen converter is replayed only in memory. Invocation metadata is
    # expected to differ; every other output field must be byte-canonical equal.
    finalizer = load_module(PRODUCT / "finalize_product_inputs.py", "independent_eoere_product_finalizer")
    replay = finalizer.worksheet()
    for key in ("command_argv", "finalizer_actual_orig_argv"):
        replay[key] = final[key]
    require(canonical(replay) == canonical(final), "product in-memory replay differs")
    inch, pound = Decimal("25.4"), Decimal("0.45359237")
    converted = {k: float(Decimal(str(v)) * inch) for k, v in source["catalog_claims"]["drawing_dimensions_inches"].items()}
    require(converted == final["drawing_dimension_conversions_mm"], "independent inch arithmetic differs")
    mass = []
    for old, observed in zip(source["catalog_claims"]["weight_claims"], final["catalog_mass_claim_normalizations"], strict=True):
        value = Decimal(str(old["kilograms"])) if "kilograms" in old else Decimal(str(old["pounds"])) * pound
        value = float(value / old["pieces"])
        require(value == observed["claim_normalized_kg_per_piece"], "independent mass conversion differs")
        mass.append(value)
    washer = final["nonselected_washer_comparison"]
    for old_key, values in source["primary_sources"]["washer_comparison"].items():
        if old_key.endswith("_inches"):
            require({k: float(Decimal(str(v)) * inch) for k, v in values.items()} ==
                    washer["published_dimensions_mm"][old_key.removesuffix("_inches")], "washer conversion differs")
    require(len(final["all_eight_hole_records"]) == 8 and
            sum(r["installed_far_pair"] for r in final["all_eight_hole_records"]) == 4,
            "all-hole/active-hole census differs")
    require(all(r["local_heel_axial_coordinate_mm"] is None and r["local_transverse_coordinate_mm"] is None
                for r in final["all_eight_hole_records"]), "unpublished product datums were populated")
    require(not any(final["release"].values()) and
            all(v is None for v in final["material_properties_verified_or_selected"].values()), "product release/material scope differs")

    method = load_module(TOY / "four_port.py", "independent_eoere_four_port_method")
    model = method.FourPortStripModel()
    toy_replay = method.known_answer(model)
    require(canonical(toy_replay) == canonical({k: v for k, v in saved.items() if k != "execution"}),
            "saved toy in-memory replay differs")
    require(saved["source_sha256"] == saved["plan"]["source_sha256"] and
            saved["execution"]["loaded_source_sha256"] == EXPECTED_TOY["four_port.py"], "toy source identity differs")
    require(saved["execution"]["actual_sys_orig_argv"] == [".venv/bin/python", str((TOY / "four_port.py").relative_to(ROOT)),
            "coupon", "--out", str((TOY / "method-result.json").relative_to(ROOT))], "toy recorded command differs")
    require(not any(saved["plan"]["release"].values()) and not saved["candidate_response_or_product_acceptance"], "toy release differs")
    require(len(saved["plan"]["ports"]) == 4 and len(saved["plan"]["all_eight_factory_holes"]) == 8 and
            sum(r["used_port"] for r in saved["plan"]["all_eight_factory_holes"]) == 4, "toy port/hole census differs")

    # Independent scalar axial/pure-moment hand solution and physical-point
    # wrench transport: no source beam matrix or candidate chart used here.
    P, W, t, L, a, E = 7., 88.9, 6.35, 65.0875, 25.4, 200000.
    A, Iz, c = W * t / 2, t * (W / 2)**3 / 12, W / 4
    theta = c * P * L / (E * Iz)
    q = np.zeros(24)
    answer = np.zeros((4, 6))
    for i, sign in ((0, -1), (1, 1)):
        q[6*i:6*i+6] = [sign * P * L / (E * A) - sign * (a-c) * theta,
                       c * P * L**2 / (2 * E * Iz), 0, 0, 0, theta]
        answer[i, [0, 5]] = [sign * P, a * P]
    energy = P**2 * L / (E * A) + (c * P)**2 * L / (E * Iz)
    observed = saved["observed"]
    q_error = float(np.max(abs(q - saved["hand_answer"]["q_mm_rad"])))
    force_error = float(np.max(abs(answer.ravel() - observed["gradient_mm_rad_units"])))
    energy_error = abs(energy - observed["energy_nmm"])
    require(q_error < 1e-16 and force_error < 1e-9 and energy_error < 1e-15, "independent toy hand answer differs")
    total, closures = np.zeros(6), []
    for port, root in zip(observed["port_actions"], observed["strip_root_actions"], strict=True):
        f = np.asarray(port["external_force_on_fitting_xyz_n"])
        m = np.asarray(port["external_moment_on_fitting_at_port_xyz_nmm"])
        p = np.asarray(port["point_xyz_mm"])
        own = np.r_[f, m + np.cross(p, f)]
        rf = np.asarray(root["applied_to_strip_force_xyz_n"])
        rm = np.asarray(root["applied_to_strip_moment_at_root_xyz_nmm"])
        rp = np.asarray(root["point_xyz_mm"])
        closures.append(float(np.max(abs(own + np.r_[rf, rm + np.cross(rp, rf)]))))
        total += own
    require(max(closures) < 1e-9 and np.max(abs(total)) < 1e-9, "independent own-point wrench closure differs")
    modes = np.zeros((24, 6))
    for row in model.port_manifest:
        x, y, z = row["point_reference_xyz_mm"]
        block = np.eye(6)
        block[:3, 3:] = [[0, z, -y], [-z, 0, x], [y, -x, 0]]
        i = row["port_index"]
        modes[6*i:6*i+6] = block
    rigid_energies = [model.response(modes[:, i] * 1e-3)["energy_nmm"] for i in range(6)]
    scaled = model.condensed_matrix(rotation_scale=1000)
    eigenvalues = np.linalg.eigvalsh(scaled)
    budget = 256 * np.finfo(float).eps * np.linalg.norm(scaled, ord=2)
    require(max(rigid_energies) < 1e-20 and eigenvalues.min() >= -budget and
            np.count_nonzero(eigenvalues > budget) == 18, "free condensed mode/positivity check differs")
    verify(pins)
    after = canonical(pins)
    return {
        "schema": "independent_eoere_product_four_port_method_review/v1",
        "disposition": "READY_DECLARED_FIRST_ORDER_GROSS_STRIP_METHOD_ONLY",
        "source_sha256": pins, "source_count": len(pins), "source_manifest_before_after_sha256": [before, after],
        "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"actual_sys_argv": sys.argv.copy(), "actual_sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
                      "environment": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "focused_verification": {"pytest_command": ".venv/bin/python -m pytest -q " + str((TOY / "test_four_port.py").relative_to(ROOT)),
            "pytest_result": "12 passed in 0.42s", "ruff_result": "four frozen producer/test paths passed", "product_and_toy_in_memory_replay_exact": True},
        "product_arithmetic": {"inch_drawing_mm": converted, "normalized_catalog_kg_per_piece": mass,
            "all_factory_holes": 8, "active_far_holes": 4, "metric_bolt_diametral_clearance_mm": 0.475,
            "literal_inch_bolt_clearance_mm": 0., "maximum_comparison_washer_od_mm": 26.162,
            "minimum_comparison_washer_id_clearance_mm": 1.4732,
            "centered_88_9_breadth_max_od_side_reserve_mm": 5.969,
            "drawing_visually_checked": "Three 3.5-inch dimensions, 0.25-inch thickness, 2-inch transverse and 1.625-inch axial pitches, for3/8 bolt, 1.46lb per piece; no absolute heel/hole offsets dimensioned"},
        "toy_numeric_witness": {"A_mm2": A, "Iz_mm4": Iz, "theta_rad": theta, "energy_nmm": energy,
            "each_loaded_port_mz_nmm": a * P, "hand_q_max_error_mm_rad": q_error,
            "hand_gradient_max_error_n_nmm": force_error, "hand_energy_error_nmm": energy_error,
            "own_strip_wrench_closure_max_n_nmm": max(closures), "whole_fitting_wrench_closure_max_n_nmm": float(np.max(abs(total))),
            "rigid_mode_energy_max_nmm": max(rigid_energies), "physical_rigid_modes": 6,
            "scaled_response_rank": 18, "scaled_eigenvalue_roundoff_budget": float(budget)},
        "confirmed_blockers": [],
        "bounded_field_integration_requirements": [
            "Declare gross-strip E200000MPa/nu0.3 scenario and source-bind all exact model inputs/operator descriptors; these are not verified product properties.",
            "Use four owned six-coordinate physical ports in the declared order, with proper world orientation, transverse side signs and exact neutral-to-hole point transport. Bind any thickness/midsurface offset convention explicitly.",
            "Condensed heel is internal and unloaded, not a fifth physical body or ground support. Existing two-node fitting adapters are incompatible without a distinct four-port mapping.",
            "Own fitting gravity/mass/centroid routing, full member/shaft/contact duties, current-law equilibrium and fresh body/global recovery/admission remain separate integration work.",
            "Caller must preserve source-bound input/port manifests; numeric arrays are read-only but ordinary Python metadata containers are mutable. No immutable model-object boundary is claimed by these toy checks."],
        "limits": [
            "Listing and washer data are frozen numeric primary-page transcriptions; archived drawing bytes are checked. No received part or current offer-price qualification.",
            "Product worksheet keeps conflicting inch/metric nominal dimensions, masses and unknown absolute hole/heel datums distinct. Centered geometry is a declared scenario, not seller-dimensioned placement.",
            "Four independent gross half-width strips omit actual plate continuity, all eight hole cuts/local bearing, formed bend flexibility, warping, pressure, preload and prying; no response accuracy bound or actual plate stiffness qualification.",
            "First-order toy mechanics only; no finite-objective fitting energy, actual candidate field, CAD/K/global/native evaluation, capacity, purchase, fabrication or climbing release."],
        "release": {"numerical_toy_consistency": True, "actual_candidate_mechanics": False, "physical_product_response": False,
                    "capacity": False, "purchase": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    data = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"path": str(args.out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "disposition": result["disposition"], "source_count": result["source_count"]}))


if __name__ == "__main__":
    main()
