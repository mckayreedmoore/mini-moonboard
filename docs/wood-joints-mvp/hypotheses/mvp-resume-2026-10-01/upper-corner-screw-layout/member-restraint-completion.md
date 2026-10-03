# N11 full-length member restraint sensitivity

[The producer](member-restraint-completion.py) prepares the cheapest remaining
scalar member comparison: reuse the completed fresh signed traces and evaluate
the existing NDS normal/stability equations with **full finished length, no
interior brace credit and declared end support**. It adds no frame, native, CAD,
load, geometry, hardware or stiffness calculation. **The parent completed
`rawlocal/member-restraint-completion/attempt01` with exit 0 and status
`CONDITIONAL_FULL_LENGTH_REFERENCE_SENSITIVITY`.** All same-cut references
remain conditional. This full-length sensitivity is non-adopted and supplies
no N11 acceptance or hardware-change decision.

The existing [42-body worksheet](knee-bridge-members.md) already calculated
full-length end-only kernels alongside its assumed timber weak restraints.
This producer reuses those exact helpers and reproduces their same-cut
end-only results. Its additional result is an explicit finished-geometry,
restraint and formula-domain disposition. It does not repeat force extraction,
section generation or the existing timber-restraint calculation.

## Exact scope and map

The saved packet contains 20 frame timbers and 22 unchanged blocks, six nominal
cases, 252 body states and 53,784 signed before/after traces. Preparation joins
every body to its current finished STEP identity, start/end length, gross
section, source material longitudinal axis, local section statuses and recorded
timber restraint candidates. `summary.json.member_restraint_map` contains the
exact per-body map; the grouped map below names all 42 consumed bodies.

| Bodies | Full-length scalar disposition |
| --- | --- |
| `base_floor_left`, `base_floor_right` | Straight gross rectangle; source end-only column and beam domains retained. |
| `base_header` | Straight gross rectangle; full-length weak-column domain excluded in compression. |
| `base_post_center_left`, `base_post_center_right`, `base_post_outer_left`, `base_post_outer_right` | Straight gross rectangle; source end-only domains retained. |
| `base_principal_center_left`, `base_principal_center_right` | Straight inclined members with aligned longitudinal grain; full-length weak-column domain excluded in compression. |
| `base_rail_bottom_left`, `base_rail_bottom_right`, `base_rail_service_lower_left`, `base_rail_service_lower_right`, `base_rail_service_upper_left`, `base_rail_service_upper_right` | Straight gross rectangle; source end-only domains retained. |
| `base_rail_top` | Straight gross rectangle; full-length weak-column domain excluded in compression. |
| `base_side_left`, `base_side_right` | Straight inclined members with aligned longitudinal grain; source end-only domains retained. |
| `lumber_leg_left`, `lumber_leg_right` | Recorded 1:12 rear recess/taper: no new prismatic `CL/CP` comparison. |
| `bottom_center_left_cleat`, `bottom_center_right_cleat`, `bottom_outer_left_cleat`, `bottom_outer_right_cleat` | Straight gross block sensitivity. |
| `center_post_cleat_left`, `center_post_cleat_right`, `center_principal_cleat_left`, `center_principal_cleat_right` | Straight gross block sensitivity. |
| `knee_outer_left_inner_frame_block`, `knee_outer_right_inner_frame_block` | Straight gross block sensitivity; actual continuation/restraint remains conditional. |
| `left_service_inner_lower_cleat`, `left_service_inner_upper_cleat`, `left_service_outer_lower_cleat`, `left_service_outer_upper_cleat` | Straight gross block sensitivity. |
| `top_center_left_cleat`, `top_center_right_cleat`, `top_outer_left_cleat`, `top_outer_right_cleat` | Straight gross block sensitivity. |
| `wj04_lower_full_stock_cleat`, `wj04_upper_g7_crosscut_full_stock_cleat`, `wj06_outer_lower_right_cleat`, `wj06_outer_upper_right_cleat` | Straight gross block sensitivity under their existing conditional material classification. |

Thus **40 bodies (18 frame + 22 blocks)** have a straight gross-member
sensitivity; two consumed rear legs receive explicit geometry refusals.
`knee_outer_left_spine` and `knee_outer_right_spine` are the two modified bodies
outside the saved 42-body source, retained as separate scope exclusions rather
than invented results. Plywood, local opening resistance and N09 washers remain
outside this method.

Global inclination and rotated transverse R/T assignments do not make grain
oblique. All 40 matching bodies have the saved longitudinal material axis
aligned with their geometric member axis. The API refuses an actual
longitudinal mismatch. Bored/passage and clipped/oblique terminal traces keep
their exact saved unsupported section status; they do not become intact
rectangles or physical failures.

## Pinned primary method

Only selected pure definitions are executed through the frozen inert AST loader:
`effective_beam_length`, `stability_factor`, `member_check`, `stability_kernel`
and `normal_check`. Their original producer/solve entry points do not run.
The current conditional DF-L No. 2 base values, existing size factors and
remanufactured-block assumptions are preserved. Baseline `Emin=580,000 psi`
is unchanged. Dry service, normal temperature, unincised wood and existing
`Cfu=Cr=1` remain declared assumptions, not delivered grading or inspection.

| Existing primary bytes | SHA-256 / governing location |
| --- | --- |
| [NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf), local `rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf` | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644`; printed pp. 17–18, 23–25. |
| [NDS 2024 Chapter 4](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf), same cache `nds2024-chapter4.pdf` | `52feedd07d3b672f0dd2666903cf8b481687d3da975cd3fccac545f66dfeb9ec`; §4.4.1, printed p. 33. |
| [NDS 2024 Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf), existing upper-block cache `appendix-2024-awc-20260911.pdf` | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31`; Appendix G/Table G1, printed p. 183; Eq. H-2, p. 184. |
| [NDS 2024 Chapter 2](https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf), existing upper-block cache `chapter2-2024-awc.pdf` | `6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100`; §2.3.2/Table 2.3.2. |

### Full-length beam and column calculation

Use `b = shorter section dimension`, `d = longer dimension` in mm, stresses in
MPa and the complete signed local `[N, Vu, Vv, T, Mu, Mv]` trace in N/N·mm.
Strong/weak axes are local rectangular axes, not global vertical/horizontal.

NDS Table 3.3.3 footnote 1 supplies unspecified-loading beam effective length:

```text
Lu = full finished member length
le = 2.06 Lu               if Lu/d < 7
le = 1.63 Lu + 3d          if 7 <= Lu/d <= 14.3
le = 1.84 Lu               if Lu/d > 14.3
RB = sqrt(le*d/b²)         [Eq. 3.3-5; RB <= 50]
FbE = 1.20 Emin' / RB²     [following Eq. 3.3-6]
CL = smaller_root(FbE/Fb*, .95)   [Eq. 3.3-6]

le1 = le2 = K_e L = full finished length, with declared K_e=1
FcE_i = .822 Emin' / (le_i/d_i)²
CP = smaller_root(min(FcE_1,FcE_2)/Fc*, .8)   [Eq. 3.7-1]
smaller_root(x,c) = 2x / (1+x+sqrt((1+x)²-4cx))
```

The helper's rationalized smaller root is algebraically the printed NDS root.
`Fb' = CL Fb*`, `Fc' = CP Fc*`. Square sections retain `CL=1` under §3.3.3.1.
For permanent operating columns, §3.7.1.4 limits the governing `le/d` to 50;
the construction-only 75 exception is not used. Outside-domain values remain
identified formula diagnostics, with unsupported comparison/`CP` fields null.
A tensile/zero-axial trace does not acquire a compression-domain refusal solely
because the same member's full-length column slenderness exceeds 50.

Compression reuses both same-cut Eq. 3.9-3 and strict Eq. 3.9-4:

```text
I = (fc/Fc')² + fb1/[Fb1'(1-fc/FcE1)]
              + fb2/[Fb2'(1-fc/FcE2-(fb1/FbE)²)] <= 1
fc/FcE2 + (fb1/FbE)² < 1
```

Nonpositive Euler denominators remain explicit; no undefined interaction is
reported as a pass. Tension reuses the existing conservative biaxial moment sum
and independent `CL`-reduced bending check with no tension relief. That extension
is identified separately from the literal uniaxial Eqs. 3.9-1/3.9-2. Every
comparison retains its simultaneous axial/moment tuple and saved centroid shift.
Separate force and moment peaks are never combined.

Both existing `CD=1` and conditional `CD=1.25` scenarios are recalculated from
the same cuts. The latter retains the seven cumulative full-peak day hypothesis.
It adjusts strength inputs before recomputing `CL/CP`; `Emin`, Euler references,
loads and restraint lengths do not change. There is no second duration/dynamic
credit. Current proposal permanent `CD=.9` is the separate N12 scope.

The completed parent build first performed two known-answer **reference algebra** checks:
`CP(x=.6,c=.8)=.5` and `CL(x=.525,c=.95)=.5`, including their quadratic residuals.
Returned roots were 0.4999999999999999 and 0.5000000000000001 respectively,
with residual magnitudes 1.1102230246251565e-16. It then reproduced the existing
applicable full-length kernels and same-cut normal records. The worker did not
execute those equations. No software-test suite or new mechanical/native
coupon ran.

## What end support means here

`K_e=1` is the Appendix G pin-ended, translation-restrained, non-sway
sensitivity. Rotation about transverse axes for a column is distinct from beam
roll about grain. For `d>b`, §3.3.3.4 requires bearing points to prevent roll even
when no intermediate beam support is credited. Full finished length is the
declared conservative span within those endpoint assumptions; **`K_e=1` is not
a conservative bound for an unqualified flexible/swaying whole frame**.
Appendix G.4 permits larger effective lengths where connected-member stiffness
is insufficient.

The map retains actual source timber station IDs, receiver IDs, directional
projections, bilateral tie or tension-plus-counterface conditions and contact
row identities. These are candidate restraint locations. Receiver restraint,
opening-slack take-up, stiffness/capacity and endpoint roll are not established
by their presence. `credited_interior_restraint_stations` stays empty for every
body. No length is shortened to a connection station or optimized to make a
comparison favorable. Hillman panel screws supply no brace credit.

Chapter 4 §4.4.1 also permits nominal depth/breadth restraint alternatives for
`CL=1`, including no lateral support at nominal ratio ≤2 and progressively
stronger end/edge restraint duties for larger ratios. This calculation retains
its explicit full-length beam kernel rather than assuming those support duties
from panel attachment or a receiver name.

## Completed same-cut results and exact refusal scopes

All **53,784 source traces** are classified separately for each duration
scenario. The following counts are identical for `CD=1` and `CD=1.25`:

| Per-scenario disposition | Traces | Meaning |
| --- | ---: | --- |
| `WITHIN_DECLARED_REFERENCE` | 21,755 | Finite normal/stability comparisons inside the declared member/formula domain; actual restraint applicability remains conditional. |
| `UNSUPPORTED` | 23,736 | Rear-leg nonprismatic geometry or an existing saved local-cut guard. |
| `UNSUPPORTED_NDS_SLENDERNESS_DOMAIN` | 8,293 | Compression traces on four straight members outside the full-length column domain. |
| Stated reference/elastic-stability exceedances | 0 | No exceedance among supported comparisons; unsupported records supply no strength disposition. |

| Supported-domain peak | Value | Same-cut witness |
| --- | ---: | --- |
| `CD=1` normal interaction | 0.37627531471806686 | `base_side_left`, A12-rear, before 2012.4551072943586 mm; cut index 570; signed axial `N=+226.21233547536332 N`. |
| `CD=1.25` normal interaction | 0.3089680188875682 | `base_rail_top`, K12-right, before 1062.3710999999998 mm; cut index 228; signed axial `N=+27.004271598641687 N`. |
| Eq. 3.9-4 diagnostic, both scenarios | 0.07175771414612914 | `base_floor_left`, A1-rear, before 103.66010892844 mm; cut index 50; signed axial `N=−552.2615075833634 N`. |

These maxima cover only the 21,755 supported records per scenario. They are
not complete envelopes over the other 32,029 traces or replacements for the
existing restrained-member results. The top-rail peak above is a tensile trace;
it does not require `CP`, although that member's compression traces encounter
the separate column-domain limit. Full signed force/moment tuples and centroid
shifts remain in the actual leaf, with no independent-peak combination.

The 23,736 general unsupported traces split without double counting:

| Named refusal scope | Traces per scenario | Relationship to existing evidence |
| --- | ---: | --- |
| Two rear legs, `NONPRISMATIC_RECESS_OR_TAPER_NO_PRISMATIC_FORMULA_TRANSFER` | 4,944, including 2,472 per leg | Entire consumed rear-leg scope; extending the old minimum rectangle does not qualify the finished taper. Local guards on these same traces overlap this geometry refusal. |
| Other bodies, `NON_APPLICABLE_BORE_OR_PASSAGE` | 18,048 | Existing source-cut/local-opening guard; current N08 families retain their own section/method comparisons. |
| Other bodies, `NON_APPLICABLE_END_TRIM_POINT_LOAD_DISTRIBUTION` | 672 | Existing terminal point-load placement guard; this scalar reuse does not supply local traction transfer. |
| Other bodies, `NON_APPLICABLE_INCOMPLETE_OR_TERMINAL_PROFILE` | 72 | Existing incomplete/clipped section guard. |

The three non-leg guard rows total **18,792**. They are source-method refusals,
not new N11 slenderness exclusions or physical failures. N08/source-cut results
must be joined by their actual station, section and method; this producer does
not overwrite them or assert that every guarded section lacks a separate
applicable result. Both `center_post_cleat_*`, both `center_principal_cleat_*`
and both `knee_outer_*_inner_frame_block` are entirely guarded here by
`NON_APPLICABLE_BORE_OR_PASSAGE` (312 per post cleat and 336 per other block).
Their zero supported records therefore do not imply absent member support.

### Conditional column domains and remaining restraint applicability

These values are read from the authenticated source kernels, not new worker
resistance calculations:

| Straight member | Full finished length, mm | Governing full-length column `le/d` at `K_e=1` | Actual compression-domain refusals per scenario |
| --- | ---: | ---: | ---: |
| `base_header` | 2435.225 | 63.916667 | 1,732 |
| `base_principal_center_left` | 2506.1671193155184 | 65.778665 | 2,217 |
| `base_principal_center_right` | 2506.1671193155184 | 65.778665 | 2,152 |
| `base_rail_top` | 2257.425 | 59.250000 | 2,192 |

Their compression traces cannot claim an NDS column-domain comparison from
that full-length sensitivity. Changing `CD` cannot repair a geometric domain
limit. All 8,293 domain-refused records have axial compression; tensile/zero
records are not refused on that column limit. The remaining matched straight
members retain the source domain. All source beam slenderness values are
within 50, which alone does not qualify end restraint.

For the header, principals and top rail, **actual applicability of the existing
restraints remains missing**. The full-length scenario intentionally credits
no interior support; it does not establish that the actual assembly has none.
Existing timber candidate stations and counterfaces remain recorded. Their
supported restraint duty, receiving-member continuation and loaded stiffness
must be interpreted within the actual source limits. Neither these domain
refusals nor zero supported-domain exceedances warrant adding hardware or
adopting this sensitivity as the operating restraint model.

The genuine N11 remainder is applicability of existing endpoint/interior
restraints and whole-frame stability/motion. Two rear-leg profiles require their
applicable tapered/finished-section method; the two modified spines retain
their separate current source. Bores, local profiles, receiver anchorage,
changed-hole/shared-knee compliance and loaded contact remain their named
existing scopes. No new hardware follows from a formula-domain exclusion,
and no blanket model of every member in three dimensions is prescribed.
The no-slip floor bound remains separate. A saved representative pose is not
a unique position or complete motion envelope.

## API, source hashes and parent handoff

Import is inert and requires only the standard library. `prepare(output)`
authenticates source/receipt closures and joins metadata without resistance
arithmetic or reading arrays. `build(output)` is **parent-only**, also standard
library: stream the existing JSONL and execute the selected scalar helpers.
Both require a fresh immediate child of `rawlocal/member-restraint-completion/`
and refuse existing attempts/symlinks. Source changes produce a `STOP` receipt;
supported exceedances remain results. No historical producer runs.

The invocation below is the completed parent command; its existing `attempt01`
must be retained. This annotation performs no rerun.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/member-restraint-completion.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-restraint-completion/attempt01
```

`prepare(Path(...))` and `build(Path(...))` are equivalent module APIs; add
`--prepare` for a separate metadata-only child. Build outputs are
`same-cut-comparisons.jsonl` (all signed trace identities, centroid data and
status-separated same-state results), `summary.json` (full map, kernels, known
algebra, per-member counts and governing witnesses), `sources.json`, the
producer snapshot, ignore marker and `receipt.json`. Unsupported and
outside-domain records are counted separately from reference exceedances;
null/inventory fields never constitute acceptance.

| Frozen input / prepared leaf | SHA-256 |
| --- | --- |
| Fresh 42-member `checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| Fresh 42-member `same-cut-states.jsonl` | `b516e2f7e69699d5767d90563e697ca6b91f6fce1b32ecd13e0b447b1a80d7e7` |
| Fresh 42-member `receipt.json` | `fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794` |
| Current finished `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Fresh gravity operator assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh frame comparison / response | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` / `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `fea/reinforced_timber_resistance.py` | `d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc` |
| `../member_stability.py` | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |
| This producer / `prepare02/producer.py.snapshot` | `280c1418529937c652dc1efa50389bb07733279aae9951a3b3023a59a982b6ab` |
| `rawlocal/member-restraint-completion/prepare02/summary.json` | `bb559153819c397e4d2b8a403b66de809c675a9c2da64d36fe1cdade142d2a54` |
| Same prepared child's `receipt.json` | `a42e814a866a52e8d459187c8a67ff8aaf5381f5a855362c5e462ae59c163011` |
| `rawlocal/member-restraint-completion/source-investigation.txt` | `e5be325b8c4f8766866109fb15f68c9304641209e3ebf2304ff5e3f2101af223` |

The actual `attempt01` receipt authenticates 163 source files before and after
publication. This Markdown is absent from that consumed source closure, so
this annotation preserves every frozen producer, input and result byte.

| Actual leaf under `rawlocal/member-restraint-completion/attempt01/` | SHA-256 |
| --- | --- |
| `summary.json` | `ff6b39468edf82855f688e9b711d355bebce11e20dd6ef988c18b5cbd8d12886` |
| `receipt.json` | `b5c4807e48f7836ee4ebdc50c95af3205be88c4c93772b711b60eff5ceb600c0` |
| `same-cut-comparisons.jsonl` | `b98c30740555b7417ee0e59b54c0b342e0681de9739fb686d34252d81715c9ec` |
| `sources.json` | `d227acc4c510ff8adfc47937185440e6972415a3609d06849c199000a4e66d54` |
| `producer.py.snapshot` | `280c1418529937c652dc1efa50389bb07733279aae9951a3b3023a59a982b6ab` |
| `.gitignore` | `cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b` |

`prepare02` authenticated **163 exact source files** before and after metadata
publication, with status `PREPARED_NO_RESISTANCE_EVALUATED`. AST parsing and
Ruff completed; no software tests or worker engineering build occurred.
`prepare01` retains the earlier snapshot. The bounded `gpt-6.1-sol` / configured
`xhigh` primary-source investigation is retained in ignored
`rawlocal/member-restraint-completion/source-investigation.txt`; it read the
existing PDF bytes and executed no engineering arithmetic.

Parent next integrates the completed conditional results into its existing
qualification/disposition entries. Reviewed 104 and unadopted 108 axes,
66 Hillman screws, source loads, history and all authority/release flags remain
distinct and unchanged. The API source and this actual-result annotation are frozen for parent publication;
staging/commits remain parent-owned. Existing raw/source packets stay active;
nothing is pruned, replaced or selected for archive.
