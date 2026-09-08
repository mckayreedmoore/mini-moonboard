# Panel-edge release sensitivity results

Three linear K12 basis cases were solved on 2026-09-08 after the
[mesh-transformation proof](panel-edge-release-diagnostic.md). The comparison
uses the preserved timber geometry, not the insert or wider-principal revision.
It answers how much the unintended finite-area panel-edge bond affects one
loaded-point displacement while the rim bond and common edge remain idealized.
It does not establish physical contact or joint capacity.

## Result and decision

For the same 300 lb, 2× downward-weight plus 300 N outward combination, the
bonded model gives **2.71169 mm** loaded-point displacement and the released
model **2.72037 mm**: approximately 0.32% more. The three new solved cases are
1000 N in +X, 1000 N in +Y and 1000 N in −Z at the same mapped K12 node. The
300 lb comparison is their linear combination, not a fourth independent solve.

This small difference does not justify making the frame heavier to compensate
for removal of that panel-edge bond. It also does not prove the real rim bolts
are sufficiently stiff or strong: their entire remaining interface is still
ideally bonded, and both leg plies still act together in this calculation.

The traction-free surfaces do overlap in the computed deformation:

| Selected 300 lb combination | Left interface | Right interface |
| --- | ---: | ---: |
| Minimum signed normal gap | −0.001094 mm | −0.002615 mm |
| Maximum signed normal gap | +0.000160 mm | +0.003557 mm |
| Pairs below −0.00001 mm classification threshold | 71 of 72 | 43 of 72 |

Negative gap means the leg and panel move into one another; positive gap means
opening. These are very small numerical movements, not measured physical
clearances. The classification threshold is not a fabrication tolerance or a
contact-convergence study. The model has no contact constraint to prevent
overlap, so it is not a conservative bound on the physical assembly.

**Decision: retain this as a sensitivity diagnostic only.** Do not distribute
its aggregate forces among the four bolts or use its local stresses for wood
or fastener approval. A unilateral contact/interface model and actual connector
load path remain necessary for a defensible joint-demand calculation.

## Numerical audit and remaining assumptions

All three endpoints include complete loaded-node displacement, floor reactions
and displacement of both sides of every released pair. Input source hashes,
exact deck/load/support reconstruction, six-component global equilibrium,
reciprocal positive loaded-node compliance and the unchanged source mesh are
checked. All 144 new nodes duplicate old coordinates; no material is removed.

Host/container NumPy versions differed only in four compliance eigenvalues by
at most 1.31×10⁻¹⁸ mm/N. Archive replay therefore permits a tightly bounded
rounding difference only in those two three-value eigenvalue arrays; compliance
matrices, loads, displacements, reactions and gaps still require exact agreement.
Regression checks reject material eigenvalue changes and any change to the
other replay fields.

The common N=0 edge still shares nodes, and the finite-area rim bond is retained.
Floor nodes—including the kicker bottom—remain fixed XYZ. There is no gravity,
wood orthotropy, fastener compliance, ply slip, material failure or unanchored
floor contact. This is a single mesh and single hold location, not a convergence
study or a validation of the 250 lb intended maximum.

## Evidence and reproduction

[Published summary and archive hashes](../fea/results/timber-release/summary.json)
identify seven compressed replay artifacts: preparation input, solver deck,
displacement/reaction output, log, status, launch record and result. Bulky FRD
diagnostics are explicitly omitted from the compact archive, not implied present.

The [derived Docker toolchain](../fea/release-toolchain/README.md) records the
actual image ID and package versions. It adds NumPy for the existing compliance
audit; it does not change the historical FEA environment.

```bash
uv run pytest -q tests/test_timber_release.py \
  tests/test_publish_timber_release.py tests/test_timber_release_evidence.py
```

No construction or climbing approval follows from these results. See the
[connection ledger](connection-qualification-ledger.md) for the remaining work.
