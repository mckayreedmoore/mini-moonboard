# Reinforced candidate: release decision and exact remaining work

**Decision: do not release `round-reinforcement-development` for construction.**
The missing work was structural response and resistance, not another fit check.
Those calculations have now been run. They identify a failed sticking-floor
assumption and several member/connection reference exceedances. This is a
substantive load-path problem, not a nearly finished fabrication checklist.

The current CAD is preserved so the failed comparisons remain reviewable.
No new variant or isolated hardware change is described as resolving the whole
assembly. Historical issue text is [preserved separately](history/issue-8-before-reinforced-checks-2026-09-12.md).

## What was actually checked

Two assembled native models used all 66 panel screws, 132 SDS screws, 24
structural bolts, 22 ML24Z bodies, two steel shoes, six independent panels and
unilateral bearing contacts. Both used hold F10, 250 lb × 2 downward, 300 N
horizontal and 100 mm outward standoff. Joint translation stiffness was
1,000 and 10,000 N/mm. Both converged in contact and passed independently
recovered global equilibrium and printed-precision constraint checks.

These are **diagnostic models**, not accepted physical design demands. Gross
timber and unperforated isotropic plywood use assumed elastic properties;
actual load-slip behavior, panel orthotropy, hole effects and hold-seat traction
are not represented. Most importantly, the solved sticking-foot reactions
cannot be supplied at the stated floor-friction assumption. Capacity
comparisons below therefore identify problems in those declared models, not a
claim that the physical assembly will rupture at the listed loads.

| Check | 1,000 N/mm model | 10,000 N/mm model | Disposition |
| --- | ---: | ---: | --- |
| Necessary center-foot friction coefficient | 0.893 left / 0.767 right | 2.274 left; right lifts | **Fails assumed μ=0.40 in both.** These are force-only necessary bounds, independent of friction-polygon approximation. |
| Top-rail gross bending/axial interaction | 1.571 | 1.262 | **Exceeds 1.0 in both.** Even ideal bracing leaves necessary ratios 1.202 / 1.040; print-error bounds still leave 1.177 / 1.030. |
| Maximum SPAX head pull-through ratio | 3.032 | 4.316 | **Reference exceeded.** Applicable head reference is 533.787 N, not the earlier 304 or 943 N alternatives. |
| Maximum SPAX wood combined-action ratio | 2.618 | 5.984 | **Reference exceeded.** Uses each recovered screw force, not equal sharing. |
| Panel/kicker screws exceeding at least one checked reference | 7 / 66 | 28 / 66 | Attachment/load-transfer revision must be assessed after correcting the system response. |
| Maximum leg-bolt wood yield ratio | 0.946 | 1.839 | **Harder case exceeds reference.** Governing timber-bearing rotation is not fixed by selecting a stronger bolt grade alone. |
| Steel shoe bolt interaction | 0.0915 | 0.1090 | Below the conditional steel limits; not a complete joint pass. |
| Square bearing-plate bending screen | 0.0607 | 0.2117 | Below the conditional screen; contact/prying assumptions remain explicit. |
| Right single-fillet weld diagnostic | 1.028 | 0.739 | Baseline exceeds the elastic screen; longitudinal root-rotation detail remains unresolved in either case. |
| Worst ML single/end force-only unity | 0.947 | 0.921 | Force components below that screen; flange couples and six bearing-like installations prevent a complete rating pass. |
| Largest separation demand at an unlisted bearing-like ML installation | 85.236 N | 178.457 N | Exact missing capacity/load path identified; a different installation's F2 rating cannot be substituted. |

Maximum total panel translations were 23.661 and 12.831 mm. They include frame
motion and are not isolated plywood bending deflections. Shell component
exceedances persist more than 100 mm from the assumed hold patch, but no
physical hold footprint or combined panel acceptance is invented from that
result. Detailed [panel](reinforced-panel-checks.md), [fastener](reinforced-fastener-checks.md),
[timber](reinforced-timber-resistance.md), [steel](reinforced-steel-capacity.md)
and [native model](reinforced-frame-demand.md) records preserve the assumptions
and individual demands.

## Calculations and reference questions that are closed

- **SPAX head reference:** direct manufacturer-evaluated 120 lbf / 533.787 N
  applies using the table's minimum-thickness and lower-specific-gravity
  footnotes. Adopted dry, ≤100°F, normal-duration adjustments are explicit.
  The earlier head-shape/plywood-column question is resolved.
  [Primary source and decision](reinforced-fastener-applicability.md).
- **Rigid-body floor equilibrium:** 768 enclosing load vertices prove
  compression-only sliding/yaw equilibrium for all 142 holds and every
  horizontal azimuth in the stated envelope at assumed μ=0.20 or 0.40.
  At μ=0.10, actual loads fail the necessary sliding bound by up to 46.633 N
  among the reported counterexamples. This establishes equilibrium existence,
  not the deformable frame's actual force allocation. The native failures
  above explain why that earlier pass cannot release the frame.
  [Proof, assumptions and numerical evidence](reinforced-floor-envelope.md).
- **Owned T-nut local bearing screen:** at the 300 lb × 2 sensitivity and
  300 N outward horizontal force, normal tension alone is 1945.370 N against
  approximately 957.107 N of annular plywood face-bearing reference: **2.033**.
  Even gross unperforated flange area gives only 1257.705 N. This is failure
  of the adopted APA indentation/bearing reference, not demonstrated rupture
  or a calibrated T-nut pull-through capacity. Standoff-couple calculations
  state their additional bolt/hold-contact assumptions.
- **Wood connection detailing:** current shoe header rows span 130 mm across
  grain versus the NDS 127 mm limit without special shrinkage detailing.
  Current detail exceeds that criterion by 3 mm. Actual trimmed rim ends and
  current washer dimensions were checked; historical hardware was excluded.
- **Hold bolts:** published wood/plastic kit lengths and complete thread
  engagement guidance are recorded. No unsupported per-hold assignment was
  added. [Hardware record](moonboard-hold-hardware.md).

## Exactly what must happen before build release

The following is the finite execution order. These are remaining design and
validation requirements, not requests for additional floor measurements.

1. **Resolve the lower-frame spreading load path.** Provide a designed bottom
   tie/strut or another restraint that carries the internal horizontal thrust,
   or solve a compatible sliding/contact model that demonstrates acceptable
   behavior under the declared friction assumption. Do not raise assumed
   friction to 0.9–2.3 simply to preserve the present sticking solution. Size
   and connect any new restraint from simultaneous forces and rerun the frame.
2. **Resolve top-rail, bracing, panel attachments and leg-joint resistance in
   that corrected response.** The current diagnostics exceed their references.
   A single 3x6 top rail is a useful fixed-demand sizing candidate (baseline
   ratio about 0.686), but needs fit and new-demand checks. Long compressed
   38.1 mm members need demonstrated lateral restraint; the full-unbraced
   sensitivities exceed slenderness 50. Panel receivers/attachment placement
   and leg bolt-group geometry must distribute the actual loads. A denser screw
   count, assumed equal sharing or a higher bolt grade is not itself closure.
3. **Complete the local hold/T-nut interface.** Obtain a verified capacity for
   the owned T-nut/plywood/hold assembly or design an actual fitting rear
   spreader. Check plate bending, contact, independent-panel edges, rail/LED
   clearance, retention screws and remaining barrel/bolt engagement. Actual
   hold contact lever arms are needed for the eccentric couple. A nominal
   36 × 70 mm plate illustrates sufficient area for one stated sensitivity,
   but some receiver locations obstruct that footprint; it is not a released
   universal washer detail.
4. **Complete the shoe and commercial connection details.** If retaining the
   shoes, replace or justify the single-sided root-rotation mechanism. A
   full-thickness CJP tee weld with an explicit qualified fabrication procedure
   is a concrete candidate; it does not fix the system failures by itself.
   For six bearing-like ML24Z joints, establish a rated separation path and
   compatible couple transfer or provide a specifically designed replacement.
   Specify a supported bolt bending-yield basis; current A307 identification
   does not by itself establish the assumed 45 ksi wood-dowel input.
5. **Finalize machining against the resulting design.** Move the rear header
   bolt row from Y=−210 to −206 mm if that shoe remains: 126 mm nominal spread
   leaves 1 mm total allowance below 127 mm. Verify new fit and connection
   resistance. Keep the requested 38.1 mm passages unless an explicit revised
   detail is selected; a centered hole in 139.7 mm stock has zero allowance
   against two 50.8 mm ligaments. Establish stock, finished-hole and centering
   acceptance or engineer the local opening. Then complete panel net-hole,
   drilled-zone, torsion, local bearing/splitting and assembly/receiving checks.
6. **Validate and issue one matching package.** After the load path is viable,
   check governing face/kicker locations, justified joint compliance, panel
   orthotropy, mesh sensitivity and applicable deflection/load criteria.
   Reconcile the accepted geometry with its cut/drill/hardware/assembly
   schedules and deployment. Do not transfer a historical candidate's pass.

Physical floor measurements/tests remain outside the owner's scope. Floor
friction, levelness and support capacity must stay explicit installation
assumptions; they cannot be silently converted into measured properties.

A broad mesh or all-hold strength sweep was not used to decorate a model that
already fails its support assumptions. The two converged comparisons, separate
continuous rigid-equilibrium proof and local conventional checks provide the
current rejection and the specific next design work. They do not complete the
six remaining release requirements above.

## Reproducibility and verification

- [Baseline native bundle](../fea/results/reinforced-F10-k1000-v4.tar.gz):
  source snapshots, final native cycle, every cycle report/log and internal
  file hashes. Archive SHA256 `8cd853bf5e3a5e4d694f93901f5b2d0acab9d7e32e3e3ff06fda7e6619b08d34`.
- [Harder-joint native bundle](../fea/results/reinforced-F10-k10000-v5.tar.gz):
  same retained evidence. Archive SHA256
  `032988d17e1ea7f1489fd3b9d2af1078d5b4d735fa49411f6cc1c5dc3d3c5c54`.
- [Nonconverged hard-joint trial](../fea/results/reinforced-F10-k10000-v4.tar.gz)
  and [earlier failed-trial record](../fea/results/reinforced-frame-failed-trials-v1.json)
  remain identifiable as failed numerical evidence.
- [Superseded calculator drafts](../fea/results/reinforced-superseded-calculation-drafts.tar.gz)
  preserve earlier JSON revisions byte-for-byte with an internal SHA256 index;
  current comparisons above use the canonical final artifacts.
- v5 removes unintended kicker-edge friction, retaining vertical bearing only.
  The v4 baseline has zero kicker normal and friction force, so this correction
  does not change that baseline response. Posts/legs retain the same whole-foot
  sticking assumption in both comparisons.
- Both converged global force residuals are below 0.0004 N and moment residuals
  below 0.5 N mm. Member-level residuals are larger; independent propagation of
  actual native print intervals explains all 18 members in each case. This is
  output-precision accounting, not an estimate of model or discretization error.
- **52 focused tests pass**, including equilibrium/interpolation, force signs,
  panel integration, resistance formulas, source isolation and print-interval
  recovery. Ruff and whitespace checks pass. CAD geometry is unchanged.
