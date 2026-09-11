# Panel screw reference review

Checked September 11, 2026. This is a source and applicability review, not a
fastening schedule or construction release. No historical models, reference
files or archived evidence were changed.

**The reviewed Moon guidance does not establish a numerical screw count or
spacing for this project's principal rows.** That absence does not establish
that the modeled screws are unnecessary. Count and placement require the
actual panel, framing, fastener and load-path checks below.

## What the manufacturer guidance establishes

The current [Moon build page](https://moonclimbing.com/build-your-moonboard)
links its DIY guide at [How-to-build-a-MoonBoard_v2.3.pdf](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf).
The filename says v2.3; the document itself is marked Version 2.2, July 2023.
Its Mini section, printed page 2, specifies four uprights at 813 mm spacing,
a 40° inclination and a 150 mm kicker. The webpage also calls for horizontal
bracing across panel joints. No numerical panel-fastener count, principal-row
pitch or matching screw specification was found in the reviewed textual
instructions. Do not count schematic symbols as an engineered screw schedule.

Those frame requirements concern the illustrated DIY kit arrangement. Our
freestanding assembly has separated center receivers, different support
positions, altered backing, purchased plywood and independent panel seams.
Manufacturer geometry guidance therefore does not approve its panel connections
or its frame. Hold-grid holes, LED holes, hold anti-rotation screws and
panel-to-timber attachment screws are different operations; a specification for
one does not set the count of another.

## Relevant connection references and their limits

[APA Technical Note E830, Fastener Loads for Plywood—Screws](https://www.apawood.org/guides-tools-training/technical-document-library/technical-notes/fastener-loads-for-plywood-screws/)
is listed as revised June 2011. APA describes ultimate withdrawal and lateral
test values for particular screwed plywood joints and a section on estimating
allowable loads. Its public summary is not a universal screw-spacing rule.
No numerical capacity or spacing has been imported from an inaccessible table.
Roof/wall diaphragm nail schedules and floor-sheathing attachment rules are not
substituted for an outward-loaded climbing-panel screw design.

The [SPAX evaluation report 2010-02](https://www.drjcertification.org/report/download/1936),
revised November 4, 2025, includes the modeled XFT08P-2000 product. Its material,
penetration, head, spacing and installation conditions must accompany any
applicable withdrawal, pull-through or lateral value. The existing
[conditional hardware reference](infill-panel-hardware-reference.json) is a
starting ledger, not an approved connection or a rule for dividing load equally
among screws. Actual plywood applicability and combined loading remain open.

## Questions the necessity audit must answer

1. Which screw rows provide a required tension/shear connection, and which
   timber surfaces provide only compression contact? An unfastened principal
   must not become an ideal restraint against outward panel movement merely
   because timber lies behind it.
2. For each face panel and principal, what are the actual screw count, occupied
   positions, maximum gap, end/edge distances and hardware/service conflicts?
   Audit both outer and center principals, not just the newly added screws.
3. Can a less dense, explicitly connected candidate meet the same load cases,
   seam-motion criterion and connection checks? Compare whole candidate patterns;
   removing a screw changes force distribution, so a small force in one prior
   case is not proof that it is redundant.
4. Do the actual screw, timber and plywood satisfy withdrawal, head pull-through,
   lateral and combined-action requirements with appropriate adjustments and
   realistic connection compliance? Include relevant load reversals, hold offset
   and tangential force. Mesh-sensitive ideal point reactions are diagnostics,
   not physical demand bounds.
5. What limits are assigned to panel motion and joint opening, and what material
   identification and installation details are still needed before release?

A useful next step is the complete per-principal schedule audit followed by a
bounded comparison of the retained pattern against a simpler candidate. Neither
more screws nor fewer screws is accepted solely from count. This review does
not change the separately established lights-last sequence: feed intact strings
through adequate closed timber passages before seating the bulbs; no harness
cutting is implied.

## User's video reference and the 12-screw comparison

The reference is Moon Climbing's [The Best Boulders on the Mini MoonBoard, assembly sequence from 0:53](https://www.youtube.com/watch?v=wDB6Lg4x_lM&t=53s).
On September 11, 2026, the locally retained 31 frames spanning 0:53–1:08
were re-inspected, including full images at approximately 1:04, 1:06.5 and
1:08. A fresh YouTube fetch was throttled; the existing local reference frames
provided direct visual evidence. They remain unredistributed.

The images show an A-profile assembly with rear legs, broad side framing,
internal longitudinal supports and horizontal members at panel levels. Four
face panels are installed in a two-by-two layout. The visible arrangement is
consistent with a freestanding frame; it is not evidence that this reference
uses wall anchors. Hidden restraints cannot be resolved from these views.

The user reports 12 attachment screws per panel. That is a reasonable pattern
to compare explicitly. This review cannot independently certify the count:
workers obscure installations, the sequence is a time-lapse, and small panel
attachment points cannot consistently be distinguished from hold-grid and LED
holes. No larger minimum screw count has been established by this video review.

The custom split-center arrangement must be compared using its actual backing,
edge overhangs, screw positions and connection properties. The reference's
visible horizontal members do not prove a bonded seam or equivalent support
compliance. Likewise, a numerical refinement failure in our ideal point-support
model is a limit of the calculation, not proof that 12 screws physically fail.
A useful comparison keeps the same loads and geometry, models an explicit
12-screw pattern per face panel, and reports panel movement and connection
limits without assuming either greater screw density or reference-video
similarity establishes adequacy. Any departure from the reference load path
should be stated specifically, rather than justified by an unspecified demand
for stricter testing.
