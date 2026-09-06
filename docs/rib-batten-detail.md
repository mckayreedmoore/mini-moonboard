# Rib/batten detail selection: side-grain bearing block

Checked 2026-09-06. **Development proposal, not a selected fastener schedule or
capacity approval.** Retain the current `2x8-foot100` geometry and all original
candidates. The minimal separately named concept is
`rib-batten-sidegrain-same-envelope`; the dimensional screen below explains why
changing the grain label alone does not finish its connection design.

## Exact candidate and geometry

The authoritative assembly is `footprint_frame.parts(100, False)` with
`footprint_frame.connections()`, which delegates its backing to `shallow_frame`.
Do not use `hybrid_frame.parts('2x8')` for this check: that older candidate has
unrotated rear crossmembers and different rib lengths.

Use board-local X/S/N from [orientation](orientation.md). Representative member:
`rib_1_mid_left`, centred at X = −519.2 mm and S = 400 mm.

| Item | Actual bounds / dimension, mm | Imperial dimension |
| --- | --- | --- |
| Rib X | −538.25 to −500.15; thickness 38.1 | 1.5 in |
| Rib S | 355.55 to 444.45; length 88.9 | 3.5 in |
| Rib N | 38.1 to 128.05; depth 89.95 | 3.5413 in |
| Front batten N | 0 to 38.1 | 1.5 in |
| Rear crossmember N | 128.05 to 166.15 | 1.5 in |
| Original front screw | S = 372; N = 0 → 88.9 | 3.5 in overall |
| Nominal screw penetration past batten | 50.8 | 2 in |
| Screw tip to rear rib interface | 39.15 | 1.5413 in |

Direct CadQuery cylinder/undrilled-solid intersections for all 12 front rib
screws found only their two declared timber members. There is **no 11.65 mm
protrusion or rear-crossmember collision in this candidate**. That apparent
protrusion belongs to the older unrotated geometry and must not be carried into
the current design decision. Cylindrical envelopes do not establish effective
thread engagement, head seating, or manufacturing tolerance.

The candidate-depth and shaft-intersection regression can be rerun with
`uv run pytest tests/test_rib_batten_geometry.py`. It uses the actual foot100
parts, not dimensions copied from its ancestor.

## One minimal concept, and what it changes

Keep that rectangular envelope and its compression-bearing front interface,
but cut it with lumber grain parallel to S rather than N. The front N-axis
screw then enters side grain. The existing rear X-axis bolts also enter side
grain, but their grain-end distances change and must be checked anew.

Required stock/cuts: use a structurally graded dressed 2×6, retain its 38.1 mm
thickness in X, rip its broad dimension to 89.95 mm in N, and crosscut an
88.9 mm length along grain in S. A nominal dressed 2×4 is only 88.9 mm wide:
it cannot supply the required 89.95 mm cross-grain dimension. Do not silently
leave a 1.05 mm bearing gap or add an unqualified shim. Actual stock size,
grade, grain deviation and cut tolerances remain procurement checks.

Compression passes through contact between batten and block, then through the
rear interface. Opening and in-plane shear need an explicit fastener load path;
one front screw is not an assumed moment connection. Do not credit glue,
friction from tightening, or perfect bonded behavior for this detail. Rotation
of grain also changes directional stiffness and bearing strength, so the old
isotropic bulk model cannot establish this block's capacity.

## Fastener screen: not a drop-in product substitution

In the same envelope the present front screw is 16.45 mm from the nearest
S-direction grain end and 19.05 mm from an X edge. Moving it to S = 400 would
increase the end distance to only 44.45 mm. The rear rib bolts are at S = 426,
giving 18.45 mm to the nearest grain end; moving grain therefore does not
resolve the rear connection either.

The manufacturer's current 2025 guide gives axial-only minimum end/edge
distances of 82.55/34.925 mm for SDS screws and 57.15/22.225 mm for SDWS16
framing screws. Neither fits this block even with the front screw centred.
Mixed lateral/withdrawal loading needs the applicable additional conditions,
not the axial-only shortcut. Thus **neither family is selected here**; reducing
screw length alone cannot cure the spacing issue. See pages 47 and 75 of the
[manufacturer technical guide](https://www.strongtie.com/resources/literature/fastening-systems-technical-supplement).

The A35 is also not an automatic replacement for the generic screw. Its
configuration, complete fastener pattern, material and load directions must
match the selected installation. The current catalog requires at least
76.2 mm joist thickness for angles on both sides; the rib is only 38.1 mm
thick. Therefore a symmetric pair cannot simply inherit that catalog rating.
Field bending is permitted once, not arbitrary cutting/re-drilling to fit.
The existing rear angle occupies part of this bay, so a front clip would need
an actual drawing/hole/head/tool-clearance study. See pages 309–310 of the
[2026 connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
and the [installation configurations](https://www.strongtie.com/resources/product-installers-guide/a35-installation).

Connector screws are product-specific. Use the manufacturer's
[approved connector/screw combinations](https://www.strongtie.com/products/fastening-systems/technical-notes/sd-connector-screw-approved-connectors),
not a generic deck screw or an SDS substitution in an SD-only connector.

## Decision and next physical detail

### Enlarging the block is a joint-layout change

A follow-up all-12-rib CAD screen uses two centred, rectangular distance
envelopes, retaining the existing N = 38.1–128.05 mm bearing depth:

| Screen, not a selected block | X width × S length, mm (in) | Overlap with each existing rear angle, mm³ |
| --- | --- | ---: |
| SDWS16 axial-only end/edge minima doubled | 44.45 × 114.3 (1.75 × 4.5) | 22,580.60 |
| SDWS16312 perpendicular-to-grain lateral end/edge minima doubled | 50.8 × 203.2 (2 × 8) | 42,858.69 |

The second envelope uses the guide's 4 in end distance and 1 in edge distance
for that specific screw and loading direction (page 47). These are necessary
centred-screw distance screens, not a combined-load design, nominal lumber
sizes, selected stock, or an allowance for cutting tolerances. The existing
off-centre screw location would not meet these symmetric end-distance limits.

Both envelopes intersect their corresponding rear angle at **every** rib.
Against the unchanged undrilled assembly, no other positive-volume body
intersection was found for these individual substitutions. This check does not
include replacement-angle geometry, fastener heads/tool access, hardware/wiring
envelopes, or a new hole layout. It cannot establish that an enlarged assembly
fits or that its connections carry the demand. The existing tests now reproduce
these overlap volumes as well as the original screw-depth checks.

Consequently, do not switch to an enlarged block in isolation. The next detail
candidate must move/redesign its rear angle and bolts together with the block,
then audit all stations and the front fastener's actual bearing/thread geometry.
A front clip with a documented applicable installation remains an alternative;
neither route currently justifies deeper perimeter rims.

The same-envelope side-grain block is a useful preserved concept, but **is not
ready to replace the current assembly**. No CAD or purchase-list change follows
from this note. Before committing to it, select an applicable smaller-fastener
system with sufficient spacing and demand capacity, or enlarge the block and
joint layout to fit a documented system. Enlargement must check all three rib
stations, seam-pair spacing, rear angles, panel screws and 40 mm hardware/wire
reliefs; a representative fit is not whole-frame qualification.

Prioritize a traceable force/moment demand envelope and this geometry/product
fit screen over a detailed thread mesh. If a larger block or side-grain clip is
required, publish it as a separate candidate, with compression-only contact and
explicit connector compliance in any local analysis. Preserve the original
bulk comparisons, and do not reinterpret their perfectly bonded joints as
tested versions of the new connection.
