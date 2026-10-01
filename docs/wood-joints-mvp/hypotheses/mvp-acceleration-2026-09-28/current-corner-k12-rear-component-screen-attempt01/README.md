# K12-rear conditional corner component screen

This packet applies the reviewed single-bolt BG001 and BG045 component
methods to the authenticated, full-factor-one K12-rear response. It also
retains BG003's signed three-member plane actions, six positive tie demands,
and twelve washer-seat pressure conversions. It does not calculate a
BG003 resistance ratio, a group or mixed-action capacity, or complete-joint
acceptance.

The source demand report is
[`corner-demand-report.json`](../current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json),
SHA-256 `a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0`.
Its parent terminal assessment records
`PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50`; the direct response reached
load factor 1.0 at all seven increments. Parent audits independently passed
the all-50-body sums and compared all 2,366 exported interface owner, point,
force, radius, and floor-sum rows against the source response. The model,
deck, and DAT hashes, plus the response, terminal, audit, freeze, and row-audit
hashes, are recorded in `screen.json`. Those gates establish conditional
numerical demands for this one case, not mechanical acceptance.

At full load, the largest BG001 individual resultant is 68.77 N at
`knee_outer_left_post_2`; the displayed ratio is 0.1244 against its conditional
Mode IV reference after the group minimum `Cdelta=0.9631`. The minimum factor
is controlled by that axis at the 0.2 increment. The largest BG045 individual
resultant is 74.09 N at `knee_outer_left_inner_header_1`, or 0.1845 against a
401.63 N Mode IV reference after `Ceg=0.67` is applied once. The second BG045
axis is 15.62 N, or 0.0391 against 399.67 N. These are individual component
comparisons, not design DCRs or group capacities.

BG003 remains the governing method gap. At full load, its first outer plane
actions are 64.93 N and 5.55 N, with a 41.29-degree vector difference; the
second pair is 59.45 N and 4.55 N, with a 162.97-degree difference. The
existing double-shear references assume equal, same-direction outer actions,
so neither reference nor plane capacities are combined for these unequal,
non-collinear actions.

The largest modeled washer-seat pressure conversion is 0.4456 MPa at
`knee_outer_left_side_1` on the spine at full load. It divides positive tie
tension by the source-modeled annulus area and is not a pressure distribution
or qualification. The only `Fc_perp` comparisons retained are at the existing
transverse-grain base-post and base-header seats; the candidate-block seats
receive no invented `Fc_perp` basis. In particular, BG045 axis 2 preserves
the physical tie convention: the first owner, inner block, receives
`[0, 0, -15.13464] N`; the second owner, header, receives
`[0, 0, +15.13464] N`. The positive scalar is tie tension.

The signed directions and conditional ratios are compared with the existing
A12-rear and A1-rear reports in `screen.json`; those are separate source cases
and their peaks are not pooled. K12 BG045 axis 1's block action has a small
`+Y` component at a source-envelope face 20.0 mm away, below the conditional
4D comparator (25.4 mm), while its rectangular force ray reaches the `+X`
face at 44.45 mm. K12 axis 2's header action has a `-Y` component at a
20.0 mm face, also below that comparator. Component-face distances and
rectangular rays remain separately labeled conditional geometry screens;
they do not define a universal loaded-edge rule for oblique actions or an
adopted joint pass/fail. Actual finished cuts, delivered wood and hardware,
splitting, net section, and full-joint load transfer remain unresolved.

Reproduce and verify the pinned calculation with:

```sh
uv run --no-sync python screen.py --write
uv run --no-sync python screen.py --verify
```

The producer rechecks the pinned method and input hashes, A12/A1 known-answer
reproductions, K12 response gates, parent terminal status, and parent export
row audit. It launches no native solve and changes no geometry.
