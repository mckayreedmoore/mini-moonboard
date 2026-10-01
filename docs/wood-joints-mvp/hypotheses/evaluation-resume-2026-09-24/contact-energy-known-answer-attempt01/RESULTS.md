# Contact energy output results, September 27

The output-only fixture preserves the passing section-force attempt02 mechanical
results in both formulations. Penalty body and contact energies pass the frozen
analytical checks. MORTAR prints zero contact energy at compression, where the
independent reference is 0.2 N·mm; that channel is not validated. The aggregate
energy-method acceptance remains false. This is a method fixture, not a joint
response, resistance result, or structural criterion pass.

## Observed energy

| Compression quantity | Analytical reference, N·mm | Penalty, N·mm | MORTAR, N·mm |
| --- | ---: | ---: | ---: |
| UPPER body ELSE | 0.4 | 0.3998398 | 0.3998398 |
| LOWER body ELSE | 0.4 | 0.3998398 | 0.3998398 |
| Body ELSE sum | 0.8 | 0.7996796 | 0.7996796 |
| Contact CELS | 0.2 | 0.1995202 | 0 |
| Observed ELSE + CELS | 1.0 | 0.9991998 | 0.7996796 |

Each nonzero reference uses the predeclared tolerance of 1% of that reference
plus 1e−6 N·mm. Open and reopen energies use an absolute 1e−6 N·mm tolerance.
Both formulations pass the body checks; penalty also passes contact and
combined totals at all three states. The penalty combined compression error
is 0.0008002 N·mm, below 0.010001 N·mm. MORTAR's combined error is 0.2003204
N·mm and fails that comparison. Its numeric zero is an observed unsupported
output, not evidence of zero stored contact energy. The pinned mode-2 source
limitation is recorded in the [energy-method review](../contact-mortar-c3d10-fullstep-attempt01/energy-method-review-2026-09-27.md).

## Execution and mechanical checks

The parent reviewed the analytical components, tolerances, exact output-only
lineage, source pins and synthetic parser checks before freezing the packet.
A prefreeze review caught an incorrect free-text negation test for source
support. It was replaced with an exact pinned interpretation assertion and
explicit unsupported disposition, and checked using the actual expected file.
No frozen input or native result was changed to obtain this correction.

Both cases ran serially in the pinned unmodified CalculiX 2.23 image, taking
about 0.32 and 0.42 seconds. Both exited normally, without OOM or a monitor
stop. The three accepted full-step states retain exact nodal DAT U/RF arrays,
STA rows and CVG numeric rows from section-force attempt02. All inherited
endpoint, equilibrium, section-force, full nodal output and iteration checks
pass. The added energy requests do not change the observed mechanics.

The [verifier result](verifier.json) reports `PASS_MECHANICAL_FIXTURE_ONLY`,
with `energy_acceptance=false`, `joint_acceptance=false` and `release=false`.
The [independent review](independent-review.md) confirms these scoped results.
The frozen README describes the preparation state and is retained unchanged;
this results note records the subsequent execution.

## Applicability

Penalty ELSE and mode-1 CELS now have known-answer evidence for this homogeneous,
frictionless two-body C3D10 fixture and these three accepted endpoints. This
does not establish energy accounting for a many-pair joint, frictional work,
nonlinear wood, transient behavior, or an entire response path. Prior production
energy failures and repaired-source investigations remain separate evidence.

The open-to-compression endpoint trapezoid crosses a force-free gap and gives
1.2 N·mm, while analytical stored energy is 1.0 N·mm. Thus this output pass
does not validate the proposed 5% work-balance gate. An exact-touch known-answer
check and an explicitly frozen absolute work floor remain necessary before
using such a gate on a current-joint path. Contact-plus-MPC motion and pair-local
bearing-onset output also remain separate method questions. No heavy joint
retry follows from this result alone.

## Immutable records

| Artifact | SHA-256 |
| --- | --- |
| [Input freeze](input-freeze.json) | `7ca80c4cdfe92b1f8dfcb0d71c9a97884dd7b6bdabb540b50902cf21c16396a0` |
| [Execution](execution.json) | `624c6b2fb3b4a72dff8fab08c4c724444bc46ecb4ad3fccea8af722e224656e1` |
| [Verifier](verifier.py) | `a6b9eb0849db95e68ed1edcc7801078ef566dcf4f9e9e5bdc52b386d2adcc33a` |
| [Verifier result](verifier.json) | `15ff0827a312df7b5c4e10860ed57f852532b1f5dc718da1a7ec94f260470951` |
