# Integrated barrel frame: nominal installed-stack reach

This screen reads the 46-pair **integrated** assembly with
`build_integrated_viewer_assembly()` and passes it to
`owner_barrel_installed_stack_audit.build_report(assembly)` (also the audit's
command-line default). It is distinct from
the [historical 48-pair outward-post audit](owner-barrel-installed-stack-audit.md).
The table groups all 46 rows by original connection-duty family and nominal
bolt length. Values are millimeters and apply to each row in that group.

| Duty family | Rows | Bolt length | Tip past assumed barrel axis | Fully threaded tip length needed just to reach near wall | Maximum possible body overlap | Tip-to-bore-cap clearance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base center | 2 | 114.3 | 12.649 | 17.653 | 10.008 | 16.700 |
| Base outer side | 4 | 114.3 | 4.549 | 9.553 | 9.553 | 12.700 |
| Bottom center | 4 | 114.3 | 4.549 | 9.553 | 9.553 | 12.700 |
| Bottom outer rail | 4 | 152.4 | 1.849 | 6.853 | **6.853** | 5.155 |
| Header center | 4 | 88.9 | 10.249 | 15.253 | 10.008 | 16.700 |
| Header outer post | 4 | 114.3 | 11.200 | 16.204 | 10.008 | 16.700 |
| Lower center rail | 4 | 114.3 | 4.549 | 9.553 | 9.553 | 16.700 |
| Lower outer rail | 4 | 152.4 | 1.849 | 6.853 | **6.853** | 5.155 |
| Top center | 4 | 114.3 | 4.549 | 9.553 | 9.553 | 12.700 |
| Top outer | 4 | 127.0 | 6.449 | 11.453 | 10.008 | **0** |
| Upper center rail | 4 | 114.3 | 4.549 | 9.553 | 9.553 | 16.700 |
| Upper outer rail | 4 | 152.4 | 1.849 | 6.853 | **6.853** | 5.155 |

The trial count is 4 × 3½ in, 26 × 4½ in, 4 × 5 in and 12 × 6 in bolts, across 24 original
connection duties. All 46 modeled shafts reach the *assumed* barrel-body
center; none exceeds its modeled machine-bore cap. All have provisional head
and washer envelopes. Yet **four top-outer tips end exactly at their bore cap**:
the nominal classification “within bore” does not supply positive tip
clearance. The shorter shafts retain their former bore depths; bore depth
has not been redesigned or approved.

### Barrel insertion holes are not yet drill sizes

The [same live 46-pair audit](../../scripts/owner_barrel_installed_stack_audit.py)
now measures each barrel body against its modeled insertion bore. All **46
barrel bores have the same 10.0076 mm nominal diameter as the modeled barrel
OD**: the viewer gives **zero nominal diametral insertion allowance**. Those
solids are occupancy envelopes, not a press-fit or bit-size instruction. The
deepest modeled insertion paths are the four center post/header blind bores,
**68.501 mm** from their entries; the other path lengths are 27.051,
57.3016 and 62.451 mm.

For scale only, a 13/32-in bit is **10.31875 mm** nominal diameter, **0.31115 mm
larger** than the modeled barrel body. [Home Depot lists a Drill America
13/32-in general-purpose six-pack](https://www.homedepot.com/p/306050162)
at $20.25 and catalogs 3.875 in of drilling depth, longer than the deepest
modeled 68.501 mm bore. This is an ordinary-store **tool lead**, not a selected
bit or tolerance: a delivered 880543 OD, actual drilled hole, wood condition,
barrel retention, internal-thread alignment and the enlarged cut-wood
sections must be measured and checked first. In particular, widening a bore
can worsen the already thin center and outer-header wood margins. Do not
drill from the CAD diameter or add this tool price to a qualified build bill.

The four top-outer bolts belong to `clip_single_top_left_1` and
`clip_single_top_right_2`, two per station. A **read-only**, source-solid
2 mm extension of each existing 125.349 mm machine bore would give 127.349 mm
depth from its wood entry face and 2 mm nominal tip clearance; a 4 mm trial
would give 129.349 mm depth and 4 mm clearance. Both tested extensions stayed
inside `base_rail_top` and reported no modeled protected-feature, service,
retained-hardware, unrelated-wood, peer-hardware, or other-barrel-path hit
above the 1 mm³ screening threshold. This is not an installed tolerance or
wood-resistance check. The maintained scene retains **zero** top-outer tip
clearance until the owner approves a bore-depth revision.

The **12 outer-rail rows** have the least nominal axial reach: their tips pass
the assumed barrel axis by only 1.849 mm and stop 3.155 mm before the far wall.
Even with a fully threaded shaft, no more than 6.853 mm of the modeled barrel
body can overlap. The **two base-center rows** now require the longest threaded
tip span merely to reach the near wall, about 17.653 mm. Neither measure is
actual usable thread engagement. Delivered bolt thread start/runout, barrel
internal thread location/depth, compatible thread form, head/washer dimensions,
tolerances, adequate engagement, wood and hardware resistance, and assembly
access remain unverified. The deep blind bores also need an insertion,
alignment, extraction and rim-withdrawal rehearsal against this **46-pair**
assembly; earlier service probes used the 48-pair composition.

### Partial-thread comparator: nominal shaft reach can conceal no engagement

An [Aspen Grade 5 1/4-20 × 3½ in drawing][aspen35],
[4½ in listing][aspen45], [5 in listing][aspen5], and [6 in drawing][aspen6]
each document a **0.750 in
(19.05 mm) nominal threaded end**. These are an illustrative bolt family,
**not** controlled dimensions of the Lowe's/Home Depot bolts in the
cost basket. The [source-bound audit](../../scripts/owner_barrel_installed_stack_audit.py)
intersects a 19.05 mm end-thread interval with each *modeled barrel body's*
axial interval. It optimistically assumes the barrel is female-threaded
throughout and ignores the male point chamfer, thread runout, tolerances and
actual Hillman internal-thread location. It is a geometry comparator, **not
qualified engagement**.

| Current family | Bolts | Maximum nominal male-thread/body overlap under 19.05 mm example |
| --- | ---: | ---: |
| Base center | 2 | 10.008 mm |
| Outer header/post | 4 | 10.008 mm |
| Center header/post | 4 | 10.008 mm |
| Base outer; bottom/lower/upper center; top center | 20 | 9.553 mm |
| Bottom/lower/upper outer rail | 12 | 6.853 mm |
| Top outer | 4 | 10.008 mm |

All **46 of 46 bolts** now have positive *nominal* male-thread/body overlap in
this optimistic 19.05 mm comparator. That is not measured, effective thread
engagement, and it does not establish that a usable female thread exists in
the overlapping span. The actual retailer bolt thread lengths,
barrel female-thread interval and minimum necessary effective engagement
must be resolved by a compatible selected product and delivered fit before
choosing bolt lengths. A shorter bolt, longer-thread or full-thread product
could change this result, but each requires its own bore, head/washer, steel,
wood and service checks. The family-specific lengths are a CAD trial, not a
selected hardware order.

## Connection-family bolt-length sensitivity

The source-bound audit now derives a **centerline-only** nominal interval for
one bolt length per original duty family. Its lower end just reaches the
*assumed* barrel axis. Its upper end is the lesser of the modeled barrel far
wall and the **existing** machine-bore cap minus an illustrative 2 mm tip
allowance. The far-wall cap is a conservative no-overrun sensitivity, not a
claim that a through-threaded barrel cannot accept a longer bolt. These are
axial dimensions from the modeled shaft start at the **outer washer face**,
**not** verified purchase lengths or thread-engagement specifications.

| Families sharing nominal interval | Pairs | Axis-to-limiting length (mm) | Current length (mm) |
| --- | ---: | ---: | ---: |
| Base center | 2 | 101.651–106.655 | 114.3 |
| Base outer side; bottom/lower/upper center; top center | 20 | 109.751–114.755 | 114.3 |
| Bottom/lower/upper outer rail | 12 | 150.551–155.555 | 152.4 |
| Header center | 4 | 78.651–83.655 | 88.9 |
| Header outer post | 4 | 103.100–108.104 | 114.3 |
| Top outer | 4 | 120.551–125.000 | 127.0 |

Thus the 12 outer-rail and 20 base/center-rail current tips fall inside this
particular no-overrun/2-mm-bore window. The other **14** tips pass the modeled
barrel far wall; four top-outer tips also end exactly at the bore cap and need at least 2 mm
additional modeled bore depth to meet the *illustrative* allowance without
shortening the bolt. Neither observation alone proves a physical clash:
internal barrel threads and exit geometry are unknown, and every shorter
candidate must still place usable bolt threads inside a real barrel. The
report retains the per-family bore-depth shortfall and far-wall overrun, so
lengths can be chosen **by connection family** once controlled hardware
dimensions are available. The viewer's trial length mix does not select
delivered hardware or deeper drilling.

The corrected 6-in
[outer-rail setback probe](../../scripts/owner_barrel_outer_rail_setback_probe.py)
also accepts the current 46-pair assembly as input. Its six-station, 12-bolt
nominal screen found no protected-feature, unrelated-wood or peer-hardware
hits at the current 60 mm setback or read-only 58 and 56 mm setbacks. These
numbers use the same provisional centered barrel thread axis and dimensions:

| Barrel setback from rail butt | Tip past assumed axis | Tip before barrel far wall | Smallest axis/far-wall margin | Probe gate |
| ---: | ---: | ---: | ---: | --- |
| 60 mm (maintained) | 1.849 mm | 3.155 mm | 1.849 mm | Nominal geometry only |
| 58 mm (read-only) | 3.849 mm | 1.155 mm | 1.155 mm | Nominal geometry only |
| 56 mm (read-only) | 5.849 mm | −0.845 mm | −0.845 mm | Far-wall gate fails |

Moving to 58 mm improves axis reach but **reduces** the smallest longitudinal
margin and leaves less wood ahead of each barrel. At 56 mm the bolt tip passes
the modeled barrel far wall; the
[Lowe's Hillman 880543 description](https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559)
says its threaded portion passes through the sides, but does not establish the
usable thread depth, exit geometry, or an installed tip-clearance allowance.
Neither read-only pose is selected or a reach/wood-strength solution. The
60 mm outer-rail setback remains unchanged pending a qualified hardware
stack and an owner-approved physical revision.

Separately, two left center-rail machine bores cross existing service voids
in the current cut scene. This reach screen does not clear those crossings.
No installed-fit pass, drilling, fabrication, load-test or climbing release
follows from these nominal numbers.

[aspen35]: https://www.aspenfasteners.com/content/2D_PDF/product80/BO016-1420X312.PDF
[aspen45]: https://www.aspenfasteners.com/1-4-20-x-4-1-2-hex-head-cap-screws-bolts-unc-coarse-thread-grade-5-steel-zinc-made-in-u-s-a/
[aspen5]: https://www.aspenfasteners.com/1-4-20-x-5-hex-head-cap-screws-bolts-unc-coarse-thread-grade-5-steel-zinc-made-in-u-s-a/
[aspen6]: https://www.aspenfasteners.com/content/2D_PDF/product80/BO016-1420X6.PDF
