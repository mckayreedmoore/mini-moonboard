# Lower-backing angle investigation

**Research candidate, not a selected replacement.** Keep the current backing
bolt limitation visible. This investigation does not authorize removing those
bolts or assign a connection resistance.

The existing 38.1 mm-wide principal gives a centered 3/8-inch backing bolt only
19.05 mm side-edge distance. An angle could retain the housed backing without
that large narrow-edge bore. The existing ML24Z is too wide along the board:
101.6 mm versus the backing's 88.9 mm.

This is not automatically resolved by halving a bolt rating. The
[2018 NDS Commentary, C12.5.1.3, printed page 264](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf)
explains the 4D perpendicular-to-grain loaded-edge requirement and states that
the section supplies no specific reduced-edge-distance geometry factors.
Its reductions for end distance or fastener spacing are different provisions.
For this 9.525 mm bolt, 4D is 38.1 mm; the existing side edge is 19.05 mm.
This establishes an unresolved cross-grain design condition, not a quantified
capacity loss or proof that all possible load directions fail. Confirm the
governing current standard and actual joint load direction before assigning
resistance; no current-edition alternative reduction was established here.

## A21 geometry and installation

Official A21 CAD is available through the
[Simpson CAD library](https://www.strongtie.co.uk/en-UK/products/angles-a).
The linked SAT contains an inch-derived A21 model, including four hole axes;
extracted coordinates and downloaded-file hashes are in
[the reference record](backing-angle-reference.json). The CAD is hosted by the
UK site. Confirm correspondence with the actual US A21/A21Z product before
treating it as its fabrication geometry. No raster-derived hole locations or
complete replacement connector solid have been invented.

The narrow model width suggests a trial at S=62 mm, on the outer side of each
principal and the backing's rear N=38.1 mm plane. Its gross width lies within
S=44.5375–79.4625 mm, beyond the lowest LED pocket's S=39.2 mm extent. This is
only a placement hypothesis; screw paths and tool clearances are not proven.
The outside bays avoid squeezing connectors into the central 38.1 mm gap.

[Simpson's approved screw schedule](https://www.strongtie.com/products/fastening-systems/technical-notes/sd-connector-screw-approved-connectors)
uses four separately purchased SD9112 screws per A21. Do not substitute the
existing ML24Z's SDS screws. Exact SD9112 head dimensions and the chosen driver
outside envelope remain missing; a nominal hex-drive size is not a tool-clearance
diameter.

## Why catalog loads do not close this joint

[ICC-ES ESR-3096](https://www.icc-es.org/wp-content/uploads/report-directory/ESR-3096.pdf),
January 2026, Table 1 lists single-angle F1/F2 values of 430/165 lbf only for
CD=1.6; it excludes other load durations and combining these directions. F1
reversal requires opposite-side angles, but that arrangement requires a
76.2 mm-thick member. Our principal is only 38.1 mm. An unpaired F2 installation
requires rotation restraint. Section 3.2.2 also specifies wood density/moisture
conditions and receiver thickness at least the selected screw length.

Consequently, the two-angle idea is **not yet a demonstrated bidirectional
replacement**. No local joint demands or applicable climbing-load duration
have been established. The housing's compression bearing alone does not prove
separation or racking retention.

## Finite next checks

Confirm product/CAD equivalence and SD9112 geometry; rigidly place the real
connector; check every screw's net receiver, front/back breakthrough, head and
driver envelope against the panels, service pockets and neighboring hardware.
Then resolve the loaded-member direction, rotation restraint and applicable
duration with the manufacturer or structural reviewer. If these conditions
cannot be met, use a different connection rather than transferring the table
values. Widening the principal is a separate lumber redesign, not an automatic
consequence of this investigation.
