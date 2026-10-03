# Parent assessment of the bounded BG003 finite proxy

The eight declared A12-rear bolt-1 scenarios completed in 23.58 seconds under
one parent-held execution lock, the 180-second CPU/wall cap and 6 GiB memory
cap. No native solve was launched. All frozen source hashes remain unchanged.
The result is `PASS_BOUNDED_PROXY_ONLY`, with `joint_accepted=false`.

The model is one continuous two-plane elastic bolt with free physical ends
and three rigid timber receivers. It applies each source receiver lateral
force and first moment once. A rotated anisotropic foundation with a circular
radial gap couples the two planes. The two literature-density scenarios and
this constitutive law are hypotheses; they are not calibrated physical
properties, conservative bounds or adopted resistance.

At 32 divisions per receiver, signed internal actions on the left part of the
bolt at the middle cut are:

| Density hypothesis kg/m³ | Radial gap mm | (Vy,Vz) N | (My,Mz) N mm | Sampled peak couple N mm | Sampled resultant p/d MPa: spine / side / inner block |
| ---: | ---: | --- | --- | ---: | --- |
| 350 | 0.000 | (+65.564, -68.384) | (+2289.415, +1975.714) | 4466.123 | 8.412768 / 5.329345 / 0.902486 |
| 350 | 0.575 | (+30.974, -42.824) | (+1954.954, +1306.956) | 3571.507 | 14.629521 / 6.574137 / 3.191230 |
| 550 | 0.000 | (+56.022, -57.696) | (+1280.071, +1121.301) | 3605.994 | 8.770228 / 6.558410 / 1.041025 |
| 550 | 0.575 | (+23.846, -32.213) | (+1498.313, +1012.135) | 2892.969 | 18.587235 / 8.179061 / 4.138075 |

The four zero-gap models also pass independently assembled linear-model
oracles. All eight final states pass the declared free-degree equilibrium,
receiver force/first-moment closure, gauge-reaction and free-end gates.
Rejected continuation trials remain recorded; none supplies adopted forces.
Signed middle shear, signed middle couple and sampled peak couple change by
less than 0.276% from 16 to 32 divisions in all four paired scenarios. These
are the predeclared action-refinement checks, not a guarantee of continuous
pressure convergence.

A separate post-run comparison finds sampled inner-block pressure changes of
3.49% and 4.27% in the two clearance scenarios; the 550 kg/m³ side sample
changes by 1.05%. Thus the pressure samples have not met a 1% refinement
criterion. No such pressure gate was included in the run's declared PASS,
and no pressure-refinement pass is claimed. Peak p/d is a projected bore
bearing proxy, not a washer pressure or a member-wide compression check.
Do not compare it directly with Fc-perpendicular as though that were an
applicable embedment resistance.

Clearance lowers the sampled peak bending in both density scenarios but
raises sampled bearing pressure. It raises the middle bending magnitude in
the 550 kg/m³ scenario and lowers it in the 350 kg/m³ scenario. Neither
zero-gap nor clearance response therefore establishes a general upper bound.

This settles the bounded question of whether the combined grain/gap law can
produce a numerically compatible, nonzero-middle-action bolt response without
end restraints or double-applied source loads. It does not settle the physical
bearing law, calibrated stiffness/engagement, shared two-bolt receiver
compatibility, continuous pressure extrema, splitting/group behavior or
axial/thread/washer/steel interaction. A12-rear bolt 1 is the only loaded
source evaluated here; no pass transfers to bolt 2 or the other rear cases.
The same-state 95.96739 N axial tie remains outside this lateral model.

Evidence: [finite results](finite-proxy-results.json),
[parent assessment](parent-run-assessment.json),
[frozen inputs](parent-run-inputs.json), and
[adapter method](README.md). The result SHA-256 is
`ad3f95de06884b2a1f63d982fa67dfee8128a2fed0c77a20cedc0624fc1de3c5`.

Stop condition reached: the declared eight-case numerical proxy is complete.
Do not expand a parameter or mesh campaign to imply physical qualification.
The next local acceptance work needs an applicable bearing/combined-joint
method and explicit material/hardware assumptions; shared receiver behavior
must be addressed before assigning group capacity. BG045's separate 5.4 mm
conditional loaded-edge exception remains open. Reviewed geometry is unchanged.
