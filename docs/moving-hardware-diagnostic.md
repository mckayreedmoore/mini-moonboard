# Fail-only moving momentum and kinetic-energy diagnostic

**No additional failures were found in these partial observations. The original
contact audit remains failed; this is not a qualified moving-contact test or a
board-strength result.**

The [retained diagnostic](../fea/results/coarse_moving_control/fail-only-diagnostic.tar.gz)
replays the original 200 native states through 20 microseconds, plus reconstructed
initial conditions. No solver was rerun. It uses the full cached native
four-point mass matrices, signed XYZ displacement/velocity fields, and signed
trapezoidal contact-force/moment integrals. Angular momentum is evaluated about
the same fixed reference point. The physical Gauss8 operator is not evaluated.

## Observations

| Quantity | Peak normalized residual | Existing comparison limit |
| --- | --- | --- |
| Core linear balance / P* | 2.24403e−8 | 1e−3 |
| Washer linear balance / P* | 2.46602e−8 | 1e−3 |
| Core angular balance / H* | 1.23679e−7 | 1e−3 |
| Washer angular balance / H* | 2.39230e−9 | 1e−3 |
| Assembly linear drift / P* | 1.48546e−8 | 1e−4 |
| Assembly angular drift / H* | 1.23927e−7 | 1e−4 |

Here P* = 0.000914115066945544 tonne·mm/s and
H* = 0.0522416760759378 tonne·mm²/s. Maximum native mass relative errors are
3.06638e−8 (core) and 5.78270e−8 (washer), versus 5e−6.
Maximum kinetic-energy discrepancies divided by the existing comparison scale
are 4.25493e−7 and 1.90244e−7, respectively, versus 5e−6. That scale includes
the original near-zero energy floor; these are not unqualified relative errors
at zero energy.

These checks found **zero additional threshold violations**, not a passing
verdict. The report always marks qualification false. The fixture consists of
two metal bodies at one local connection; it is not a full board, plywood joint,
climber-load case, floor-contact model or joint-capacity calculation.

## What remains unresolved

The [original audit](../fea/results/coarse_moving_control/README.md) rejected two
pressure rows. This diagnostic deliberately does not revalidate CDIS/CSTR/CELS
contact rows, contact completeness or traction consistency. Its parsed contact
resultants therefore remain unqualified. The
[native reader reproduction](contact-energy-output-investigation.md) also means
printed CELS cannot qualify total energy. No internal/contact/total-energy
balance, refinement agreement or resistance check is performed here.

A subsequent source review also found inconsistent work-array dimensions on
the quadratic surface-contact path in the pinned CalculiX 2.21 build
(`resultsmech.f:61,428–451` and `springforc_f2f.f:38–39`). The source files are
identified by the retained native build manifest. The effect on the optimized
binary's recorded results has **not** been measured; the proposed instrumented
reproduction was not completed after an assistant-tool safety interruption.
Do not treat the small residuals above as resolving that source concern.
Evaluate a supported solver release and independently qualify the applicable
contact path before relying on it for design demands; no corrected build has
yet been selected or validated.

The [official CalculiX site](https://www.calculix.de/) advertises version 2.23.
Its [release notes](https://www.dhondt.de/new_calc.htm) do not identify a CELS
indexing correction. A read-only comparison of the official 2.23 source with
the retained 2.21 sources still found the compact-index reader in
`printoutelem.f` and the `igauss`-based writer in `resultsmech.f`. Therefore an
upgrade is **not an established fix**. Any vendor-release evaluation must be
separate from the preserved 2.21 evidence and pass the same applicable numerical
qualification gates. No 2.23 solve was performed by this review.

Source: [official 2.23 archive](https://www.dhondt.de/ccx_2.23.src.tar.bz2),
1,551,289 bytes, SHA256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.

Recommendation: **do not alter the frame because of these numerical controls.**
The observations narrow the investigation: no extra momentum or native
kinetic-energy discrepancy was exposed, while unilateral-contact behavior and
contact-energy extraction still need resolution. Next qualify a writer-to-reader
energy path and contact behavior before selecting the refined moving comparison
and then the full joint-demand comparison. Continue connector/product and CAD
development separately; do not interpret this result as clearance to build.

## Reproducibility and limits

The selected replay completed in **168.524 seconds**, exit 0, with successful
owned-container cleanup and subsequent confirmation that the container was
absent. Bounds were 900/920 seconds, 8 GiB memory/memory-plus-swap, two CPUs,
no network and read-only repository/input mounts. The archive retains the
supervisor, its mocked tests, diagnostic source/tests, commands, terminal record,
all 201 derived states and their source/hash references. The original large
native files and failed audit remain in their existing immutable archives.

```sh
uv run pytest -q tests/test_moving_hardware_diagnostic.py
uv run pytest -q tests/test_moving_diagnostic_publication.py
```

The focused tests use synthetic fields; publication tests verify the retained
evidence and recompute arithmetic from its derived observables. Neither reruns
the DAT/full-mass-matrix reconstruction. The maintained diagnostic is
`fea/moving_hardware_diagnostic.py`; its
explicit CLI invocation is a computation, not a solver or an acceptance test.
