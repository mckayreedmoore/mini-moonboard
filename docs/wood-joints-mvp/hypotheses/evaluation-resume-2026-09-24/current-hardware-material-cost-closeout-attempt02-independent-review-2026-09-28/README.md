# T08 attempt02 independent review

**Reviewed:** 2026-09-28  
**Candidate / revision:** `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
**Verdict:** supported as a partial, fail-closed closeout. No concrete defect was found in the requested local-integrity, count, arithmetic, or claim-boundary checks. This review does not close T08 or establish a candidate cost bound.

The reviewed packet is [current-hardware-material-cost-closeout-attempt02](../current-hardware-material-cost-closeout-attempt02/). Its terminal `SHA256SUMS` file has SHA-256 `baaac3c26624c92ff96e391cbc914366321c37081186a3d212ee424754da09fd`; all seven payload files listed there passed verification. The attempt's `source-pins.json` contains 30 distinct paths. At the completed review checkpoint, I independently verified all 30 pinned input hashes, including the task-queue pin `e624e043f15b3fd361dc99b05be6a37ff625b6bcb0e1da2cccaf3cb557a0a35c`; the terminal `verification.json` also records 30/30 matches. During subsequent packet assembly, the coordinator refreshed the live queue, whose current SHA-256 is `3441773c3491a0a6a4127816178bfb656ae2fbe6bb11576a1865b60cee639180`. This is a post-freeze difference, not an attempt02 defect: the historical pin remains bound to the frozen attempt, and the review record distinguishes the completed-review checkpoint from the later queue state.

The axis identities reconcile exactly against the pinned attempt01 register: 92 candidate bolt axes, 12 retained starting frame-bolt axes, 66 Hillman 42605 screw axes (58 unchanged and eight previously owner-moved), and 144 removed SDS25112 reference axes. Candidate lead coverage and catalog-row groups also reconcile. The arithmetic reproduces: eight candidate bolt pages have numeric price cells; the observed per-bolt display envelope is $0.2314–$2.54 across unlike parts and tiers; the retained reference formula is $31.12; and the hypothetical Hillman replacement-listing formula is $15.96. The envelope and reference calculations are not candidate cost bounds or required purchase totals.

The attempt appropriately leaves the candidate total and range, compatible material cost bounds, Hillman receipt amount, product selection, delivered identity, fit, weight, and readiness/criterion pass unproved. It describes itself as partial. The pinned T08 exit gate remains unmet: the packet does not establish 104 matched stacks or close product/fit, current material/yield, receiving, or other readiness evidence. Counts of bolt/nut/washer roles do not demonstrate matched or delivered stacks.

Review scope was limited to the frozen local artifacts, their hashes, axis identities/counts, displayed-price arithmetic, and narrative claim boundaries. Supplier pages were not reopened; this review does not independently reproduce their page displays, availability, or prices. The attempt's `build_attempt02.py` was not run because it writes into the reviewed attempt directory. No attempt02, queue, manifest, status, ledger, or plan file was changed for this review.

From this directory, verify the review artifacts and the bound attempt02 terminal manifest with:

```sh
sha256sum -c SHA256SUMS
```

The following read-only check reproduces the 30 source-pin, exact axis-identity, candidate price-envelope, retained-reference, and Hillman-formula checks from the repository root. Run `sha256sum -c SHA256SUMS` first from this review directory.

```sh
python3 - <<'PY'
import hashlib, json, math, pathlib, re
root = pathlib.Path.cwd()
base = root / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt02"
pins = json.loads((base / "source-pins.json").read_text())
frozen = json.loads((base / "verification.json").read_text())["source_pin_checks"]
assert len(pins["sources"]) == len(frozen) == 30
assert len({x["path"] for x in pins["sources"]}) == 30
assert all(x["matches"] and x["actual_sha256"] == x["expected_sha256"] for x in frozen)
# A coordinator queue refresh occurred after the reviewed freeze; preserve and check it explicitly.
live = [(x["path"], x["sha256"], hashlib.sha256((root / x["path"]).read_bytes()).hexdigest()) for x in pins["sources"]]
live_mismatches = [(p, expected, actual) for p, expected, actual in live if expected != actual]
assert len(live_mismatches) == 1
assert live_mismatches[0] == ("docs/wood-joints-mvp/luna-max-task-queue.json", "e624e043f15b3fd361dc99b05be6a37ff625b6bcb0e1da2cccaf3cb557a0a35c", "3441773c3491a0a6a4127816178bfb656ae2fbe6bb11576a1865b60cee639180")
reg = json.loads((base.parent / "current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json").read_text())
rec = json.loads((base / "axis-count-reconciliation.json").read_text())
ca = sorted(x["axis_id"] for x in reg["candidate_axis_rows"])
ra = sorted(x["axis_id"] for x in reg["retained_axis_rows"])
ha = sorted(x["axis_id"] for x in reg["hillman_axis_rows"])
ma = sorted(x["axis_id"] for x in reg["hillman_axis_rows"] if x["owner_moved_axis"])
ua = sorted(x["axis_id"] for x in reg["hillman_axis_rows"] if not x["owner_moved_axis"])
sa = sorted(reg["removed_legacy_sds25112_axis_ids"])
assert ca == rec["candidate_axis_ids"] and len(ca) == 92
assert ra == sorted(x["axis_id"] for x in rec["retained_starting_frame_bolt_axes"]) and len(ra) == 12
assert ha == rec["hillman_42605_policy"]["axis_ids"] and len(ha) == 66
assert ma == rec["hillman_42605_policy"]["previously_owner_moved_axis_ids"] and len(ma) == 8
assert ua == rec["hillman_42605_policy"]["unchanged_axis_ids"] and len(ua) == 58
assert sa == rec["removed_sds25112_policy"]["reference_axis_ids"] and len(sa) == 144
prices = json.loads((base / "public-price-observations.json").read_text())
rows = [r for r in prices["candidate_catalog_lead_rechecks"] if r.get("displayed_prices")]
assert len(rows) == 8
normalized = []
for row in rows:
    for cell in row["displayed_prices"]:
        m = re.search(r"(\d+)-piece (?:box|carton)", cell["basis"])
        count = int(m.group(1)) if m else 1
        normalized.append(cell["amount"] / count)
assert math.isclose(min(normalized), 0.2314) and math.isclose(max(normalized), 2.54)
ret = prices["retained_selected_baseline_reference_only"]
byid = {x["product_id"]: x["displayed_each_price"] for x in ret["source_pages"]}
assert math.isclose(4*byid["407"] + 4*byid["2573"] + 8*byid["15025"] + 4*byid["367"] + 4*byid["368"] + 8*byid["2571"] + 16*byid["15023"], 31.12)
hill = prices["separate_hillman_panel_kicker_purchase_reference"]
assert math.isclose(math.ceil(66/50) * hill["displayed_price"]["amount"], 15.96)
print("PASS: frozen pin record 30/30; current workspace pin check 29/30 after the documented queue refresh")
PY
```

The review data and hashes are recorded in [review-record.json](review-record.json). The adjacent [SHA256SUMS](SHA256SUMS) binds both review artifacts and the reviewed attempt02 terminal manifest.
