# C3D10 mortar known-answer result

**FAIL — mortar method fixture.** The separate, law-matched penalty control passes
all frozen force, displacement, gap, compliance, output and convergence checks.
The mortar case completes normally but fails the force and geometry oracle.
This result does not qualify a candidate joint or permit a full-joint mortar run.

## Execution and preserved audit history

The two unmodified inputs ran serially on the pinned, unpatched CalculiX 2.23
binary. Both exit codes are zero, with no OOM or watchdog stop. Elapsed times
are 0.622 s for mortar and 0.522 s for penalty. Each accepts all 30 increments.
Mortar records 72 CVG iterations, maximum four per increment; penalty records
63, maximum three. Neither has a rejected attempt. The complete stdout iteration
identities agree with CVG and the accepted STA rows. Mortar never reaches the
source's iteration-greater-than-14 active-set override.

Native input notices are retained: the requested minimum increment of `1e-8`
is raised to `1e-6` times the unit step duration. All accepted increments remain
0.1, with no retries. The zero large-clearance tension value is also replaced
by a default; the notice explicitly limits that value to node-to-surface contact.
The pinned mortar LINEAR parameter routine uses the specified normal slope K.
Neither run uses node-to-surface contact.

The original [frozen verifier](verifier.py) failed parsing native numbers such as
`4.420147-101` and `2.825378-103`. Its [failed record](verifier.json) is preserved.
Fortran `Ew.d` formatting can omit `E` for three-digit exponents, as documented
by [Intel's compiler reference][fortran]. The separate
[attempt02 adapter](verifier_attempt02.py) accepts that spelling while retaining
finite-number checks and every frozen acceptance gate. No native job was rerun.
The [corrected audit](verifier-attempt02.json) fails mortar at total time 1.1 and
passes penalty at every accepted state. Its mortar evaluation is fail-fast;
the endpoint diagnostics below come directly from the same native DAT records.
The frozen README and readiness documents retain their pre-run state.

## Observed response

Positive geometric gap means clearance between the matching interface faces.
Forces are sums over the prescribed end-face nodes in native DAT output.
These faces contain no contact nodes. The gap is the upper-minus-lower mean
interface U3, with the initially coincident reference geometry included.

| Case / total time | Top U3 (mm) | Top RF3 (N) | Bottom RF3 (N) | Geometric gap (mm) |
| --- | ---: | ---: | ---: | ---: |
| Mortar / 1.1 | +0.000400 | -39.995198 | +39.995198 | +0.000800012 |
| Penalty / 1.1 | +0.000400 | approximately 0 | approximately 0 | +0.000400000 |
| Mortar / 2.0 | -0.005000 | -448.437982 | +448.438065 | -0.000531175 |
| Penalty / 2.0 | -0.005000 | -399.519900 | +399.519900 | -0.000998800 |
| Mortar / 3.0 | +0.001000 | approximately 0 | approximately 0 | +0.001000000 |
| Penalty / 3.0 | +0.001000 | approximately 0 | approximately 0 | +0.001000000 |

At time 1.1 both prescribed ends imply open, unloaded blocks. Mortar instead
produces approximately 40 N while the interface faces remain separated. At the
compression endpoint, the predeclared small-strain reference is 400 N and
0.001 mm overlap. The source-derived finite-strain reference recorded before
execution is 399.519872 N and 0.000998799680 mm overlap. Penalty agrees with both
within the frozen tolerance. Mortar's 448.438 N and 0.000531175 mm overlap fail;
finite-strain correction cannot account for the difference. Mortar also loses
uniformity: the nine endpoint gaps range from -0.001040053 to -0.000065651 mm.
Independent read-only review by `coupon_gate_strategy` confirms the numeric
rows, all output and source hashes, iteration guard, parser-only change and
result-table identities.

The failure does not arise from the iteration override, the original number
parser, or using transformed contact fields as pointwise pressure. It is
visible in support reactions and nodal coordinates. Its underlying cause is
not yet established. Keep the failed evidence, investigate the documented
formulation and history handling, then freeze any minimal discriminator
separately. Do not alter tolerances or carry convergence forward as acceptance.

## Evidence identities

| Artifact | SHA-256 |
| --- | --- |
| Input freeze | `28b9370f2e1100a82c4b371584131f3565b26bf91886cf2bec57135b86558899` |
| Execution record | `c09e9d37dff3f8702c5a651f78f7ab44f508265ea82c5f2ef3f0019cb209c49c` |
| Original verifier | `bcc10408e3ecdc65731ce928cba959808964b7daf61eb35fe8668f6a117e3170` |
| Original failed audit | `e9628a4bf8b85c3dc17f73d8e16a8e9a3acdddddbb98a2a4161e6e33eee79875` |
| Parser-only adapter | `9e7aeefc348c3d26965f66b963d6ea6d0e9aac130cf6457a49c91c62a0c2764a` |
| Corrected failed audit | `d3a40b6b8dec400cb59a14c5574b72ec15ac3c582b964a973245267bc20369d0` |

The [execution record](execution.json) binds both inputs, solver identity,
container terminal state and native output hashes. [Parent review](parent-review.json)
records the pre-run source and finite-strain checks. The [expected contract](expected.json)
contains the unchanged known-answer gates. No model geometry, joint capacity,
load history, candidate selection or physical release changes follow from this result.

[fortran]: https://www.intel.com/content/www/us/en/docs/fortran-compiler/developer-guide-reference/2023-0/e-and-d-editing.html

Follow-up source research: [gap history and penalty adjustment](source-gap-history-screen.md)
and [official documentation screen](source-screen.md). These identify bounded
discriminators and retain the distinction between source paths and causal proof.
