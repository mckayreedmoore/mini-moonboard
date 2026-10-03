# Current retained frame-bolt load paths

This packet rechecks the twelve retained starting frame-bolt arrangements in
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. It joins current finished receiver
geometry to signed simultaneous A1-rear, A12-rear and K12-rear forces at factors
0.1, 0.2, 0.3, 0.45, 0.675, 0.925 and 1.0. It establishes no resistance or joint
acceptance. The 92 candidate bolts remain a separate group.

The reproducible report contains 12 current axes, 24 receiver memberships,
252 bolt states, 504 combined receiver wrenches, 504 retained interface actions
and 168 complete receiver-body states. Each case's complete eight-body boundary
contains 568 interfaces and 720 scalar channels, including candidate bolts,
panel screws, timber contact and floor actions. This covers every modeled port
touching these bodies, rather than treating the retained bolts as their only
load path. It does not qualify every local failure mode.

The force table below is a locator into the report. Each row gives that axis's
largest lateral magnitude among the 21 states and the axial tie **from the same
state**. Rows are separate extrema, not a simultaneous assembly load scenario.
Full signed first/second vectors, source-token rounding radii, scalar provenance,
physical interface points and both receiver wrenches remain in the report.

| Retained axis | Case at lateral maximum | Factor | Lateral N | Simultaneous tie N |
| --- | --- | ---: | ---: | ---: |
| lumber_leg_bolt_left_1 | a12-rear | 1 | 1183.331812 | 262.706800 |
| lumber_leg_bolt_left_2 | a12-rear | 1 | 1723.082062 | 529.439400 |
| lumber_leg_bolt_right_1 | k12-rear | 1 | 1169.766183 | 301.750300 |
| lumber_leg_bolt_right_2 | k12-rear | 1 | 1695.336452 | 611.771100 |
| rail_front_bolt_left_1 | a1-rear | 1 | 152.693441 | 19.926730 |
| rail_front_bolt_left_2 | a12-rear | 1 | 405.959901 | 63.817350 |
| rail_front_bolt_right_1 | k12-rear | 1 | 29.216337 | 26.283270 |
| rail_front_bolt_right_2 | k12-rear | 1 | 393.404219 | 62.512240 |
| rail_rear_bolt_left_1 | a12-rear | 1 | 40.122415 | 11.550010 |
| rail_rear_bolt_left_2 | a12-rear | 1 | 86.156487 | 14.920780 |
| rail_rear_bolt_right_1 | k12-rear | 1 | 33.612550 | 16.255290 |
| rail_rear_bolt_right_2 | k12-rear | 1 | 81.152243 | 14.410380 |

The leg/side receiver pair has two half-inch modeled axes per side. The front
post/floor and rear floor/leg pairs each have two three-eighth-inch modeled axes
per side. These are source geometry envelopes and hardware-policy records;
they do not establish delivered shank, purchased length, bit size or capacity.

`produce.py` binds each lateral interface to the common end of the two current
finished bore intervals, and each axial tie to their two exterior interval ends.
All twelve maps and 24 memberships resolve. Missing or duplicate axes,
receivers, projection rows, owners, source bytes or required gates refuse the
join. The report pins the finished STEP bytes and geometry/source/helper inputs;
it does not run CAD or inspect physical parts.

Body moments use the exact authenticated all-body audit references. The sloped
leg references differ from their descriptor midpoints, which are kept as
separate geometry datums. Neither datum is called a mass centroid. The source
body checks retain 0.1 N and 2 Nmm at their original references. Origin moments
are equivalent transported actions, with radii independently reconstructed
using origin lever arms; no invariant 2 Nmm origin gate is asserted. Arithmetic
matches use 1e-8 N and 1e-6 Nmm, not relaxed physical gates.

External loads come from `physical_body_loads` before support elimination.
Selected floor tangent reactions and explicitly released zero actions stay
distinct. Numerical SPRINGA grounds are excluded from physical owners and
balances. The unverified no-slip floor assumption remains conditional.

Transported moments describe point-force actions about a reference. They are
not recovered internal bolt bending. Complete joint resistance, local wood and
steel stresses, washer/seat behavior, engagement and stiffness sensitivity,
delivered hardware compatibility and the remaining load-case envelope remain
outside this packet. No preserved-candidate pass, historical demand or capacity
is transferred. All acceptance and fabrication-release flags remain false.

See [source-plan.md](source-plan.md) for the duplicate audit and source lineage,
[validation.md](validation.md) for checks and hashes, and the independent
[raw oracle](raw_oracle.py) for the DAT-token sign and moment checks. The primary
owns integration; this packet changes no shared ledger, CAD, native input,
candidate selection or shop instruction.
