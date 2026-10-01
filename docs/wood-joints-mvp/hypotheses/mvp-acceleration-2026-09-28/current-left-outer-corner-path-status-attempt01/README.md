# Left outer corner path status — attempt01

**Status:** one source-bound conditional response now traces the modeled left
outer path from post through header, but no complete joint resistance or
acceptance exists. The only usable result in the reviewed packets is
`a12-rear` at load factor 1.0; it is one case, not a six-case envelope.

## Path and inventory boundary

The modeled load path is:

```text
base_post_outer_left
  -- BG001 (two new axes) --> knee_outer_left_spine
  -- BG003 plane 37/39 --> base_side_left
  -- BG003 plane 38/40 --> knee_outer_left_inner_frame_block
  -- BG045 (two new axes) --> base_header
```

The parent corner contract lists 92 **new block/candidate axes** and
separately lists 12 preserved original LEG/FLOOR-RUNNER axes. BG001, BG003,
and BG045 below are six members of the new-axis lane; none of the 12 original
axes is included as a substitute or credited capacity.

| Group | New axis IDs | Lateral interfaces | Outer-seat tie actions |
| --- | --- | ---: | ---: |
| BG001: post ↔ spine | `knee_outer_left_post_1/2` | 2 | 2 |
| BG003: spine ↔ side ↔ inner block | `knee_outer_left_side_1/2` | 4 | 2 |
| BG045: inner block ↔ header | `knee_outer_left_inner_header_1/2` | 2 | 2 |
| **Total for this path** | **6 of 92 new axes** | **8** | **6** |

The source contract separately calls for all concurrent plane forces and
outer-seat actions, signed member/group wrenches at recorded datums, contact
normal actions and areas, and closing each member force/moment balance. The
accepted a12-rear export supplies these for this one modeled response.

## Conditional a12-rear results

The demand report is bound to the current candidate geometry revision and
`a12-rear` model/response. It has seven accepted increments, uses the final
full-load factor 1.0 here, and passes the recorded MPC, spring-law, retained
bilateral, selected-floor, five-corner-body, and raw/interval body/global
balance gates. This establishes numerical transfer for the reported model
and support branch; it does not establish physical fit or resistance.

| Connection | Current final-load action on receiver(s) | Existing conditional comparison |
| --- | --- | --- |
| BG001 post bolt 1 | Base post `(0, 151.250, 260.999)` N; resultant 301.657 N; tie 64.966 N | Separate Y/Z ratios to the existing unadjusted single-bolt references: 0.2664 / 0.3278. |
| BG001 post bolt 2 | Base post `(0, −213.222, 258.461)` N; resultant 335.061 N; tie 18.473 N | Separate Y/Z ratios: 0.3755 / 0.3246. |
| BG003 side bolt 1 | Spine plane `(0, −292.424, 385.608)` N = 483.948 N; inner-block plane `(0, 0.918, 65.907)` N = 65.913 N; tie 95.967 N | Plane resultant ratio 7.342; directions differ 37.973°. Conditional outer-member Mode Is component ratios are 0.2754 and 0.0313 only. |
| BG003 side bolt 2 | Spine plane `(0, 230.451, −64.212)` N = 239.230 N; inner-block plane `(0, −20.715, 84.481)` N = 86.983 N; tie 43.508 N | Plane resultant ratio 2.750; directions differ 119.347°. Conditional outer-member Mode Is component ratios are 0.1533 and 0.0434 only. |
| BG045 header bolt 1 | Base header `(-89.016, −14.035, 0)` N; resultant 90.116 N; tie 119.343 N | Separate X/Y ratios to prior Ceg-only directional references: 0.2216 / 0.03689. |
| BG045 header bolt 2 | Base header `(-24.272, −5.761, 0)` N; resultant 24.946 N; tie 19.882 N | Separate X/Y ratios: 0.06043 / 0.01514. |

Vectors and full precision are in the linked source JSON files. BG001 and
BG045 component ratios do not include a mixed-axis interaction, two-bolt
group capacity, or bolt tension. The BG003 symmetric double-shear references
are inapplicable to its observed unequal/non-collinear plane actions; the
four Mode Is values are separate necessary outer-member component screens,
not a full three-member capacity. No two-plane or two-bolt capacities are
summed.

All six axial tie magnitudes are positive. Across the 12 modeled washer seats,
the conditional full-annulus area is 222.726 mm² and uniform-average pressure
is 0.08294–0.53583 MPa. Only the two base-post seats and two base-header seats
have conditional DF-L No. 2 `Fc⊥` component references (ratios 0.06769,
0.01925, 0.12434, 0.02071). The other eight spine/block seats have no sourced
block bearing reference. These are not washer-seat checks: installed washer
product, support area, pressure distribution, actual wood and washer bending
remain unresolved.

## Minimum remaining dependencies

1. **A demand envelope:** a source-bound accepted response and the same eight
   lateral planes, six tie actions, contact actions, recorded-point wrenches,
   and body/global balance for every remaining authenticated load case. The
   a12-rear export alone does not establish a governing case. The latest
   a12-left swapped-floor run is terminal, return zero in 49.77 seconds;
   both original and source-supported zero-U representation audits reject
   inactive SPR1302. Its corner demands remain withheld. See its exact
   `parent-terminal-assessment.json`; a12-rear remains the sole usable case.
2. **Physical/analytical compatibility for these six new axes:** verified
   stack order, side/member bearing lengths normal to each action, contact and
   hole/bolt fit, actual material grain direction, and washer/nut seat geometry
   must agree with the source-bound model. The current response demonstrates
   equilibrium only for its modeled zero-gap/contact and selected no-slip
   floor-support branch.
3. **Complete connector resistance:** actual bolt product, nominal/root/shank
   diameters, thread intervals at both BG003 shear planes, ASTM-supported
   `Fyb`, wood species/grade/condition/grain, and NDS spacing/end/edge inputs;
   then applicable adjustments and group effects. BG001 and BG045 currently
   have only separate directional single-bolt components, not multi-axis or
   two-bolt resistance. BG003 additionally needs a source-supported method for
   this continuous three-member bolt under unequal, non-collinear shear-plane
   actions and the resulting coupled middle-member/dowel force and moment;
   the symmetric NDS route and independent plane-capacity sum do not resolve
   it.
4. **Wood and seat failure modes:** signed internal cut/member actions at the
   critical section locations, with a supported splitting/net-tension,
   row/group shear, tear-out and bearing method plus actual design values.
   Existing section geometry has void areas and uniform-stress coefficients,
   but not those signed section actions or resistances. Whole-body equilibrium
   is not a substitute. Separately resolve the six tie forces against bolt
   tensile and lateral/tension interaction and the 12 actual washer seats.

These are the minimum dependencies to turn this one-case force transfer into
a complete conditional corner check. No fabrication, climbing, or physical
inspection status is changed by this report.

## Source pins

- Parent demand contract: `current-corner-demand-contract-attempt01/contract.json`,
  SHA-256 `f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74`.
- Accepted conditional demand export: `current-corner-native-demand-export-attempt03/corner-demand-report.json`,
  SHA-256 `812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`.
  It binds response SHA-256 `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274`,
  model SHA-256 `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8`,
  and source case manifest SHA-256 `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`.
- Reused conditional comparison: `current-corner-a12-conditional-resistance-screen-attempt01/screen.json`,
  SHA-256 `ee247af7e2271e63dcf1f8d8b86ef5eeca203f3dec3e37c55f2f6a8addb1e5cb`.
- Reused BG003 applicability screen: `current-bg003-unequal-action-applicability-attempt01/screen.json`,
  SHA-256 `d87f20ca167f0418388dba5afe4ff0b08fbfbcdf60885477775a5ea756049790`.

The inventory contract's `actual_case_demands_available=false` and
`complete_joint_validated=false` are pre-export, scope-setting flags. The later
conditional report supplies actual forces for one case; it does not change
the contract's no-complete-joint-validation boundary.


### Current actual-direction single-bolt lateral references

The [resultant-direction packet](../current-corner-resultant-direction-single-shear-attempt01/README.md)
now evaluates the actual a12-rear lateral direction for both connected
members at each BG001 and BG045 bolt. It replaces the need to infer a
lateral comparison by combining separate coordinate components. Under the
existing smooth full-body quarter-inch, Fyb 45,000 psi, zero-gap, proposed
grain and Fe 5,600/4,450 psi endpoint scenarios, all six yield modes are
retained and Mode IV governs all four bolts. BG001 ratios are 0.42363 and
0.49082 against 712.070 and 682.661 N references. BG045 ratios are 0.22468
and 0.06230 against 401.080 and 400.416 N after the existing conditional
Ceg=0.67 once. They remain individual-bolt lateral reference comparisons,
not adjusted design DCRs, group/axial interaction checks or complete-joint
passes. BG003 remains a coupled unequal, non-collinear three-member problem.

Parent independently recomputed force norms, proposed grain angles,
Hankinson Fe interpolation, reduction angle and Mode IV arithmetic without
importing the yield helpers. The parent audit binds final screen SHA-256
`d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10`.
The producer replay and its final checksum manifest pass. All four actual
axial tie vectors/magnitudes remain separate; no missing field is defaulted
to zero. Twelve original LEG/FLOOR-RUNNER arrangements remain out of scope.
