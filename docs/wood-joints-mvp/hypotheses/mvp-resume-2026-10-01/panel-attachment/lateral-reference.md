# Generic No. 10 screw lateral and simultaneous loading references

## Current all-two-receiver force replay

`results/lateral-attempt02/` consumes the unchanged 792 records in
`results/attempt08-all-two-receiver/`, bound to
`two-receiver-frame-attempt03/`. It generates no force allocation. The generic
lateral references remain **386.752 N / 463.413 N** for the two declared plywood
scenarios. Using the larger reference and optimistic full nominal thread
projection, the modeled-gap combined index peaks at **2.724895** in K12-rear,
`round_panel_upper_right_rim_4`: simultaneous **V=1274.054 N, T=625.635 N**.
Twelve nominal records exceed that unadjusted reference scenario.

Separately, A12-rear `round_panel_upper_left_edge_2` has **T=1836.884 N,
V=807.662 N** and withdrawal term **1.567661**. No finite lateral reference
can make that same-state combined comparison pass. These are conditional
generic comparisons, not a Hillman rating or a physical failure claim.
Head transfer retains its independent reference deficit. Bounded fixed-force
seating supplies neither a unique pose nor a motion envelope.

Current comparison SHA-256:
`1a08d6b241c3039985dfaf71cb75fa258b5d4a52fd64abf18cb1391e83088e89`;
receipt `6d9b4dc09c345c24561ce53f9a3d9a7c2c2539de98f581ae8a28175c00398337`;
same-state CSV `cc2638f59a71dc1c3c74e1e6a2ce81f6ba4be25ce4ce6531d6d701624e124bfa`.
The executed producer/snapshot SHA-256 is
`8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2`.
Use `--source results/attempt08-all-two-receiver --output results/lateral-attemptNN`
with full repository paths and a fresh numbered directory. Prior output01 and
its executed snapshot remain preserved.

## Preserved six-joint and softer-law comparisons

The declared generic NDS lateral references are **386.75 N** for other/unknown
plywood and **463.41 N** for Structural I/Marine plywood. Both are governed by
yield mode **IIIs**. The favorable 100 N/mm axial allocation requires
**1876.16 N** lateral reference at upper-left `rim_4`, A12-rear, modeled gaps.
That requirement is **4.05 times** the larger declared lateral reference.
The same-state combined index there is **2.9093**; the envelope over that
allocation's modeled-gap states is **2.9446** at a different screw.

These are unadjusted, contacting-member, standard wood-screw references under
explicit hypotheses. They establish no Hillman 42605 rating, measured product
law, adjusted capacity, complete-joint acceptance or physical release. The
independent **277–629 N head references remain failed** across all three saved
allocations; no head capacity or favorable duration factor is introduced.

## Frozen force allocations

[`lateral_reference.py`](lateral_reference.py) consumes the existing
`screw-states.csv`, `comparison.json`, `receipt.json`, and producer snapshot in
each packet:

| Saved packet | Axial stiffness hypothesis | Screw states |
| --- | ---: | ---: |
| `results/attempt05-baseline/` | 2689.678816784642 N/mm | 792 |
| `results/attempt06-k1000/` | 1000 N/mm | 792 |
| `results/attempt07-k100/` | 100 N/mm | 792 |

Each packet has six cases at zero and modeled frame gaps, with 66 screws per
state. All 132 lateral components retain 2689.678816784642 N/mm. The comparison
is bound to its **saved producer snapshot**, not the concurrently maintained
`attachment_screen.py`. The old packets are unchanged. No original force
record is regenerated, no stiffness sweep is repeated, and no new frame
allocation is produced. The newer all-two-receiver frame is outside this
calculation; the parent owns its execution and integration.

The current receiver inventory joins each saved screw to its panel and timber
receiver. All 66 nominal receiver overlaps are 45.24375 mm to rounding. The
saved receiver grain directions and screw axes are perpendicular within
3.17e-10 in their unit-vector dot product. This supports the declared
side-grain geometry in the model; it does not inspect delivered timber or
installed screws.

## Explicit geometry, material and steel hypotheses

The primary sources are the pinned AWC 2024
[Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf)
and [Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf)
in `../../upper-block-strength-2026-10-01/source-cache/`.
The cached Chapter 12 contains specification pages despite its
`withCommentary` filename; the calculation does not presume an unavailable
Commentary rule. Appendix I and L are identified as nonmandatory in that source.

| Input | Declared basis |
| --- | --- |
| Nominal diameter `D` | Standard No. 10, **0.190 in**, Appendix Table L3, printed p.193 |
| Effective lateral diameter `Dr` | **0.152 in**, Table L3 standard rolled-thread/reduced-body hypothesis; not a measured 42605 root |
| Screw nominal length | 63.5 mm purchase policy, not verified installed length |
| Plywood side-member bearing length | **18.25625 mm**, the actual thickness used by the saved geometry; not a field measurement |
| Timber nominal penetration to tip | `63.5 - 18.25625 = 45.24375 mm` |
| Tapered tip `E` | `2D = 9.652 mm`, permitted hypothesis in §12.3.5.3/Table L3 |
| Timber dowel bearing length | `p - E/2 = 40.41775 mm`, §12.3.5.3 |
| Timber bearing strength `Fem` | **4650 psi**, rounded Table 12.3.3 small-diameter value at DF-L `G=.50`, pp.93–94 |
| Plywood bearing strength `Fes` | **3350 psi** for other grades/unknown ply species, or **4650 psi** for Structural I/Marine, Table 12.3.3B, p.95 |
| Bending yield strength `Fyb` | **80,000 psi**, generic low/medium-carbon steel wood-screw estimate for nominal `D=.190`, Table 12L note 2, p.115 and Appendix I, pp.185–186 |
| Reduction term `Rd` | **2.2 for every mode**, Table 12.3.1B, p.92, because effective diameter is below 0.17 in |
| Face separation for the reference | **Zero**, §12.3.1 contacting-member hypothesis |

The small-diameter timber bearing value is independent of the direction of
lateral load relative to grain. No large-diameter parallel/perpendicular
formula is substituted. The `K_theta` multiplier in the reduction-table
footnote applies when nominal diameter is at least 1/4 in and root diameter
is smaller; it does not apply to this nominal 0.190 in screw.

Both members use the root diameter conservatively. The full-body exemption
in §12.3.7.2 requires thread bearing no greater than one quarter of the
member's bearing length. An illustrative cut-thread length of approximately
`2L/3 = 42.3333 mm` would start about 21.1667 mm below the head, shortly beyond
the 18.25625 mm panel, and would exceed that quarter-length criterion in the
timber receiver. Thus this calculation does not silently use the nominal
0.190 in body for its lateral resistance. The rolled-thread and cut-thread
dimensions are generic alternatives; conformity of the delivered screw to
either standard is unresolved.

The nominal model penetration exceeds the §12.1.5.6 minimum `6D = 28.956 mm`,
including the tip. Minimum penetration, effective withdrawal thread length,
and reduced dowel bearing length are different quantities. The modeled bore
envelope and the historical occupied diameter/length do not establish any of
the delivered product dimensions or engagement.

## Six lateral modes

The existing [`fea.dowel_yield.single_shear`](../../../../../fea/dowel_yield.py)
primitive receives explicit bearing intensities `Fe * Dr`, dowel moment
`Fyb * Dr^3 / 6`, member lengths, zero separation and the six `Rd=2.2` terms.
For these inputs it supplies the six Table 12.3.1A single-shear references:

| Yield mode | Other/unknown plywood, N | Structural I/Marine plywood, N |
| --- | ---: | ---: |
| Im | 2274.04 | 2274.04 |
| Is | 740.00 | 1027.16 |
| II | 713.98 | 765.52 |
| IIIm | 767.25 | 816.39 |
| **IIIs** | **386.75** | **463.41** |
| IV | 476.05 | 520.19 |

The minimum of all six governs. The large Im value is not an available screw
lateral reference. No SPAX or SDS capacity, stiffness, pilot rule or
installation requirement is transferred. The shared bolt-specific wrapper is
not used for this small-diameter wood-screw calculation.

## Same-state §12.4.1 comparison

For each saved screw tuple, `V` is its lateral resultant, `T` its withdrawal
force, and `R = sqrt(V^2 + T^2)`. Equation 12.4-1 is evaluated as

```text
I = V^2 / (R Z) + T^2 / (R A),
A = W p_thread,
W = 2850 G^2 D lbf/in,    timber G = .50.
```

The equation formally uses adjusted `Z'` and `W'`. Here unit adjustment
hypotheses are explicit, and the resulting index is an **unadjusted reference
comparison**, not an adopted adjusted design check. `I > 1` exceeds that
declared combined reference. Independent lateral and withdrawal peaks are
never paired.

The four effective timber thread-penetration hypotheses are reused from the
existing worksheet:

| Effective thread penetration | Unadjusted withdrawal reference `A` |
| --- | ---: |
| 30.0 mm | 711.23 N |
| 38.1 mm | 903.27 N |
| 42.3333 mm, illustrative `2L/3` thread length | 1003.63 N |
| 45.24375 mm, full nominal timber projection | 1072.63 N |

The last row is the favorable reference, not measured effective thread.
These four withdrawal hypotheses share the same saved nominal lateral
bearing geometry. Two plywood references times four withdrawal references
give **eight scenarios and 19,008 same-state comparisons** on 2,376 saved
screw states. The full signed lateral components remain in the derived CSV.

With the most favorable declared plywood and withdrawal references:

| Saved allocation | Zero-gap maximum `I` | Modeled-gap maximum `I` | Same screw at modeled-gap maximum | Simultaneous `(V,T)`, N |
| --- | ---: | ---: | --- | ---: |
| Baseline | 2.4211 | 2.5965 | K12-rear, upper-right `rim_4` | (1214.27, 623.10) |
| Axial 1000 | 2.4819 | 2.6338 | K12-rear, upper-right `rim_4` | (1231.75, 635.53) |
| Axial 100 | 2.7922 | 2.9446 | K12-rear, upper-right `rim_4` | (1376.51, 653.45) |

There are respectively 12, 11 and 10 modeled-gap screw states exceeding even
these favorable combined references. Other/unknown plywood instead gives
modeled-gap envelopes **3.0586, 3.1020 and 3.4765**. Shorter effective threads
increase the withdrawal term. The complete scenario envelopes and governing
tuples are retained; favorable passing individual rows do not establish a
passing allocation or complete joint.

For `B = T^2/(R A) < 1`, the required lateral reference is
`Z_required = V^2/[R(1-B)]`. If `B >= 1`, no finite positive lateral reference
can make that simultaneous tuple pass. The baseline has six such states at
zero gaps and five at modeled gaps. The 1000 N/mm allocation has two at zero
gaps and none at modeled gaps; the 100 N/mm allocation has none in either set.

The modeled-gap 1000 N/mm allocation requires up to **10,432.88 N** at
upper-right `edge_2`, K12-rear, `(V,T)=(847.88,1239.85) N`. For 100 N/mm, its
**1876.16 N** requirement occurs at upper-left `rim_4`, A12-rear,
`(V,T)=(1360.77,794.79) N`. At that latter same state, using `Z=463.41 N`
gives lateral term **2.5356**, withdrawal term **0.3737**, and total **2.9093**.
This is the requested available-versus-required comparison; it does not mix
that screw's withdrawal with another screw's lateral peak.

## Applicability and adjustments

The generic equation path requires standard screw geometry, a defensible
bending-yield basis, applicable installation, sufficient edge/end distances
and spacing to prevent splitting, the required penetration and contacting
faces. Actual 42605 root/thread conformity and `Fyb` remain unestablished.
The side-member panel grade is a hypothesis; no grade is claimed inspected.
The saved compatible allocations include positive normal screw opening,
reaching 9.16 mm at the 100 N/mm withdrawal peak. A saved face-contact inventory
does not establish contacting faces at every loaded screw. These zero-separation
lateral references therefore cannot be adopted for an unverified separated
connection. No gapped connection model is added here.

The pinned [Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
Table 11.3.1 identifies applicable adjustments. This arithmetic applies no
duration, moisture, temperature or treatment enhancement or reduction and
does not establish their end-use applicability. No duration factor is selected
to close a deficit. §11.3.6 sets `Cg=1` and §12.5.1.1 sets `C_delta=1` for
these sub-quarter-inch fasteners; those rules do not establish splitting,
plywood tear-out, receiver support or compatible group sharing. The reference
is for side-grain insertion, not withdrawal from end grain. Direct yield
equations use the declared penetration; the common-table `p/10D` multiplier
is not applied again. No toe-nail or metal-side-plate enhancement applies to
the declared geometry.

Section 12.2.2.5 independently limits withdrawal by the screw's tensile strength
at its root. The output records required mean tensile stress at the hypothetical
root as a demand only. `Fyb` is a bending reference and does not supply a tensile
capacity. The existing head sensitivities, **276.825–628.941 N**, remain separate.
The modeled-gap peak withdrawal/head-reference ratios, even using the largest
head reference, are **2.8805, 1.9713 and 1.4565** for the three allocations.
The head limit is neither replaced by timber withdrawal nor inserted as an
invented capacity in the combined equation. Measured product laws, Hillman
resistance, steel-root capacity and every acceptance/release flag remain false.

## Reproduction and retained evidence

Attempt01 was executed with its preserved original producer snapshot, using:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/lateral_reference.py
```

The executed attempt01 snapshot remains at SHA-256
`42be7313c3e18b2f38b6e15b2dc03d60d795249e8284f677eec0b861fb5e3e64`.
It authenticates the existing numeric result. The maintained source is now
`fresh-output-v2`, SHA-256
`8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2`.
This version adds output selection, relative source-path normalization,
fresh-directory protection, and explicit binding of the executing source to
the new report, snapshot and receipt. It has not rerun attempt01. The generic
equations and its recorded numeric evidence are unchanged.

The optional `--output` retains the original default
`results/lateral-attempt01/`, and permits only fresh directories named
`lateral-attempt` followed by digits directly under this packet's `results/`.
Any existing output directory is rejected. The source reader accepts one to
three completed 792-state packets through repeated `--source` arguments;
relative paths are resolved. Future runs bind each saved receipt, comparison,
CSV and producer snapshot, capture the executing source bytes/hash, and write
that captured producer snapshot. They do not require the upstream maintained
`attachment_screen.py` to retain its historical byte hash.

After the parent-owned panel attempt08 receipt is written, the parent can run
only that new allocation into fresh attempt02 from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/lateral_reference.py \
  --source docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/results/attempt08-all-two-receiver \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/results/lateral-attempt02
```

The explicit source argument omits the three old default allocations. This
command has not been executed here. The calculation does not call the
producing frame or panel solver. The parent owns future execution and
integration; existing result packets remain preserved.

| Consumed artifact | SHA-256 |
| --- | --- |
| Baseline CSV | `7035199a52ae0fdcdbc3b65ed53fe9f6f0e87f8c7b829a9ccc5ad3247fe1c892` |
| Axial 1000 CSV | `99b6b0b0d081464a40375716ac94d873468c6313dcae3fbdafb8b87d8775bd84` |
| Axial 100 CSV | `d8c2048d299d083e2e954e95e240169ee1432199803daf3baab408871ed4c27e` |
| All three saved panel producer snapshots | `e791bb3e914fcbfa70e4e28deb827d0cfc68d93d8c1a11e50e9dc2e52ad11e61` |
| Chapter 12 PDF | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| Appendix PDF | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| Chapter 11 PDF | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| Shared six-mode primitive | `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45` |
| Executed attempt01 producer snapshot | `42be7313c3e18b2f38b6e15b2dc03d60d795249e8284f677eec0b861fb5e3e64` |
| Maintained `fresh-output-v2` source | `8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2` |
| Derived `same-state-references.csv` | `a9c66e750e24207e599ed05f019272e0cb8449af528f05d89dd6e75ad806de4a` |
| Derived `comparison.json` | `1a3b02dc4a206b1c578b5f1387e3b8b8b71f8cd524d59930e1598230c3a78e48` |
| Derived `receipt.json` | `daf913ba3342f9887c3512ba984fe329cb66282608d3bd01e1b19473d5dcacdd` |

All consumed comparison, receipt, receiver and law-inventory hashes are in the
derived report. The CSV, report, snapshot and receipt total 1,316,743 bytes;
three ignored PDF table previews retain the inspected root, yield-mode and
bearing tables without another PDF copy. An initial stop while reading the
older baseline's metadata is retained in `startup-stop.json`; the final source
reader uses its frozen scalar-law inventory. No tests, reviews, CAD, native or
frame solves, commits, staging or other agents were used. These two maintained
files and the local result packet stay active; old force packets stay retained.
No archive or pruning operation occurred.
