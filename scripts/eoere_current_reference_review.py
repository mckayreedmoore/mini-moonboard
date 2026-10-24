"""Route immutable reference/bracing formulas to one admitted candidate bank.

The candidate analysis module must supply its own checked geometry/readiness
and six independently replayed fields. Historical forces cannot satisfy this
intake. All numerical formulas remain in issued helpers. The separate vector
output path corrects the preserved v8 routing stop without changing a result,
strength reference or numerical gate.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib
import inspect
import math
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import eoere_v8_bracing_review as bracing
from scripts import eoere_v8_checks as template
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
HELPERS = {
    Path(template.__file__).resolve(): "95c173c3cc03254ce47e12ccaa5b6cdba06e7a62a31cc22ccbf253ecc1b61fb6",
    Path(bracing.__file__).resolve(): "fd307925205015389b0d5f99669446e6358d0dc8f9c0cfccb92e420c101fd8d5",
    Path(template.vector.__file__).resolve(): "ae1e9df7e1b9e084a5b1e59a343672f05657c7421e8cc46ed7054b39e8f45acd",
}
V8_CORE_SHA = "0fbfd368dfd52605f69f36c1c64212d90b2c4d1f0d7b05ca6617d9d4dd608372"
require = bracing.require


def verify_stack_windows(geometry, field):
    """Detect stale capture positions even when an axis line is unchanged."""
    axes = {axis["id"]: axis for axis in geometry["axes"]}
    for shaft in field["source_inputs"]["shafts"]:
        axis = axes[shaft["axis_id"]]
        washer = axis["hardware_scenario"]["washer_thickness_mm"]
        head = -axis["before_plate_mm"] - washer
        nut = axis["grip_mm"] + axis["after_plate_mm"] + axis.get("nut_side_spacer_mm", 0.) + washer
        ends = {end["end"]: end for end in shaft["ends"]}
        expected = ((ends["head"]["pressure_face_s_mm"], head),
                    (ends["nut"]["pressure_face_s_mm"], nut),
                    (shaft["shaft_interval_mm"][0], head),
                    (shaft["shaft_interval_mm"][1], head + axis["nominal_under_head_length_mm"]))
        require(all(math.isclose(actual, target, rel_tol=0, abs_tol=1e-7) for actual, target in expected),
                "own current head/nut capture and full shaft interval required: " + shaft["axis_id"])


class CurrentIntake:
    def __init__(self, bindings, analysis):
        self.bindings, self.analysis = bindings, analysis
        self.captured = {}

    def load(self):
        analysis, bindings = self.analysis, self.bindings
        pins = {ref(OWN)["path"]: sha(OWN)}
        for path, digest in HELPERS.items():
            require(sha(path) == digest, "preserve issued reference helper: " + str(path))
            pins[ref(path)["path"]] = digest
        ready = read(analysis.BASE / "adapter-readiness.json", pins)
        require(ready["producer"] == ref(analysis.OWN), "own analysis producer required")
        for name in ("receipt", "physical_geometry", "physical_clearance"):
            require(ready[name] == bindings[name], "own prepared candidate differs: " + name)
        require(ready["load_contract"] == {"weight_lb": 250, "downward_multiplier": 2,
                "horizontal_force_N": 300, "accessory_mass_kg": 25, "duration_factor_CD": 1},
                "owner load contract required")
        expected = {"analysis_geometry": analysis.BASE / "geometry/geometry.json",
                    "material": analysis.BASE / "material.json",
                    "inputs": analysis.BASE / "four-hosts/preparation/inputs.json",
                    "method_readiness": analysis.BASE / "readiness.json"}
        for name, path in expected.items():
            require(ready[name] == ref(path), "own prepared path/hash differs: " + name)
            read(path, pins, ready[name]["sha256"])
        for path, digest in ready["source_sha256"].items():
            require(sha(path) == digest, "prepared source changed: " + path)
            pins[path] = digest
        geometry = read(expected["analysis_geometry"], pins)
        material = read(expected["material"], pins)
        require(geometry["revision"] == analysis.REVISION
                and geometry["parent_owner_geometry"] == bindings["physical_geometry"]
                and geometry["perfect_bond_analysis"] is True,
                "own current analytical/physical geometry join required")
        require(len(geometry["axes"]) == 96 and len(geometry["screw_axes"]) == 66
                and material["physical_qualification"] is False,
                "current conditional 96-bolt/66-screw inventory required")
        fields = []
        run = analysis.BASE / "four-hosts"
        for case in CASES:
            folder = run / case
            field = read(folder / "field.json", pins)
            replay = read(folder / "independent-replay.json", pins)
            plywood = read(folder / "independent-replay-plywood.json", pins)
            binding = ref(folder / "field.json")
            require(field["case_id"] == case, "own case identity required")
            bracing.admit_field(field, replay, plywood, binding,
                                ref(expected["analysis_geometry"]), ref(expected["material"]))
            require(field["source_inputs"]["scenario"]["perfect_bond_analysis"]["physical_parent"]
                    == bindings["physical_geometry"], "own field physical parent required")
            verify_stack_windows(geometry, field)
            fields.append(("nominal", case, binding, field))
        pins.update(bindings["source_sha256"])
        self.captured = {"prepared_readiness": ref(analysis.BASE / "adapter-readiness.json"),
                         "analysis_geometry": ref(expected["analysis_geometry"]),
                         "material": ref(expected["material"]), "fields": [row[2] for row in fields]}
        return geometry, fields, pins


def core_profiles_match(core, previous, current):
    names = [row["member"] for row in core["rows"]]
    require(len(names) == len(set(names)) == 20, "exact twenty-member core census required")
    for row in core["rows"]:
        name = row["member"]
        require(previous["profiles"][name] == current["profiles"][name],
                "changed timber profile requires fresh geometric evidence: " + name)
        require(row["source"] == current["profiles"][name]["finished"],
                "reused core must refer to the identical finished solid: " + name)


def reuse_cores(analysis, review, bindings):
    """Reuse all-interval containment only for byte-identical timber profiles."""
    geometry, fields, active = CurrentIntake(bindings, analysis).load()
    source = analysis.WORK / "owner-inward-angles-v8/analysis-v1/reference-review-v1/complete-v1/timber-net-geometry-v1.json"
    pins = {}
    core = read(source, pins, V8_CORE_SHA)
    previous = read(core["geometry"]["path"], pins, core["geometry"]["sha256"])
    core_profiles_match(core, previous, geometry)
    require({row["member"] for row in core["rows"]} == {
        row["name"] for row in fields[0][3]["source_inputs"]["timber_rows"]
        if not row["name"].startswith("eoere_cleat_")}, "own current sawn inventory required")
    for path, digest in core["source_sha256"].items():
        require(sha(path) == digest, "original containment source changed: " + path)
    for row in core["rows"]:
        require(ref(row["source"]["path"]) == row["source"], "finished solid changed")
    core["source_sha256"].update({**active, **pins})
    core["geometric_evidence_reuse"] = {
        "producer": ref(OWN), "original_containment": ref(source), "previous_geometry": core["geometry"],
        "identical_complete_sawn_profiles": True, "profile_count": 20,
        "hole_bands_ligaments_and_full_interval_containment_unchanged": True,
        "force_or_strength_result_transferred": False, "new_CAD_query_or_rebuild": False}
    core["geometry"] = ref(analysis.BASE / "geometry/geometry.json")
    destination = review / "complete-v1"
    destination.mkdir(parents=True, exist_ok=True)
    template.write_new(destination / "timber-net-geometry-v1.json", core)
    template.write_new(destination / "geometry.current-intake.json", {
        "schema": "eoere_identical_timber_containment_reuse/v1", "producer": ref(OWN),
        "geometry_revision": analysis.PHYSICAL_REVISION, **bindings,
        "result": ref(destination / "timber-net-geometry-v1.json"),
        "reused_evidence": core["geometric_evidence_reuse"], "structural_acceptance": False})
    print(ref(destination / "geometry.current-intake.json"), flush=True)


@contextmanager
def routes(analysis, review, public):
    """Bind paths/intake only; keep both formula helpers immutable."""
    complete, vector = review / "complete-v1", review / "vector-bound-v2"
    old_hook, old_replace = template.source_hook, template.issued.replace

    def source_hook(path_intake, path, *args, **kwargs):
        code = old_hook(path_intake, path, *args, **kwargs)
        if kwargs.get("vector_bound") and path.name == "up15_timber_sections.py":
            code = old_replace(code, "with (BASE/'timber-sections-v1.json').open('x')",
                               f"with (Path({str(vector)!r})/'timber-sections-v1.json').open('x')")
        return code

    def replace(code, before, after):
        if before == "owner-principal-pairs-v6/analysis-v1/material.json" \
                and after == "owner-inward-angles-v8/analysis-v1/material.json":
            after = str(analysis.BASE.relative_to(analysis.WORK) / "material.json")
        return old_replace(code, before, after)

    with ExitStack() as stack:
        for name, value in {"OWN": OWN, "analysis": analysis, "GEOMETRY": analysis.BASE / "geometry/geometry.json",
                            "RUN": analysis.BASE / "four-hosts", "REVIEW": review, "OUT": complete,
                            "VECTOR_OUT": vector, "source_hook": source_hook,
                            "Intake": lambda bindings: CurrentIntake(bindings, analysis)}.items():
            stack.enter_context(patch.object(template, name, value))
        stack.enter_context(patch.object(template.issued, "replace", replace))
        for name, value in {"OWN": OWN, "analysis": analysis, "GEOMETRY": analysis.BASE / "geometry/geometry.json",
                            "MATERIAL": analysis.BASE / "material.json", "RUN": analysis.BASE / "four-hosts",
                            "Intake": lambda bindings: CurrentIntake(bindings, analysis)}.items():
            stack.enter_context(patch.object(bracing, name, value))
        source = inspect.getsource(template.report)
        source = old_replace(source, "eoere_v8_conventional_reference_review/v1",
                             "eoere_current_conventional_reference_review/v1")
        source = old_replace(source, "docs/bolted-frame-development/owner-frame-v8",
                             str(public.parent.relative_to(ROOT)))
        source = old_replace(source, "this review is tied to the frozen v8 hardware",
                             "this review is tied to this frozen candidate's hardware")
        scope = dict(vars(template))
        exec(compile(source, str(OWN), "exec"), scope)  # noqa: S102 -- only schema and public destination routing
        yield scope["report"]


def summarize_bracing(analysis, out, public, bindings, reference):
    data = read(out / "result.json", {})
    receipt = read(out / "candidate-intake.json", {})
    require(receipt["physical_geometry"] == bindings["physical_geometry"], "own bracing physical join required")
    require(data["geometry"] == ref(analysis.BASE / "geometry/geometry.json"), "own bracing analysis join required")
    for path, digest in data["source_sha256"].items():
        require(sha(path) == digest, "bracing source changed: " + path)
    require(len(data["cases"]) == 6 and {c["case_id"] for c in data["cases"]} == set(CASES),
            "all six own bracing states required")
    probes = [{"case_id": case["case_id"], **probe} for case in data["cases"] for probe in case["probes"]]
    require(len(probes) == 72, "all 72 current bracing comparisons required")
    modes = {probe["mode"] for probe in probes}
    audits = [audit for case in data["cases"] for audit in case["audits"].values()]
    result = {"schema": "eoere_current_panel_bracing_summary/v1", "producer": ref(OWN),
              "geometry_revision": analysis.PHYSICAL_REVISION, "physical_geometry": bindings["receipt"],
              "analysis_geometry": data["geometry"], "case_ids": list(CASES), "case_count": 6,
              "source_bindings": {"raw_result": ref(out / "result.json"), "candidate_intake": ref(out / "candidate-intake.json"),
                                  "reference_review": ref(reference), "method": ref(bracing.METHOD_PATH)},
              "tools": data["tools"], "controls": data["controls"],
              "all_six_case_ranges": {mode: {"minimum": min((p for p in probes if p["mode"] == mode),
                                                            key=lambda p: p["modeled_stiffness_ratio"]),
                                             "maximum": max((p for p in probes if p["mode"] == mode),
                                                            key=lambda p: p["modeled_stiffness_ratio"])} for mode in sorted(modes)},
              "probes": probes,
              "numerical_checks": {key: max(a[key] for a in audits) for key in (
                  "maximum_relative_equilibrium_error", "maximum_relative_binary64_equilibrium_error",
                  "maximum_normalized_reciprocity_error")},
              "inventory": {"corners": 2, "probe_comparisons": 72, "factorizations": 12,
                            "balanced_rhs_solves": 144, "panels_removed": 6, "screw_springs_removed": 66},
              "model_assumptions": {"Hillman_axial_N_per_mm": 1000., "Hillman_lateral_N_per_mm": 1000.,
                                    "physical_Hillman_law_qualified": False, "panel_contact_N_per_mm3": 2.,
                                    "contact_branches_frozen_at_braced_state": True},
              "literature_review": ref(analysis.WORK / "owner-principal-pairs-v6/analysis-v1/panel-bracing-review-v1/literature-review.json"),
              "stiffness_comparison_only": True, "strength_gain_factor": None,
              "new_unbraced_climber_load_equilibrium": False, "double_strength_credit_applied": False,
              "compression_capacity_or_buckling_gain_established": False,
              "limits": data["limits"], "structural_acceptance": False,
              "fabrication_released": False, "climbing_released": False}
    template.write_new(public, result)
    print(ref(public), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=(*template.KINDS, "bracing", "bracing-report"))
    parser.add_argument("--analysis-module", choices=("scripts.eoere_v8_analysis", "scripts.eoere_v9_analysis"), required=True)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--physical-sha256", required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--bracing-out", type=Path)
    parser.add_argument("--public-folder", type=Path, required=True)
    args = parser.parse_args()
    analysis = importlib.import_module(args.analysis_module)
    review = (args.review or analysis.BASE / "reference-review-v1").resolve()
    out = (args.bracing_out or analysis.BASE / "panel-bracing-review-v1").resolve()
    public = args.public_folder.resolve() / "reference-review.json"
    require(review.is_relative_to(analysis.BASE) and out.is_relative_to(analysis.BASE), "own ignored candidate packet required")
    require(public.parent.parent == ROOT / "docs/bolted-frame-development", "own public development packet required")
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        bindings = analysis.context(args.receipt_sha256, args.physical_sha256)
        with routes(analysis, review, public) as report:
            if args.kind == "report":
                report(bindings, public)
            elif args.kind == "bracing":
                # The issued v8 adapter expects previous.HOSTS. Normalize that
                # interface only; floor host selection remains the issued set.
                bridge = SimpleNamespace(**vars(analysis))
                bridge.previous = SimpleNamespace(HOSTS=template.issued.analysis.HOSTS)
                with patch.object(bracing, "analysis", bridge):
                    bracing.run(out, bindings)
            elif args.kind == "bracing-report":
                summarize_bracing(analysis, out, public.parent / "panel-bracing-review.json", bindings, public)
            elif args.kind == "geometry" and args.analysis_module == "scripts.eoere_v9_analysis":
                reuse_cores(analysis, review, bindings)
            else:
                template.execute(args.kind, bindings)


if __name__ == "__main__":
    main()
