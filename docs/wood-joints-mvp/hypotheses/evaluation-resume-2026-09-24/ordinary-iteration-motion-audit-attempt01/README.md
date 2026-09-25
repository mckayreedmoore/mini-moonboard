# Ordinary transient iteration-motion audit — attempt 01

This post-processes the terminal `ResultsForLastIterations.frd` from
[checkpoint attempt 01](../ordinary-transient-checkpoint-attempt01/). The
parent launcher recorded a 600 s bounded timeout, return code 137, no accepted
observations, and no mechanical acceptance. The file hash matches the
terminal `execution.json`; all 34 `DISP` blocks close with `-3`, declare and
contain 120,694 unique node IDs, and use consecutive iteration labels for
step 1, increment 1. The frozen `CURRENT_ALL_PHYSICAL_NODES` set contains
116,162 nodes; all displacement maxima exclude control and generated
nonphysical nodes.

For each trial field, the script computes the original work-conjugate actuator
observation from the hashed `actuator.json`:

`q = Σ fᵢ · Uᵢ`

It retains the two owner terms separately: `bottom_center_right_cleat` and
`base_principal_center_right`. The pilot comparison is the accepted first
increment value `6.989744242963423e-6 mm` from
[pilot03](../ordinary-transient-pilot-attempt03/execution.json). The checkpoint
shortened the step period from 0.025 s to 0.0025 s, so even close q values are
not proof of first-point equivalence.

| Trial | Total q (mm) | Cleat term (mm) | Principal term (mm) | Difference from pilot03 q |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 6.915662514e-6 | 5.472415144e-6 | 1.443247370e-6 | −1.060% |
| 8 | 6.945276131e-6 | 5.496795039e-6 | 1.448481092e-6 | −0.636% |
| 13 | 6.992538201e-6 | 5.536362962e-6 | 1.456175239e-6 | +0.040% |
| 17 | 7.067239311e-6 | 5.597060878e-6 | 1.470178433e-6 | +1.109% |
| 18 | 7.315633829e-6 | 5.781599174e-6 | 1.534034655e-6 | +4.662% |
| 30 | 7.726421447e-6 | 6.094150758e-6 | 1.632270689e-6 | +10.541% |
| 31 | 7.735356440e-6 | 6.101209361e-6 | 1.634147079e-6 | +10.669% |
| 32 | 7.754417611e-6 | 6.115271220e-6 | 1.639146391e-6 | +10.942% |
| 33 | 7.780087147e-6 | 6.134270780e-6 | 1.645816367e-6 | +11.309% |
| 34 | 7.823002338e-6 | 6.163883041e-6 | 1.659119297e-6 | +11.921% |

Trials 2 and 8 are close to pilot03, and trial 13 is especially close, but q
then rises sharply at trial 18 and continues increasing through trial 34.
Across trials 30–34, the total q range is `9.658089156e-8 mm`, or 1.382% of
the pilot value. The cleat and principal ranges are `6.973228324e-8 mm` and
`2.684860831e-8 mm`, respectively. Since this is a monotone drift, the small
five-trial range is not evidence of a settled response. The final written
trial is 11.921% above the accepted pilot point and cannot be used as a
reproducible accepted endpoint.

Across the trial file, maximum physical-node `|U|` is `6.305792e-6 mm` at
node 7 in trial 34. Maximum adjacent-iterate physical-node displacement
change is `5.382597e-7 mm` at node 33161 from trial 17 to 18. The latter is a
`|Uₖ − Uₖ₋₁|` update proxy, not CalculiX's residual or a separately reported
correction norm.

The FRD header labels these blocks at time zero. CalculiX 2.21's `results.c`
calls `frditeration` while `iout=0` and passes `ttime`; in this first increment
the saved blocks are Newton trial displacements, not an accepted t=0 solution.
See the pinned source extract's `src/results.c` and `src/frditeration.f`, and
the manual's `*NODE FILE, LAST ITERATIONS` description (§7.96). Do not infer
convergence from the contact counts or these displacement values; this run
timed out before accepting an endpoint. The other audit separately owns the
per-iteration contact-pair count analysis.

The executable parser is [`audit.py`](audit.py); full per-trial values,
terminal pins, and input hashes are in [`report.json`](report.json). Re-run
from the repository root with `python3
docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-iteration-motion-audit-attempt01/audit.py`.

## Publication boundary

This parser and report are not a runnable solver/audit bundle. The checkpoint's raw `ResultsForLastIterations.frd` (223,870,747 bytes; SHA-256 `051c0959db436a51e2777904cd48473d7f8ab3222788ecc6d1958879eef6bd2d`) remains local and is not committed. The comparison run's raw `pilot.frd` (35,694,964 bytes; SHA-256 `64113dd62b4e97d923dae71500e2ddbd3b294dd97d8cbf00757f5ddd98968a38`) and `pilot.dat` (3,936,134 bytes; SHA-256 `cbbca38de8de43d718be48442cc0c6f61ccbc6ff85b15014df47485aca0868f7`) also remain local. Run-directory duplicate `mesh.inp` and `mesh.json` files are retained locally, not shipped here. The tracked source mesh bundle is [`ordinary-patch-mesh-attempt02/complete-mesh-evidence.tar.gz`](../ordinary-patch-mesh-attempt02/complete-mesh-evidence.tar.gz), SHA-256 `3bd1b28bdbc9c109c6c96183a01e132cbd4c15f86867dca54e0c6ec3a309f4ac`; its `mesh/mesh.inp` and `mesh/mesh.json` hashes match the report's frozen mesh pins. The reports preserve terminal hashes and values, but rerunning requires the original outputs and full frozen inputs.
