"""Independent byte, census, coordinate and final-browser audit; no CAD imports."""
import copy
import gzip
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
RAW = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/2026-adjustments-v10")
OUT = Path(__file__).resolve().parent
EXPECTED = {"occupied-adjusted-base-v3.json": "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7",
            "occupied-2026-adjustments-v3.json": "5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134"}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_bytes())

def near(first, second):
    assert len(first) == len(second)
    # Saved OCCT bounds carry its nominal 1e-7-mm bounding tolerance.
    assert max(abs(a-b) for a,b in zip(first,second)) < 1e-6

def binding(path, expected):
    assert digest(path) == expected, str(path)

def no_release(record):
    assert record["mechanics_ready"] is False
    assert set(record["release"]) == {"candidate_accepted", "complete_joint_acceptance", "capacity_established",
        "fabrication_released", "structural_released", "climbing_released"}
    assert all(value is False for value in record["release"].values())

source = read(DOC / "occupied-aligned-wire-v1.json")
base = read(DOC / "occupied-adjusted-base-v3.json")
extra = read(DOC / "occupied-2026-adjustments-v3.json")
pairs = []
for report, raw, scene in [("occupied-adjusted-base-v3.json", RAW/"base", "eoere-adjusted-base-v3-scene.json.gz"),
                           ("occupied-2026-adjustments-v3.json", RAW, "eoere-2026-adjustments-v3-scene.json.gz")]:
    binding(DOC/report, EXPECTED[report])
    assert (DOC/report).read_bytes() == (raw/"geometry.json").read_bytes()
    assert (Path("site")/scene).read_bytes() == (raw/"scene.json.gz").read_bytes()
    assert gzip.decompress((Path("site")/scene).read_bytes()) == (raw/"scene.json").read_bytes()
    record = read(DOC/report)
    for name, sha in record["source_sha256"].items():
        binding(name, sha)
    for solid in record["changed_finished_solids"]:
        binding(solid["path"], solid["sha256"])
    no_release(record)
    assert all(not hits for hits in record["collisions"].values())
    pairs.append({"report": str(DOC/report), "raw_report": str(raw/"geometry.json"), "layout_sha256": digest(DOC/report),
                  "scene": "site/"+scene, "raw_scene": str(raw/"scene.json.gz"),
                  "compressed_sha256": digest(Path("site")/scene),
                  "decoded_sha256": digest(raw/"scene.json"), "source_pins_verified": len(record["source_sha256"]),
                  "saved_solids_verified": len(record["changed_finished_solids"])})
assert (RAW/"driver.py.snapshot").read_bytes() == Path("scripts/eoere_2026_adjustments.py").read_bytes()

# Derive the moved-duty closure independently from the preserved axes.
duties = {a["duty_id"] for axis in source["axes"] if "base_principal_center_right" in axis["receivers"]
          for a in axis["attachments"]}
while True:
    additions = {a["duty_id"] for axis in source["axes"]
                 if any(a["duty_id"] in duties for a in axis["attachments"]) for a in axis["attachments"]}
    if additions <= duties:
        break
    duties |= additions
assert set(base["affected_duties"]) == duties and len(duties) == 6
expected_axes = {axis["id"] for axis in source["axes"] if any(a["duty_id"] in duties for a in axis["attachments"])}
assert set(base["moved_bolt_axes"]) == expected_axes and len(expected_axes) == 22
assert len(base["axes"]) == len(source["axes"]) == 100
original_axes = {axis["id"]: axis for axis in source["axes"]}
for axis in base["axes"]:
    expected = copy.deepcopy(original_axes[axis["id"]])
    if axis["id"] in expected_axes:
        expected["point_xyz_mm"][0] -= 39.2
        for attachment in expected["attachments"]:
            attachment["point"][0] -= 39.2
            direction = attachment["direction"]
            first = next(value for value in direction if abs(value) > 1e-8)
            delta = -39.2 * direction[0] * (1 if first > 0 else -1) / math.sqrt(sum(v*v for v in direction))
            attachment["interval_mm"] = [v + delta for v in attachment["interval_mm"]]
    assert axis == expected, axis["id"]
expected_screws = {s["axis_id"] for s in source["screw_axes"] if s["receiver"] in
                   {"base_principal_center_right", "base_post_center_right"}}
assert set(base["moved_panel_screw_axes"]) == expected_screws and len(expected_screws) == 10
assert len(base["screw_axes"]) == len(source["screw_axes"]) == 66
original_screws = {s["axis_id"]: s for s in source["screw_axes"]}
for screw in base["screw_axes"]:
    expected = copy.deepcopy(original_screws[screw["axis_id"]])
    if screw["axis_id"] in expected_screws:
        expected["origin_xyz_mm"][0] -= 39.2
    assert screw == expected, screw["axis_id"]
assert extra["bolt_axes_unchanged_sha256"] == hashlib.sha256(json.dumps(base["axes"], sort_keys=True).encode()).hexdigest()
assert extra["screw_axes_unchanged_sha256"] == hashlib.sha256(json.dumps(base["screw_axes"], sort_keys=True).encode()).hexdigest()
assert len(base["extended_rails"]) == 3 and len(base["canonical_interval_checks"]) == 12
for row in base["canonical_interval_checks"]:
    near(row["canonical_interval_mm"], row["saved_receiver_x_bounds_mm"])
    near(row["canonical_interval_mm"], [11.75,49.85])
assert all(r["distance_mm"] < 1e-5 and r["intersection_mm3"] < .01 for r in base["restored_contacts"])
assert all(r["full_body_fraction"] > .999999 for r in base["screw_support"])
assert all(r["after_fraction"] > .999999 for r in extra["screw_backing"])
assert base["retained_service_bodies_audited"] == extra["retained_service_bodies_audited"] == 405
assert set(extra["retained_services_checked_timber_ids"]) == set(extra["changed_timber_ids"]) | {
    s["id"] for s in base["changed_finished_solids"] if s["kind"] == "timber"}

base_patch = read(RAW/"base/scene.json")
extra_patch = read(RAW/"scene.json")
assert len(base_patch["replacements"]) == 136
assert Counter(r["fabrication"]["kind"] for r in base_patch["replacements"]) == {
    "timber": 7, "panel": 3, "bracket": 6, "bolt": 110, "screw": 10}
assert set(r["name"] for r in base_patch["replacements"]) == set(s["id"] for s in base["changed_finished_solids"])
assert set(r["name"] for r in extra_patch["replacements"]) == set(s["id"] for s in extra["changed_finished_solids"])
assert len(extra_patch["replacements"]) == 23 and len(extra_patch["additions"]) == 359
assert Counter(r["fabrication"]["kind"] for r in extra_patch["additions"]) == {"light":120,"tnut":120,"wire":119}
assert base_patch["counts"]["total_visible_parts"] == 1021 and extra_patch["counts"]["total_visible_parts"] == 1380
assert extra_patch["unofficial_2026_positions"] is True and extra["all_midpoints_are_assumed_not_confirmed"] is True
assert base["unofficial_2026_grid_included"] is False and extra["original_grid_retained"] is True
assert len(extra["grid"]) == 120 and len(extra["new_wire_routes"]) == 119 and len(extra["rerouted_original_wire_links"]) == 10
for patch in [base_patch, extra_patch]:
    no_release(patch)
    assert patch["design"]["qualified_for_design"] is False

mesh_path = OUT/"independent-actual-mesh-check-v1.json"
mesh = read(mesh_path)
assert mesh["passed"] is True and mesh["visible_parts"] == 1380 and mesh["unchanged_parts"] == 998
assert mesh["red_revision_parts"] == [] and len(mesh["rejected_controls"]) == 7
for name, sha in mesh["source_sha256"].items():
    binding(name, sha)
producer_mesh_path = RAW/"actual-mesh-check-v1.json"
assert mesh == read(producer_mesh_path)

browser_path = RAW/"browser-v1/result.json"
browser = read(browser_path)
assert browser["passed"] is True and browser["page_errors"] == browser["failed_requests_or_responses"] == []
assert browser["update_toggle_on_off_on"] is True and browser["preserved_option_navigation"] is True
assert browser["page_context_code_evaluation"] is False and browser["mechanics_or_physical_release"] is False
assert [r["view"] for r in browser["results"]] == ["front", "rear"]
for name, sha in browser["source_sha256"].items():
    binding(name, sha)
binding(browser["shared_runner"]["path"], browser["shared_runner"]["sha256"])
screenshots = []
for row in browser["results"]:
    binding(row["screenshot"]["path"], row["screenshot"]["sha256"])
    assert row["index_html_sha256"] == digest("site/index.html")
    screenshots.append(row["screenshot"])
off = RAW/"browser-v1/adjusted-base-2026-off.png"
assert off.exists()
screenshots.append({"path":str(off), "sha256":digest(off), "binding":"independent audit of producer OFF screenshot"})

# Freeze the exact reviewed sources; recheck all pins at closure.
sources = {str(path):digest(path) for path in [Path(__file__), Path("scripts/check_eoere_2026_adjustments.mjs"),
    Path("scripts/check_eoere_2026_browser.cjs"), Path("scripts/eoere_2026_adjustments.py"), Path("site/index.html"),
    Path("site/eoere-2026-adjustments-overlay.mjs"), mesh_path, producer_mesh_path, browser_path]}
for record in [base,extra]:
    for name, sha in record["source_sha256"].items():
        binding(name,sha)
receipt = {"schema":"eoere_frozen_v3_independent_verification/v1", "passed":True,
    "substantial_findings":[], "raw_published_pairs":pairs, "source_sha256":sources,
    "base_replacements":136,"base_visible_parts":1021,"extra_visible_parts":1380,"affected_duties":6,
    "moved_bolt_stacks":22,"moved_Hillman_axes":10,"retained_bolt_axes":100,"retained_Hillman_axes":66,
    "coordinate_and_attachment_metadata_verified":True,"optional_axes_preserved":True,
    "browser_evidence_reused":True,"screenshots":screenshots,
    "actual_mesh_check_rejected_controls":mesh["rejected_controls"],"base_missing_replacement_control_rejected":True,
    "no_CAD_rebuild_native_solve_or_materialization":True,"mechanics_or_physical_release":False,
    "limits":["Hashes and receipts bind nominal geometry; no structural, tooling, tolerance or actual-build acceptance.",
              "Front, rear and OFF screenshots are existing producer captures; no browser recapture performed."]}
with (OUT/"verification-result-v1.json").open("x") as handle:
    handle.write(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({"passed":True,"receipt":str(OUT/"verification-result-v1.json"),"receipt_sha256":digest(OUT/"verification-result-v1.json")}))
