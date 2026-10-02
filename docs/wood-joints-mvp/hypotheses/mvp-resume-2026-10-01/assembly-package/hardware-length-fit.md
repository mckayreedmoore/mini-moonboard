# Proposed bolt-length occupancy

**Status: parent-owned saved-source screen complete; no added-occupancy clash found.** This
bounded check covers twelve proposed bolt-tip extensions and the matching
increase in headward travel. It does not select hardware, establish delivered
shank or thread position, or qualify the full nut and washer removal sequence.
See the [hardware engagement worksheet](hardware-engagement.md) for the
separate purchasing fit conditions and the [shop guide](shop-guide.md) for the
assembly sequence.

## Proposed shaft lengths

The saved headward endpoint, bolt axis, diameter, receiver order, and direction
stay fixed. Each proposed shaft adds length only at its saved nutward tip.

| Family and axes | Count | Saved shaft length, mm | Proposed shaft length, mm | Added tip, mm |
| --- | ---: | ---: | ---: | ---: |
| `center_post_left_1/2`, `center_post_right_1/2` | 4 | 139.2174 | 152.4 (6 in) | 13.1826 |
| `center_principal_header_left_1/2`, `center_principal_header_right_1/2` | 4 | 190.0174 | 203.2 (8 in) | 13.1826 |
| `knee_outer_left_inner_header_1/2`, `knee_outer_right_inner_header_1/2` | 4 | 202.5 | 203.2 (8 in) | 0.7 |

All twelve model shafts use nominal 1/4 in (6.35 mm) diameter. The first two
saved values retain their recorded precision; 139.217 and 190.017 mm are
rounded purchase-table labels. Proposed lengths describe modeled cylindrical
occupancy. Nominal catalog length does not guarantee delivered under-head
length, smooth-shank length, or full-form thread location.

## Headward travel increment

The existing saved-source travel values end when the shorter shaft clears the
head-side receiver face. Holding the headward endpoint and receiver geometry
fixed makes the proposed travel increase equal to the added tip length. The
resulting lengths below are arithmetic travel references for the completed
screen, with zero added terminal allowance.

| Family | Saved headward travel, mm | Added travel, mm | Proposed headward travel, mm |
| --- | ---: | ---: | ---: |
| Four center-post routes | 137.5664 | 13.1826 | 150.749 |
| Four principal/header routes | 188.3664 | 13.1826 | 201.549 |
| Four inner knee/header routes | 200.849 | 0.7 | 201.549 |

The two inner knee/header bolts on each side point in opposite directions;
their source headward directions remain unchanged. These values extend the
saved travel record. They are not new extraction-path measurements.

## Saved-source screen

The parent-owned run checks proposed tip segments and associated headward
travel against the fifty pinned timber, block, and panel STEP bodies. It uses
the four frozen top-corner STEP replacements for `base_side_left`,
`base_side_right`, `top_outer_left_cleat`, and `top_outer_right_cleat`, plus
the other saved hardware and wires. It does not rebuild or modify source
geometry.

Disjoint saved axis-aligned bounds certify separation for that source pair.
Pairs whose bounds overlap require exact intersection against the corresponding
saved STEP shapes. An overlapping bound alone does not establish a collision.
If a required saved shape cannot be loaded or bound to its recorded source,
that pair remains explicitly undecided. T-nut and light enclosures use their
saved STL vertices and recorded global extents; temporary tool and hold
projection envelopes are outside the installed obstacle set. The eight remote
corrected top stacks use conservative enclosures under the recorded nominal
length and catalog dimensions.

Preparation recorded 1,009 installed obstacle entries and 48 added-occupancy
queries: one tip, one added headward shaft segment, and the additional head and
head-washer movement for each axis. Of 48,192 external source pairs, 48,190
have positive conservative box separation. The two overlapping boxes were
resolved against their saved STEP solids:

| Query | Saved STEP obstacle | Intersection volume, mm³ | Minimum distance, mm |
| --- | --- | ---: | ---: |
| `knee_outer_left_inner_header_1/tip_extension` | `base_rail_bottom_left` | 0 | 18.157582 |
| `knee_outer_right_inner_header_1/tip_extension` | `base_rail_bottom_right` | 0 | 18.157582 |

No added-occupancy pair has a modeled overlap or remains undecided. The two
distances above describe those exact pairs, not the minimum clearance of all
moving hardware. The source run loaded only those two STEP obstacles; it did
not rebuild the scene.

This result applies to the recorded enclosures and additional movements. The
screen does not rerun the full installed bolt stacks, nut or washer removal, or the
separate captured-nut paths. Preserve the existing captured-nut sequence and
intact harness assumptions in the shop guide; this length screen does not
change them.

## Engineering record

Producer: [hardware_length_fit.py](hardware_length_fit.py). Setup and result
files belong in ignored `rawlocal/hardware-length-fit/`. The standard-library
preparation bound twelve unique target axes, fifty member STEP paths, four
corrected STEP replacements, and 535 source hashes. It imported no CAD modules.
The source pins, endpoints, separation certificates, exact intersections,
and unresolved pairs belong in the generated result.

Parent executed the following command in the serialized geometry slot:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 180s .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/hardware_length_fit.py --run --output-dir docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-length-fit/saved-source-attempt02
```

The run completed in 2.189624 seconds. All 535 source pins still matched after
execution, and the maintained producer matches its execution receipt. The
earlier prepared setup in `saved-source-attempt01/` remains unchanged. Use a
fresh output directory for another run; the producer refuses to replace
different saved output.

| Artifact | SHA-256 |
| --- | --- |
| Executed producer | `fd54fbe3d7d59c504b4ec80519155a12802e593c98c8043867d80746977d5b8b` |
| `saved-source-attempt02/setup.json` | `c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529` |
| `saved-source-attempt02/result.json` | `df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5` |

Ruff passes. No software tests or native mechanics were run. This screen does
not establish physical access, received hardware dimensions, assembly
feasibility, or structural acceptance. No proposed length, hardware change,
reviewed geometry change, or physical release is adopted.
