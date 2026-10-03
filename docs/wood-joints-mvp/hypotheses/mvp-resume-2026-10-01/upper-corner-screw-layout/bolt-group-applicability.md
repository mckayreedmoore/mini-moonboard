# Bolt-group applicability: individual forces, Cg and Cdelta

## Working conclusion

**A second sharing reduction is not established for the current conditional
individual-bolt assessment.** The frozen global compliance and connector
laws already allocate simultaneous forces; the corner replay supplies its
own first-order local allocations. Applying an additional `Cg` to those
individual forces can count unequal sharing twice. The N02 expanded-area
peak **1.627961439975** comes from a degenerate declared area, so that result
alone does not warrant a hardware or geometry change.

This is a mechanics interpretation within the stated MVP assumptions.
**It is not an NDS exemption for every model that outputs bolt forces.**
For a connection assessed by the NDS adjusted-row-capacity procedure,
applicable `Cg` remains required. The frozen gross `H` does not establish
delivered connection laws or complete local group resistance. Applicable
`Cdelta` and Table 12.5.1 obligations remain separate. No existing criterion,
factor, source, geometry, hardware or result is changed by this note.

## Primary source basis

The pinned 2024 specification controls. Its Chapter 11 §§11.2.2 and 11.3.1
require the applicable adjusted individual design values in the connection
sum. Section 11.3.6.1 requires `Cg` for qualifying rows; §11.3.6.2 defines
the equal-diameter, load-aligned row and the adjacent staggered-row rule.
Section 11.3.6.3 uses gross member areas, or the specified thickness × group
width construction for perpendicular loading. A generic projection of any
bolt pair onto grain is not a general oblique-group area rule.
[NDS 2024 Chapter 11, printed pp.71 and 74](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf).

AWC's publicly accessible **2018 Commentary**, C11.2.2 and C11.3.6,
printed pp.250–252, explains that row reduction addresses unequal fastener
loads from member elasticity and joint slip. Its derivation assumes uniform
direct stress within each member section and linear fastener load/slip,
using member `EA`, spacing, count and slip modulus. It also explicitly
requires the applicable factor when summing individual references. This is
primary background for the sharing mechanism, not verified 2024 Commentary
wording or a current exemption for a finite-element calculation.
[AWC 2018 Commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf#page=58).

The official [2024 NDS errata, March 23, 2026, PDF p.7](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
confirms `gamma = 180000 D^1.5` for wood-to-wood connections, with inch
units. This resistance-method slip modulus is not automatically the
constitutive law used in `H` or the delivered bolt/wood law.

The two pinned specification PDFs were read directly from the repository;
their filenames containing `withCommentary` do not make them Commentary.
The online 2024 chapter links could not be retrieved during this task.
The public 2018 Commentary and current official errata were browsed.
Current 2024 Commentary angular wording remains unverified.

## What the frozen force model already does

[The gravity record](knee-bridge-gravity.md) preserves filled-bore gross
`H/D/B`, connector rows and constitutive `k`, and changes gravity `F/e/W`.
In the existing [frame formulation](../simple_frame.py), the active elastic
compliance is `S = H + diag(1/k)` for finite springs, with equilibrium
`D.T @ f = W`. The current [frame wrapper](knee-bridge-frame.md) also
retains the existing circular-clearance/contact laws. Thus the individual
forces are solved from coupled compliance and compatibility, not set to
the total connection force divided by bolt count.

The model distinguishes 104 existing global bolt axes from the 108-axis
unadopted proposal: the four internal axial ties have no global operator
rows. The sixteen original top/bottom corner axes use the completed
[first-order local replay](knee-bridge-corner-replay.md), which retains both
host transfers and moments but does not feed redistribution back into the
global frame. The other 84 physical axes use the saved global allocations.
The internal pairs retain their separate simultaneous axial allocations.

The double-counting argument is a **conditional inference**, illustrated
by an ideal proportional, aligned row with identical adjusted individual
reference `R`, positive fractions `a_i`, and `sum(a_i)=1`:

```text
V_i = a_i P
max_i(V_i/R) <= 1  gives  P_limit = R/max_i(a_i)
C_sharing = P_limit/(n R) = 1/(n max_i(a_i))
```

An applicable row factor represents the reduction from the nominal `n R`
sum for its assumed distribution. If the direct model already reproduces
that same distribution, reducing every `R` again by that sharing factor
introduces another reduction for the same mechanism. This algebra does
not identify the frozen model's distribution with Eq.11.3-1. Its positive
scalar fractions also cannot replace the current signed vectors, couples,
unequal references or changing contact/clearance states.

| Assessment route | Treatment of sharing |
| --- | --- |
| NDS qualifying row assessed from total load and summed adjusted references | Determine applicable `Cg` with supported row, areas and slip inputs. A global joint load or bolt-force output alone does not waive it. |
| Mechanics assessment of actual individual demands with supported member/connector laws | Compare each same-state force with its individual resistance, retaining applicable geometry/service factors. An extra sharing multiplier needs a distinct mechanism or an explicit separate sensitivity. |
| Current gross-`H` MVP and first-order corner model | Use the saved individual-force comparisons within their conditional scope. Keep N02 area scenarios as sensitivities; neither an actual row factor nor an NDS waiver is established. |
| Same-body internal axial ties | Lateral-row `Cg` is inapplicable to their axial route. Their axial material proxies do not establish lateral transfer or complete anchorage. |

The exact limitation is the supplied mechanics basis: filled bores preserve
gross elastic compliance despite actual openings; connector/material/contact
laws are conditional rather than measured product laws; continuous shafts
retain separate global interfaces; and corner timber is rigid in the local
first-order transfer. Solver equilibrium and local balance do not establish
actual embedment stiffness, slip redistribution, yielding or local timber
group resistance. A justified analysis must cover the applicable sharing
mechanism before its direct forces can replace a prescribed row allowance.
No universal additional factor resolves these specific limitations.

## Why the projected-area scenario approaches Cg = 0.5

The saved [N02 result](bolt-group-completion.md) retains the right top side
pair's 67.85 mm pitch. Its projection on cleat grain is only
**1.0447159581872256e-8 mm**; multiplying by the 88.9 mm saved bearing length
and converting units produces **1.4395692337225552e-9 in²**. The cleat gross
section in the same record is approximately **12.25 in²**.

The tiny positive projection survives the producer's `1e-12 in²` inclusion
threshold. In the unequal-area two-fastener equation, that artificial weak
`EA` drives sharing toward one bolt carrying the row load, and the declared
factor tends to `1/2`. This explains the saved
`Cg=0.500000011853` and the doubled sensitivity index. It does not show that
the physical cleat has a vanishing load-carrying width. The projection is
within the already adopted `1e-6 mm` geometry precision, and the load is
oblique to the pair line rather than the qualifying row assumed by the
equation. The full crossed group cannot acquire an NDS area from this
rounding residual. No area floor, substitute width or replacement factor
is invented here.

At right/K12-rear `side_2`, the saved individual component index is
**0.813980739284** for lateral **1098.817241621 N**, reference
**1349.930273027 N** and `Cdelta=1`. The expanded sensitivity is
**1.627961439975**. Its simultaneous tension remains **505.714971352 N**;
the other bolt retains **437.381846542 N** tension and a lateral vector
near `1e-8 N`. Those axial actions and the interface moment remain part of
the load path. The five expanded-hypothesis exceedances are retained in
the frozen raw result, while this unsupported area sensitivity supplies
no physical-failure finding or hardware-change basis.

Fresh N02 peaks remain distinct: original equal-EA sensitivity
**0.953004650342**, retained mixed-area sensitivity **0.962156600827**,
and the consumed finished-path comparison **0.160370287864**. The latter
checks its named path and is not divided by a lateral sharing factor.
The historical **0.962538** result is not transferred.

## Table 12.5.1 and Cdelta remain independent

For the current bolts, all nominal diameters are at least 1/4 inch.
Sections 12.5.1.2–.3 therefore remain applicable where their loading and
geometry conditions are met. Reduced end distance or in-row spacing uses
the permitted ratio and minimum tier; the smallest applicable `Cdelta`
extends across the group and, for multiple shear/asymmetric three-member
connections, across shear planes. Tables C/D are minimum placement rules;
they provide no generic factor that cures an inadequate edge or row spacing.
[NDS 2024 Chapter 12, printed pp.97–99](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf).

| Current provision | Required distinction |
| --- | --- |
| Table A, end distance | Softwood toward-end loading: 3.5D minimum / 7D full value; away-end or perpendicular loading: 2D / 4D. |
| Table B, in-row spacing | 3D minimum; parallel full value 4D; perpendicular full value depends on the attached member. |
| Table C, edges | Parallel: 1.5D, or the larger half-row spacing when `l/D>6`; perpendicular: loaded 4D / unloaded 1.5D. |
| Table D, between rows | Parallel 1.5D; perpendicular 2.5D to 5D with the specified `l/D` interpolation. |
| Tables C/D notes | Use the lesser main bearing length or total side-member bearing length. Preserve actual common-shaft topology. |

Here `l` is bearing length, not purchased bolt length. Direction signs select
the end/edge branch on each actual receiver; neither total force magnitude
nor a favorable `Cg` supplies that selection. The row direction follows
loading, not grain by definition. Section 12.5.1.2(b)'s equivalent shear-area
rule concerns loading at an angle to the **fastener axis**, and is not a
general angular-to-grain interpolation. The current pinned specification
does not supply the missing generic angular end/edge law. The historical
2018 Commentary discusses tension-end interpolation but explicitly supplies
no angular edge rule; it is not adopted here as current 2024 wording.
[AWC 2018 Commentary, C12.5.1, printed pp.263–264](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf#page=71).

N02 carries saved corner rail `Cdelta` values near **0.975253093** and
**1.0** elsewhere. These are reference modifiers applied once, not proof
that every current host satisfies Tables A–D. N01's completed `Ceg` is
another separate adjustment and does not close `Cdelta`.

[N03's completed attempt02](bolt-detailing-completion.md) supplies finite
finished geometry but assigns no ordinary group or connection `Cdelta`.
Its 456 end-table nulls concern terminal faces not classified as square-cut
grain ends. Its minimum-tier shortfalls are conservative hypotheses,
unoriented envelopes or nonordinary-axis comparisons; none is a pure
tabulated shortfall. An end-grain bearing interval reaching a reference
end is not an ordinary side-grain bolt center located at that end. This
note retains N03's classifications rather than treating their margins as
physical failures or creating another detailing assessment.

### Numerical precision and lightly loaded directions

Use the adopted producer/extractor precision for the quantity being
interpreted. The current frame contract retains force/law audit tolerances;
the local transfer uses 0.001 N host-force balance and the lateral extractor
uses `1e-7 N` absolute force matching. Those different checks are not a new
universal zero-load threshold. A lateral residual near `1e-8 N` cannot
define a meaningful loaded-edge or row angle beyond those saved precisions.
Preserve its value and the existing source's unresolved-direction treatment;
do not introduce a new force cutoff or snap a resolved oblique force into
parallel/perpendicular loading.

The N02 strict helper's near-exact angular guards and same-sign checks are
its method boundary, not new NDS angular tolerances. Its 324 null actual
`Cg` outputs remain preserved. Tiny residual directions do not prove that
all those states physically lack an applicable row; a zero-direction state
also does not establish a geometry or group pass.

## Exact remaining basis and preserved evidence

The remaining N02 basis is specific:

1. Identify whether each actual connection is assessed by a qualifying NDS
   row procedure or by the conditional individual-force mechanics route;
   establish the member/connector sharing basis for that route. Gross `H`
   and saved vectors alone do not establish a general prescriptive waiver.
2. Assess the four continuous shafts through the completed
   [common-reference record](knee-common-references.md), preserving its
   common-pose distribution and stated first-order limits. N02's original
   four interface pairs × six cases = **24 pair/case states**, containing
   48 bolt/interface states, remain outside its two-receiver pair helper's
   applicability. This is a helper-scope limit, not missing common-reference
   arithmetic. The two interfaces cannot become independent single-shear
   capacities or a summed pass; the common component references do not
   themselves supply an adjusted complete-group resistance or row `Cg`.
3. Use N03's actual finished geometry to resolve applicable end/edge/row
   branches, non-square/end-grain scope and any justified oblique treatment.
   Propagate the applicable group/shear-plane `Cdelta` once. Its geometry
   census and conservative envelopes do not themselves supply that factor.

The parent completed `rawlocal/knee-common-references/attempt01` with status
`COMPLETE_SAVED_COMMON_REFERENCE_COMPARISONS`. Its saved smooth-steel,
nominal-thread, wood-mean and wood-local-pressure comparisons have no
exceedances; wood and bore reference-null counts are zero. Its maximum
shared-pose rotation is **5.615900727115 degrees**, explicitly first order;
finite rotation was not rechecked. Those actual common-field comparisons
supersede the missing-arithmetic description in the earlier applicability
note. They do not alter the frozen N02 result, close its pair-helper scope,
or establish complete joint acceptance. No additional sharing factor is
introduced.

Local timber group/stress mechanisms remain with their existing owners;
this note supplies no splitting, washer, contact or steel capacity.
It introduces no new review loop or external approval prerequisite.

The six frozen nominal cases and sources remain those of N02 `attempt01`:

| Preserved input or result | SHA-256 |
| --- | --- |
| Gravity `operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Frame `comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Frame `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| N02 `checks.json` | `4db21cc2d7fa76cebc021ef8574331d520f247b78de5acb4270ac90dc80713de` |
| N02 producer/API | `424b54a2df560bcfbe98e6916a9eaeb6d6bae53826094644f3cfcb4627b033e2` |
| Frozen N02 annotation | `eef07bfd0fa759f8b40c42bf4d2f4f871e6dfedf1da1c288c5401eca6d2de6fa` |
| Completed common-reference receipt | `172d616910ef2ff898383905eed795c82fa0a63b01e7a5861fef83399dafc5a9` |
| Completed common-reference summary | `18e4558eeecea5b75f618fcffb9b4bc694c13b57da3af861f3b13f60abb0800e` |
| Pinned 2024 Chapter 11 PDF | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| Pinned 2024 Chapter 12 PDF | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |

Only this new Markdown leaf is authored. Source reading, saved-result joins
and PDF text extraction supply this interpretation; no mechanics, code,
frozen result, criterion or geometry is amended, and no build, software test
or review loop is executed. Actual group resistance, complete joint
acceptance, proposal adoption and release remain unassigned/false.
