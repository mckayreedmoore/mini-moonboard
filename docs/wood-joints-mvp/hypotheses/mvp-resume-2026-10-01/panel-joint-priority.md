# Upper-panel screw joint: next unresolved load path

## Current finite result

The current coherent force reference is `two-receiver-frame-attempt03/`.
Its [792-record panel replay](panel-attachment/README.md) retains modeled-gap
peak withdrawal 1836.884 N with simultaneous lateral 807.662 N. The
[generic lateral/combined worksheet](panel-attachment/lateral-reference.md)
gives lateral references 386.752/463.413 N under explicit standard-screw
hypotheses. The most favorable modeled-gap combined index is2.724895,
K12-rear upper-right rim4, using that screw's V/T 1274.054/625.635 N.
Independent head and withdrawal deficits remain; no Hillman rating is assigned.

The separate [member replay](member-stability.md) finds top-rail face
shear/torsion 1.039209 against the declared 180 psi allowance. These specific
reference exceptions govern the next corrections; no geometry, material
factor or panel-hardware change is adopted. The owner's October 2 challenge
now puts [mounting-pattern fidelity](panel-attachment/official-pattern-comparison.md)
and the [force direction/load basis](panel-attachment/force-direction-and-load-basis.md)
before selection of a hardware correction. The source count is twelve screws
per main panel, but the upper vertical-row endpoints sit 65.95 mm below the
top-rail screw row, and the lower endpoints differ from the bottom-rail row
by 76.9 mm. This is not the same rectangular shared-corner layout described
by the owner. Its effect on compatible force sharing is not yet calculated.
The following six-joint sensitivity records remain preserved, with their own
force scopes.

The [panel-attachment worksheet](panel-attachment/README.md) now joins all
66 Hillman stations to the frozen six-joint frame: 792 screw states, signed
same-state lateral/withdrawal demands, generic thread/head references and
upper-panel statics. The current modeled-gap withdrawal peak is **1811.645 N**;
its simultaneous lateral force is **743.7 N**. Declared unadjusted head
references are **277–629 N**, and generic DF-L withdrawal references are
**711–1073 N** for the listed thread-penetration hypotheses. Neither the
generic equations nor the observed product listing supplies a Hillman rating.
The current force allocation does not meet those reference scenarios.

The parent retained all geometry, lateral screw laws and six selected
clearance joints while changing only the assumed withdrawal stiffness:

| Withdrawal stiffness, N/mm | Largest modeled-gap withdrawal | Same-screw opening | Complete twelve-state frame-law result |
| --- | ---: | ---: | --- |
| 2689.679, preserved baseline | 1812 N | 0.674 mm | Pass within declared laws |
| 1000 | 1240 N | 1.240 mm | Pass within declared laws |
| 100 | 916 N | 9.160 mm | Pass within declared laws |
| 90 | No complete envelope | Not established | STOP at K12-rear zero gap: positive spring domain exceeds 10 mm |

The two softer completed runs preserve their producer snapshots under
`panel-stiffness-attempt01-k1000/` and `panel-stiffness-attempt02-k100/`.
The zero-gap peaks are 1314 and 951 N; they are not omitted from the study.
Both completed softer scenarios still exceed the declared head references.
For the 100 N/mm scenario, the same-state combined wood-screw equation also
requires an unprovided lateral reference of at least 1876 N somewhere in
the modeled-gap envelope. No stiffness value or favorable duration factor
is selected to produce a pass.

A further finite trial used one-quarter of the source stiffness for both
withdrawal and lateral components, **672.419704 N/mm**. It stops at A12-forward
modeled gap on a normal active-set cycle. The seven earlier returned states
do not establish a twelve-state bound. Its source snapshot and STOP are
preserved in `panel-stiffness-attempt04-kquarter-both/`; this is a numerical
method stop, not an observed frame or screw failure.

Before selecting a correction, the parent is also including the saved bore
gaps at all **88 two-receiver candidate bolts**, rather than only six joint
groups. Their source relative gaps are 1.15 or 0.95 mm, with the corrected
top-side gap 1.0625 mm. Four continuous bolts retain their separate common-
bolt modeling requirement, and the twelve retained bolts retain zero-gap
laws. The first nominal-gap case satisfies balance, spring, floor and domain
gates but stops at force-bearing rigid rank **296/300**.
[The finite certificate](bounded-clearance.md) identifies bounded, nonunique
center-cleat translations in that case, with at most 1.134 mm conservative
additional movement. The rank/stability flags remain false; this does not
establish a unique pose or dynamic behavior.

The parent then completed `two-receiver-frame-attempt03/`: all six zero-gap
and all six nominal-gap states satisfy the declared force and finite laws.
Every nominal-gap state has a finite fixed-force seating certificate;
force-bearing rank is 296 or 297, explicitly reported separately from
boundedness. Original strict rank300 acceptance is not transferred. The
nominal withdrawal peak is **1836.884 N**, so including all these bolt gaps
does not cure the current head-reference deficit. The comparison SHA-256 is
`0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5`;
the response SHA-256 is
`774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52`.
Fresh same-state component replays now give top-corner ratios 0.7268/0.8138,
bottom-left 0.2819, lower-service 0.00704, central wood-pressure 0.1425,
end-grain 0.04648, continuous-knee conditional sum 0.9192 and remaining eligible
individual 0.9521. The corresponding elementary member normal/shear references
are 0.5746/0.3700. The corresponding member torsion/restraint replay finds
top-rail combined face shear/torsion 1.0392 against the declared 180 psi allowance,
with braced normal interaction 0.6144. That separate member exception is being
located; no strength factor or geometry change is adopted. The final header
replay now gives adjusted sensitivity 0.04692 and washer wood-pressure 0.2627;
the former six-joint worksheets and all complete-joint flags stay preserved.
Both earlier full-clearance terminal packets remain preserved.

## Preserved original necessity check

The [zero-withdrawal calculation](no-withdrawal-frame-checks.md) establishes
that face contact and in-plane screw action alone cannot balance either
upper panel in any recorded case. The representative A12-rear necessary
statics problem is infeasible. Its original largest individual screw demand
is **1922.134 N** at `round_panel_upper_left_edge_2`, from `main_upper_left`
into `base_rail_top`. This is a demand from unsupported parametric stiffness,
not a measured load or an accepted Hillman connection capacity.

The parent checked the source geometry's normal orientation. The upper panel's
source mesh node mean lies 78.978 mm outward of those of the ordinary rear frame members along
`(0, 0.766044443, -0.642787610)`. Face compression pushes the panel outward;
screw withdrawal restrains it inward. The downward component of the outward
normal makes panel and climber weight require inward restraint. Reversing
contact signs would therefore misrepresent this overhanging geometry.

## A simple reference shows the required evidence

The pinned 2024 NDS Chapter 12, §12.2.2.1–2, gives the side-grain cut/rolled
wood-screw reference `W = 2850 G²D` in lbf per inch of thread penetration.
For the existing conditional `G = 0.50` scenario and a hypothetical standard
No. 10 diameter `D = 0.190 in`, this gives:

| Explicit reference scenario, before end-use adjustments | Value |
| --- | ---: |
| Unit withdrawal reference | 135.375 lbf/in = 602.178 N/in |
| Reference with an optimistic entire 2.5-inch screw length in threaded wood | 1505.445 N |
| Original peak demand / entire-length reference | 1.2768 |
| Thread penetration needed at that unadjusted reference | 3.19197 in = 81.076 mm |
| Illustrative 1.5-inch thread penetration reference | 903.267 N |
| Original peak demand / illustrative 1.5-inch reference | 2.1280 |

The source connection record specifies a purchased nominal length of
63.5 mm, while its old 50.8 mm CAD occupancy is an analysis envelope.
Even the entire-length comparison exceeds the nominal purchased length
needed under this particular reference scenario; actual threaded wood
penetration also excludes the panel, unthreaded portions and tip.

**This is not a Hillman capacity, a physical upper bound or an adopted
resistance check.** Actual Hillman thread geometry, standard applicability,
root strength, panel head transfer, installation and all applicable adjustments
remain unresolved. The 1.5-inch comparison is illustrative, not a measured
thread interval. The generic reference demonstrates why assigning a unit
axial-to-lateral stiffness ratio does not resolve resistance. It does not
prove that a different supported product-specific resistance could not exist.

The exact equation comes from the preserved chapter PDF, SHA-256
`53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f`,
printed page 83; Table 12.2B, printed page 86, includes No. 10 and G = 0.50.
The source row identity and simultaneous demands are bound in the
[zero-withdrawal results](no-withdrawal-frame-results.json). The generic
calculation uses no product resistance or properties from SPAX or SDS.

## Next finite joint task

Propose the simplest panel correction within the owner's constraint decision,
then evaluate its six-case sharing and the top-rail demand together. Bind panel-to-receiver thread penetration
and a supported head/withdrawal basis for the purchased Hillman policy.
Standard No. 10 dimensions alone would not close the current numerical head
deficit. Any proposed correction must carry the same-state panel wrench and
identify required geometry/hardware changes before altering the reviewed model.
The 66-axis policy and all other owners' work remain preserved.

The parent's corner work remains useful conditional evidence, but a corner
pass cannot close this panel attachment. The upper-left service-joint agent
continues to own its separate joint. Physical release remains false.
