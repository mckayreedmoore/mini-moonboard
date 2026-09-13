# Current DIY completion record

This record defines the agreed endpoint for the `no-shoes-development` project:
a documented **engineer-unreviewed DIY design**. The owner has explicitly removed
independent engineering review as a completion requirement. This package does
not claim professional certification, a verified climber weight rating, or
inspection of a physical assembly.

The purpose of this record is to keep the remaining work finite. Completing a
calculation, passing a software test, and satisfying a structural comparison are
different outcomes. The status below distinguishes them instead of describing
all three as “testing complete.”

## Settled scope and assumptions

| Item | Agreed basis |
| --- | --- |
| Current geometry | Shoe-free frame with a 277 mm floor-to-main-face datum: 150 mm exposed kicker plus a 127 mm (5-inch) pad covering the entire lower front section across the full board width. Timber feet bear on the floor; the pad provides no structural support. |
| Main design task | Resolve the single-2×6 rear support legs and their integral connections, using the assembled-frame response to establish their demands. Preserve the baseline and identify any selected revision explicitly. |
| Panels and holds | Retain the accepted plywood, panel layout and T-nut construction. Neither a general plywood/T-nut test campaign nor comparison with another frame is a completion prerequisite. This owner decision is a design premise, not evidence that Moon has tested this particular frame. |
| Floor | Assume the timber feet do not slide. Permit compression contact and uplift in the calculation. Physical floor-friction qualification is excluded; the assumption does not establish friction or imply an installed anchor. |
| Timber | Use the documented dry, unincised Douglas Fir–Larch No. 2 basis and actual nominal-member geometry. Published grade values do not establish the species, grade or condition of subsequently purchased stock. |
| Load inquiry | Retain the existing 250 lb one-climber target and 150 lb comparison. Treat static downward loading and twice-downward-force loading separately, with the documented horizontal cases up to 300 N and eccentricity up to 100 mm. |
| Load interpretation | The doubled downward force and horizontal force are project scenarios, not a measured impact spectrum. They do not establish a safe body-weight limit or encompass every climbing action. |
| Resistance factors | The published climbing-case comparisons use normal-duration factors of 1.0. No additional short-duration capacity increase is credited merely because the downward load is doubled. |
| Weight and equipment | The current response uses 171.039 kg modeled assembly mass plus a separate 25 kg equipment allowance. A geometry or hardware revision must update its weight or justify the retained value. Equipment placement differs between the response case and the separate equilibrium envelope and must remain labeled. |
| External review and testing | Independent engineer review is not a gate. No physical load test is added automatically. If a consequential joint assumption cannot be resolved by published evidence or calculation, report the unresolved limitation explicitly rather than inventing a passing result. |

Other pad heights require the coordinated changes described in the
[construction package](current-construction-package.md#adapting-to-a-different-pad-height):
main-face height equals pad height plus 150 mm, with revised kicker, posts, leg
lengths, datums and affected checks. Changing only the pad leaves an exposed
kicker of 277 mm minus the new pad height.

These choices preserve the owner's scope without converting a leg-focused
assessment into qualification of every part of the frame.

## Evidence already available

The [assembled-frame response report](current-frame-response.md) contains nine
calculated cases: six distinct loading situations and additional numerical
comparisons. The model includes member deformation, individual connections,
bearing, panel seating and uplift-capable feet. Its numerical checks address
force and moment balance, contact, interpolation, selected-case mesh refinement
and material implementation. The dependency refactor produced a byte-identical
initial input deck, as recorded there. These are checks of the implemented
calculation, not acceptance of every physical design detail.

The [whole-body equilibrium report](current-frame-equilibrium.md) covers a much
larger load-location and horizontal-direction envelope. A feasible support
resultant does not itself establish internal-force coverage, actual contact
pressure, or a specified overturning safety factor.

The current four-bolt leg connection has a **calculated shortfall under the
stated response and resistance assumptions**. At A12 with twice the downward
force of 150 lb and 300 N rearward, the refined result gives approximately
1,816 N at the governing bolt against a conditional 917 N reference, a ratio
of 1.981. The connection also transfers approximately 0.220 kN·m about the
global X axis. Its gross-section leg comparison is 0.462 in that case. Thus
the connection, rather than that evaluated leg section, is the immediate
design problem. This is not a predicted collapse load.

The [independent mechanism audit](current-leg-response-audit.md) reproduces
the joint moment from the leg/floor free body. The
[replacement screen](current-leg-revision-screen.md) records bounded alternative
layouts against saved resultants; no alternative is selected or qualified by
that screen. The current joint decision therefore remains unresolved.

The [resistance assumption audit](current-response-resistance-basis.md) explains
why the nominal bolt-diameter comparison is conditional and why increasing
steel grade alone does not resolve its governing yield mode. The response
report also records stiffness sensitivity; its tested half/double values are
engineering variations, not measured upper and lower bounds for the installed
joint.

Other response comparisons remain disclosed without reopening the accepted
panel scope. Concentrated panel-screw comparisons depend on the modeled load
transfer and conservative resistance references; they do not demonstrate that
the plywood or T-nuts require replacement. Base-angle separation and flange
moments have limited direct catalog applicability. The 250 lb doubled-load
case has a conditional outer-rim gross-section ratio of 1.271. These facts
limit whole-frame claims even if a subsequent leg revision passes its own
checks. Preserve them in the evidence rather than silently deleting them or
calling them measured failures.

## Finite completion checklist

| Deliverable | Completion evidence | Current disposition |
| --- | --- | --- |
| Leg and integral connection decision | One identified current detail, its governing simultaneous force/moment cases, applicable member and connection comparisons, geometric installation requirements, and an explicit pass or unresolved result. A revision must be evaluated with its changed load transfer. | Open: the existing four-bolt detail does not meet its conditional reference in the demanding upper-left cases. Historical larger-bolt and wider-stock candidates do not close this item. |
| Matching construction package | Cutting dimensions, drilling coordinates and diameters, complete hardware specifications, and assembly instructions refer to the same selected geometry. Any unresolved connection drilling is marked as such. | A package may document the current candidate before the joint decision, but final connection instructions must follow the selected and checked detail. |
| Assumptions and limitations | The owner-approved endpoint, load scenarios, floor premise, material premises, analytical limitations and omitted claims are explicit and linked to their evidence. | Recorded here. Update only for an actual design or evidence change. |
| Final consistency check | The selected model, schedules, construction instructions and calculation identify the same configuration; required current-candidate rebuild and affected focused checks pass. | Run after the final detail is selected. Historical variants remain available but need not be repeatedly rebuilt for documentation-only changes. |

The [current construction package](current-construction-package.md) provides
the candidate's stock, hardware and attachment schedules. These documentation
deliverables can be prepared in parallel with the joint work. Their completion
does not make unresolved joint drilling suitable for issue as a final
construction detail.

## Stopping rule and status changes

The project can end as an engineer-unreviewed DIY package once the agreed
leg/connection task has a supported decision, the instructions match that
decision, and the remaining scope limits are explicit. No external sign-off,
general panel qualification campaign, floor-friction test or destructive
failure-weight search is added at that point.

If the connection still exceeds its applicable reference, the record must say
so. Accepting an engineer-unreviewed endpoint does not change that arithmetic.
If the owner elects to retain such a detail, document that choice as an
unresolved calculated limitation; do not relabel it as a passing structural
check. Conversely, do not keep a completed connection task open for speculative
future improvements unrelated to its stated load cases and installation.

Record the selected leg detail and its result here when that work concludes.
Until then, this document completes the assumptions-and-limitations record,
not the outstanding connection calculation.
