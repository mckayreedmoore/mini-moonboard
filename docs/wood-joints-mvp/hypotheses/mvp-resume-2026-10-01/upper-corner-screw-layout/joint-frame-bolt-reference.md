# Compatible original104 bolt references

This packet postprocesses the separately source-bound original **104-axis
coupled frame sensitivity**. Its required inventory is fourteen states: six
live cases and gravity-only, each at zero and nominal clearance. It compares
only actual audited, accepted force fields. The source
`joint-frame-action-reconciliation` receipt and compatible response remain
the force authority. No knee-bridge proposal force or accepted isolated
shaft result is reused.

## Exact comparison scope

The 100 retained scalar connector axes provide 100 simultaneous T/V
comparisons per accepted state. Signed components, directions, receiver identities and axial rows
come from the original 1,888-row sourceD map. Each selected row must be
available in the reconciliation mask. The twenty replaced knee rows are
unavailable placeholders; they cannot be consumed as zero bolt demands.

Pure existing helpers supply nominal UNC thread tension and same-section
smooth-shank average T/V material references at the declared 92 ksi scenario.
These references contain no bending. Candidate lateral comparisons retain
the existing rounded DF-L Fe scenario, with the top corners retaining their
separate diameter-dependent Fe formula; retained 3/8- and 1/2-inch bolts retain
the diameter-dependent primary NDS route. The twelve end-grain axes use the
existing Ceg=0.67 zero-interface-gap single-fastener route within its recorded
domain. C_D is 1.0 for the recorded live reference and 0.9 for permanent
lateral references. These are conditional single-fastener comparisons before
group, detailed geometry and complete receiver/joint qualifications.

The scalar ideal-annulus wood mean uses the existing 625 psi Fc-perpendicular
reference without a duration multiplier. It records an ideal reference; it
does not establish actual support, pressure distribution or washer metal
resistance. The partial `center_principal_right_2` seat retains its support
limit. The source scalar model still uses **quarter-inch top-side axes**;
the later shop packet specifies four 5/16-inch top-side stacks. Those
diameter/hardware bindings are explicit limits. This pass keeps the source
quarter-inch material/reference geometry rather than silently importing the
larger later corner replay family. No member, bore or hardware is changed.

The four continuous knee shafts provide four comparisons per accepted state. Their
source response already contains same-state, same-position two-component
bending/shear envelopes, signed axial force, receiver bore pressures and
own-end wood-seat pressures. This pass joins those exact diagnostics by
case, clearance and physical shaft. It preserves each complete source
diagnostic; it does not construct continuous fields from replaced scalar
rows or combine peaks from different positions. The declared 92 ksi
smooth-section proxy is a conditional material comparison, not exact
fiber-level stress, connection resistance or hardware qualification.

The scalar laws supply no compatible continuous shaft bending or
own-end washer moment fields. Those quantities remain unavailable. A finite
direct T/V comparison never fills the missing complete steel result. A
separate isolated shaft or washer refinement would need an explicit force
join, frozen hypotheses and parent-owned execution scope; it cannot inherit
the four continuous shafts' compatibility or an old proposal result.

## Preparation and parent execution

The source-independent analytic 3/4/5 shear oracle checks the existing direct
reference helper against `sqrt(3)*5/(A*Fy)`:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-bolt-reference.py --self-check
```

`--prepare` authenticates the completed action export receipt, its full source/output
closure and the reference helpers, then runs only that direct oracle. It
freezes source/document snapshots and a source plan in a fresh ignored child.
The receipt binds the consumed documentation snapshot as an output; this
maintained leaf may then record the saved result without changing that input.
Each accepted action state must match an audit-passed source state and its
exact comparison JSON pointer. A completed partial frame packet is usable
only with its explicit required-state disposition inventory. Raw stopped or
diagnostic arrays cannot become comparison inputs. Stopped, quarantined or
unassessed states retain unavailable demand/reference fields; no zero demand
is invented. The parent supplies the
actual completed action receipt hash; no result is prepared from an assumed
future receipt.

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-bolt-reference.py \
  --prepare \
  --actions docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-action-reconciliation/attempt03 \
  --receipt-sha256 370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-bolt-reference/preparation01
```

The arithmetic run uses the same command without `--prepare`, and a fresh
`rawlocal/joint-frame-bolt-reference/attempt03` output. Estimated runtime is
under 30 seconds and memory under 512 MB; it performs no solve. The parent
owns execution timing and frozen inputs. The adapter receipt authenticates
the original104 force basis before and after arithmetic. Outputs retain each
scalar demand/reference, continuous diagnostic, numerical exceedance and
explicit method limit, with a source closure and producer receipt.

The final frozen action producer is
`8eaf209dc594be9468b9bea60ddd02974e1a05f2bc915fd2dc41dcf2b11eaf8c`.
Its frame-attempt08 source has twelve accepted states and two declared
stops, `a12-left_zero` and `k12-right_zero`. The source-bound
action receipt yields **1,200 scalar and 48 continuous shaft
comparisons**, with **208 unavailable axis-state entries**. Completion of the
finite disposition inventory remains separate from fourteen accepted force
states and from resistance acceptance.

The preserved source action attempt02 receipt is
`d79abda0dd3df21c84b65b83f95d1f2e0d4c00e5139fd356533b5b0ec0d60f18`.
The first consumer execution stopped during source authentication because
it still pinned the previous adapter producer. It produced no comparisons;
any saved failure bytes remain preserved. The fresh arithmetic attempt02
uses only the confirmed current adapter pin and receipt.

## Preserved attempt02 result

The parent arithmetic run finished in 1.732 seconds without a source solve.
Its status is
`COMPLETE_DIRECT_REFERENCES_FOR_ACCEPTED_SUBSET_WITH_DECLARED_METHOD_LIMITS_AND_UNAVAILABLE_STATES`.
It saved all 1,248 accepted axis comparisons and all 208 unavailable
axis-state entries. The latter retain null T, V and reference indices; there
are no force arrays or comparisons for either stopped state.

| Reference family | Maximum index | Numerical outcome |
| --- | ---: | --- |
| Scalar nominal UNC thread tension | 0.0574708 | 1,200 comparisons; no exceedance |
| Scalar same-section average T/V at 92 ksi | 0.1302534 | 1,200 comparisons; no exceedance |
| Existing scalar single-fastener lateral routes | 1.7416814 | 1,200 comparisons; ten exceedances |
| Scalar ideal-annulus wood mean | 0.8124404 | 1,200 ideal comparisons; no exceedance |
| Compatible continuous same-state/position smooth proxy | 0.1946741 | 48 comparisons; no exceedance |

The controlling lateral and scalar average T/V comparison is
`top_outer/clip_single_top_right_2/side_2`, `k12-rear`, zero clearance.
The ten lateral exceedances occur on the two top `side_2` axes and
`rail_front_bolt_left_2` / `rail_front_bolt_right_2`; their exact states and
ratios remain in the summary and scalar rows. They remain numerical
reference exceedances. The thread/ideal-annulus peak occurs on
`top_outer/clip_single_top_right_2/rail_1`, `k12-right`, nominal clearance.
The compatible shaft peak is `knee_outer_left_side_1`, `a12-rear`, nominal
clearance. These outcomes do not fill the 1,200 missing scalar continuous
bending/own-end washer-moment fields or qualify any washer metal resistance.

The preserved continuous diagnostics contain 144 receiver-bore summaries
and 96 own-end wood-seat summaries. Their peak nominal Fe ratio is
0.1236889 (`knee_outer_left_side_1`, `a12-left`, nominal clearance,
`base_side_left`). The peak own-end full-annulus mean / Fc-perpendicular is
0.2286081 (`knee_outer_left_side_2`, `k12-rear`, nominal clearance, head),
and the peak sampled pressure diagnostic is 0.5246223
(`knee_outer_right_side_2`, `k12-right`, nominal clearance, head).
These are exact saved compatible fields under the source contact hypotheses;
pressure ratios remain diagnostics, separate from joint resistance.

All lateral routes were finite within their declared formula domains.
The four source quarter-inch / shop 5/16 top-side mismatches remain **48
hardware-binding limits**. The partial center-right seat and each scalar
ideal-annulus support/tilt limitation remain recorded on their rows. Formal
criteria, complete joints, delivered hardware and physical release remain
unaccepted. Reference assumptions, common-host compatibility scope and
no-slip support remain conditional.

The independent saved-data audit verified all 117 numerical source bindings
and ten output hashes, all 1,456 unique required axis-state identities,
exact signed T / lateral component / xyz-vector joins for every scalar row,
and exact equality of all 48 copied continuous diagnostics to their source.
The independently recomputed direct average T/V error was at most
1.39e-17; thread and demand joins were exact. All acceptance/release flags
remain false. It performed no mechanics solve.

| Saved artifact | SHA256 |
| --- | --- |
| Producer consumed by attempt02 | `d6bef23c9a49a17dd6237c71881ec5a038b00a045f0449d4986ae12bf9ee83eb` |
| Attempt02 receipt | `f3ed178bda72688246fadcda45ac2067c248dcd0e2fe5c6352d2ce7b0b487097` |
| Attempt02 summary | `96ecd3343f9e05a5098f468ee68a02c60836e71672ebc353497332ed4b60d1b7` |
| Consumed documentation snapshot | `edab4dd2d04b058d2bd6e780bb20b227b268ea2872f9ef5002d4cfd7ebfd1364` |
| Independent validation02 checks | `2fb7fab75514b60d2f076b62eb5f4350c66423033f557a10a5aedfac509e6fe1` |

The receipt retains source/tool/formula identities, producer and consumed
documentation snapshots and every comparison output. Attempt02 and its
validation02 bytes remain unchanged. Their historical producer/action
versions remain in their frozen snapshots; the later maintained source
paths must not replace those versions in the historical receipts.

## Final frame08/action03 join

The parent directed a fresh direct-reference run against the final
frame-attempt08 / action-attempt03 source. Its exact action receipt is
`370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e`;
action summary is
`353ce1316bbd005be0e3f286e416eab7bd549c465a99c629d6f34ce11d8c7330`.
The sole numerical producer change is the deliberately updated frozen
action-method identity. The comparison formulas and method limits stay
those already recorded above.

Fresh bolt-reference **attempt03** completed in 1.927 seconds with no
mechanics solve. It retains twelve accepted states, 1,200 scalar rows,
48 continuous rows and 208 unavailable entries for the same two stopped
case/gap identities. It preserves ten lateral exceedances across the same
four axes. Final maxima are thread tension **0.0574707776**, scalar average
T/V **0.1302533955**, lateral **1.7416814324**, ideal-annulus wood
**0.8124404155**, and compatible smooth shaft proxy **0.1946741234**.
Governing identities, continuous bore/wood-seat diagnostic peaks and the
48 top-side hardware-binding limits match those reported above.

The final saved-state audit verifies all **124 source bindings and ten
output hashes**, all 1,456 unique required axis-state identities and null
unavailable demands. All scalar signed T, components and xyz vectors match
the final action fields exactly; all 48 continuous diagnostics equal the
final compatible source. Independent direct algebra differs by at most
1.39e-17. All release/acceptance flags remain false. The old attempt02's ten
saved output hashes also verify unchanged.

The final source revision changes some accepted demands slightly: the
largest scalar T change from attempt02 is 0.010758 N and V change is
0.00301047 N. The largest lateral-index change is 1.98133e-6 and continuous
shaft-index change is 3.27232e-8. These differences are retained in fresh
rows; no old forces or comparison result are transferred to the new source.

| Final artifact | SHA256 |
| --- | --- |
| Attempt03 receipt | `730144d3762ff0238528dee23eca2e0ac52c61845d48a847ec47f099f4418885` |
| Attempt03 summary | `d07a799272f029fdc72495bd7bf31912b01d4fd75565895ce6c4bcffa8c6bda8` |
| Consumed documentation snapshot | `a6d59fb80731f5619b1ff5eb918413ddea526977712cb9f22d0dcaba2f299e04` |
| Independent validation03 checks | `b24bc337ccc01bae608fe69a7fe2bd3f2f2c7603b60527e79a5355dfe94d8d09` |

Reproduction of the final join uses the command above without `--prepare`
and a fresh owned output child. The maintained leaf adds the saved results
without replacing frozen inputs or outputs. Complete scalar shaft bending,
own-end washer moments, washer metal resistance, the four shop/source
diameter joins and the two stopped force states remain the exact limits.

This producer and its saved raw evidence stay active. Preserved
proposal comparisons and unsuccessful coupled-frame attempts remain
recoverable history. No shared summary, old producer, geometry, staging or
commit is changed by this packet.
