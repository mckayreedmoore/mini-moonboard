# Bolted MVP: active rated-hardware development focus

Status: **G1 open; concept development only.** This amends the sequence for
the owner-authorized hidden-frame redesign. It does not alter the selected
baseline, release fabrication, or adopt a connector capacity for the board.

The physical build is kerf-right. Keep the climbing surface, panel outlines,
holds, T-nuts, LEDs, all 48 main-panel and 18 kicker screw axes, and their
existing panel-screw policy. Hidden structural members, their ends and
locations, and positively attached timber backing may change. Use only
factory brackets at converted structural joints: no direct wood lap joint,
custom steel, structural wood-thread move interface, or manufacturer inquiry.
Keep the no-slip floor assumption explicit. The twelve old frame-bolt duties
are starting references and must be rechecked. Actual lumber and brackets
remain unmeasured, uncut, and undrilled.

## Immediate design decision

Focus on manufacturer-rated bolted-timber HL angles. Compare at most two
connected center architectures, not more isolated old-frame bracket poses:

1. **A — common structural core with HL33.** One structural center core/post
   receives accessible paired brackets. Separate front backing receives the
   fixed panel/kicker screws and is itself attached by factory-bracket
   connections. Rework header, backing, and affected rail ends together.
   One HL33's F1/uplift table is not a moment or unlisted F2 rating; the
   rotational and transverse paths must be explicit.
2. **B — spaced structural ribs with HL53.** Start with 480/520/560-mm
   rib-center separation and independent fixed front carriers; their
   bracketed connections are part of the model. The shorter bend length
   and two-hole flanges merit a coarse comparison, but 5.75-in reach and
   3.5-in minimum wood must fit. Rework the same neighboring duties.

These are search concepts, not selected dimensions. HL35 remains a local
candidate where its 127-mm bend length and documented installation fit;
the two recent Astra notes disagree on making it the primary center model.
The existing shorter-bend HL53 seed supplies a more distinct two-rib
comparison. Choose from installed fit, action coverage, stock, mass, and
disassembly evidence, not from which prototype already has more code.

The [Simpson HL catalog page](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
provides bolted wood-installation references, not a six-axis board rating.
Retain its specified bolts, supported wood faces, pair rule, and local F1/
uplift axes. Resolve duration applicability and every unlisted transverse,
moment, separation, and simultaneous action through an independently
supported path or calculation. Do not transfer the old proxy forces or
multiply paired lateral values. The
[corrected load-axis audit](bolted-candidate-prototypes/hl-load-axis-audit.md)
maps the outward-X pose's F1 to X; Y is the unlisted horizontal direction.
Neither mapping alone qualifies the joint.

**Bounded resistance-route fallback, not a selected connector.** Home Depot's
[MiTek UB66](https://www.homedepot.com/p/313507617) maps to B66 in
[MiTek's retail cross-reference](https://images.thdstatic.com/catalog/pdfImages/2f/2f1009db-047c-4da8-a283-bcda2c494ebe.pdf).
Unlike the public HL page, [ESR-3455](https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf)
identifies its 12-gauge ASTM A653 SS Grade 40 steel and 0.099-in minimum
base thickness, four 3/8-in ASTM A307 Grade A-or-better bolts, and at least
3 in of receiving wood. One coordinated
[B66 660-mm rail probe](bolted-candidate-prototypes/hardware_first_b66_660_component_route.md)
has now been run: its first complete upright bore exits the rib, so that
nominal pose is rejected, not the B66 family. ESR-3455's F1/F2 table is only
at `C_D = 1.6` and expressly
forbids duration conversion; it is not a normal-duration rating. An
independent route still needs 2024 NDS wood/bolt checks, formed-steel checks
on a consistent ASD basis, load sharing and combined action, deformation,
and the complete installed joint. No B66 rating or architecture is adopted.

## What advances G1

One connected center assembly **and one representative rail joint** must
show all required wood, brackets, bolt paths and access, receiver mapping,
panel-edge support, feasible stock, and a defensible route for the actual
local actions. A collision with a now-changeable neighbor requires a
coordinated redesign, not an automatic family rejection. Positive screw/
wood intersection alone is not proof of edge support, embedment, or load
transfer. A catalog load may be used only for its specified installation,
direction, fasteners, timber and duration; unlisted actions stay open until
another real path is shown. No drilling or whole-board acceptance follows
from a nominal geometry pass.

## v2 task disposition under the authorized redesign

| v2 work | Disposition |
| --- | --- |
| LB-00/01 baseline, scope, 66-axis inventory | Retain; add candidate-specific receiver mapping. |
| LB-02/03 A66, AB205, BR904 and old fixed-frame poses | Historical research; not prerequisites to rated-HL concept selection. |
| LB-04/G1 | Rework as connected center plus representative rail-joint selection. |
| LB-05/06 schemas and CAD scaffold | Reuse/adapt to the chosen physical frame. |
| LB-07–09 old AB90 family/width sketches | Rework duties and kerf-right geometry; preserve both software presentations. |
| LB-10–12 mechanics, wood/bolt helpers, producer | Reuse validated methods with actual new geometry and source-bound inputs. |
| LB-13/G2 and all 36 criteria | Still required, mapped to actual mechanisms; no proxy pass. |
| LB-14A–F/15 six cases | Still required on one frozen candidate, including `a12-forward`. |
| LB-16/17 shop packet and independent review | Still required after geometry and resistance gates. |

The [BR904 drawing and reserve screens](bolted-candidate-prototypes/br904-lowes-drawing-followup.md)
remain honest geometry evidence. BR904 is not an active selection because
its pictured dimensions do not supply a bolted-wood or formed-angle rating.
The partial mixed BR904/HL33 lower script left by the interrupted study is
not an adopted result. Earlier rated-HL prototype failures remain
pose-specific. Keep their data; do not turn supersession into a pass.

## Current concept result, 2026-09-20

The [corrected axis audit](bolted-candidate-prototypes/hl-load-axis-audit.md)
places outward-X F1 along X, not Y; lower inverted HL53 seats have a rotated
`-Z` geometric axis without an adopted inverted-installation uplift rating.
The [action-coverage matrix](bolted-candidate-prototypes/hl-action-coverage-preliminary.md)
still leaves transverse Y, reversals, moments, simultaneous allocation and
ordinary-duration resistance unsupported. These must be resolved for one
current-geometry center and representative rail joint before a G1 selection.

The tested [HL33 common-core backing revision](bolted-candidate-prototypes/hardware_first_hl33_backing_revision.md)
removes its shared three-wood bolt but still fails nut/tool access and an
ordinary one-piece stock comparator. The [HL53 wider-rib comparison](bolted-candidate-prototypes/hardware_first_hl53_wide_ribs.md)
finds 620/660-mm partial header fits and one *isolated* 660-mm zero-gap
bottom-right rail bracket with full nominal seat contact. Its
[parent-neighbor screen](bolted-candidate-prototypes/hardware_first_hl53_660_parent_neighbor.md)
now clears modeled clashes, but five rail attachments remain unchecked;
a Lowe's 6×6 is only
a dimensionally fitting stock lead. B is the stronger **nominal geometry**
lead, not a selected or rated architecture. No shop or drilling release follows.
