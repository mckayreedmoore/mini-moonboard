# Current left outer-corner washer-seat screen

This bounded screen records the modeled outer washer-seat geometry for the
six current left-corner axes: BG001 `knee_outer_left_post_1/2`, BG003
`knee_outer_left_side_1/2`, and BG045
`knee_outer_left_inner_header_1/2`. It supplies geometry and a unit-action
average-pressure coefficient only. It does not assign a physical tie action,
qualify a washer or wood seat, or accept a connection.

The pinned reduced-property method derives each washer's annular plan area from
its saved CAD component volume divided by the measured per-axis thickness.
All six axes give `t = 1.651 mm` and `A = 222.726212 mm²` per outer washer.
For an ideal full-supported annulus with uniform average pressure,

```text
p_avg = T / A = 0.004489817 MPa per N of tie action
        = 4.489817 kPa per N = 0.651193 psi per N.
```

Thus each outer seat on a physical bolt would see the same axial tie action
`T` in a two-ended idealization; the coefficient is not a predicted load split
or local pressure field. The current reduced record does not include the
washer opening radius or the finished support polygon. The full annulus is
therefore conditional on the opening clearing the modeled 3.75 mm wood-bore
radius and the whole footprint bearing on sound, flat wood without other cuts,
gaps, or unsupported edge. A smaller actual contact area raises average
pressure. The saved gross member envelopes do not close those contact inputs.

The per-axis receiver pairs and seat coordinates are in
[`seat-screen.json`](seat-screen.json). BG003 axes each pass through three
receivers, but the represented axial action is **one physical tie from one
outer washer seat to the other**; the middle `base_side_left` receiver has no
independent axial washer-seat tie. The two header axes reverse the outer-seat
order because their modeled bolt directions reverse.

The repository's existing wood-annulus helper uses the 2024 NDS Supplement
Table 4A DF-L No. 2 `Fc⊥ = 625 psi` reference. At the modeled area this is
`959.777 N` per seat, as an unadjusted wood-bearing reference only, if the seat
is full-supported, sound DF-L No. 2 and loaded perpendicular to grain. The
limited current seats matching that material/orientation scenario are the
`base_post_outer_left` seats in BG001 and `base_header` seats in BG045. It is
not an adjusted design resistance or joint capacity. Candidate-block bearing
strength is not bound by its elastic-modulus scenario. In BG045 the
`knee_outer_left_inner_frame_block` seats load along the proposed grain `Z`,
so the `Fc⊥` reference is inapplicable there; no parallel-to-grain end-bearing
reference is introduced.

Hardware remains unresolved. The axis register lists K.L. Jack 25NWUS only as
a conditional lead at the post and inner-header axes; it lists no washer lead
for these two current side axes. The prior supplier evidence covered 16 side
and four outer-post axes, not the inner-header axes. None of these records
selects or documents delivered washers. The reviewed washer method packet
still has no applicable steel bending/load-spreading method or direct product
rating. This screen does not transfer the MIT clamped-annulus boundary or
infer steel resistance from dimensions, hardness, or bolt proof load.

Missing inputs for a physical seat check are the accepted signed tension at
each of the six bolts; selected and delivered washer product/lot dimensions,
opening, thickness and flatness; actual head/nut footprints; exact finished
wood support polygons, cuts, seat gaps and flatness; and applicable verified
wood bearing properties. Washer steel response/resistance also remains
unresolved. No load case demand or capacity is supplied here.

Reproduce and source-verify with the standard library:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/check_closure.py
```

The source-pinned `fea/wood_joint_reduced_properties.py` builder was also run
read-only with `uv run --no-sync`; it returned the same six areas, thicknesses,
two end points and (for BG003) three-receiver stacks. No native solve, CAD
regeneration, or mesh operation was performed.
