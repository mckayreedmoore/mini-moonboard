# Upper-block adjustment and method applicability

This note evaluates adjustments and member-check methods for the eight
reviewed upper blocks and 32 quarter-inch bolt axes, prioritizing the two top
outer `side_2` bolts. It uses the existing conditional
`led-clearance-2x6-runner-seated-blocks-v1` action and geometry packets. It
adopts no resistance, splitting method, or complete-joint acceptance. The
underlying lateral reference is still the unadjusted, partial-thread
six-mode calculation using unadopted `Fyb = 106 ksi` in
[`lateral.md`](lateral.md).

The source basis is AWC's [2024 NDS publication page](https://awc.org/resources/2024-nds/),
its linked [Chapter 2](https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf),
[Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf),
[Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf),
and the [Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf).
The public source identities and checked bounds are listed below. The
local-only `source-cache/source-bounds.json` additionally records retrieval
and cache paths; it is excluded from Git.
The current Chapter 11 and Chapter 12 PDFs are specification pages only,
despite `withCommentary` in their filenames. A public 2024 Commentary source
for intermediate-angle end treatment was not located. The historical 2018
interpolation remains only a sensitivity in the existing
[method correction](../service-upper-frame-joint-review-2026-09-30/method-correction.md).

| Primary source | Checked provisions and printed pages | SHA-256 of local PDF |
| --- | --- | --- |
| 2024 Chapter 2, linked above | §§2.3.2.1–.3, Table 2.3.2; pp.12–13 | `6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100` |
| 2024 Chapter 11, September 11 version | §§11.1.2–.3, 11.2.2–.3, 11.3.1–.6; Tables 11.3.1/.3/.4; pp.70–76 | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| 2024 Chapter 12, September 11 version | §§12.1.2–.3, 12.3.4/.9.1, 12.5.1.1–.2/.2.2; Tables 12.5.1A/C/D; pp.96–99 for detailing | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| 2024 Appendix, September 11 version | Appendix E pp.174–175 (PDF pp.9–10); Table L8 p.195 (PDF p.30) | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |

## Adjustment scenarios

NDS-2024 §11.3.1 and Table 11.3.1 give the wood-controlled lateral value as
`Z' = Z CD CM Ct Cg CΔ Ceg` (with a toe-nail factor only for toe-nailed
connections). Section 11.2.3 does not apply wood factors to metal-part
resistance. The factors adjust capacity, not the source packet's per-bolt
actions. The controlling outer ratios are 1.1631 left and 1.3667 right.

| Conditional scenario | Stated factor assumptions; all unnamed factors held at 1 only for arithmetic | Multiplier | Left ratio | Right ratio |
| --- | --- | ---: | ---: | ---: |
| Dry, normal duration | `CD=1`, `CM=1`, `Ct=1` | 1.00 | 1.163 | 1.367 |
| Wet service | `CM=0.7`, `CD=1`, `Ct=1` | 0.70 | 1.662 | 1.952 |
| Ten-minute duration class | `CD=1.6`, `CM=Ct=1` | 1.60 | 0.727 | 0.854 |
| Wet service and ten-minute class | `CM=0.7`, `CD=1.6` | 1.12 | 1.038 | 1.220 |

These are not acceptance results. In particular, no `Cg` or `CΔ` value is
calculated into them; a further applicable reduction increases the ratios.
The reference `Z` itself uses unadopted `Fyb`, idealized contacting faces,
and a partial-thread scenario, so multiplying it by NDS factors does not
make it an adopted design value.

NDS-2024 §§2.3.2.1–.3 and Table 2.3.2 base `CD` on cumulative duration of
the maximum load and the shortest-duration load in a combination. Table
values include 0.9 permanent, 1.0 ten-year, 1.15 two-month, 1.25 seven-day,
1.6 ten-minute, and 2.0 impact; its note disallows factors above 1.6 for
connections. The upper packets' seven increments are response amplitudes,
not elapsed durations or a climber-event time history. No short-duration
factor is adopted, and `CD=2.0` is unavailable for these connections.

For lateral dowels, Table 11.3.3 gives `CM=1.0` for fabrication and service
moisture at or below 19%, `CM=0.7` when service moisture exceeds 19%, and
`CM=0.4` when fabricated wet but kept dry in service for `D≥1/4 in.` A
footnote exception to 0.4 is limited to a single fastener or specified rows
parallel to grain; the two-bolt pairs have different pitch/grain relations
in their two members, so the exception must be evaluated per member and
receiver. Actual moisture history is unknown. Under §11.3.4, `Ct=1` is
conditional on sustained temperature at or below 100°F; actual sustained
temperature is also unknown.

## Group factor and end/edge treatment

NDS-2024 §§11.3.6.1–.3 and Eq. 11.3-1 make `Cg` a resistance factor for
qualifying dowel rows. Section 11.3.6.2 defines a multi-fastener row as
same-diameter dowels aligned with the load; Eq. 11.3-1 needs row count,
diameter, pitch, and main/side member `E` and gross areas. For wood-to-wood,
the equation uses `γ=180,000 D^1.5`. It is not a per-bolt demand allocation.

Each top outer block has separate 33.0 mm-spaced side and rail pairs; these
are not one four-bolt group. For the top outer side pairs, the 21 same-state
records give the following projections when the pair resultant is declared
as the group load direction:

| Side pair | Angle between resultant and bolt-center line | 33.0 mm spacing along load | Transverse spacing |
| --- | ---: | ---: | ---: |
| Left | 78.26–89.00° | 0.575–6.716 mm | 32.309–32.995 mm |
| Right | 78.80–89.99° | 0.009–6.411 mm | 32.371–33.000 mm |

Under that declared direction, the two bolts are two single-fastener rows
(`n=1`, hence `Cg=1` for each), not a two-fastener loaded row. The staggered
row merger does not apply: transverse row separation is at least 32.3 mm,
while one-quarter of the greatest along-row offset is only 1.68 mm. This is a
positive `Cg` disposition for the singleton-row idealization, not a
calculation of group resistance. These projections use `R=f1+f2`,
`along=|s·Rhat|` and `transverse=sqrt(|s|²−along²)`, where `s` joins the two
bolt centers; the action-line spread is `acos(|f1·f2|/(|f1||f2|))`.

The extracted local actions also show why the resultant cannot stand in for
the complete pair action: within a same-state pair the bolt force vectors are
near-opposite, while their unoriented lines differ by 3.77–27.80° (left) and
0.88–27.26° (right); the bolt magnitudes also differ substantially. That is a
force couple, not equal sharing of the resultant. It prevents treating the
local actions as one common two-fastener row; it does not invalidate the
singleton `Cg=1` classification above. Preserve the individual actions and
check their complete force/moment transfer, local wood stresses, and
splitting separately. If a different group load direction or row grouping
is proposed, recompute its projections and bind that definition to the
receiver. The existing
[`nds_2024_group_action.py`](../../../../mini_moonboard/nds_2024_group_action.py)
is a caller-bound equation helper, not evidence for a different row.

For `D=1/4 in.`, the `D<1/4 in.` `CΔ=1` exception in §12.5.1.1 does not
apply. Section 12.5.1.2 requires the minimum applicable `CΔ` in a shear
plane to govern the connection. Tables 12.5.1A, C, and D provide
pure-direction end, edge, and row-spacing cases. At this diameter, the
softwood parallel-tension end reference is 3.5D minimum and 7D full
(22.225 and 44.45 mm). The modeled top outer side stations have at least
59.85 mm outer-box grain-end distance in the cleat and 66.0 mm in the host;
recorded outer-box loaded-edge distances exceed the pure-perpendicular 4D
comparison (25.4 mm). These screens omit nearer bores, seats, intersections,
and unobserved finished boundaries, and they do not themselves determine an
oblique-load `CΔ`.

Keep the angle definitions separate. Section 12.3.4 uses the member's
load-to-grain angle for bearing. Section 12.5.1.2(b) treats load angle to the
**fastener axis**. The modeled upper axes are perpendicular to conditional
grain (`a·g≈0`), and the lateral vectors are bolt-normal. The outer side-2
vectors are about 0–5° to grain in cleats and 85–90° in hosts, with
nonzero cross-grain components. Therefore §12.5.1.2(b) is not triggered by
the grain-angle obliquity. The specification's pure-direction tables do not
provide a verified 2024 intermediate-angle end or oblique-edge rule here.
Section 12.5.2.2's `Ceg` applies to a bolt axis parallel to grain/end grain;
the present modeled bolt axes are perpendicular to grain, conditionally
excluding that factor. Delivered orientation is not observed.

## Splitting and finished sections

NDS-2024 §11.1.2 requires applicable local member-stress checks, and §11.1.3
calls for appropriate engineering procedures or tests when eccentric
connection action induces tension perpendicular to grain. The distance
tables and parallel-grain Appendix E methods do not, by themselves, supply a
complete oblique receiver splitting check. No supported splitting method is
yet bound to each member, force/moment, and critical path in these packets.

Appendix E is a nonmandatory method for a single fastener or closely spaced
group loaded parallel to grain. E.2-1 uses adjusted `Ft'` and finished net
area; E.3-2/E.4-1 address the stated row/group tear-out paths. The parent
verified the matching arithmetic in
[`bolted_timber_checks.py`](../../../../mini_moonboard/bolted_timber_checks.py);
those base-property helpers do not qualify the oblique complete joint. See
[`local-stresses.md`](local-stresses.md) for the source-bound helper scope
and the 40 exact block-solid section samples. Their faces include modeled
bores, but the forces and moments have not been assigned among the
disconnected section regions, no continuous minimum between samples is
claimed, and host sections are not included. Summed section area with
uniform `Ft'` stress would add an unsupported load-share assumption.

Conditional arithmetic can use explicitly declared properties, moisture,
temperature, duration, dimensions, and section actions without claiming
those facts were observed. To adopt a criterion, still bind qualified bolt
`Fyb`; actual load duration/combination; moisture and sustained temperature;
the receiver's row direction, `E`, and gross areas if using `Cg`; each
member's signed load direction and finished boundaries for `CΔ`; the
critical finished section and its forces/moments; and a suitable splitting
method. An actual-build conclusion additionally needs observed cuts, holes,
member identity/orientation, and delivered dimensions. The missing whole-
frame demand cases and complete-joint acceptance remain open.
