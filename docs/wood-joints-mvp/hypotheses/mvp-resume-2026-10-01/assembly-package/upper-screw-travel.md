# Relocated upper screws and the saved bolt-travel increments

**Completed: all 192 changed enclosure pairs have positive conservative box
separation.** There are no overlapping-box candidates requiring a parent
geometry check. This finite arithmetic receipt closes the four-screw obstacle
difference identified in the [current-joint addendum](current-joint-addendum.md),
within the original [nominal length screen](hardware-length-fit.md)'s added-tip
and additional-travel scope. The frozen addendum and earlier receipt remain
unchanged. No full-scene, CAD or mechanics run was performed.

## Exact scope

The [producer](upper-screw-travel.py) consumes the saved forty-eight query
boxes from `rawlocal/hardware-length-fit/saved-source-attempt02/setup.json`.
They represent four components for each of twelve proposed longer-bolt
routes: tip extension, additional headward shaft segment, and additional
head and head-washer movement. The routes remain four center-post six-inch,
four center-principal/header eight-inch and four inner knee/header eight-inch
proposals. Their axes, endpoints, diameters and travel increments do not change.

Only these four installed screw enclosures change:

- `round_panel_upper_left_rim_4`
- `round_panel_upper_right_rim_4`
- `round_panel_upper_left_center_4`
- `round_panel_upper_right_center_4`

Each original saved enclosure is translated by
`(0,42.391842858827275,50.5206310236966)` mm. Its direction, nominal
63.5 mm occupied length, 4.1402 mm occupied diameter and original 0.001 mm
box inflation remain unchanged. These are the existing nominal cylinder
enclosures, not mesh reconstructions or delivered screw-head envelopes.
The translation and preserved direction bind the frozen
[upper-screw overlay](../upper-corner-screw-layout/shop-addendum.md)'s
before/after records and sixty-six-axis CSV. Both moved center receivers
remain `base_rail_top`; the rim receivers remain their same-side members.

The producer authenticates the original four bounds against their recorded
before datums, then adds the overlay translation to both ends of every box
coordinate. It imports only the frozen `hardware_length_fit.py` standard-library
box-distance helper. It does not call that helper's scene preparation or CAD
run, import CAD, load STEP/mesh geometry, change sources or repeat the original
48,192-pair screen.

## Result

Four changed screw bounds × forty-eight unchanged query bounds produce
**192 distinct pairs, all separated**. For each pair, the helper takes the
Euclidean norm of the three nonnegative coordinate-interval gaps. A positive
gap between conservative enclosures certifies separation for the enclosed
pair. An overlapping box would remain an undecided candidate for the parent,
without a collision or clearance claim; no such candidate occurs here.

| Relocated screw | Closest saved query | Conservative box-distance lower bound, mm |
| --- | --- | ---: |
| Upper left center | `center_principal_header_left_2/head_headward_increment` | 2167.746444 |
| Upper right center | `center_principal_header_right_2/head_headward_increment` | 2167.746444 |
| Upper left rim | `knee_outer_left_inner_header_2/head_headward_increment` | 2226.079748 |
| Upper right rim | `knee_outer_right_inner_header_2/head_headward_increment` | 2226.079748 |

These distances apply only to the four relocated screw enclosures versus the
forty-eight added-tip/travel queries. They are not a minimum clearance for
the entire frame, the existing extraction stroke or complete installed
hardware. `result.json` retains all before/translated bounds and all 192
pair distances/statuses; `pairs.csv` is the same pair census.

Combining these changed-pair certificates with the prior saved screen's
unchanged pairs preserves the nominal longer-bolt occupancy result for this
specific screw overlay. It does not select longer bolts, establish delivered
smooth shank/full-form thread, or qualify full nut/tool/counterhold/removal
sequences. Preserve the [shop guide](shop-guide.md)'s captured-nut paths,
intact harness and conditional operation order. No physical observation,
new release gate, joint acceptance or climbing release is added; Actual and
Disposition fields remain blank.

## Reproduction and receipts

The worker executed only this owner-scoped standard-library arithmetic and
targeted Ruff lint. No software tests, heavy/native/frame/CAD run or review
loop occurred. Use a fresh ignored output child; the producer refuses an
existing output directory:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/upper-screw-travel.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/upper-screw-travel/fresh-attempt
```

Completed output is `rawlocal/upper-screw-travel/attempt01/`. Six frozen input
files plus the executing producer remain byte-exact after arithmetic and
receipt writing. The producer snapshot and pair CSV are bound by the result.

| Artifact | SHA256 |
| --- | --- |
| `upper-screw-travel.py` and saved producer snapshot | `08d879823afb9396d9af6197a9e5d82a0887485bff29a7292d6295575f881993` |
| `rawlocal/upper-screw-travel/attempt01/result.json` | `76379eb78eb73fbdcf9c6d4b5a0edf5497a0fcb67129f5d0eb956144b4dfb925` |
| `rawlocal/upper-screw-travel/attempt01/pairs.csv` | `97d22df89774cd976ab0cdd518c1285a1977e23d2c7df3842e6fae1f9e33e68a` |
| Frozen `hardware_length_fit.py` helper | `fd54fbe3d7d59c504b4ec80519155a12802e593c98c8043867d80746977d5b8b` |
| Earlier length `saved-source-attempt02/setup.json` | `c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529` |
| Earlier length `saved-source-attempt02/result.json` | `df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5` |
| Upper overlay `rawlocal/attempt01/setup.json` | `00cfa71d30a1d8d789df7c4a40770f9ec46e3e56c0ee9d23018d62e6c11583bc` |
| Upper overlay `rawlocal/shop-axes/axes.csv` | `46406c559d1f427ad4422edf033759831a83d0ddcef4bbb871579da132853eca` |
| Upper overlay `rawlocal/shop-axes/receipt.json` | `535bcdaeb85ed683e66040c8042dd6c3bdea7d835ca7a9d7c510de99d6cf773d` |

Parent owns integration, shared staging and publication. Both maintained
leaves and the completed producer snapshot are frozen at handoff.
