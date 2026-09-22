# Two full-inventory bolted viewer concepts — owner comparison

Status: **development comparison, 21 September 2026; neither concept is
viable, build-ready, or a drilling release**. This compares the current
[corner-block viewer](owner-corner-viewer.md) and the developing
[barrel-nut assembly](../../scripts/owner_barrel_layout_assembly.py), not the
selected construction packet. Both aim to replace 24 historical angle/SDS
duties in a kerf-right frame while retaining the 66 panel/kicker screw axes,
12 original frame-bolt arrangements, owner-approved center posts at X = ±180
mm, and separate kicker-screw backers. The two backers are common to both
layouts; their attachment is not yet qualified. Original brackets/SDS remain
part of the selected baseline, not accepted replacement hardware.

| Measure | Corner-block concept | Cross-dowel/barrel concept |
| --- | --- | --- |
| Visible replacement | 24 solid timber blocks | 20 direct poses; four mixed fallback blocks |
| New hardware axes | 92 bolts | 48 bolt/barrel pairs |
| Added timber | 24 blocks | Four unfastened fallback blocks |
| Assembly | Through bores; two-sided seats | Perpendicular bores; barrel alignment |
| Current status | **REVISE** | **REVISE** |

The [corner assembly](../../scripts/owner_corner_layout_assembly.py) requires
all 24 blocks and 92 new bolt axes, but it is not a complete physical hardware
screen. Its [viewer note](owner-corner-viewer.md) records protected
light/wire/T-nut and access conflicts in the ten rail duties, bottom-center
E1/G1 nut/tool conflicts, and outer-base/outer-header block–stack clashes.
Its cross-family check omits several bore, stack, and tool interactions. The
PB09 wire relief is an actual modeled cut only where its measured pre-cut
wire overlap requires one; owner approval, feeding, net wood section, and
joint resistance are open. None of those problems is cured by hiding a red
solid in the viewer.

The barrel concept is source-distinct, not a replacement of those corner
results. Its [ten rail duties](owner-barrel-rail-layout.md) have nominal
intersecting bore pairs and true rail/principal or rail/side butt contact;
two right-center direct poses still hit protected geometry and display
unfastened compact cleat volumes. The [center six](owner-barrel-center-layout.md)
include two principal/header mixed/REVISE positions with zero nominal
washer-to-edge margin. The [outer/top eight](owner-barrel-outer-top-layout.md)
are all **REVISE**, including explicit outer-base neighbor-access exceptions.
The integrated barrel
assembly exposes barrel bodies, diagnostic shafts, bores, and access volumes,
but does not finish same-family collisions, full protected-service clearance,
or a physical assembly sequence. Showing a direct bore intersection proves
neither thread engagement nor a load path. The four fallback blocks are space
illustrations, not fastened joints.

For repeated disassembly, both concepts have a plausible *mechanical action*
but no qualified cycle life. Corner bolts could be removed from nuts if both
ends remain reachable; washer crushing, hole wear, bolt preload, and re-seating
after transport have not been tested. Barrel bolts could be backed out, but a
recessed/slotted barrel must stay aligned or be recovered through its cross
bore; thread damage, lost parts, wood wear, real tool access, and repeatable
reassembly remain untested. Neither concept earns a durability advantage from
its furniture-hardware label or from the viewer animation.

## Retail and cost scale, not a bill of materials

On this date, Lowe's
[Hillman 880543](https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559)
displayed **$1.48 each**. [Home Depot lists the same model](https://www.homedepot.com/p/202242356)
but did not expose a usable public price in this check. A Home Depot
[Everbilt 800676 1/4-20 × 5-in bolt](https://www.homedepot.com/p/204633308)
result displayed **$0.62 each**; other verified retail web results showed
**$0.57–$0.62** by location/time. Thus 48 nominal barrel/bolt pairs allocate about
`48 × ($1.48 + $0.57–$0.62) = $98.40–$100.80` **only if** every pose uses
those exact single pieces. This excludes washers, approved hardware grade,
spares, freight, tax, tooling, wood, and any changed lengths or fallbacks.
Retail identity and nominal dimensions do not control the Hillman thread-axis
offset, usable internal thread, material resistance, or delivered fit.

For a rough *bolt-only arithmetic scale*, 92 pieces at the observed 5-in
$0.62 would be $57.04, while 92 at the currently displayed
[8-in Everbilt 800696 $0.94](https://www.homedepot.com/p/204281626)
would be $86.48. **Neither is a corner-concept quote or a bound**: actual
length mix and compatible purchased stacks are not established, and the
corner option additionally needs nuts, washers, 24 suitable timber blanks,
cutting, tooling, waste, and delivery. A
[12-pack nut lead](https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718)
was $1.98 online, but its grade/fit and the correct washer OD for every
corner station have not been selected. The prior
[stock-cost study](simple-pb05-short-stock-cost.md) is a different scoped
eight-block study and must not be transferred as a full 24-duty cost.
No complete installed-price comparison or savings claim is supported.
Online prices and stock vary by store and date.

## Gates before a choice or any construction packet

Both layouts need all finite hold/T-nut/unused-hole/hold-bolt, LED/wire,
panel-screw, frame-bolt, candidate-hardware, and tool interactions closed in
the *integrated* geometry. They also need selected, measurable hardware and
clearances; repeatable drilling/insertion and transport sequence; wood
edge/end/net-section and full joint-family resistance; whole-frame load path;
backer attachment; and resolution of every recorded REVISE/exception.
Barrel hardware specifically needs a controlled Hillman-equivalent body and
thread-axis tolerance, complete engagement and tip clearance, barrel metal
and thread resistance, and wood bearing/splitting checks. Corner hardware
specifically needs delivered bolt grip/thread, nut/washer seats and access,
block stock/cut quality, and the unresolved protected-service reliefs.
Neither a shaft rating, a nominal bore intersection, nor a store listing is a
complete joint verdict. All drilling, fabrication, structural, and climbing
release flags remain **false**.

Do not request an owner selection yet. First publish and inspect **both**
switchable full-inventory viewers with their blocked solids and limitations
visible; only then ask which development concept to advance for further
engineering. That choice would select a research path, not authorize a build.
