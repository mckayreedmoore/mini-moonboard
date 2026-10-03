# Finite timber member and opening coverage

This audit joins the current saved nominal strength comparisons to all **44
timber bodies: 20 frame members and 24 blocks**. It assesses coverage under the
existing material, duration, pressure-placement and nominal ligament-sharing
hypotheses. It performs no new strength calculation. Splitting, tangential
fracture, local compatibility, stability and permanent loading remain with
their assigned owners; their absence is not counted as a missing nominal
section calculation here.

The result is **incomplete fresh opening coverage**, not an absence of member
arithmetic. The 42-body screen contains 33,912 applicable bore-free traces.
Of its 19,872 null local traces, other fresh packets calculate 4,488; **14,208
remain without a fresh nominal opening comparison**, and 1,176 are excluded
terminal cuts. The 14,208 comprise **13,944 finished-opening traces at 1,162
stations**, plus **264 traces at 22 moved-screw exclusion stations** that are
not holes in the saved STEP. Each station represents six cases and two signed
limits. The residual lies on **24 bodies: all 20 frame members and four outer
corner cleats**. The other 18 unchanged blocks have completed finite opening
comparisons; the two modified spines have their own fresh six-bore calculation.

## Small coverage matrix

“Below one” means the named nominal comparison under its recorded hypotheses.
It does not transfer a historical force result or combine independent maxima.

| Body/section scope | Fresh proposal evidence | Numerical disposition | Exact remaining nominal scope |
| --- | --- | --- | --- |
| 42 unchanged bodies, bore-free full/recess rectangles | [Member references](knee-bridge-members.md), 33,912 traces | At C_D=1.25: timber-restraint normal 0.518822; face shear 0.817219; sufficient component bound 0.951344, below one | Bore-free nominal arithmetic is calculated. The source's 19,872 local nulls are partitioned below. |
| Two modified outer knee spines | [Fresh static replay](knee-bridge-joint-replay.md), 5,124 grain and 2,352 normal cuts | Grain tension/compression/bending 0.134417/0.077064/0.090194; regional shear/torsion 0.416327; constructed normal pressure 0.615570, below one | No missing named finite nominal comparison in this replay. Original four-bore descriptors are overridden, not reused as six-bore strength geometry. |
| Six longitudinally bored header/inner cleats | [Remaining sections](knee-bridge-remaining-sections.md), 1,968 limits | Normal diagnostic 0.020888; same-state shear/torsion 0.137945, below one | None in the existing finite rectangle-subset hypothesis. Sound wood omitted by the subset does not make this a local stress bound. |
| Twelve remaining corner/service blocks | Same fresh packet, 2,304 limits | Normal diagnostic 0.001795; shear/torsion 0.032102, below one | None in the existing finite bore-chord section hypothesis. |
| Header paired-bore centers | Same fresh packet, 72 limits at six stations | Normal diagnostic 0.163057; shear/torsion 0.348582, below one | 936 additional source-null traces remain on the header, including paired-bore shoulders/interior stations and screw openings. Six centers do not cover all header openings. |
| Top rail, four top-corner bores | [Fresh physical pressure](knee-bridge-top-rail.md), 144 traces | C_D=1.25 face/bound 0.976448/0.976501, below one. C_D=1 bound 1.220627, with 14 face/bound exceedances | 516 source-null traces elsewhere: 372 finished-opening traces and 144 moved-screw exclusion traces. |
| Four outer corner cleats | Fresh [transfer](knee-bridge-corner-replay.md) and [bolt references](knee-bridge-corner-references.md); nominal timber sections remain [source-104](corner-group-finish.md) | Source-104 grain shear/torsion peak 0.334875, below one; eight earlier deciding cuts have bound 0.241977. Neither is a fresh proposal pass | Refresh grain normal/shear/torsion from each cleat's fresh physical actions. The 42-body ledger leaves 1,008 bore traces on these four bodies without fresh comparisons. |
| Other frame openings, rear-leg bores, service passages and screw voids | Fresh signed member actions; finished geometry/intervals and some exact sections are saved | No fresh nominal section strength comparison at the residual stations | 11,748 source-null traces beyond header/top rail/four cleats: 11,628 finished-opening traces and 120 moved-screw exclusion traces. |
| Trimmed runner ends, inclined side/principal bases, rear-leg tips | Source finite outward profiles and signed actions | **Inapplicable to the point-load rectangle method**, not an exceeded strength ratio | 98 stations / 1,176 traces. The declared source supplies no terminal pressure field; do not divide a finite end-point load by vanishing slice area. |

The original C_D=1 42-body screen retains 74 face exceedances and 166
component-bound exceedances. The C_D=1.25 coefficient-5 sensitivity reaches
1.054428; it is explicitly non-adopted. The fresh top-rail point-placement
diagnostic bound is 1.184430 at C_D=1.25; physical pressure placement is the
recorded working assumption. These are calculated sensitivities, not missing
checks. The 8,293 end-only slenderness exceptions are retained in the member
packet and are not added to the opening gap. The parent owns restraint/stability
disposition and the permanent-load comparison.

## Which source can carry forward

The reviewed geometry/inventory has **104 bolts**. The four-bolt knee proposal
has **108 bolts**, with the same 44 timber bodies and 66 Hillman axes. Its
global connector inventory still has 104; the four bridge bolts are internal
static allocations with no new receiver-interface rows.

Fresh member, remaining-section, rail-pressure and spine packets use the six
nominal proposal-frame cases, mass **225.19791414318078 kg**, dead factor
**1.1110134616260479**, 250 lb × 2, signed 300 N and the original 100 mm lever.
The original member geometry JSON remains byte-identical. That identity carries
finished section recipes forward for the 42 unchanged timbers; it does not
carry old forces, local cut wrenches, utilization or acceptance forward.

The current effective STEP hashes match the 42 unchanged-body descriptors.
The four corner cleat hashes also match the source-104 group worksheet. That
worksheet contains 101,276 cuts across grain and transverse directions under
the original local transfers. Its geometry, bore-wall integration and nominal
section helpers are reusable. Its numerical pass remains source-104 evidence.
The [eight-cut net-section worksheet](corner-net-section.md) is an even narrower
source-104 comparison, not coverage of every new cleat state.

The source-104 [top-host packet](top-host-net-sections.md) contains 156 nominal
traces on each corrected side, at 13 recorded stations, with C_D=1.25 bounds
0.553263 left and 0.546025 right. All **312** are inside this audit's fresh gap.
Their geometry can carry forward; their loads cannot. The original rail
point-placement exceedance was separately refreshed with current physical
pressure. No equivalent fresh section refresh exists for the side hosts.

The 160 matching saved CAD sections in the member geometry packet provide
area, centroid, covariance and connectivity only. Their body distribution is
top rail 6, header 105, outer right post 21, right inner knee block 9 and right
spine 19. The modified right spine requires its explicit geometry override.
No exact-area record is itself a strength pass. Old corrected-side sections
whose STEP hashes differ remain inapplicable.

## Retained base recess and original notch identity

The retained **1:12 runner-clearance recess is cut into `lumber_leg_left` and
`lumber_leg_right`**, not into `base_floor_left/right`. Its maximum X removal
is 38.1 mm from an 88.9 mm width, leaving 50.8 mm, with constant 139.7 mm
section depth and a 457.2 mm grain-aligned return. Runner members instead have
their own flush front/rear end profiles and four retained bolt bores each.

The original square-notch source is
[compact_floor_recess_frame.py](../../../../../mini_moonboard/compact_floor_recess_frame.py):
an open inner-face cut with `NOTCH_TOP_Z_MM=141.7`, an explicit 2 mm shoulder
gap and no credited shoulder bearing. The later
[taper source](../../../../../mini_moonboard/compact_floor_taper_frame.py)
replaces that shoulder with the 1:12 runout; its cutter is still named
`leg_taper_recess_<side>` and tagged `tab_notch`. That tag is not evidence of
an additional surviving square notch. The
[flush source](../../../../../mini_moonboard/compact_floor_flush_frame.py)
retains the taper dimensions and updates the trimmed leg profiles.

The [current STEP rebind](../../evaluation-resume-2026-09-24/current-taper-geometry-rebind-attempt01/README.md)
authenticates the actual current leg geometry. Left STEP SHA-256 is
`1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065`;
right is `e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4`.
The right source includes its recorded −3.175 mm translation relative to the
older kerf-right taper. Local dimensions match; old global coordinates must
not silently replace the current datum.

The fresh 42-body screen already checks **51 bore-free reduced-profile
stations per leg**, or **1,224 signed traces across both legs**, using the
actual retained rectangle and its centroid. Its overall leg component-bound
peaks at C_D=1.25 are 0.180320 left and 0.175964 right. There is therefore no
missing bore-free nominal normal/shear/torsion comparison created merely by
calling the recess a notch. Each leg still has **27 bore-intersecting stations
/ 324 traces** with no fresh net-section strength comparison, plus 18 excluded
terminal stations / 216 traces. Those are the exact nominal gaps.

The original [floor_taper_checks.py](../../../../../scripts/floor_taper_checks.py)
uses a conditional EC5 support-notch reduction with the existing US ASD shear
reference. Its `checks` API accepts the preserved taper/flush candidates, not
this wood-joint proposal. Its factor of one was never established as a bound
for the full combined-load taper problem; see the existing
[method review](../../../../../docs/history/taper-method-applicability-review.md).
Recalculating that factor cannot fill a missing fresh net section or create a
new adopted resistance. Taper-edge transverse tension, notch-root splitting
and tangential fracture belong to the splitting peer. This audit commissions
no new local fracture law, notch factor, geometry change or native run.

## Exact finite residual and all-body census

The completed machine ledger is
[`rawlocal/member-opening-coverage/attempt03/coverage.json`](rawlocal/member-opening-coverage/attempt03/coverage.json).
`uncalculated_fresh_opening_stations[]` lists every residual station with body,
station/index, feature IDs, both source trace indices, all six cases, opening
identity kind, source-104 host comparison availability and source-104 corner
method availability. `opening_feature_inventory[]` joins every saved bore or
passage interval to those station indices. `inapplicable_terminal_stations[]`
retains every excluded profile station. Each body also retains its saved
outward profile planes and current/effective STEP binding.

The inventory has **314 interval descriptors**: 298 unchanged cylindrical
patches, 12 corrected transverse-bore descriptors and four moved-screw shaft
exclusions. Thus **310 describe finished voids**, while four explicitly do
not claim a finished cut. The two spines add four actual proposal bores in
their separate override, for **314 finished-void descriptors** across the
effective proposal plus four unmachined exclusions. These are geometric
descriptor counts, not purchased-fastener counts or drill sizes. Existing
radius-2.0701 screw voids remain CAD envelopes; no SPAX resistance, Hillman
pilot size or new machining instruction is inferred.

Below, F is the original interval-descriptor count, R is fresh bore-free
reference traces, O is refreshed original-null opening traces, G is the
uncalculated original-null opening traces (including the separately named
screw exclusions), and X is inapplicable terminal traces. The spines' dashes
mean their six-bore replay is counted separately, not zero strength demand.

| Timber body | F | R | O | G | X |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_floor_left` | 4 | 1632 | 0 | 312 | 48 |
| `base_floor_right` | 4 | 1632 | 0 | 312 | 48 |
| `base_header` | 22 | 2808 | 72 | 936 | 0 |
| `base_post_center_left` | 4 | 300 | 0 | 288 | 0 |
| `base_post_center_right` | 4 | 300 | 0 | 288 | 0 |
| `base_post_outer_left` | 6 | 396 | 0 | 432 | 0 |
| `base_post_outer_right` | 6 | 396 | 0 | 432 | 0 |
| `base_principal_center_left` | 19 | 2616 | 0 | 1212 | 168 |
| `base_principal_center_right` | 19 | 2592 | 0 | 1236 | 168 |
| `base_rail_bottom_left` | 11 | 900 | 0 | 684 | 0 |
| `base_rail_bottom_right` | 11 | 984 | 0 | 600 | 0 |
| `base_rail_service_lower_left` | 11 | 912 | 0 | 684 | 0 |
| `base_rail_service_lower_right` | 11 | 984 | 0 | 600 | 0 |
| `base_rail_service_upper_left` | 11 | 912 | 0 | 684 | 0 |
| `base_rail_service_upper_right` | 11 | 984 | 0 | 600 | 0 |
| `base_rail_top` | 14 | 2256 | 144 | 516 | 0 |
| `base_side_left` | 21 | 2952 | 0 | 1368 | 156 |
| `base_side_right` | 21 | 2952 | 0 | 1368 | 156 |
| `bottom_center_left_cleat` | 4 | 228 | 192 | 0 | 0 |
| `bottom_center_right_cleat` | 4 | 228 | 192 | 0 | 0 |
| `bottom_outer_left_cleat` | 4 | 228 | 0 | 192 | 0 |
| `bottom_outer_right_cleat` | 4 | 228 | 0 | 192 | 0 |
| `center_post_cleat_left` | 4 | 0 | 312 | 0 | 0 |
| `center_post_cleat_right` | 4 | 0 | 312 | 0 | 0 |
| `center_principal_cleat_left` | 4 | 0 | 336 | 0 | 0 |
| `center_principal_cleat_right` | 4 | 0 | 336 | 0 | 0 |
| `knee_outer_left_inner_frame_block` | 4 | 0 | 336 | 0 | 0 |
| `knee_outer_left_spine` | 4 + 2 new | — | — | — | — |
| `knee_outer_right_inner_frame_block` | 4 | 0 | 336 | 0 | 0 |
| `knee_outer_right_spine` | 4 + 2 new | — | — | — | — |
| `left_service_inner_lower_cleat` | 4 | 228 | 192 | 0 | 0 |
| `left_service_inner_upper_cleat` | 4 | 228 | 192 | 0 | 0 |
| `left_service_outer_lower_cleat` | 4 | 228 | 192 | 0 | 0 |
| `left_service_outer_upper_cleat` | 4 | 228 | 192 | 0 | 0 |
| `lumber_leg_left` | 4 | 1932 | 0 | 324 | 216 |
| `lumber_leg_right` | 4 | 1932 | 0 | 324 | 216 |
| `top_center_left_cleat` | 4 | 228 | 192 | 0 | 0 |
| `top_center_right_cleat` | 4 | 228 | 192 | 0 | 0 |
| `top_outer_left_cleat` | 4 | 180 | 0 | 312 | 0 |
| `top_outer_right_cleat` | 4 | 180 | 0 | 312 | 0 |
| `wj04_lower_full_stock_cleat` | 4 | 228 | 192 | 0 | 0 |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 4 | 216 | 192 | 0 | 0 |
| `wj06_outer_lower_right_cleat` | 4 | 228 | 192 | 0 | 0 |
| `wj06_outer_upper_right_cleat` | 4 | 228 | 192 | 0 | 0 |
| **42-body total** | **306** | **33,912** | **4,488** | **14,208** | **1,176** |

The G column's finished-void subset is 13,944. Subtract 144 exclusion traces
from `base_rail_top` and 60 from each `base_side`; all other G entries refer
to finished geometry. The four corner G entries total 1,008. All-frame G is
13,200, of which 12,936 is finished-opening scope.

## Smallest next arithmetic

1. **Refresh the four corner cleats' grain comparisons only.** Consume the
   24 fresh physical cleat states in `knee-bridge-corner-replay/attempt01`,
   each with its weight once. Reuse the source-104
   `corner-group-finish.py` pressure/cut definitions and
   `corner-net-section.py:nominal_section`; reuse the unchanged finished
   geometries. Recover fresh before/after grain cuts and compare normal,
   regional transverse shear and full torque under the existing sharing
   hypotheses. Do not rerun the historical producer or recalculate its
   transverse fracture worksheet. The prior 101,276-cut count is not a new
   required workload: it includes transverse planes owned by the peer.
2. **Refresh the two corrected side-host opening families.** Their existing
   13 stations per side and exact bore geometry are already available.
   The smallest original-point arithmetic is 312 fresh signed comparisons
   with complete saved member actions. To claim the local physical-pressure
   interpretation, instead replace each corner interface once using the
   fresh host actions and the existing top-host pressure helpers. A whole
   interface balance alone does not reproduce an internal cut inside its
   transfer footprint. Report which of these existing hypotheses is used.
3. **Complete the residual frame-opening section comparisons by recorded
   feature family.** Use the exact station ledger and fresh saved signed
   actions; preserve all six wrench components and actual centroid shifts.
   Reuse the header's paired-bore geometry/helper at its already recorded
   shoulder and interior stations where applicable, rather than treating
   six center passes as all-header coverage. Reuse saved exact section
   properties and full-width bore-chord helpers within their existing
   applicability. Service passages and blind/partial screw voids require
   their actual geometry; a cylindrical face radius or interval alone is
   not authority to remove a full-width stripe or assign rectangular torsion.
   Where the saved geometry lacks a supported section recipe, record that
   exact feature/section input as unavailable before arithmetic; no CAD or
   native rerun is authorized by this sidecar.

The completed ledger does not prescribe a new continuous-station search,
fracture law or extra case. It identifies which current recorded stations
have no nominal comparison. A supported finite bound covering several
stations can reduce arithmetic without changing this coverage obligation.
The four moved-screw envelopes need their own nominal geometry disposition
within the existing candidate policy; they must not be called observed holes.

## Reusable producer and receipt

[member-opening-coverage.py](member-opening-coverage.py) exposes inert import
and `build(output)`. It reuses the existing member producer's pin dictionary,
classifier and authentication functions; no geometry, strength or frame
pipeline is copied or executed. It reads seven saved results, binds their
receipts, joins saved trace identities, authenticates the 44 effective timber
bindings and preserves the spine overrides. It authenticates **68 consumed
pins before and after** and writes only a fresh immediate child of its own
ignored directory.

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/member-opening-coverage.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-coverage/fresh-child
```

Completed `attempt03` has status
`COMPLETE_FINITE_SOURCE_JOIN_WITH_EXACT_GAPS`. Coverage SHA-256 is
`a9dc39d5dbd153c7928923caf79dcf678e653c0b707a35514e1177c8bd4337b2`;
receipt SHA-256 is
`5d9dba87ff93e0a218d5c74d7dc4830708bf2ac4b263bf229dde69b245737f02`.
The output receipt hashes coverage, producer snapshot and ignore file.
Attempts 01/02 preserve the earlier coverage join and subsequent explicit
finished-void/exclusion partition; nothing was removed. Only finite source
authentication, inventory counting and coverage joining ran. No software
tests, CAD/native/frame execution, review loop, staging or commit ran.

This sidecar and its final ignored ledger remain active for the parent's
numerical assessment. Source packets, historical runs and foreign work stay
active or recoverable at their existing paths; no archive or prune occurred.
There are no bulky permanent artifacts: only the producer and this note are
new source files, and the raw coverage inventories are ignored. Formal row
status is not used as a substitute for the exact missing calculations above.
