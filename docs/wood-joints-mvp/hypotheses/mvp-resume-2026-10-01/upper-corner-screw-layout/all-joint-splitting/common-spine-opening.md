# Common-shaft spine opening bound

This producer evaluates the normal-v necessary condition for the two unchanged
outer knee spines, invariant under accepted bore-pressure spreading while
retaining other fresh source-point actions. It consumes all twelve saved common
shaft states: six nominal cases on each side. It does not include permanent-only
states, update the global frame, evaluate the four proposed internal-v ties, or
establish a splitting resistance.

Its force basis is the reviewed 104-axis global connector layout and fresh
104-row connector response under the 108-axis planning inventory mass. Four
proposed internal-v ties have no global reaction rows; this diagnostic does not
transfer their separate static allocations or claim a coupled 108-axis
response. The reviewed axis census is pinned to the saved working joint
register. The four-bore section reference and fresh member screen are also
checked against the same unchanged left and right spine STEP path and hash.

## Field and geometry contract

The unchanged four-bore geometry is read from
`../rawlocal/knee-spine-net-sections/attempt02/checks.json`. The full radial
supports set the cut: common `side_1` maps to `facet007` (second-high local v),
common `side_2` maps to `facet006` (high local v), and the two retained post
bores map to `facet008` and `facet009` below the cut. The cut is halfway across
the open interval between the two high-v supports. `high_force` refuses any
support interval that intersects the cut and sums signed resultants on its
positive-v side.

The common-shaft field replaces the old side-axis point actions for `facet006`
and `facet007`. The lower post-bore force resultants come from the fresh
same-state point-action arrays. Every other fresh action retains its point,
signed force and free couple. Its signed normal-v force contributes to the
appropriate side of the cut; nonzero body-load node forces are not discarded.
Common outer-seat wood tractions must retain zero local-v force within 1e-6 N.
Fresh forces on the two common side axes remain original-source diagnostics;
their complete point wrenches are replaced once by the common fields.

For each of two axes, the producer sums the saved on-wood bore point forces and
the saved **wood-side** head or nut washer traction points for all three
receivers. It takes moments about that axis's recorded geometry datum and checks
each complete force/moment wrench against
`independently_recovered_connector_wrench` (1e-6 N, 215.9e-6 N mm). It does not
use the washer's bolt-side tractions. Bore point forces already include their
quadrature weights; no second weight is applied. The field samples contain no
separate point free couples.

The signed normal resultant above the cut is invariant with respect to the
accepted bore-pressure spreading inside the complete bore supports, while
all other fresh actions retain their source-point placement. This is not
invariance under arbitrary placement of the complete physical body boundary.
The calculation adds the exact signed above-cut nonbore force to the whole
bore resultants. It must retain complete source and updated body force/moment
accounting and the matching signed gap balance. Body-load whole wrenches and
their above-cut nodal subsets remain separate records; individual mapped node
forces do not establish physical horizontal gravity.

The source body and mapped body-load wrenches are compared with the saved
member-screen records. The updated body accounting compares the fixed source
actions plus new common fields with the source body minus the old common-axis
wrenches plus their replacements. Above- and below-cut sums must recover the
complete updated local-v force. Common bore half resultants use the verified
complete support intervals. These are accounting checks; updated whole-body
equilibrium is recorded as unclaimed.

A positive result means the zero-perpendicular-tension necessary condition
is not met within this placement scope. It is not a wood capacity, stress,
failure load, bolt replacement force or complete-joint result. A nonpositive
value does not qualify splitting resistance.

## First actual run and revised scope

The parent ran producer
`300ac19ea2e3615fe93bf8ef4fca8b64f7aa7b09bf944fea04b184fdcd572808`
in `rawlocal/common-spine-opening/attempt01/`. It exited 1 at the blanket
individual nonbore-v zero guard before a final twelve-state result existed.
The parent preserved its exact producer snapshot and `execution-stop.json`;
the stop is not a physical failure or resistance result.

The first saved witness is `knee_outer_left_spine`, `a12-rear`, action index
28, `body_load_node_2449`, role `discrete_body_load`, row −1:

| Quantity | Saved value |
| --- | --- |
| Global point, mm | `[-1257.3, -182.05, 139.7]` |
| Global force, N | `[-0.006632166973783493, -0.0026838996419623336, 0.6571792387402188]` |
| Free moment, N mm | `[0, 0, 0]` |
| Local-v station, mm | `-69.85` |
| Local-v force, N | `-0.0026838996419623336` |

Read-only inspection found 288 nonzero individual nonbore records across
the twelve saved states, all mapped body-load nodes. Some lie above the gap:
in the same first state, indices 30 and 46 lie at local-v `+69.85 mm` and
have approximately `−0.002683899642 N` and `+0.002683899642 N` respectively.
A below-gap exception alone therefore cannot repair the blanket assumption.
Their aggregate cut contribution and full wrenches must be computed and
reported by the revised producer. No node is silently deleted, and no
unverified cancellation is asserted here.

The existing fresh member screen separately records that first state's
complete mapped body-load wrench about the body's physical-node mean:
force `[3.6298465899665786e-17, 1.5178830414797062e-17, -11.736378985080606] N`
and moment `[-6.114902504797442, 24.642989417174814, -1.4675760606763788e-15] N mm`.
This saved complete force has zero horizontal components to recorded
roundoff despite the individual nonzero node components. It does not prove
an above-cut cancellation or define a complete physical gravity distribution.
The source is
`../../member-screen-attempt02/knee-bridge-gravity01/member-results.json`,
SHA-256 `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0`,
`cases[0].members[member=knee_outer_left_spine].mapped_body_load_wrench_about_node_mean`.

The revision retains every source action and limits the claimed invariance
to bore spreading. The parent completed its new `attempt02`; the failed
`attempt01` remains preserved with its original snapshot and stop report.

The revised producer is frozen at SHA-256
`297b3605b0b23735a6c3a009bdb6f06113d0d42396f914a5247b1923a8cca48f`.
Its result schema is `common-spine-bore-spreading-invariant-opening/v2`.
Read-only readiness checks authenticated 33 direct pins, 153 pins after the
common-source closure and 219 after the fresh-source closure, with twelve
common states and 134 member-source manifest entries. AST parsing and Ruff
passed. These checks did not execute `build` or the engineering arithmetic.

## Completed parent run and saved-result audit

The parent executed the frozen revised producer in
`rawlocal/common-spine-opening/attempt02/`. Independent read-only
authentication matched all **220 source pins and two outputs**, including
the unchanged producer snapshot. The run contains **12 states and 72 full
receiver-wrench recoveries**, covering each side and all six nominal cases.

| Saved artifact | SHA-256 |
| --- | --- |
| `producer.py.snapshot` | `297b3605b0b23735a6c3a009bdb6f06113d0d42396f914a5247b1923a8cca48f` |
| `checks.json` | `949770568a16880c0477109a244cc76a9b634be28fc74e6216ff8eea3a9d7a39` |
| `receipt.json` | `5f0c6a62f928f4007baabafba541e04679bb7c9f360abced5216a8e36f8d20aa` |

All twelve signed normal resultants are positive. The maximum is
**360.62265490247955 N**, left spine, `a12-left`, at local-v
**20.43463456643 mm**. Thus none of these twelve states satisfies the
zero-perpendicular-tension necessary condition in the recorded placement
scope. The result remains a required-tension lower bound, not a resistance
ratio or physical failure load.

| Case | Left required-tension lower bound, N | Right required-tension lower bound, N |
| --- | ---: | ---: |
| `a12-rear` | 313.729209 | 1.805382 |
| `a12-forward` | 329.347290 | 1.983438 |
| `a12-left` | 360.622655 | 2.831184 |
| `k12-right` | 2.964652 | 352.596627 |
| `k12-rear` | 1.829621 | 305.611324 |
| `a1-rear` | 4.090306 | 2.865272 |

The parent's requested postprocessing compared each saved updated whole-body
wrench with zero and with the corresponding saved original source wrench.
All twelve comparisons remain within the producer's recorded component
tolerances: **1e-6 N** and **0.0002159 N mm**. No producer or solver was rerun.

| Maximum absolute component over all 12 states | Saved-result audit value |
| --- | ---: |
| Updated whole-body force balance | `4.420450806915874e-8 N` |
| Updated whole-body moment balance | `3.3188393047112186e-6 N mm` |
| Updated minus original source force | `4.4204511606693586e-8 N` |
| Updated minus original source moment | `3.3188523786975566e-6 N mm` |
| Above-plus-below cut-force accounting residual | `2.842170943040401e-14 N` |
| Retained nonbore above-cut local-v contribution | `1.3756763199857284e-18 N` |

The last row verifies the aggregate above-cut cancellation for these twelve
saved states. All individual mapped-node forces remain in the source and
accounting; none was dropped to obtain that result. Source and updated
prescribed boundary actions balance numerically, and the replacements retain
the original body wrenches. This saved arithmetic does not establish elastic
timber compatibility, a compatible global response or a complete physical
boundary field. The producer's `updated_body_equilibrium_claimed` flag remains
false in the immutable result. Splitting resistance, complete joint
acceptance, permanent qualification and adoption/release flags remain false.

## API and execution

The import is inert and standard-library-only. Parent owns the one bounded
build; it authenticates the frozen sources and emits twelve cut records plus
the 72 receiver wrench recoveries. Output must be a fresh child of
`rawlocal/common-spine-opening/`.

```sh
uv run --frozen --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/common-spine-opening.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/common-spine-opening/attempt02
```

`checks.json` keeps `splitting_resistance_established`, `complete_joint_acceptance`,
`permanent_load_state_qualified`, `global_frame_feedback`,
`internal_v_ties_included_or_transferred`, `proposal_adopted`, and
`physical_release` false. It also records
`complete_physical_boundary_claimed` and `updated_body_equilibrium_claimed`
as false. Whole-body wrench accounting establishes only
accounting of the prescribed source actions and replacement fields; it does
not establish a compatible physical timber field. No new solver, resistance
or capacity model is part of this diagnostic.

## Frozen hashes

The producer's `PINS` and `STATE_SHA256` maps hold the direct hashes below. At
build time it also verifies every source and output named by the common-shaft
receipt and by the fresh member-action manifest.

| Frozen input | SHA256 |
| --- | --- |
| Common `report.json` | `dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0` |
| Common `receipt.json` | `7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda` |
| Common `input-contract.json` | `7a38255a5e4bfcc49e7e2fd74b12117de7673dca769c6b17611a29cd0aa0f3a6` |
| Common `engineering-reference.json` | `24b3eb2e865b00cf02fb448bbfb533cf37a11b56a37b8cce127cb928c0c34183` |
| Fresh gravity assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh gravity `model.json` | `c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1` |
| Fresh gravity `operators.npz` | `7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f` |
| Fresh gravity `row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Fresh frame `comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Fresh frame `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Fresh response `summary.json` | `da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70` |
| Fresh response `receipt.json` | `57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933` |
| Fresh response `global-demands.jsonl` | `f0d9bb8a8a25775a2571692183860b209708111b089f16538f7eab5d9adbe4c3` |
| Reviewed 104-axis working joint register | `c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c` |
| Fresh member `member-results.json` | `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0` |
| Fresh member `inputs.json` | `34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457` |
| Fresh member `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Fresh member `action-section-arrays.npz` | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Four-bore spine `checks.json` | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |
| Left unchanged spine STEP | `081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0` |
| Right unchanged spine STEP | `f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa` |

The twelve common state files are pinned individually:

| State | SHA256 |
| --- | --- |
| `state-00.json` | `073a42216510eb9338d1512e278dfa82753b1639a93ed6e18d87d88792299b10` |
| `state-01.json` | `9f506732b6592bf96412af7ae4a65457ea3d16c3c9293fb043269b30588ade79` |
| `state-02.json` | `024ca9345a3ffb60122d1d64b21b8cd07c61ad9ab1063459b728ceec92a7c5a4` |
| `state-03.json` | `e817ad753fec4764ef9ee01817c5981bbba8a657814f544e4e1fd349ab90974c` |
| `state-04.json` | `53cce46683db1d49d964d466b88535cfac79d9ded318a8451dc2fde505228f38` |
| `state-05.json` | `78f955b6be7a69756fee79fcc2d747e71fd4e6a9647c448cc1763409aee038ef` |
| `state-06.json` | `df5588a2fd0f6b9c543626e06a56b6935aab2425ccdc08cc91bca61340011088` |
| `state-07.json` | `e691027bf78db84a3da6fe81b23fd4d3b17a65267294debed9a5bd6a46eada0d` |
| `state-08.json` | `043b3c5937c8dc22615ac735e292ae9680a0b37f3713b3e9cefabb37b157422d` |
| `state-09.json` | `e081cd4e55b48d9677950206edf304180e9d5cb6615a2b3beb49d39d511b34c2` |
| `state-10.json` | `c67b0948a1d100240df2afd4f4b9b52073d8952732e0879b5c3656c053747ebc` |
| `state-11.json` | `d577df15f50a6948c3f9fca047c392d8709f802e73d6b8b22f2df403a992738d` |
