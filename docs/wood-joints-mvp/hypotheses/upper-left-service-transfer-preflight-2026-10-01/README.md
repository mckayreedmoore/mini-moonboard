# Upper-left service cleat: simple working scenario MVP

**The calculation prototype is complete and runnable. The complete joint remains HOLD.**
This is the owner's requested simple working scenario from which to improve the
joint. It preserves `left_service_outer_upper_cleat`, its four bolt axes and the
reviewed `led-clearance-2x6-runner-seated-blocks-v1` geometry. It does not change
the full 47-criterion authority or any physical release. The authenticated
[source packet](../upper-left-service-joint-mvp-2026-10-01/README.md) is unchanged.

## Working result

Use the 21 existing simultaneous signed rail/side wrench pairs at **twice their
saved values**, including the matching body-load margin. This is a declared
local scenario for A1-rear, A12-rear and K12-rear; it does not establish coverage
of A12-forward, A12-left or K12-right. Values below are deliberately rounded.
Peaks occur at different states; they are not one combined bolt demand.

| Output at 2× saved demand | Peak | Interpretation |
| --- | ---: | --- |
| Bolt tension | 119 N | Two-bolt/contact spring allocation |
| Bolt lateral force | 73 N | Compatible two-bolt allocation with clearance |
| Bolt steel scenario | 299 MPa / 634 MPa = 0.47 | Same assumed root, tension/shear and the declared bending scenario |
| Lateral reference budget ratio | 0.51 | Existing hypothetical 45 ksi Fyb reference with the existing 25% budget |
| Quarter-annulus wood compression ratio | 0.52 | Ideal average pressure over 25% of the nominal supported annulus |
| Timber-face patch average pressure | 0.14 MPa | Quarter of each source contact-cell area; pressure distribution unqualified |
| Washer radial-strip index | 83 MPa / assumed 250 MPa = 0.33 | A demand sensitivity, not qualified washer stress or resistance |
| Relative movement at a bolt-pair datum | 1.2 mm | Local spring-model motion, including assumed bore clearance |
| Relative rotation | 3.6° | Local rotation; no frame acceptance limit has been established |

The force/material references have useful margin at the doubled scenario.
**Movement deserves the next practical check.** The modeled 7.5 mm bore and
6.35 mm bolt give 0.575 mm radial clearance in each receiver, or 1.15 mm relative
clearance before bearing. Those are analysis dimensions, not a drilling or
purchased-part instruction. Actual bore/profile conformance is unobserved.
The movement estimate cannot be transferred to the frame's diagnostic laws.

A useful dimensional sensitivity keeps the same spring laws and saved loads:

| Assumed relative clearance before bearing | Peak translation | Peak rotation | Peak bolt lateral force |
| ---: | ---: | ---: | ---: |
| 0 mm | 0.26 mm | 0.58° | 67 N |
| 0.50 mm | 0.58 mm | 1.63° | 72 N |
| 1.15 mm, saved scenario | 1.20 mm | 3.62° | 73 N |

This identifies clearance as the main movement sensitivity in the small model.
Zero clearance is a mathematical sensitivity, not a proposed fit or installation
instruction. No bore, bolt axis, or reviewed member geometry has been changed.

## The small model

Treat the cleat and both receivers as rigid bodies, using the cleat as a fixed
reference. Invert each receiver's same-state wrench independently to find its
six relative motions. The frame does not constrain those motions in this local
sensitivity; no shared-cleat deformation or frame compatibility is solved.
Each interface has two tension-only bolt springs, four
compression-only timber contact patches, and two lateral bolt springs with
circular clearance. Face opening and bolt stretch use one compatible affine
motion. Lateral force sharing includes compatible motion at both bolt points;
it is not an equal division where clearance and torque require another share.
The saved interface wrenches are target restoring tractions on the cleat, not
additional external loads applied to the same springs. The model inverts
these tractions to find cleat motion relative to each receiver; restoring
traction opposes relative motion. Body-load effects enter through the
authenticated source reactions: the preflight verifies both interface
tractions plus body loads in simultaneous source balance. The spring producer
does not apply body loads separately or re-solve that global equilibrium.
There is no friction or preload credit. Faces and axial hardware are assumed
initially seated with zero gap/slack.

The study assumes an effective timber modulus of 300 MPa and steel modulus of
200,000 MPa. Face patches use one quarter of the existing source cell areas;
their stiffness is `E × effective area / total wood grip`. Bolt axial stiffness
combines the assumed root-section steel rod and two quarter-annulus timber
seat springs in series. For lateral stiffness, the simple symmetric
beam-on-Winkler-foundation relation is `beta = (k / (4 EI))^(1/4)` and
`K = EI beta³`, with `k = 300 N/mm²`. These are study assumptions, not calibrated
joint laws. Finite embedment, rotational restraint and timber anisotropy need
later assessment; no native solver or its pending output methods are used.

The steel sensitivity uses `M = V × wood grip / 4`, the assumed 0.189 in circular
root at the common checked section, maximum circular-section shear, and
von Mises stress. This is an explicit bending scenario. It is **not a proved
bending bound**. The sourced 1.913 N·m receiver-datum moment is never assigned
to a bolt section. The washer index uses radial strips with the catalog minimum
0.051 in thickness and the total axial load spread around the inner
circumference. It excludes hoop action and the real head/nut/washer/wood
boundary. Its comparison with 250 MPa defines a hypothetical material
sensitivity; it does not claim a catalog yield minimum or close metal transfer.

The normal and lateral models deliberately omit local bolt free couples,
washer bending compliance and finite shared-cleat deformation. The working
scenario is suitable for finding important motions and demand scales. These
simplifications prevent complete-joint acceptance even when scalar ratios are
below one. Use the explicit assumptions rather than treating rounding as a
way to discard a missing load path.

## Why face bearing stays in the model

The [signed preflight](transfer-preflight.json) shifts each receiver wrench
from the common block datum to its bolt-pair midpoint using
`M_new = M_old - (new - old) × F`. For two point forces at positions
`±a p`, the moment parallel to their connecting line is zero:
`p · ((±a p) × F) = 0`. All **42 receiver states** require a nonzero couple
about this line, outside the saved rounding intervals.

The largest such source couples are **0.55 N·m on the rail interface** and
**1.59 N·m on the side interface**, both at full K12-rear. The saved normal
contact ports supply these couples in the diagnostic source model. They are
receiver moments, not local bolt bending. The preflight rejoins 336 source
ports and 420 body-load instances without rerunning the completed source
checker, CAD or a native solve. Contact-pressure qualification remains open.

## Conditional assembly and service concept

Use the existing one-cleat/four-bolt/four-nut/eight-washer concept and the
already declared partially threaded 6 in and 8 in profile targets. Assume
compatible Grade 5 regular hex nuts, the specified full-form external thread
coverage, ordinary head/nut bearing lands and captured washers. These are
procurement conditions, not selected SKUs or receiving observations.

For this working scenario, assemble the supported rail, side and cleat as a
bench subassembly with both sides exposed to matched tools. Service may require
supported partial frame disassembly after a reversible panel/light service
state. Remove only metal-thread stacks and keep each timber member separate
for transport. This is an assembly concept to evaluate, not a shop instruction.
The saved 24 clear component paths do not establish installed turning,
counterhold, capture, cleat extraction or a complete disassembly sequence.

## What to improve next

1. Check the frame's tolerance for the predicted clearance movement and
   rotation. Explore actual dimensional scenarios before proposing any changed
   bore or bolt arrangement; reviewed geometry stays fixed.
2. Replace the local bending scenario and washer strip index with one complete
   bolt/head/nut/washer/contact transfer model, reusing the primary's qualified
   methods when available. Preserve simultaneous interface wrenches.
3. Assign actions to actual finished sections and check the shared cleat and
   both hosts for splitting/group effects. Parallel-grain Appendix E checks
   alone do not cover the two orthogonal groups.
4. Validate matched hardware, two-sided tools, supported assembly/removal,
   transport, BOM/cost and the missing-case or adopted local-envelope coverage.

All seven original joint gates remain open in `working-scenario.json`.
`working_scenario_mvp_complete=true` describes this calculation prototype;
`local_joint_mvp_complete=false` and `complete_joint_accepted=false` preserve
the engineering disposition. All release flags remain false.

## Run and check

The retained `/tmp` source replay remains required and hash-bound. Do not
overwrite that authenticated source file.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-left-service-transfer-preflight-2026-10-01/working_scenario.py > /tmp/mini-moonboard-upper-left-simple-working-scenario.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/upper-left-service-transfer-preflight-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/upper-left-service-transfer-preflight-2026-10-01
```

Eight known-answer/source-refusal checks cover wrench translation, two-point
moment transfer, rounding propagation, source drift, pure tension/compression,
shear clearance and opposed forces under torque. They check the small software
model; they do not qualify the physical joint. Preserve this folder and the
referenced `/tmp` evidence. No commit or push is part of this packet.

The [parent validation receipt](parent-validation.json) records exact replay,
lint, artifact hashes and the clearance sensitivity values. The retained unit
suite was not rerun after the final motion-direction correction. To reproduce
the dimensional sensitivity without modifying geometry or the saved default:

```sh
.venv/bin/python - <<'PY'
import json
import sys
sys.path.insert(0, "docs/wood-joints-mvp/hypotheses/upper-left-service-transfer-preflight-2026-10-01")
import working_scenario as scenario
for clearance in (0.0, 0.5, 1.15):
    scenario.RELATIVE_CLEARANCE_MM = clearance
    result = scenario.produce()["maxima"]
    print(json.dumps({"relative_clearance_mm": clearance,
                      "translation_mm": result["relative_translation_mm"],
                      "rotation_degrees": result["relative_rotation_degrees"],
                      "bolt_lateral_n": result["lateral_n"]}))
PY
```
