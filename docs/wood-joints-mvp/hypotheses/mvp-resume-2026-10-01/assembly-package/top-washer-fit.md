# Eight top-rail washer replacements: bounded saved-source fit

**Completed bounded nominal fit: `BOUNDED_NOMINAL_ENCLOSURES_CLEAR`.** The parent
reports exit 0 for `rawlocal/top-washer-fit/run-attempt01/`, using the frozen
`prepare-attempt02/setup.json`. The saved result records 37,268 AABB-separated
pairs, twelve finite-cylinder projection certificates, and 72 clear exact
intersection pairs against five imported saved STEP solids. Overlap and
undecided counts are both zero. The parent now uses the eight 2.5-mm washers
for [conditional working-order planning](hardware-engagement.md#working-order-export); delivered fit, physical access, full turning
and complete-joint acceptance remain unestablished.

## Frozen scope and sources

The [producer](top_washer_fit.py) reuses the saved installed inventory and
enclosure functions from [hardware_length_fit.py](hardware_length_fit.py),
its `saved-source-attempt02/setup.json`, and its unchanged result. It does not
call that producer's preparation, inventory reconstruction, or CAD execution.
The [upper-screw travel receipt](upper-screw-travel.md)'s four translated
installed enclosures replace their matching before bounds; the other 62
nominal screw enclosures are unchanged. Their 63.5-mm length and 4.1402-mm
diameter describe an occupied footprint, not a physical screw-head enclosure.

The completed [48-end washer suite](../upper-corner-screw-layout/retail-washer-suite.md)
provides the repeated physical exterior seat coordinates, bolt directions,
and eight corrected support lands. Its unchanged model has ID 8.3058 mm,
OD 25.4 mm, thickness 2.5 mm, analytical head-contact radius 5 mm,
E 200 GPa and assumed Fy 250 MPa. Its maximum sampled stress proxy is
207.205343 MPa. This fit producer performs no mechanics calculation and
transfers no resistance or joint acceptance from that result. The recorded
minimum nominal outer-disk edge margin is approximately 30.65 mm; that is
a wood-support margin, not an installed-obstacle clearance.

The four rail axes are `top_outer/clip_single_top_left_1/rail_1`,
`top_outer/clip_single_top_left_1/rail_2`,
`top_outer/clip_single_top_right_2/rail_1`, and
`top_outer/clip_single_top_right_2/rail_2`. Each receives two exterior washers.
The host disk starts at its named `base_rail_top` seat and extends opposite
the head-to-nut axis. The cleat disk starts at its named same-side cleat seat
and extends along that axis. The filled outer disks conservatively enclose
the annuli; their ID is recorded, and their own shaft/contact exclusions are
explicit. No invented washer eccentricity, loaded tilt or deflection is added.

All 50 saved wood STEP paths, including the four corrected replacements,
remain installed obstacles. Retained hardware, modeled wire STEP solids,
T-nut/light enclosures, other candidate hardware and all 66 screw footprints
remain in the inventory. Eight previously oversized corrected-stack boxes
are replaced by forty named component enclosures at their saved corrected
endpoints: shaft, head, head washer, nut washer and nut for each stack.
The four side stacks retain their saved catalog bounds; only the four rail
stacks receive the washer proposal. This yields 1,041 installed obstacles.

Exterior head/nut enclosures use the existing catalog's maximum height and
maximum across-flats dimensions. A coaxial cylinder with radius
`maximum_across_flats / sqrt(3)` encloses the conditional regular hex profile.
The 5-mm mechanics contact radius is not substituted for a head dimension.
These remain catalog profile enclosures without exact installed STEP geometry;
they are not measurements or a qualification of delivered chamfers, fillets,
threads, runout or bearing faces. A missing required bound or mismatched datum
stops preparation with its exact source fact.

## Datum and removal model

The saved catalog washer thickness range is 1.2954–2.032 mm. Substitution with
2.5 mm adds 0.4680–1.2046 mm at each end and 0.9360–2.4092 mm across both ends.
The new head and nut positions are tied to their physical wood seats. The nut
moves by its own washer increment relative to the cleat, and by the sum of
both increments relative to the bolt's shifted under-head datum. The head-side
shaft collar covers the entire minimum-to-maximum catalog increment range.
The nominal shaft remains 203.2 mm (8 in); the wood grip remains 177.8 mm.
Its shifted under-head origin introduces no new wood axis.

The original saved headward stroke is 150.368 mm for the former 152.4-mm shaft.
The corrected 8-in shaft with a 2.032-mm head washer would require 201.168 mm.
The replacement model requires 200.700 mm: thicker head seating reduces the
required stroke by 0.468 mm from that corrected maximum-thickness reference.
There is **no additional headward stroke**. Nut and nut-washer slide lengths
are respectively 20.400 and 22.900 mm, with zero added terminal allowance.
These lengths follow the saved endpoint/receiver method and retain its
conditional disengagement and capture assumptions.

The 36 queries comprise sixteen installed washer/head/nut enclosures, sixteen
replacement removal enclosures, and four added shaft collars. Full replacement
enclosures conservatively cover their added diameter/thickness/offset occupancy;
the producer does not subtract the earlier occupancy or replay its checks.
No unchanged moving components or full scene are rebuilt. Straight approaches
remain conditional; thread turning, counterhold, hands, real tools and complete
operation sequences remain outside this screen. Existing captured routes for
other joints and the intact-harness sequence remain unchanged.

The [existing retail-washer arithmetic](../upper-corner-screw-layout/retail-washer.md)
remains conditional: required `LB >= 145.375 mm`, conservative full-form window
182.8000–188.5404 mm, and three-pitch `Lmin = 192.3504 mm`. The nominal shaft
does not establish any delivered body/thread interval.

## Completed bounded fit

The setup retains every source ID, query enclosure, pair margin and explicit
exclusion. There are 37,352 evaluated pairs and 124 named exclusions. Exclusions
identify only the active component, its named coaxial shaft or adjacent contact,
or its own documented prerequisite removal. There is no same-axis blanket skip.
Own wood seats remain evaluated STEP pairs, marked as intended seat contact;
positive enclosure penetration still requires disposition.

| Saved result disposition | Pairs |
| --- | ---: |
| Positive conservative AABB separation | 37,268 |
| Positive conservative finite-cylinder projection separation | 12 |
| Clear by exact saved STEP intersection | 72 |
| Unsupported non-STEP pairs remaining | 0 |
| Enclosure overlap pairs | 0 |

The parent result retains all 36 queries against 1,041 installed obstacles,
37,352 evaluated pairs and 124 explicit exclusions. Its eight washer roles,
four rail axes and four moved/62 unchanged screw enclosures match the frozen
preparation. The source-unchanged flag is true; the geometry-rebuilt and
new-physics flags are false.

The smallest positive AABB distance is 2.605362828 mm, between left rail 1's
nut-washer removal enclosure and left rail 2's installed nut enclosure. This
is a lower bound for that enclosure pair; it is not the global assembly clearance.

The twelve additional certificates all involve a same-side neighboring rail shaft.
The following table gives the complete census; each listed query component
has both an `installed` and a `replacement_removal_enclosure` pair. Query IDs
start with the rail-axis prefix above. Obstacle IDs start with
`corrected_top_component/` followed by the neighboring axis and `/shaft`.

| Side | Query rail | Query components | Neighboring shaft | Pairs |
| --- | --- | --- | --- | ---: |
| Left | 1 | `nut_washer`, `nut` | Rail 2 | 4 |
| Left | 2 | `nut_washer` | Rail 1 | 2 |
| Right | 1 | `nut_washer`, `nut` | Rail 2 | 4 |
| Right | 2 | `nut_washer` | Rail 1 | 2 |

Both participants in each of those twelve pairs have a pinned primitive:
start datum, unit axis, radius and finite cylinder length. The additional
standard-library certificate uses only these existing enclosures. After global
AABB overlap, it chooses a unit projection normal along the component of the
start-datum difference perpendicular to the query axis. Each finite cylinder's
projected interval contains the projections of both axial endpoints, expanded
at each end by `R * sqrt(max(0, 1 - dot(unit_axis, normal)^2))`. The gap between
disjoint intervals is a conservative separation certificate. Each source axis
is checked for unit length and normalized for projection arithmetic. The method
does not require parallel axes, an angular tolerance or an infinite-axis
assumption. A zero perpendicular datum difference provides no certificate.

All twelve actual source pairs are parallel to the recorded precision; their
perpendicular datum distances are 33 mm within floating-point roundoff. The eight
nut-washer pairs have query radius 12.7 mm and obstacle radius 3.175 mm, giving
computed minimum separation **17.124999999999886 mm**, or 17.125 mm rounded.
The four nut pairs use their pinned conditional
regular-hex enclosure radius `11.1252 / sqrt(3) = 6.423137214788425 mm`, giving
computed minimum separation **23.401862785211677 mm**. These values are calculated
from the source primitives rather than hardcoded into the producer. Every pair
retains its source IDs, projection normal, perpendicular datum distance, both
finite-cylinder projection intervals and positive certificate margin; the
primitive radii remain in the query and obstacle records.
The function does not assume a cylinder for an obstacle missing a primitive;
unsupported or overlapping projected intervals retain their undecided disposition. No
exact physical shaft profile, new mechanics, CAD or turning model is introduced.

The parent run checked the other 72 overlap candidates using their saved
STEP bytes and the defined conservative query cylinders. Every recorded overlap
volume is **0.0 mm³**, within the inherited 1e-6 mm³ volume criterion. Five
STEP solids were imported; all other pair decisions reused the saved bounds
or finite-cylinder certificates.

| Imported saved STEP obstacle | Exact pairs | Minimum recorded distance, mm |
| --- | ---: | ---: |
| `base_rail_top` | 20 | 0.0 |
| Corrected `top_outer_left_cleat` | 18 | 0.0 |
| Corrected `top_outer_right_cleat` | 18 | 0.0 |
| `main_upper_left` | 8 | 50.65000004458682 |
| `main_upper_right` | 8 | 50.65000004458717 |

The overall exact minimum distance is zero at a named intended washer/wood
seat contact, with zero positive-volume penetration. This is not a positive
assembly-wide clearance. Among the exact pairs not marked as intended wood-seat
contact, the minimum is **1.417281250089542 mm**, for left rail 2's
`shaft/added_underhead_offset` query against `wood/base_rail_top`. The separate
AABB and neighboring-cylinder margins above remain 2.6053628276154086 mm,
17.124999999999886 mm and 23.401862785211677 mm in the saved result.

Any positive-volume enclosure conflict above that criterion yields
`STOP_ENCLOSURE_OVERLAP`; any unsupported pair would retain
`BOUNDED_FIT_UNDECIDED`. With neither type of unresolved pair, the actual result is
`BOUNDED_NOMINAL_ENCLOSURES_CLEAR`. Clearance from an enclosing cylinder certifies separation;
an enclosing-cylinder conflict does not by itself prove the real hex/annular
part cannot fit.

## API, command and receipt bindings

Import and `--prepare` use only the standard library. The prepared producer is
358 lines. No CAD, software tests, review, mechanics or scene replay was executed
by this worker. The parent executed the saved-source geometry check in its
serialized slot. The API remains `run(output_dir=Path(...), setup_path=Path(...))`;
the command below records its frozen setup and completed output paths:

```sh
uv run --no-sync python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/top_washer_fit.py --run --setup docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/top-washer-fit/prepare-attempt02/setup.json --output-dir docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/top-washer-fit/run-attempt01
```

The completed `run-attempt01` child must be preserved. Any reproduction requires
a different fresh immediate child of `rawlocal/top-washer-fit/`.
The preflight pins 589 source paths and snapshots every input byte into 588
SHA-addressed files, including the producer and frozen helper. Byte-identical
inputs share one snapshot. The active ignored snapshots occupy 126,258,863 bytes;
this retains the exact dependency graph and temporary-source bytes without
changing original files. The parent imported only required saved STEP snapshots.
The producer authenticates sources and snapshots before execution and rechecks
original sources and the prepared setup afterward. The saved result and output
receipt report `source_unchanged_after_run: true`. The result's `setup_sha256`
and the saved input receipt bind the same frozen attempt02 setup. The output
receipt binds the producer snapshot, input receipt and result hashes below;
its `producer_sha256` matches the frozen producer. Parent owns final run
authentication and publication. No source `/tmp` file is modified or removed.

| Artifact | SHA256 |
| --- | --- |
| Completed run `result.json` | `bc1bbfd01d6c002ffc7a9da4b14b44e47bb98c4809ef5059c7b3e10bddd1d797` |
| Completed run `receipt.json` | `eb40764257349f6d24472c71278e990195d583c4de02e7a10909c184d583de89` |
| Completed run `inputs-before.json` | `d783bf04cf0c972ac9caeb8e719a179712c34584dd4f61b2dee045e5ba59091a` |
| Completed run `producer.py.snapshot` | `8c48b3f423e94e693d17182b70726205425e71de627dda9afd88c17645479c1a` |
| `top_washer_fit.py` | `8c48b3f423e94e693d17182b70726205425e71de627dda9afd88c17645479c1a` |
| Active attempt02 `setup.json` | `d5b885bf3e023ca4efdcecd219453a288294d264692beb4d4bce100702928128` |
| Active attempt02 `snapshot-manifest.json` | `c046e1d5b93a3ea69105171b1ab8958915f2a2ae81450c0fdc1d5b3547de7086` |
| Reused length helper | `fd54fbe3d7d59c504b4ec80519155a12802e593c98c8043867d80746977d5b8b` |
| Reused length setup | `c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529` |
| Reused length result | `df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5` |
| Completed 48-end suite result | `3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74` |

All formal-acceptance, complete-joint, physical-release, delivered-fit,
physical-access and full-turning flags remain false. Physical Actual and
Disposition fields are not populated. The completed run receipt/result and
active attempt02 source snapshots remain retained as the bounded fit evidence.
The earlier attempt01 directory,
its producer snapshot and dependency snapshots remain unchanged; its setup
still has SHA256 `28aa4944ab58b99376b51f91ee8b721739c17a8e399a798281760dff69225412`.
Attempt02 is the current preparation; attempt01 preserves the earlier twelve
undecided pairs without a CAD run. The preceding parallel-bound preparation
is retained byte-for-byte at `rawlocal/top-washer-fit/prepare-attempt02-parallel/`;
its setup still has SHA256 `843d35cc95a4829a1ddb0829460217cdd2f78c1a13c199a9c9b1de0b0b8bf702`.
The fresh attempt02 uses the finite interval certificate for the same twelve
original candidates. No raw output is eligible for
pruning through this task. This leaf now annotates the returned parent result;
the worker performed no additional geometry execution or code changes. Parent
owns run authentication, integration, every other Markdown file, shared staging,
commit and publication.
