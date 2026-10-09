"""Bind applicable retained v3 interval proof. No CAD imports or query rerun."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
REVIEW = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-review-v1/current-geometry-followups-v1/testing")
V3 = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/2026-adjustments-v3-review-v1")
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
SELF = Path(__file__).resolve().relative_to(ROOT)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


prior_path = REVIEW/"result-v1.json"
prior = read(prior_path)
base_path = DOC/"occupied-adjusted-base-v3.json"
base = read(base_path)
audit_path = DOC/"bounded-strength-v1/revised-base-audit-v1/verification.json"
audit = read(audit_path)
correctness_path = V3/"correctness/receipt.json"
correctness = read(correctness_path)
summary_path = V3/"correctness/review.json"
summary = read(summary_path)
assert sha(base_path) == "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7"
assert base["revision"] == "eoere-midpoint-ready-frame-v3"
assert base["unofficial_2026_grid_included"] is False
assert correctness["reviewed_sha256"][str(base_path)] == sha(base_path)
for path, expected in summary["receipt_bindings"].items():
    assert sha(path) == expected, path
for path, expected in correctness["source_sha256"].items():
    assert sha(path) == expected, path
for path, expected in prior["source_sha256"].items():
    assert sha(path) == expected, path
checks = correctness["checks"]
assert checks["metadata"]["canonical_shifted_ports"] == 24
assert checks["factory_and_shafts"]["raw_port_intervals"] == 24
assert checks["factory_and_shafts"]["maximum_interval_error_mm"] < 1e-6
rows = base["canonical_interval_checks"]
assert len(rows) == 12
assert len({(row["axis_id"], row["duty_id"]) for row in rows}) == 12
axes = {row["id"]: row for row in base["axes"]}
errors = []
for row in rows:
    assert all(abs(value-target) < 1e-6 for value, target in zip(row["canonical_interval_mm"], [11.75, 49.85]))
    errors.extend(abs(a-b) for a,b in zip(row["canonical_interval_mm"], row["saved_receiver_x_bounds_mm"]))
    matching = [attachment for attachment in axes[row["axis_id"]]["attachments"] if attachment["duty_id"] == row["duty_id"] and attachment["receiver"] in {"base_principal_center_right", "base_post_center_right"}]
    assert len(matching) == 1 and matching[0]["interval_mm"] == row["canonical_interval_mm"]
assert abs(max(errors)-audit["checks"]["maximum_interval_bbox_error_mm"]) < 1e-12
files = [SELF, prior_path, base_path, audit_path, correctness_path, summary_path,
         V3/"correctness/review.py", V3/"verification/verify_frozen_v3.py", V3/"verification/verification-result-v1.json"]
bindings = {str(path): sha(path) for path in files}
receipt = {"schema": "eoere_revised_base_testing_interval_reuse_supplement/v1",
    "status": "NUMERIC_INTERVAL_COVERAGE_ALREADY_CLOSED_BY_APPLICABLE_V3_PROOF",
    "source_sha256": bindings,
    "prior_testing_receipt": {"path": str(prior_path), "sha256": sha(prior_path)},
    "reused_proof": {"path": str(correctness_path), "sha256": sha(correctness_path),
        "exact_base_geometry_sha256": sha(base_path), "canonical_moved_port_intervals": 24,
        "maximum_actual_raw_timber_interval_error_mm": checks["factory_and_shafts"]["maximum_interval_error_mm"],
        "reusable_principal_and_kicker_post_interval_subset": 12, "maximum_recorded_saved_bounds_error_mm": max(errors),
        "supporting_retained_checker": {"path": str(V3/"correctness/review.py"), "sha256": sha(V3/"correctness/review.py"), "line": 179}},
    "review_finding_disposition": {"numeric_correctness_concern": "Not found; prior exact-scope proof and twelve saved rows cover the interval values.",
        "remaining_provenance_gap": "The audit receipt's separately claimed new independent saved-BREP execution still has no retained checker. Preserve its frozen observation; a superseding source-bound entry may explicitly reuse the prior v3 proof instead of repeating geometry work.",
        "severity": "medium", "file": str(audit_path), "line": 4},
    "limits": ["Existing actual-solid observations were reused and source-authenticated, not executed by this supplement.",
        "Only hash, JSON identity and scalar saved-bound comparisons ran; no CAD/BRep import or new geometry/force/capacity check.",
        "Old action/base-v3 scope remains separate from the subsequent extended-cleat geometry and any future response."],
    "command": sys.argv}
with Path(sys.argv[1]).open("x") as stream:
    stream.write(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
print(json.dumps({"receipt": sys.argv[1], "sha256": sha(sys.argv[1]), "reused_intervals": 12}))
