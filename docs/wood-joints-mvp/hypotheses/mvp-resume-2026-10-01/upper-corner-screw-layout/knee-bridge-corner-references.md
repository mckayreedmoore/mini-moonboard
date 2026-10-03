# Fresh original-corner component references

**Parent execution complete: all applicable finite indices are below one.**
[The producer](knee-bridge-corner-references.py) evaluated all 96 saved states
once. The parent authenticated 106 source pins and four receipt artifacts.
No software tests, coupons, solve, CAD rebuild or review loop ran.

The bounded question is whether the retained component hypotheses can be
evaluated on every saved simultaneous bolt state from the completed fresh
[original-corner replay](knee-bridge-corner-replay.md). Expected coverage is
16 original outer-corner axes × six nominal cases = **96 bolt states**, with
48 top states, 48 bottom states, 24 cleat/case states and 48 host/case states.
The completed worksheet has exactly that census.

## Frozen load authority

Paths below are relative to this folder. The producer authenticates the
completed replay, its receipt and its exact **94-source closure**, then adds
the component arithmetic, material and producer pins it consumes. The total
consumer pin count therefore need not be 94.

| Source | SHA256 |
| --- | --- |
| `rawlocal/knee-bridge-corner-replay/attempt01/checks.json` | `e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976` |
| `rawlocal/knee-bridge-corner-replay/attempt01/receipt.json` | `50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `rawlocal/knee-bridge-frame/attempt02/response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |

The only case-load authority is this fresh nominal frame: modeled mass
225.19791414318078 kg, dead factor 1.1110134616260479, 250 lb with impact
factor 2, signed 300 N directions and the fixed 100 mm lever. Case order is
`a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, `a1-rear`.
Historical component packets supply geometry and reference hypotheses only.
Their case forces, maxima and acceptance are not transferred.

## Retained comparisons and applicability

Only the **92 ksi conditional smooth partially threaded bolt hypothesis** is
evaluated. Delivered shank coverage and thread exposure remain unobserved.
No 45 ksi or 106 ksi scenario, load variant or contact-law change is added.

| Interface | Diameter / bore, mm | Ordered host / cleat bearing lengths, mm | Wood-bearing hypothesis |
| --- | --- | --- | --- |
| Top rail | 6.35 / 7.5 | 38.1 / 139.7 | Retained diameter-dependent top function |
| Top side | 7.9375 / 9.0 | 88.9 / 88.9 | Retained diameter-dependent top function |
| Bottom rail | 6.35 / 7.5 | 38.1 / 88.9 | Retained 4450 / 5600 psi bottom function |
| Bottom side | 6.35 / 7.5 | 88.9 / 88.9 | Retained 4450 / 5600 psi bottom function |

The producer loads the existing `corner_checks.py:lateral_reference`,
`lateral_reference.py:angle/bearing/reference` and
`fea/dowel_yield.py:single_shear` pure functions from their pinned definitions.
It excludes their module imports and all producer entry points. This avoids
importing CAD or running historical full builds. The top and bottom
[component](corner-first-order-components.py)
[replays](bottom-corner-components.py) retain the modifier, path, washer and
steel-screen hypotheses; the bottom replay also supplies its pure physical
balance function.

The authenticated finished local replay governs diameters and bearing
lengths. `model-inputs.json` still contains older raw bolt envelopes in
`source_record`; those envelopes must not override the finished local
geometry. Current member grain is bound to the fresh input packet, with
bottom grain checked against the saved finished-member descriptors.
Positive bore quadrature weights must cover each ordered receiver length.

Each worksheet row uses the same axis/case's compatible signed axial tie,
signed host bore resultant, independently recovered cleat bore force, bore
couple, end contacts and complete beam fields. The extractor is checked
against the saved host state and full beam-field list. Peak beam stress must
have its complete saved witness, including bending. All source physical
host, interface and whole-cleat receipts retain their original tolerances.

The numerical comparisons are adjusted individual lateral reference,
signed parallel force against its finished bore-tangent path, supported
washer mean pressure against conditional wood seat compression, direct
combined axial/shank shear steel stress and complete smooth-beam stress
against 92 ksi. The existing bottom simultaneous axial/shear steel reserve
is retained; its reduced available bending stress is not an additional
material scenario. No corresponding top reserve hypothesis is invented.

Top mean-seat arithmetic uses the retained supported concentric annuli.
Bottom mean-seat arithmetic uses the retained minimum supported areas for
the existing combined offset envelope. Both own outer-seat locations must
match the saved pressure recovery. The existing radial-strip worksheet
reports required washer stress only. Mean pressure does not qualify tilted
contact pressure, washer metal or a complete joint. Saved face pressures
and end-contact peak pressures remain visible as diagnostics.

End-grain and multi-receiver individual lateral references remain null.
Missing same-geometry finished paths and unsupported own seats also remain
null with explicit reasons. Actual hardware, actual washer, native joint,
group and splitting capacities remain null. No splitting capacity or
historical whole-host splitting demand is invented or adopted.

## Parent API and outputs

`build(output)` requires a new immediate child of
`rawlocal/knee-bridge-corner-references/`. Importing the producer performs no
evidence reads or calculations. The build returns a JSON-compatible record
with `status`, `counts`, `states`, `interfaces` and `component_summary`.
The preparation expects `COMPLETE_FRESH_SAME_STATE_COMPONENT_REFERENCES`
only after the parent completes the arithmetic and evidence checks.

`component_summary(states)` returns six named component entries, each with
`finite_states`, `null_states`, `maximum`, `peak_witness`, `above_one` and
`null_reasons`. A witness gives the zero-based worksheet row and its level,
side, case, host, cleat and axis. Maxima retain independent same-state
witnesses; they are not combined into a synthetic loading state. Exhausted
bottom steel reserves are listed separately without emitting infinity or
turning a missing reference into a zero utilization.

The parent call writes these ignored local files:

- `worksheet.json`: all 96 reference rows, full local bolt states and beam
  fields, interface diagnostics, finite summary, provenance and limits.
- `component-summary.json`: the finite summary for parent integration.
- `producer.py.snapshot`: the exact executed producer bytes.
- `receipt.json`: consumed source pins and output hashes, with source
  authentication before and after writing.
- `.gitignore`: excludes every file in that output child.

The parent may execute the prepared command once when ready:

```sh
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  "$packet/knee-bridge-corner-references.py" \
  --output "$packet/rawlocal/knee-bridge-corner-references/attempt01"
```

The parent ran that command into `attempt01`. Source changes or census/geometry/
same-state contradictions stop the parent call. Above-one indices and
exhausted conditional reserves remain explicit for parent disposition;
arithmetic completion is not acceptance. Formal criterion, complete-joint,
fabrication and physical-release flags remain false.

## Completed finite comparisons

| Named comparison | Applicable states | Fresh maximum index |
| --- | ---: | ---: |
| Adjusted individual lateral reference | 96 | 0.813981 |
| Finished parallel path | 96 | 0.160371 |
| Mean washer/wood pressure | 96 | 0.768962 |
| Direct axial/shank shear steel | 96 | 0.070710 |
| Complete smooth-beam stress | 96 | 0.318737 |
| Existing bottom same-state steel reserve | 48 bottom | 0.280477 |

The top reserve is null because no corresponding top reference is defined;
it is not a zero index or missing force state. No above-one comparisons or
exhausted bottom reserves occur. Actual capacity and complete-joint assertions
remain false.

| Artifact under `rawlocal/knee-bridge-corner-references/attempt01/` | SHA-256 |
| --- | --- |
| `worksheet.json` | `c7c2bbde84cf48bd5042e06cbe218b741da684fa7477eed56da2add4f132c051` |
| `receipt.json` | `fcd986b018bb121df464292449cedcb23f1c069bd5ec611dd49b654c6d840288` |
| `producer.py.snapshot` | `188b7626d989eb16fb09ee75b8218dd9968974c95c72830dcd83c33f856c4b83` |

The producer, note and frozen input evidence remain active. Historical inputs
and runs are preserved; bulky parent outputs remain in the ignored child.
