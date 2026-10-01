# Bottom-outer bolt edge-distance method review

## Finding

For the modeled `D=1/4 in` scenario, Table 12.5.1C has two applicable
`ℓ/D` branches for the current two-member bolt planes: `ℓ/D=14` for the side
planes and `ℓ/D=6` for the rail planes. The value is the lesser of the length
in the wood main member and the total length in the wood side member(s),
divided by `D`; this is the table's footnote, not a value inferred from the
connector load. Equality at `ℓ/D=6` belongs to the `≤6` branch, so it does not
use the `>6` between-row term.

The exact 2024 NDS Table 12.5.1C rules are:

| Source plane / lesser `ℓ/D` | Parallel-to-grain loading | Perpendicular-to-grain loading |
| --- | --- | --- |
| Side plane / `14` | If `ℓ/D>6`, edge distance is `max(1.5D, S/2)`, where `S` is spacing between rows | Loaded edge `4D`; unloaded edge `1.5D` |
| Rail plane / `6` | If `ℓ/D≤6`, edge distance `1.5D` | Loaded edge `4D`; unloaded edge `1.5D` |

For `D=6.35 mm`, `1.5D=9.525 mm` and `4D=25.400 mm`. The side-plane
parallel case additionally depends on the actual between-row spacing `S`; do
not replace it with `1.5D` unless the applicable layout establishes that the
between-row term does not govern. The NDS specifies these branches directly;
there is no interpolation between `ℓ/D=6` and `ℓ/D=14`.

A geometry-only sufficient screen can be defined without adopting a strength
value: for the `ℓ/D=6` plane, require each candidate edge distance to be at
least `4D`; for the `ℓ/D=14` plane, require each candidate edge distance to
be at least `max(4D, S/2)` when a between-row spacing applies (or `4D` when
the layout establishes that it does not). Applying the larger threshold to
all potentially loaded and unloaded edges is conservative for the two
parallel/perpendicular edge categories in Table 12.5.1C. It does not require
choosing the loaded edge or interpolating for an oblique load. This is only a
sufficient **edge-placement** screen; it is not a complete NDS check or a
connection resistance.

For the explicitly limited two-axis interface-pair envelope, the source
center-to-center spacing is `33 mm`. Any putative between-row separation of
those same two centers is a projection of that vector, so `S≤33 mm` and
`S/2≤16.5 mm`. Since `16.5 mm < 4D=25.4 mm`, `4D` dominates the worst
Table 12.5.1C edge threshold for either `ℓ/D` branch **within that pair-only
scope**; this gives a numeric conservative screen of `25.4 mm` per relevant
edge for each two-axis interface. It does not establish that the two axes
form an NDS row or group, establish the actual edge clearances, or exclude
other axes from the complete cleat connection. The four cleat axes are two
orthogonal interface pairs; no group ownership or row-merging across them is
implied. If the complete NDS connection group includes other axes, its actual
between-row spacing and worst edge threshold must be determined for that
larger group before using this bound.

## Source basis and limits

The inspected official AWC 2024 Chapter 12 source is
`hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf`,
SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
Table 12.5.1C and its footnotes are on printed p. 99. Section 12.1.2.1
(printed p. 81) defines edge distance perpendicular to grain and defines the
loaded edge, for a member loaded perpendicular to grain, as the edge toward
which the fastener is acting. Section 12.5.1.3 (printed p. 98) applies the
edge-distance and between-row tables when `D≥1/4 in`; exactly one quarter
inch is included. Table 12.5.1C footnote 2 also cites NDS §§3.8.2 and 11.1.3
for heavy or medium concentrated loads suspended below a sawn-lumber or
glulam beam neutral axis; that separate tension-perpendicular-to-grain
restriction is not resolved here.

The pinned official AWC 2024 Chapter 11 extract is
`upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf`,
SHA-256 `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33`.
Sections 11.3.6.1–.3 (printed pp. 74–75) make group-action applicability
depend on a row aligned with load, define how staggered adjacent rows may be
merged, and require gross/equivalent member areas for `Cg`. Chapter 12
§12.1.2.4 (printed p. 81) also defines a row relative to load direction.
These group rules are distinct from Table 12.5.1C's edge thresholds.

The separate end-distance and geometry-factor rules are in Chapter 12
§§12.5.1.1–.2 and Table 12.5.1A (printed pp. 97–98). They address `CΔ`, not
the Table 12.5.1C edge-distance minimum. Section 12.5.1.2 applies at
`D≥1/4 in`; its group rule applies the smallest applicable `CΔ` to the
fasteners in the group and, for multiple-shear or asymmetric three-member
connections, across shear planes of the same connection. It does not turn an
edge-distance check into `CΔ`, nor establish that the side and rail bolt
pairs sharing a cleat are one NDS group.

There is an angle limitation. Table 12.5.1C gives parallel- and
perpendicular-to-grain categories; §12.1.2.1's loaded-edge direction is
explicitly framed for perpendicular-to-grain loading. A worst-category edge
screen as above can show the modeled centers clear both tabulated edge
thresholds, but it does not assign the actual direction category for an
oblique receiver load. Root's separate source-bound station/load-sign work
must identify the member edges, actual row orientation and between-row
spacing before reporting even that geometry result. No edge locations or
force signs are calculated in this note.

The whole bolt action also includes the separate axial outer-seat tie.
Chapter 12 §12.3.9.1 (printed p. 96) requires checking the component
perpendicular to the fastener axis against adjusted lateral `Z′` for the
specified two-member geometry and providing ample bearing area for the
parallel-axis component. For `D≥1/4 in`, §12.5.1.2(b) (printed p. 98) and
Figure 12E (printed p. 96) provide an equivalent shear-area geometry factor
for loading at an angle to the fastener. Neither is satisfied by an
edge-distance screen.
Likewise, Chapter 12 §§12.6.2–.3 and Chapter 11 §11.1.2 require appropriate
group distribution and local-stress evaluation for angled, multiple-fastener
connections. This note adopts no load direction, `Cg`, `CΔ`, property,
capacity or joint disposition.

The conditionally assigned diameter, bearing lengths, and proposed member
frames are analysis inputs, not delivered hardware or inspected timber. The
edge screen can be completed against root's source-bound locations without
choosing `Fyb`, adopting a resistance, or inferring acceptance from source
force fidelity.
