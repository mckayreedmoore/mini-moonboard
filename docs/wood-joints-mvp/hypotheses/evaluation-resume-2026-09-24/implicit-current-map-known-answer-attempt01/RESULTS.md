# Current-map implicit benchmark result

The three frozen native cases pass the predeclared current-map known-answer
checks. Each accepts ten increments from 0.001 to 0.010 s in two iterations
per increment, with complete required DAT and FRD fields. The original body,
its six original free mapping coordinates, and the added zero-density rigid
nut carrier meet the reference, control, kinematic, equation and parity gates.

This qualifies one actual A00 map under this small global-Y rotational forcing,
timestep and material/method configuration. It is not a joint response,
resistance result, qualification of all four maps or arbitrary histories, or
an elastic-error theorem. No full structural-criterion disposition changes.

## Execution and preservation

Parent ran the cases serially on September 28 UTC (September 27 Denver), after
the terminal independent preflight and 24 synthetic controls passed. The only
acceptance changes before freezing were readiness/status metadata; numerical
gates were unchanged. The parent readiness record binds those changes and
every other frozen local file.

| Case | Accepted states | DAT / FRD nodes per U or V state | Elapsed seconds | Native output bytes |
| --- | ---: | ---: | ---: | ---: |
| `direct` | 10 | 11,348 / 11,348 | 13.283884 | 24,717,801 |
| `mapped_no_carrier` | 10 | 11,350 / 11,348 | 18.906411 | 24,719,917 |
| `mapped_carrier` | 10 | 12,457 / 12,455 | 20.108165 | 27,133,306 |

The two unmeshed REF/ROT controls appear in DAT, not FRD. All three cases use
one CPU, one GiB memory with no extra swap, no network and the same pinned
CalculiX 2.23 executable. All exits are normal, with no OOM or limit stop;
each remains below its 120-second and 64-MiB caps. The runner retained the
stopped containers and raw output files. There is no live fixture solve.

The input freeze binds 24 local files and 14 external dependencies. The
verifier checks those inventories again, all case inputs and outputs, normal
exits, exact accepted schedules and non-overlapping execution times.

| Artifact | SHA-256 |
| --- | --- |
| [Input freeze](input-freeze.json) | `36b624a9d4658862e96a225a28b844b8372150dc449e4749a4b683faf5adcf9e` |
| [Execution](output/execution.json) | `29e7705be56e655758c8133ee2cd3e5f5325b1ea3d2d98058fd1002702cac4b5` |
| [Verifier result](verifier.json) | `e9c2da08d7ff1bffdd8fcffbb06d921ab71472ec409494c91334e1767c506603` |
| [Final acceptance](acceptance.json) | `4aee8f74437640a2eb8a87f75c4fb70b16ce72a2e6df974a0f5f37406acb0ce3` |
| [Independent preflight](verifier-preflight.md) | `043b034ad6b78e1e79383575ccda12d6deded294837b2e0dfd68759c86913cf7` |

## Numerical result

Every body U/V component is checked against the declared linearized discrete
reference at every state. Across cases, maximum physical errors are
5.12043e-12 mm (DAT U), 5.71413e-10 mm/s (DAT V), 5.06150e-11 mm (FRD U),
and 5.23820e-9 mm/s (FRD V). All pass their frozen absolute-plus-relative
criteria; the largest error/allowance ratio among these checks is below 0.797.
Printed output resolution is included only as specified by the acceptance
contract, not by postrun adjustment.

The mapped cases each check all six intended controls, their independent
weighted fit to the physical shaft nodes, and all six original displacement
equations at every state. Maximum printed equation residual is 1.58112e-12,
with the largest ratio to its coefficient/token/arithmetic allowance below
0.476. These residuals are equation-row values, not an independent force or
strength check. Controller fit and intended-reference checks also pass.

All 1,107 carrier nodes satisfy total Rodrigues displacement and the
source-defined rotation-vector velocity derivative using measured controls.
Maximum DAT carrier errors are 4.99869e-13 mm and 5.12889e-11 mm/s; maximum
FRD errors are 5.02319e-12 mm and 5.12846e-10 mm/s. Carrier mass and ELKE
are printed as zero. Its numerical ELSE reaches 4.853587e-25 N mm and passes
the frozen small-strain-energy ceiling; it is not claimed exactly zero.
The undefined auxiliary centroid/inertia statistics caused by zero mass are
outside the required-output contract. All required channels are present and
finite.

Positive-body mass, volume, ELSE and ELKE pass in all cases. Maximum ELKE
reference error is 3.87810e-17 N mm. Direct-to-mapped physical DAT differences
are at most 1.01e-19 mm and 1.01e-16 mm/s. Adding the carrier changes printed
common physical DAT by at most 1.01e-12 mm and 1.01e-9 mm/s, within the
separately frozen two-record parity allowances. All FRD, energy and mapped
control parity gates pass. Exact physical equality is not claimed.

## Reproduction and next decision

Use the frozen verifier read-only from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-current-map-known-answer-attempt01/verifier.py --audit-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-current-map-known-answer-attempt01/output
```

Do not repeat `--freeze`, `--run` or `--write` in this directory. Any changed
method/input belongs in a separately frozen attempt.

The [independent postrun review](independent-postrun.md) reproduces the passing
verifier and confirms raw coverage, execution, numerical results and every
frozen/captured hash. Its SHA-256 is
`38b3bb457451535756a4ea15d4667a8f291d7487d54809f9e8ecd977d1cd46d6`.
Before a current-joint retry, reconcile this tested map/mode with the actual
four-map loading contract and finish the needed bounded contact observations,
engagement and complete-transfer gates. A new benchmark must identify the
specific unsupported behavior it resolves. None of this changes the reviewed
frame geometry or authorizes fabrication.
