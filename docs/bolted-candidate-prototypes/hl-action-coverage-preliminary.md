# Preliminary HL action coverage: common core and one cut bottom rail

**Scope and status.** This is an action inventory for the present
[common-core HL33 center trial](hardware_first_hl33_common_core.md) and its
left cut bottom rail. It is not a load allocation, connector selection,
resistance check, or fabrication release. The two sampled common-core poses
are already rejected for backing-connection catalog inapplicability and
bolt-end access. The cut rails have no modeled factory-bracket attachment.
The [corrected axis audit](hl-load-axis-audit.md), committed in `32fe0c4`,
supersedes the earlier 90-degree F1 mapping. This document changes no pose.

## Simultaneous source and reference point

The six applied case definitions are retained in
[`clear_space_batch.CASES`](../../scripts/clear_space_batch.py). A current
common-core model has **no established simultaneous local wrench** for the
lower core/header joint, either upper principal/header joint, or either cut
rail/header joint. Contact state, stiffness, and force sharing in that
topology are also unknown. The [center demand worksheet](../bolted-candidate-center-demand-worksheet.md)
records why the old ML24Z/SDS proxy reactions cannot fill these rows: even
same-case old results belong to another load path. The
[A1-rear 10k evidence bundle](center-evidence-bundle.md) is a provisional
old-topology diagnostic, not a current-geometry station demand. Do not take
separate maximum force and moment entries from different cases as one wrench.

For each future case, declare **one common joint origin `O`** and a global
right-handed `X,Y,Z` basis (`X` across the board, `Y` front to back, `Z` up).
Every force and **every wrench moment must be stated about that declared
origin** before comparing or summing actions. A wrench reported about `P`
must use `M_O = M_P + (P - O) × F`; merely rotating axes does not translate
the moment. Record member-on-joint versus joint-on-member signs, all contact
forces and application points, and the simultaneous equilibrium residual.
The [axis helper](../../scripts/hl_load_axes.py) projects a wrench already
at one origin; it neither translates moments nor allocates load. Equilibrium
alone **cannot apportion an indeterminate load among angles, bolts, and
contact patches**. Such allocation needs the actual geometry, contact state,
and defensible relative stiffness or a tested assembly model.

## Catalog boundary and local axes

The current [Simpson C-C-2026 catalog, HL page 315][catalog] and
[HL applicability card](hl33-hl53-applicability-card.md) specify one 1/2-in
structural through-bolt per HL33 leg, wood at least 3-1/2 in thick, and a
single-angle DF/SP table with **uplift 740 lb and F1 1,040 lb only at (160)**.
These are catalog directions, not capacities adopted for this pose. The
[ordinary-duration decision](hl-ordinary-duration-decision.md) establishes
no manufacturer-published HL33 (100) value. The catalog supplies no F2,
moment, separation rating along any other axis, slip, or installed-assembly
interaction value for the present joints. Its depicted `+Z` uplift is
published at (160). Two connectors may double tabulated uplift under the stated
conditions; lateral load may not be doubled, and both sides are required for
F1 in both directions. No such pair is qualified here. The catalog's general
simultaneous-load unity rule (p. 289) requires applicable allowable values
for each nonzero component; it does not fill the missing HL transverse or
moment cells, resolve angle sharing, or establish a (100) combination.

For a horizontal-seat-up HL, local `e1` is the **signed horizontal flange
reach and F1 axis**, `e2 = +Z × e1` is the bend-line/transverse axis (unlisted
for HL), and `e3 = +Z` is the catalog uplift axis. Signs describe geometry,
not verified resistance in both senses:

| Present center angle | `e1` / F1 | `e2` / unlisted transverse | `e3` / uplift |
| --- | --- | --- | --- |
| Upper right, outward principal face | `+X` | `+Y` | `+Z` |
| Upper left, outward principal face | `-X` | `-Y` | `+Z` |
| Lower, rearward core face | `-Y` | `+X` | `+Z` |

The **left bottom rail** is represented by an inner cut near `X = -130 mm`
and a length running toward `-X`; its representative local bookkeeping axes
are `r1 = +X` toward the center, `r2 = +Y`, `r3 = +Z`. These are **rail axes,
not HL load axes**: no rail bracket, flange reach, mating seat, or bolt
layout has been selected. Its original 38.1-mm section is below HL33's
88.9-mm minimum. The separate
[profiled bottom-rail relief](hardware_first_center_rail_relief.md) finds a
90.4748-mm full-section side band only as a nominal geometry comparator;
it does not install or rate an HL33. A direct bracket on the new X-normal
end would require a through-bolt along the roughly 1-m rail and is rejected
as that simple pose.

## Preliminary action-coverage matrix

“Possible contact” means **compression normal to a verified, closed wood
face only**, with bearing and downstream path still unchecked. An open face
provides no tension; tangential shear or friction is not credited. An ideal
butt in CAD is not proof of actual contact, force share, or wood resistance.

| Action at `O`, each sign considered | Center: lower core/header and two upper principal/header joints | Left cut bottom rail/center | Coverage now |
| --- | --- | --- | --- |
| `+Z`, vertical separation/uplift | HL drawing lists `+e3` uplift for its typical installation; no current assembly allocation or (100) value. Opening core or principal butt contact carries none. | Rail/center separation mode and bracket orientation unknown; no uplift transfer assigned. | **Unsupported as a rated current action.** Establish exact load path and ordinary-duration connector value. |
| `-Z`, vertical compression | Core/header and principal/header closed bearing faces are possible contact paths, conditional on fit, load direction, bearing and other members. Do not assign it to an HL uplift cell. | A cut X-normal end cannot supply vertical normal bearing; other actual seated faces are unproved. | Conditional contact-only center path; rail vertical path unsupported. |
| `+X`, horizontal reversal A | Upper-right local `+e1`; upper-left local `-e1`. Lower local `+e2`, **unlisted**. Which angle takes force is unknown; common center action is not a per-angle action. | Toward-center compression could close an X-normal end **if** a real opposing face and contact are established; no bracket path is modeled. | Upper F1 direction only is listed at (160), with sign/pairing and (100) open; lower transverse and rail bracket paths unsupported. |
| `-X`, horizontal reversal B | Opposite upper F1 signs; lower `-e2` is unlisted. A single outward upper angle per principal does not establish reversible F1. | Opens a left rail end contact; needs positive attachment. | Unsupported reversal without verified opposing bracket/load path. |
| `+Y`, horizontal reversal A | Lower `-e1` (opposite signed reach); upper right `+e2`, upper left `-e2`, both **unlisted**. | Tangential to an X-normal cut face; no friction credit or bracket. | Upper transverse and rail paths unsupported; lower F1 sign, (100), and allocation open. |
| `-Y`, horizontal reversal B | Lower `+e1`; upper transverse signs reverse and remain unlisted. One lower rear-face HL does not establish reversible F1. | Tangential to an X-normal cut face; no friction credit or bracket. | Unsupported reversible lower/rail path; upper transverse remains unlisted. |
| `M_X` about common `O` | A `Y` offset acting through `F_Z`, or `Z` offset through `F_Y`, can make this couple; finite contact patches and bolt/angle stations may participate only when their actual lever arms and stiffness are known. | Torsion about the rail length: a `Y`/`Z` force couple would need spaced attachments or qualified contact and restraint. | No HL moment rating or resolved couple. |
| `M_Y` about common `O` | A `Z` offset through `F_X`, or `X` offset through `F_Z`, can make this couple; vertical separation can remove the assumed compression arm. | Bending in the rail's `X-Z` plane needs a longitudinal `X` arm for `F_Z`, or vertical `Z` arm for `F_X`. | No HL or rail-joint moment rating or resolved couple. |
| `M_Z` about common `O` | An `X` offset through `F_Y`, or `Y` offset through `F_X`, can make this couple; opposing upper angles are not automatically a rated pair. | Bending in the `X-Y` plane needs longitudinal `X` separation for `F_Y`, or `Y` separation for `F_X`. | No HL or rail-joint moment rating or resolved couple. |

For every moment row, use **actual force application points** and
`M_O = Σ(r_i - O) × F_i + ΣM_i`; any direct local couple must be identified
separately. The table names mechanisms and required lever arms, not available
resistance. Compression on one side of a face could contribute a moment only
if contact stays closed over a finite patch and an opposing action completes
the couple. A point butt, unverified friction, or one bolt does not establish
that couple. No unlisted force or moment component is assumed zero.

## Smallest next design changes implied by the gaps

1. **Center reversals:** a physically opposed, catalog-applicable bracket
   path is the smallest conceptual addition for each single-angle F1 reversal;
   the opposite sign and shared bolts still need their own fit and mechanics.
   It does not cover transverse `e2`.
2. **Transverse actions and moments:** retain a separate, positively attached
   path with documented applicable axes, or develop an explicit whole-joint
   wood/bolt/formed-angle and contact assessment with actual lever arms.
   Merely adding an HL33 or multiplying its F1 entry does not rate `e2` or a
   moment. The separate front backing connection needs a catalog-applicable
   arrangement and two-ended bolt access before that path can be used. The
   [independent-bolt backing revision](hardware_first_hl33_backing_revision.md)
   in `b72d638` still fails access and ordinary-stock fit.
3. **Left bottom rail:** add one compatible factory-bracket connection on an
   accessible transverse rail face with a real center mating seat; first
   preserve enough wood thickness and verify its through-bolt direction,
   geometry, access, and all required actions. The nominal profiled band is
   a starting fit constraint, not a completed connection.
4. **Load allocation and duration:** obtain simultaneous current-topology
   wrenches about declared origins for every case and a justified contact/
   stiffness allocation. Establish an applicable ordinary-duration value
   or independent complete resistance basis, then check combined actions,
   deformation, wood, bolts, and steel. Simpson's (160) F1/uplift entries
   alone cannot close the (100) or interaction gate.

The latest development
[B wide-rib geometry JSON](hardware_first_hl53_wide_ribs.json) is a promising
**geometry-only comparator**, separate from this A common-core matrix. Its
620- and 660-mm spacing cases show eight modeled header links with holes and
receivers, with no recorded failure class beyond open rail-to-rib connections.
At 660 mm, the 15-mm-gap **bottom-right** HL53 rail probe leaves 15 mm of
seat reach unsupported; a separate zero-gap probe has isolated nominal seat
fit. The other five rail ends remain open. The 700-mm case also records a
screw-hardware clash. None of these cases has a connected-architecture
verdict, an adopted material or rating, or a drilling release. The probe
does not supply the left-rail action path evaluated above, and it does not
close the reversal, moment, interaction, or ordinary-duration gaps.

These are bounded next gates, not instructions to alter the present geometry
or evidence that either concept is selected or structurally qualified.

## Appendix: B wide-rib action coverage at 660 mm

This appendix reads the development
[wide-rib script](../../scripts/hardware_first_hl53_wide_ribs.py), its
[report](hardware_first_hl53_wide_ribs.json), and the parent
[spaced-rib script](../../scripts/hardware_first_hl53_spaced_ribs.py).
The 660-mm parent has **eight HL53 header links**: two upper and two lower
on each side. The separate zero-gap **bottom-right** rail HL53 is an isolated
probe, not a ninth integrated parent link. No simultaneous B-geometry joint
wrenches or angle/contact load shares have been established. Use the declared
common origin `O` and wrench translation rule above for every future case;
old-proxy station reactions are not B demands.

The parent `add_bracket` solids put each upright leg on an X-normal wood
face and each horizontal seat along signed X. Their bolt axes are X through
the upright wood and Z through the header seat. The rail probe likewise has
an X-normal upright leg on the right rib and a +X seat over the rail. By the
[corrected HL axis audit](hl-load-axis-audit.md) and the updated
[signed-axis helper](../../scripts/hl_load_axes.py), geometric F1 follows
the seat reach, **not** the Y bend line. Here `e2 = e3 × e1`; lower seats
have `e3 = -Z`, so their signed transverse axes reverse:

| B orientation | Reach / F1 `e1` | Transverse `e2` | Geometric `e3` |
| --- | --- | --- | --- |
| Left upper front | `-X` | `-Y` | `+Z` |
| Left upper rib | `+X` | `+Y` | `+Z` |
| Right upper front | `+X` | `+Y` | `+Z` |
| Right upper rib | `-X` | `-Y` | `+Z` |
| Left lower front | `-X` | `+Y` | `-Z` |
| Left lower rib | `+X` | `-Y` | `-Z` |
| Right lower front | `+X` | `-Y` | `-Z` |
| Right lower rib | `-X` | `+Y` | `-Z` |
| Right bottom rail, zero-gap probe | `+X` | `+Y` | `+Z` |

These are **modeled orientation axes**, not proof that any one angle works in
both F1 signs. The four lower seats are inverted relative to the catalog's
typical horizontal-seat-up drawing. Their `-Z` e3 is a **coordinate
transform only**: the catalog's seat-up `+Z` uplift allowable cannot be
transferred to them by rotation alone. Simpson
[C-C-2026 p. 315][catalog] lists HL53 DF/SP F1 **1,310 lb** and uplift
**740 lb** per angle at **(160)** only;
it lists no transverse component or moment, and the
[duration decision](hl-ordinary-duration-decision.md) supplies no HL (100)
rating. No number is adopted for this B installation or its simultaneous
actions.

| B action at common `O` | Preliminary path and limit |
| --- | --- |
| Global `+Z` / `-Z` | Upper/header or rail seats may transfer closing **normal compression** only if contact is actually closed and bearing is checked; open contact transfers no tension. The catalog depicts `+Z` uplift at (160) for a seat-up installation, but its application to each installed upper/rail pose remains unproved. Lower seats have geometric `e3 = -Z`; neither their opening/closing sense nor a rated uplift path follows from that transform. No other separation axis is rated. |
| `+X` and `-X` reversals | The model contains +X and -X reaches among the eight header links, but their presence does not establish which sees either sign or a reversible rated pair. An actually closed X-normal rail end could take compression toward the right rib; opening needs positive attachment. The zero-gap CAD fit establishes no force share or bearing value. |
| `+Y` and `-Y` reversals | Y follows every header/rail bracket's **unlisted transverse** bend-line axis. X-normal face contact gives no Y normal reaction; friction is not credited. Both reversals need another verified path. |
| `M_X` | A `ΔY` arm on `F_Z` or `ΔZ` arm on `F_Y` is needed. Front/rib Y stations and upper/lower heights are nominal geometry, not a resolved couple or HL moment rating. |
| `M_Y` | A `ΔZ` arm on `F_X` or `ΔX` arm on `F_Z` is needed. Upper/lower level and front/rib spacing could form arms only after actual force points, contact state and load sharing are established. |
| `M_Z` | A `ΔX` arm on `F_Y` or `ΔY` arm on `F_X` is needed. Opposite reaches and spaced stations do not by themselves rate a torsional couple; Y shear remains unlisted. |

For all three moment rows, `M_O = Σ(r_i - O) × F_i + ΣM_i` uses **the same
declared `O`**. Actual bearing patches, bolt/angle deformation and contact
state determine the forces; equilibrium alone cannot apportion this
indeterminate network. No unlisted component is set to zero. The catalog's
general interaction rule cannot close a combination with missing (100),
transverse, or moment values.

The zero-gap probe records full 146.05-mm modeled seat reach over wood, four
contained bores, and no clash within its isolated rib/rail/panel/short-tool
screen. Its **parent-neighbor integration was not checked** against the
changed header and front carriers, other original wood, or the eight header
brackets and their bolt/tool envelopes. Actual head/nut stacks and tool
sweep, delivered HL53 dimensions, catalog installation applicability, wood
resistance, and ordinary stock for the one-piece rail also remain open.
The **other five rail ends** have no factory connections or action paths in
this report. The 660-mm header fit and isolated probe therefore establish
neither a connected assembly nor a selected or structurally qualified B
architecture.

[catalog]: https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf
