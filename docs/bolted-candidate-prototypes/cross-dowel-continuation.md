# Cross-dowel continuation for PB05/PB06

21 September 2026. **PARK — independent evidence-incomplete alternative.** This
continues exactly the `recessed_centered_receiver_pair` in the
[PB01 CD-01 trial](simple-pb01-cross-dowel-trial.md), using its
[pose inputs](../../scripts/simple_pb01_cross_dowel_trial.py). This is a bounded
continuation for the PB05/PB06 alternative lane, not a new station selection
or an installed PB05/PB06 geometry. It leaves PB05, PB06, the
selected candidate, and all shared ledgers unchanged. It preserves all 66
panel/kicker screw axes and does not transfer a PB01, corner-block, shaft, or
solved-case capacity. It is not a purchase, drilling, fabrication, or structural
release.
No manufacturer was contacted. The corner-block work continues independently.

Run the reproducible bounded screen with:

```sh
uv run --no-sync python -m scripts.simple_cross_dowel_continuation
uv run --no-sync pytest -q tests/test_simple_cross_dowel_continuation.py
```

## Exact retail route and source result

The concrete barrel lead remains **Hillman 880543**, Lowe's item 137362 and
Home Depot Internet 202242356. [Lowe's lists][lowes-barrel] one 1/4-20
zinc-plated steel barrel nut for **$1.48**. [Home Depot identifies][hd-barrel]
the same model as 3/8 × 5/8 × 1/4-20. Hillman's customer-service answer on the
Lowe's page gives 0.394 in OD and 0.630 in length. Neither retail page supplies
a Hillman-controlled dimension drawing with end-to-thread-axis limits,
complete internal-thread span, tolerances, steel grade, proof load, or joint
resistance.
Home Depot explicitly labels the model **Not Graded**; Lowe's generic
**All-Purpose** field is not a strength classification for this barrel.

The exact mating lead is [Everbilt 800676][bolt], Home Depot Internet
204633308: 1/4-20 × 5 in, fully threaded, zinc-plated steel, listed as A307,
one piece at **$0.62** when checked. Its page specifies a 7/16 in drive. The
washer lead is [Hillman 490687][washer], Lowe's item 58124: sixteen 1/4 in
zinc-plated flat washers for **$1.98**. The washer's thickness, OD tolerance,
hardness, and bearing suitability are not controlled by that listing.

Two nominal stacks allocate **$4.4475**: $2.96 barrels, $1.24 bolts and
$0.2475 washers. Checkout for two singles and one washer pack is **$6.18**,
before tax, delivery, drill tooling, jig, waste and wood. Local stock and price
can change; no item was bought or inspected.

These are the recorded public prices from the first-pass live check, not a new
local stock check. Added timber for this direct detail is zero. The retained
six-inch corner-block comparator uses 139.7 × 57.15 × 152.4 mm of timber
(1.216740 L) and four bolts across two interfaces. Its complete stock yield
and installed cost are unresolved too. The $6.18 is a hardware subtotal;
complete installed cost and savings remain unknown until compatible stacks,
bits, depth stop, jig, labor, waste and delivery are costed.

A manufacturer comparator exists, but does not identify the retail SKU.
[Stafast JCD14201606][stafast-product] is a factory 1/4-20 cross dowel; the
[Stafast catalog][stafast-catalog] tabulates `L=.630`, `L1=.236`, and
`d1=.394 in` and gives general decimal tolerances of ±.016 in. Stafast also
warns that functional dimensions may change and asks users to obtain a current
print. No public evidence ties Hillman 880543 to Stafast JCD14201606. The
Stafast dimensions, tolerance, steel description and marketing about high
torque therefore are **not** assigned to Hillman stock. No exact Lowe's/Home
Depot SKU with both a manufacturer-controlled drawing and usable strength or
load evidence was found in the bounded live search.

## Whole-section geometry and assembly

The exact CD-01 participants are `base_principal_center_right` and
`base_rail_service_lower_right`, meeting at X=89.05 mm. Both bolts run +X
through 38.1 mm of principal and into the rail end. Barrel axes sit 70 mm
beyond the butt at local N=265 and 310 mm. The first enters from minus-T and
the second from plus-T. The whole rail section is 38.1 mm T × 139.7 mm N.

The source CAD bounds, read with CD-01's `_local_bounds` helper, are
N=209.84096785931308–349.54096785931307 mm. Thus the rows lie 55.159 and
100.159 mm from the lower N edge, 45 mm apart; their nearest edge distances
are 55.159 and 39.541 mm. The first pass incorrectly centered this row pair
and reported 47.35 mm edge distances. The continuation now uses the actual
CD-01 coordinates. These distances do not establish end/edge/spacing capacity.

The **original trial** uses a 10 mm OD × 16 mm body, recessed 11.05 mm,
with the thread axis 8 mm from the barrel end: 19.05 mm from the entry face.
The body occupies depths 11.05–27.05 mm, leaving 11.05 mm behind it. The
cross-bore is blind and 27.05 mm deep; neither barrel nor bore traverses the
full timber thickness. Its machine-bore envelope is 7.5 mm diameter, bolt
envelope 127 mm long, and access cylinder 20 mm diameter × 40 mm long.
These are diagnostic envelopes, not drill sizes or verified tools.

**Hillman comparison, separate from the original trial:** nominal OD 10.0076
and length 16.002 mm differ by +0.0076 and +0.002 mm. These are public nominal
dimensions, not measured actual parts. Centering that body needs an 11.049 mm
recess and 27.051 mm blind bore, and preserves the original thread axis only
if the unreported end-to-axis offset is 8.001 mm. Insertion depth locates the
body; it does not determine internal thread location or engagement.

The bolt/thread axis stays at the original 19.05 mm depth for the separate
offset sensitivity. For the nominal
16.002 mm body, an explicitly non-Hillman axis-offset sensitivity of 6 to
10 mm requires 13.05 to 9.05 mm body recess and leaves 9.048 to 13.048 mm of
wood beyond the barrel. All three sensitivity poses fit the nominal timber
body. This is a body-containment result only. It is not an NDS spacing/end
distance acceptance, a worst-case delivered fit, or a resistance value.

The nominal outside-seat-to-axis wood path is 108.1 mm. A 127 mm bolt with the
carried 1.651 mm washer-thickness sensitivity reaches 17.249 mm beyond the
axis, with its tip 125.349 mm from the seat before any clearance allowance.
The original washer-free trial projects 18.9 mm beyond the thread axis and
13.9 mm beyond the 10 mm barrel's far X surface. The retail washer page
does not establish 1.651 mm, and the barrel page does not establish complete
thread span. Consequently thread overlap, required engaged turns, bottoming,
and tip clearance remain open even though the nominal body fits.

Complete engagement is the overlap of the bolt's complete-thread interval
and the nut's complete-thread interval after translating both to the installed
axis datum. Exclude lead threads, chamfers and runout; then compare that overlap
with the engagement required by the supported stripping calculation. Neither
11.05 mm insertion nor 18.9 mm tip projection supplies engaged length. Reuse
the existing [interval-fit helper](../../scripts/simple_pb01_cross_dowel_geometry_screen.py)
when those measured limits exist. A positive interval overlap alone is not
sufficient resistance evidence.

Assembly requires controlled end drilling, opposite-face cross drilling,
orientation of each recessed slotted barrel with a flat-head screwdriver, and
tightening the bolt with a 7/16 in wrench. A jig must control the intersecting
axes and cross-bore depth. Recessed-barrel extraction, chip clearing, repeated
alignment, actual tool sweep, and an assembly/removal trial remain
undemonstrated. The prior CAD clearance belongs to its own trial dimensions;
this continuation makes no new physical clearance finding.

## Conservative joint-family screen

Nominal geometry advances only as a sensitivity. Every resistance route stays
open: barrel transverse section and bending; internal-thread stripping; bolt
tension, shear, bending and threads; washer and principal-face bearing; barrel
bearing into the rail; end tear-out, splitting and reduced section; group
distribution, rotation and stiffness; and simultaneous changed-topology
PB05/PB06 actions. Compression may cross the butt face, but friction receives
no capacity credit. The cross dowel is not assumed to be a shear key.

Separation follows head/washer → bolt tension → internal threads → barrel
bearing into the rail parallel to X grain. Barrel anchorage needs actual
contact bearing, splitting, end tear-out and net/group checks: the intersecting
7.5 mm trial bolt bore interrupts contact, so OD × length is only gross area.
Shear in T and N requires bolt bearing in both the principal and end-entering
rail bore, plus bolt bending/shear and wood splitting checks. The N-separated
rows may provide one bending couple with unilateral butt-face contact; they
do not by themselves establish torsion or all-axis rotational restraint.

[AWC TR12][tr12] provides dowel-yield equations and identifies member
strength, geometry, spacing, group action and fabrication as separate design
inputs. It provides no Hillman barrel anchorage or thread value. The Everbilt
bolt's A307 label cannot establish the barrel, wood interface, complete joint,
or rotation stiffness. Shaft strength alone is not a joint strength claim.
An applicable calculation route is acceptable: establish traceable material,
thread and actual geometry inputs, calculate barrel section/bending and thread
stripping, apply lateral dowel methods only within their assumptions, and
separately check anchorage, timber failure, contact and group distribution
against simultaneous changed-topology actions. An assembled-joint product
rating is not inherently required. Where a calculation model is unsupported,
part-specific qualification evidence must cover that mechanism; the larger
USDA dowel-nut specimens cited in CD-01 supply no transferable load here.

## Bounded conclusion and open gates

**PARK.** The ordinary retail route and nominal whole-2×6
pose are concrete, inexpensive and geometrically plausible. Public evidence
still cannot support a conservative joint capacity or even worst-case thread
engagement. **Reopening trigger:** obtain SKU-linked body, marked-end axis and
complete-thread limits, together with a traceable barrel material/thread
resistance basis or part-specific test evidence. Then rerun this exact
recessed-centered pose with the actual bolt/washer stack and changed-topology
joint checks. No manufacturer contact is part of this continuation. Reopening
does not select the joint; the following gates remain, and none blocks the
independent corner-block work:

1. Tie one purchased SKU to a controlled manufacturer drawing or measured lot
   limits for OD, length, marked-end axis offset, complete threads, chamfers
   and tolerances.
2. Establish traceable barrel material/thread minima or part-specific proof
   testing, plus compatible bolt and washer properties. Do not infer them from
   the bolt shaft or a dimensionally similar Stafast part.
3. Prove the complete wood and steel mechanisms under simultaneous PB05/PB06
   actions, including spacing, end/edge, splitting, net section, group action,
   contact, slip, rotation and stiffness.
4. Re-run exact CAD clearance against all 66 protected axes and remaining
   frame duties, then demonstrate jig accuracy, tool access, assembly,
   removal, delivered stack length and blind-hole clearance physically.
5. Cost the required tooling, jig, waste, delivery and complete station count;
   preserve all remaining PB05/PB06 conversion, frame-bolt, transport and
   packet duties.

[lowes-barrel]: https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559
[hd-barrel]: https://www.homedepot.com/p/202242356
[bolt]: https://www.homedepot.com/p/204633308
[washer]: https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987
[stafast-product]: https://shop.stafast.com/cross-dowels/cross-dowels-with-1-hole/jcd14201606
[stafast-catalog]: https://shop.stafast.com/catalogdownloads/downloads.aspx
[tr12]: https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf
