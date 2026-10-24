"""Protect the separate vector output and immutable scalar reference."""

import copy
import runpy
from pathlib import Path

import pytest

from scripts import eoere_current_reference_review as current
from scripts import eoere_v8_analysis as analysis
from scripts import eoere_v8_checks as template


def test_vector_routing_reads_original_core_and_writes_only_its_own_output(tmp_path):
    review = tmp_path / "review"
    scalar, vector = review / "complete-v1", review / "vector-bound-v2"
    scalar.mkdir(parents=True)
    vector.mkdir()
    (scalar / "timber-sections-v1.json").write_text("immutable original scalar reference")
    source = """from pathlib import Path
BASE=OUT
core_location=BASE/'timber-net-geometry-v1.json'
s=max(rr['same_state_shear_bound_over_Fv'] for rr in comparison['regions'])
pins={}
for p,d in pins.items():assert sha(p)==d,p
with (BASE/'timber-sections-v1.json').open('x') as stream: stream.write(str(s))
"""
    method = runpy.run_path(str(current.ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-net-section.py"))
    refs = {"Fv_parallel": 1.2, "Fb": 6., "Ft_parallel": 4., "Fc_parallel": 9.}
    comparison = method["nominal_section"]([0, 20, 30, 1000, 0, 0],
        [{"bounds_uv_mm": [[0, 88.9], [0, 139.7]]}], refs)
    scope = {"OUT": vector, "comparison": comparison, "prop": {"refs": refs}, "sha": current.sha}
    public = current.ROOT / "docs/bolted-frame-development/owner-frame-v9/reference-review.json"
    with current.routes(analysis, review, public):
        code = template.source_hook(lambda path: source, Path("up15_timber_sections.py"), vector_bound=True)
        exec(compile(code, "vector_output_routing_control", "exec"), scope)  # noqa: S102 -- fixed numerical control
    assert scope["core_location"] == scalar / "timber-net-geometry-v1.json"
    assert (scalar / "timber-sections-v1.json").read_text() == "immutable original scalar reference"
    assert float((vector / "timber-sections-v1.json").read_text()) == pytest.approx(
        template.vector.section_upper(comparison, refs["Fv_parallel"]))


def test_path_adapter_cannot_change_references_or_silently_match_twice(tmp_path):
    public = current.ROOT / "docs/bolted-frame-development/owner-frame-v9/reference-review.json"
    with current.routes(analysis, tmp_path, public), pytest.raises(AssertionError):
        template.source_hook(lambda path: "BASE=OUT\nBASE=OUT", Path("up15_timber_sections.py"), vector_bound=True)


def test_changed_spacer_requires_new_nut_capture_and_shaft_interval():
    axis = {"id": "cleat", "hardware_scenario": {"washer_thickness_mm": 2.6416},
            "before_plate_mm": 0., "grip_mm": 127., "after_plate_mm": 6.35,
            "nut_side_spacer_mm": 25.4, "nominal_under_head_length_mm": 190.5}
    shaft = {"axis_id": "cleat", "shaft_interval_mm": [-2.6416, 200.5584],
             "ends": [{"end": "head", "pressure_face_s_mm": -2.6416},
                      {"end": "nut", "pressure_face_s_mm": 174.0916}]}
    field = {"source_inputs": {"shafts": [shaft]}}
    with pytest.raises(ValueError, match="own current head/nut capture"):
        current.verify_stack_windows({"axes": [axis]}, field)
    shaft["ends"][1]["pressure_face_s_mm"] = 161.3916
    with pytest.raises(ValueError):
        current.verify_stack_windows({"axes": [axis]}, field)
    shaft["shaft_interval_mm"][1] = 187.8584
    current.verify_stack_windows({"axes": [axis]}, field)


def test_containment_reuse_rejects_even_one_changed_finished_hole_or_profile():
    profiles = {f"timber_{i}": {"finished": {"path": f"solid_{i}", "sha256": str(i)},
                              "vertices": [[0, 0, 0], [1, 2, 3]]} for i in range(20)}
    previous, candidate = {"profiles": profiles}, {"profiles": copy.deepcopy(profiles)}
    core = {"rows": [{"member": name, "source": profile["finished"]} for name, profile in profiles.items()]}
    current.core_profiles_match(core, previous, candidate)
    candidate["profiles"]["timber_4"]["finished"]["sha256"] = "new hole"
    with pytest.raises(ValueError, match="fresh geometric evidence"):
        current.core_profiles_match(core, previous, candidate)
