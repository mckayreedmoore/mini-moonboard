# Bottom-bolt adjustment and complete-action disposition

The calculation keeps all four bolts and 21 states per bolt. It retains the
separate axial ties, signed receiver actions, complete eight-action interface
wrenches, 21 complete cleat-boundary states and 252 contact-cell states from
the pinned upstream packets. It does not reinterpret a favorable resultant
as reduced bolt demand. Archived report bytes are authenticated; DAT tokens
and native responses are not reparsed by this producer.

## Service and material factors

The [pinned sources](source-note.md) identify the wood-controlled lateral
adjustments under NDS Table 11.3.1. This packet declares normal-duration ASD,
seasoned-dry fabrication and service at ≤19% moisture, sustained temperature
≤100°F and untreated timber. Under those conditional assumptions,
`CD=CM=Ct=1`. They are analysis inputs, not observed conditions. The seven
response amplitudes are not elapsed-time measurements or a duration basis.
No favorable duration factor is selected to dismiss the 1.0945 scenario.

For another service scenario, Chapter 11 Table 11.3.3 supplies wet-service
`CM=0.7`; wet fabrication followed by dry service gives `CM=0.4` at this
diameter unless its specified singleton/parallel-grain-row exception applies.
Table 11.3.4 depends on sustained temperature and moisture. The maximum
connection `CD` is 1.6. These alternatives are documented applicability,
not factors applied in the output. Fire-retardant treatment would need its
own §11.3.5 basis. Chapter 11 §11.2.3 does not apply wood adjustment factors
to direct steel resistance.

Both proposed receiver grains are transverse to each bolt axis in this
four-bolt cohort, so the end-grain factor is conditionally `Ceg=1`. This
does not adopt observed grain or the cleat's sawn-grade/material assignment.
The perpendicular/parallel bearing endpoints remain the original rounded
SG=0.50 scenario, with angles computed from the individual source vectors.

## Group, geometry and signed action

At exactly `D=1/4 in`, neither the `D<1/4 in` automatic `Cg` exception nor
the automatic `CΔ` exception applies. Chapter 11 §11.3.6.2 defines a
multi-fastener dowel row by fasteners “aligned with the direction of load.”
The two side axes and two rail axes are separate two-member shear planes
on a common cleat; they are not one continuous multiple-shear bolt. Their
33 mm pitch alone establishes neither a common loaded row nor a group.

The [placement packet](../bottom-outer-bolt-placement-2026-10-01/README.md)
retains all 84 complete interface wrenches. Every resultant is oblique to its
pair line beyond source rounding. Those interface boundaries omit the other
joint interfaces and body loads and cannot establish an adopted group from
the whole member. `Cg` therefore remains null. A declared future row needs
its actual load direction, stagger/merger check, main/side roles, `n`, `s`,
moduli and gross areas, including the perpendicular-grain equivalent area
rule. At quarter inch the equation's wood-to-wood `γ=22,500 lb/in` is a
known input, not a complete group factor or demand allocation.

The existing three-depth finished-ray screen has a minimum external edge
distance 27.9 mm. A two-axis-interface-only `4D=25.4 mm` envelope has
2.5 mm sampled margin; that screen neither qualifies a larger group nor
proves continuous-depth extrema or bore ligaments. The rail-cleat's minimum
43.35 mm end distance is below the softwood parallel-tension full-value
`7D=44.45 mm`. Its conditional ratio `43.35/44.45=0.97525309` applies only
if that group's complete load/category invokes the rule. It is not applied
to `side_1`. Its cleat ends are 59.85 mm away; its host's minimum sampled
finished end is 256.714903 mm. Oblique loaded-edge/category, row spacing,
neighboring perpendicular bores and complete local stresses stay separate.

The flagged bolt's A1 complete action is inclined to its axis because the
661.948743 N lateral resultant coexists with a 197.1248 N axial tie. NDS
§12.3.9.1 limits the lateral component to adjusted `Z′` and states
“Ample bearing area shall be provided.” Section 12.5.1.2(b)'s equivalent
shear-area geometry provision therefore remains live. Per-receiver angle
to grain and `Kθ` do not supply this bolt-axis check. `CΔ` and adjusted
reference resistance remain null. No contact compression is credited as
bolt capacity, and no washer annulus or catalog material fact closes the
axial load path, combined steel action or local splitting/tear-out.

## Useful arithmetic budget

All six modes are recalculated for each receiver-role assignment at both
45 and 106 ksi. Under the stated unity service factors, `side_1` requires
`Cg × CΔ≥0.7131364066` in the 106 ksi hypothesis to make this lateral-only
comparison no greater than one. This is a required multiplier, not an
assigned factor, adopted design value or permission to choose a favorable
group. The 45 ksi hypothesis requires a multiplier 1.0945088665.

Holding all adjustment factors at one, the Mode IV inverse arithmetic gives
`Fyb=53,907.734650 psi` at lateral equality. The producer checks that Mode IV
still governs all six modes there. This is a sensitivity threshold, not a
specified material minimum or a complete-joint remedy; a reduction factor
`c` would raise that Mode IV threshold by `1/c²`, subject to renewed mode
checks. A source-supported input must still be established independently.
No favorable quotient closes the 47-criterion development endpoint.
