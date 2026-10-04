# Receiver revision: fixed-force necessary geometry bounds

## Bounded question

The saved [beam comparison](../beam-connection-shear-completion.md) has eight
available actual-edge outer-post component exceedances under both recorded
duration references. This leaf asks whether translating each complete bolt
pair through its unchanged receiver depth could meet that scalar component
reference **with the saved induced section shear held fixed**.

It covers both outer-post/knee pairs and both outer-post/floor pairs: four
physical pairs, eight axes and all six cases. Every same-pair case remains
present. Zero and opposing transfers receive no invented loaded edge or
inverse comparison. A nonempty receiver-only interval is not an accepted
repair, a splitting qualification, or whole-joint feasibility.

The reviewed 104 structural axes and 66 panel/kicker screws remain unchanged.
Fresh forces still have 104 connector axes; gravity includes the unadopted
108-inventory planning mass. The four proposed internal ties receive no
global force or resistance here.

## Primary rule and inverse

[NDS 2024 §3.4.4.1](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
printed p.21 / PDF p.7, supplies the near-end component:

```text
Vr = (2/3) Fv' b de (de/d)^2
required_de = cbrt(3 abs(V) d^2 / (2 Fv' b))
```

Units are mm, MPa and N. Each scenario uses its own saved adjusted `Fv'`;
the duration factor is not applied again. The producer first reproduces
the saved capacity and index, then verifies that the inverse returns the
original saved shear. All four source pairs are in the near-end branch;
a branch change stops this bounded calculation.

For a uniquely established loaded-edge sign `s`, let `t` be common pair
translation along the saved positive receiver depth axis:

```text
de(t) = existing_de - s*t
```

Increasing `de` therefore moves toward the unloaded edge. For `s = -1`,
the inverse supplies a lower bound on `t`; for `s = +1`, an upper bound.
Intersecting both signed branches across all available same-pair cases
retains reversals without selecting a favorable side.

## Geometry and existing constraints

The producer uses saved receiver faces, bolt centers, occupied bore radii,
nominal diameters, grain ends and exact constant-prism edge rays. It intersects
the fixed-force beam bounds with receiver bore-envelope containment and the
existing finite edge-distance hypotheses. It does not change a face, center,
hole, material, source force or stiffness. Occupied bore radii are analysis
envelopes, not bit instructions.

[NDS Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf),
Tables 12.5.1A–D and §§12.1.2 / 12.5.1, supply conditional edge, square-end
and row comparisons. The saved [detailing assessment](../bolt-detailing-completion.md)
retains oblique endpoint envelopes as hypotheses. This leaf reuses their
finite recorded requirements and preserves null applicability; it does not
adopt a universal angular rule or assign `Cdelta` or `Cg`.

Receiver grain coordinates and square-end distances remain unchanged under
this transverse translation. All original end comparisons, including any
existing hypothetical shortfalls and null rules, remain visible. Common
translation preserves the pair's own pitch; source row classification and
spacing acceptance do not transfer. Spacing to other axes, bore intersections,
washer lands and access still require checks for an actual revision.

The nominal knee and floor diameters are 6.35 and 9.525 mm respectively;
their occupied bore radii are 3.75 and 5.55625 mm. These distinct bases stay
bound to their own source axes and comparisons.

Partner references remain explicit. Moving the floor axes in global Y changes
their floor partners' grain-end distances. The knee partners' effective N03
geometry is the six-bore proposal, while their reviewed geometry has four
bores; both STEP identities are recorded without acceptance transfer.
The knee partner's transverse action has the opposite sign: moving toward
the post's unloaded edge can worsen the spine's effective depth. No
translated partner face, end, edge, contact, washer or whole-joint path is
qualified by receiver containment.

## API and execution ownership

```python
prepare(output: pathlib.Path | str) -> dict
build(output: pathlib.Path | str) -> dict
```

Importing [receiver-revision-bounds.py](receiver-revision-bounds.py) is inert.
`prepare` authenticates source identities and inventories the four joins,
six cases and exact eight saved exceedance witnesses. It performs no inverse,
translation, resistance or new geometry arithmetic. Only the main parent
calls `build`, with a fresh immediate output child:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/receiver-revision-bounds.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/receiver-revision-bounds/attempt01
```

Add `--prepare` and use a new preparation directory for identity preparation.
Both paths preserve a failed attempt's STOP report and receipt. There are no
load, edge-selection, material, geometry or favorable-duration overrides.

The completed actual run preserves all 24 complete source state rows,
calculates only available signed components, and reports four pair envelopes
under each duration scenario. It records the nearest-to-zero conditional translation
and hypothetical receiver centers where the interval is nonempty. These are
specific geometry questions for a proposed revision, not drill locations.

## Limits and next decision

Moving bolts changes force placement, free-couple accounting, contact and
possibly global response. Fixed-force inversion does not predict the revised
frame's demand. A future revision needs its actual shifted geometry and
loads, both timber sides, all simultaneous duties, detailing and support
checks. Existing opening, shear, torsion, moments and axial washer actions
are not removed by satisfying this scalar component.

No complete joint, repair, candidate, fabrication or physical-release flag
is accepted. No native, CAD, frame or engineering workflow is invoked by
preparation. The source beam report and its raw labels remain unchanged.

The producer binds the frozen beam receipt/report/state stream and its
255-source map, the actual N03 attempt02 receipt and outputs, the primary
Chapter 3 and Chapter 12 PDFs, and the frozen receiver interpretation. The
new receipt records every resolved input and output hash. The parent's
completed actual result and its finite interpretation are recorded below.

## Preparation and source review

The initial `prepare01` completed with 263 authenticated source identities,
two output identities, all 24 pair/case states and the exact eight original
exceedance witnesses. It performed no engineering arithmetic. Its snapshot
predates the stricter all-end-normal guard in the current producer; the
parent must use the newly frozen source, not that preparation snapshot.
Independent source-only checks confirmed the equation, signed translation
map, source faces, distinct diameters, all six-case directions and the partner
geometry limitations. AST and Ruff checks passed; no engineering build ran.

`prepare02` then completed against the current stricter source, again with
263 input identities, two outputs and no numerical arithmetic. The snapshot
is byte-identical to the current producer. Its identities are:

| Artifact | SHA-256 |
| --- | --- |
| Current producer / `prepare02/producer.py.snapshot` | `7589288a4a7ec9c9d5c24153800f14128866358207ead2d7b883f9c07dad42b9` |
| `prepare02/checks.json` | `47ff8eb042845816a1da3bcf04221265fc0432ce9f2e81ee8172c589ea5f507f` |
| `prepare02/receipt.json` | `9a99528490b62fa25493e98c273e190674c6854a9001e640a7ce716e8404faca` |

## Completed parent calculation

The parent executed the frozen producer into
`rawlocal/receiver-revision-bounds/attempt01/`. Its status is
`COMPLETED_NECESSARY_BOUNDS`, with numerical arithmetic true. Independent
read-only authentication confirms all **263 input identities and four output
identities**. No engineering producer was rerun for this interpretation.

All **24** original pair/case states are retained. Thirteen states have a
unique applicable component edge and produce **26** inverse comparisons,
one per duration. Eleven zero/opposing states retain **22** physical-edge
diagnostic entries with no inverse assigned. These are overlapping method
counts, not additional hardware or qualified joint counts.

The governing saved bounds are below. `t` is translation in **global +Y**;
positive and negative values therefore denote opposite physical moves.
Values are minimum receiver-only offsets under the respective recorded
strength scenario, rounded for reading. Each pair's envelope also includes
all its other available signed cases and existing edge hypotheses.

| Receiver pair | Governing case | Required `de`, CD1 / CD1.25, mm | Nearest-zero `t`, CD1 / CD1.25, mm |
| --- | --- | ---: | ---: |
| Left outer-post / knee | `a12-left` | 84.800686 / 78.721984 | +46.700686 / +40.621984 |
| Right outer-post / knee | `k12-right` | 84.353885 / 78.307210 | +46.253885 / +40.207210 |
| Left outer-post / floor | `a12-left` | 78.413024 / 72.792204 | -8.885165 / -3.264345 |
| Right outer-post / floor | `k12-right` | 78.121668 / 72.521732 | -8.593809 / -2.993873 |

Existing actual-edge `de` is 38.1 mm for the governing knee cases and
69.5278589284 mm for the governing floor cases. The remaining saved inverse
rows are below the governing movement bound or govern its opposite signed
branch; none is discarded to select a favorable case.

| Receiver pair | Conditional CD1 window for `t`, mm | Conditional CD1.25 window for `t`, mm |
| --- | --- | --- |
| Left outer-post / knee | [46.700686, 76.200000] | [40.621984, 76.200000] |
| Right outer-post / knee | [46.253885, 76.200000] | [40.207210, 76.200000] |
| Left outer-post / floor | [-32.072141, -8.885165] | [-32.072141, -3.264345] |
| Right outer-post / floor | [-32.072141, -8.593809] | [-32.072141, -2.993873] |

All eight windows are nonempty **for the post receiver only**, with saved
forces and the conditional edge-distance envelopes. They do not establish
that a complete shared-axis relocation works on both timbers. In particular:

- Post grain ends and the moved pair's internal spacing remain unchanged.
  The upper knee bolt retains 25.4 mm to the post's upper grain end versus
  the recorded 44.45 mm full-value softwood endpoint hypothesis: a -19.05 mm
  source margin. The five loaded-direction occurrences remain conservative
  oblique hypotheses; the seven other occurrences are unoriented envelopes.
  Transverse relocation does not resolve that existing detailing question,
  and these hypotheses are not reclassified as adopted failures.
- Positive-Y knee movement increases the post's `de` while moving toward
  the knee partner's loaded edge. The partner's opening, finished sections,
  effective-depth comparison and host/contact transfer cannot inherit the
  post improvement. The source partner geometry remains the unadopted
  six-bore proposal, distinct from the reviewed four-bore spine.
- Negative-Y floor-pair movement changes its floor partner's grain-end
  distances and spacing to the rear pair. Those translated end/row/support
  checks have not been performed; the original far-end square-end method
  limitation remains visible.
- Other-hole clearance, washer seats, tool access, changed force/couple
  placement and the revised global load distribution remain outside this
  fixed-force inversion.

Thus the concrete next design question is whether a coupled receiver/cleat
revision can accommodate roughly **41 mm** knee-pair and **3.3 mm** floor-pair
movement under the existing CD1.25 hypothesis, or a different supported
transfer layout, while resolving the preserved partner and end constraints.
The normal-duration counterparts are roughly **47 mm** and **8.9 mm**. These
are proposed-revision bounds for owner review, not adopted positions or a
new duration choice. No geometry is changed and no repair is accepted here.

| Actual artifact | SHA-256 |
| --- | --- |
| `attempt01/producer.py.snapshot` | `7589288a4a7ec9c9d5c24153800f14128866358207ead2d7b883f9c07dad42b9` |
| `attempt01/checks.json` | `6424efdf0a78d971acd5d0636cddc64344b822773b603e93267a812f1f1bde25` |
| `attempt01/bounds.json` | `ee711a5ab76158620b9ccabbec94aed175f1288cd37563a14f8fc9cc5d5147bb` |
| `attempt01/source-states.jsonl` | `bff1b2b282a78d84048536053d20d99874f6817a9ac881592b7d1de2a3fbc5cd` |
| `attempt01/receipt.json` | `d4af62076df3f9676c426da9f433a5b9749d5232ae31b0c30e8aba9a396f192f` |

All resistance, complete-joint, partner-transfer, repair-adoption and release
flags remain false. The all-30 splitting-qualification objective is unmet.
