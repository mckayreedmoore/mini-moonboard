# Fabricated shoe steel resistance calculation

This calculation evaluates the frozen `steel_base_reinforcement.py` geometry:
two 9.525 mm A36 welded shoes, sixteen 9.525 mm nominal A307 bolts, and sixteen
32 × 32 × 6.35 mm A36 bearing plates. It consumes simultaneous connection
forces from `reinforced_frame_demand.py`; it does not transfer old ML24Z
ratings or assume that a rigid shoe has no prying deformation.

The current single external fillet is the decisive detail concern. Its large
direct-force resistance does not provide a comparable longitudinal bending
resistance. The finite-throat diagnostic and primary AISC discussion are in
[the weld calculation](reinforced-weld-capacity-review.md). A passing diagnostic
does not resolve the single-sided weld's root-rotation condition.

## Material and resistance basis

Required fabrication materials are A36 plate and E70 matching weld filler.
SSAB lists A36 minimum yield/tensile strengths of 36/58 ksi; ASTM A307 Grade A
provides 60 ksi minimum tensile strength. The latter is not a specified bolt
yield strength and does not establish an NDS dowel-bending value.
[SSAB A36](https://www.ssab.com/en-us/brands-and-products/commercial-steel/structural-steel/astm-a36),
[ASTM A307](https://store.astm.org/a0307-21.html).

The AISC 360-16 A307 row supplies nominal tension/shear stresses of 45/27 ksi.
Its long-grip note reduces both values by 4% for the actual 53.975 mm grip.
The calculation retains that conservative historical basis explicitly; the
current full specification could not be independently retrieved because the
publisher returned HTTP 403. It does not label the historical table a newly
verified current table. ASD uses gross bolt area and Ω = 2.
[AISC 360-16, Table J3.2](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_march-2021_linked.pdf).

For plate bearing, tearout, and gross/net section checks, the current AISC
design-value card supplies the ASD expressions. Hole-bearing deformation is
considered. No directional fillet-weld strength increase is taken. Net bolt-hole
sections include the additional 1/16-inch deduction.
[AISC 2022 basic design values](https://www.aisc.org/media/vlynv2sw/p325-23aw.pdf).

| Item | Conditional ASD value |
| --- | ---: |
| A307 bolt tension | 10.612 kN |
| A307 bolt single-plane shear | 6.367 kN |
| Square plate minimum-direction tearout | 15.912 kN |
| Square plate net-section shear rupture | 14.703 kN |
| Square plate net-section tension rupture | 24.505 kN |
| Square plate one-way elastic bending **screen** | 2.410 kN |
| E70 fillet direct-force **diagnostic** | 84.200 kN |
| E70 fillet longitudinal moment **diagnostic** | 59.538 N·m |

Bolt admissibility uses the conservative envelope
`(T + Q)/10,611.886 + V/6,367.132 <= 1`, with forces in N, nonnegative additional
prying `Q`, and total shear on one plane. The backing plate does not earn an
unsupported double-shear benefit. Positive receiver force opposite the bolt's
installation axis is tension; compression earns no tensile-resistance credit.

For plate thickness `t`, nominal bolt diameter `d`, and clear edge distance
`Lc`, the bearing/tearout screen is `V <= min(1.2*d*t*Fu, 0.6*Lc*t*Fu)`.
The square plate's nearest center-to-edge distance is 16 mm. The shoe's
minimum in-plane center-to-edge distance is 25 mm. Both use the actual
11.1125 mm clearance hole.

## What the force calculations actually check

1. Every one of the sixteen bolt records must exist at its frozen flange/wood
   interface. Missing values are rejected rather than set to zero. Tension,
   transverse shear, remaining prying allowance, plate bearing/tearout, and
   square-plate bending are reported for each bolt.
2. The web free body contains the four rim-bolt actions, evaluated about the
   actual weld-throat centroid. Timber seat reactions act on the foot and
   therefore cannot be credited across the web-to-foot weld. The three forces
   and three moments feed the finite-throat weld diagnostic.
3. Web section recovery checks the gross root and more than 200 horizontal
   cuts, including the actual LED opening and bolt-hole net deductions. It
   includes axial force, two bending moments, direct shear, and an upper bound
   on Saint-Venant torsional shear. Perforated strips share twist. This remains
   an elastic beam-section approximation; local bolt-zone stress, buckling,
   and restrained warping are not hidden inside a blanket pass.
4. The foot calculation solves an optimistic equilibrium program with four
   downward bolt tensions and four nonnegative compression contacts over the
   actual foot/header overlap. It retains the external six-component wrench
   and actual header shear. It minimizes the maximum bolt interaction while
   enforcing plastic bending limits at four foot cuts. If this best-case
   problem fails, the specified limits cannot carry the wrench. Success is
   only a necessary-condition result: arbitrary point compression and omitted
   displacement compatibility make it too favorable to establish actual prying.

The rectangular torsion constant uses the Saint-Venant odd-term series;
the omitted tail is bounded conservatively. The shear bound is `|M|*b/J` for
the short rectangle dimension `b`, summed with direct shear before the
von Mises screen. The rectangle solution assumes free warping.
[Original rectangular-torsion research](https://link.springer.com/article/10.1186/s10033-018-0214-9).

The square bearing plate screen sends its entire axial force through one
32 mm simply supported net-width strip. Its central-load bending capacity is
`4*(Fy/1.67)*(32-12.7)*t²/(6*32)`. This is an explicit one-way bending model,
not a solved two-dimensional wood-contact distribution. Reported average wood
pressure uses 927.013 mm², excluding the hole; timber bearing resistance is
checked separately. Ordinary round washers are not assigned the square plate's
larger bearing area.

## Initial diagnostic and concrete repair direction

The first evaluated native response, `/tmp/reinforced-F10-k1000-v2/report.json`,
did **not** converge its contact active set. Its forces are invalid for design
acceptance. They are useful only for identifying the scale and direction of a
potential failure: maximum bolt interaction was 0.09082, square-plate bending
screen 0.06185, and single-fillet weld diagnostic 1.03736 on the right shoe.
The right web delivered 60.364 N·m about the weld's longitudinal axis. The
left weld diagnostic was 0.44633. The foot's optimistic equilibrium program was
feasible. These values do not establish accepted actual loads or a safety factor.

The subsequent F10 / 1,000 N/mm response converged in native cycle 13 and
passed its equilibrium and MPC checks. Its source-bound steel result is
[reinforced-steel-F10-k1000-v4.json](../fea/results/reinforced-steel-F10-k1000-v4.json).
The earlier v3 consumer result is retained; r2 adds the explicit necessary
floor-friction gate and an in-plane equilibrium guard for the foot program.

| Converged conditional case | Maximum ratio/result |
| --- | ---: |
| Bolt tension/shear envelope | 0.09148 |
| Square-plate one-way bending screen | 0.06071 |
| Web elastic section screen, including holes and torsion | 0.28001 |
| Left single-fillet six-component diagnostic | 0.46545 |
| Right single-fillet six-component diagnostic | **1.02799** |
| Optimistic foot equilibrium minimum bolt utilization | 0.01176 |

The right weld receives `[384.548, −308.960, 138.775] N` and
`[10.369, 59.886, −63.628] N·m` about its actual throat centroid. The current
single-fillet diagnostic therefore fails this converged conditional response.
The producer still marks actual joint demands unqualified: its rigid-connector,
isotropic timber and sticking-floor assumptions are not physical qualification.
In particular, the actual whole-foot reaction sums require friction coefficients
0.89302 and 0.76698 at the two center posts, inconsistent with the considered
0.2/0.4 scenarios. The legs require 0.27365 and 0.27552. These are necessary
force-only lower bounds. The separate larger 2.176/3.318 polygon-allocation
values include yaw and are sufficient certificates, not necessary coefficients;
they should not be used to overstate the minimum required friction.
This case must not be presented as an accepted operating-load envelope merely
because numerical contact iteration converged.

If converged response envelopes remain comparable, the finite fabrication
revision is a continuous full-thickness CJP tee-groove weld between the same
9.525 mm A36 web and foot, using matching E70 filler. Weld the empty shoe
before timber assembly, with an actual AWS D1.1 qualified or applicable
prequalified joint procedure and required inspection. Prepare and complete the
root under that procedure; finish any timber-side reinforcement flush to
preserve the seat. The external triangular fillet CAD volume must be removed
if this revision is adopted. No permanent backing may occupy the wood seat.

This changes the physical root detail, rather than merely increasing a fillet
leg. The gross web's elastic first-yield longitudinal moment scale is
308.048 N·m, approximately 5.17 times the current finite-throat diagnostic.
That scalar comparison is not the combined-stress check: the actual CJP detail
must be assessed using the complete wrench, adjacent plate strength, contact,
and any required fatigue provisions. The current CAD remains the single-fillet
candidate until explicitly revised.

Separately, the current header rows are 130 mm apart across grain. The timber
review identifies the 127 mm NDS limit. Moving the rear row from Y = −210 to
−206 mm gives 126 mm nominal spacing and 1 mm fabrication margin without
interacting with the CJP joint. This recommendation does not silently change
the frozen geometry or its source hashes.

## Reproduction and acceptance boundaries

Run `uv run python -m fea.reinforced_steel_capacity --demands INPUT.json
--output NEW_OUTPUT.json`. Omitting `--demands` produces material/capacity
constants only. The writer refuses to overwrite evidence and hashes sources
before and after the calculation. Producer equilibrium, MPC, and contact
convergence flags are retained. An unconverged or incomplete response is
explicitly labeled `INVALID_RESPONSE_DIAGNOSTIC_ONLY`.

The output's overall `qualified` flag remains false: this script alone cannot
qualify material procurement, a weld procedure, timber connections, fatigue,
or contact compatibility. Its purpose is to perform the stated strength
calculations and expose exact demands, failures, and repair requirements.

## Completed harder-joint comparison

The [10,000 N/mm case](../fea/results/reinforced-steel-F10-k10000-v5.json)
also converges, but fails the physical μ=0.4 floor assumption. Its maximum
steel bolt interaction is 0.109, square bearing-plate bending screen 0.212,
and right-weld elastic diagnostic 0.739. The baseline right-weld diagnostic
is 1.028. This sensitivity confirms that a passing isolated force or weld
comparison cannot close the unverified system load path or single-sided
root-rotation detail. The CJP detail remains a proposed structural revision,
not an installed or qualified replacement.
