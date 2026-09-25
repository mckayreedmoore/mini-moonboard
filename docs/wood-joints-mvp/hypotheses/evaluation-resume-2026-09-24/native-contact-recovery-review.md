# CCX 2.21 face-to-face contact recovery

This review checks whether a longer unchanged run could reach a different
nonlinear recovery path after the ordinary transient checkpoint stopped at 34
iterations. It uses the official CalculiX 2.21 source extracted from the
archive with SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.

The current checkpoint reached iteration 34 at the requested increment
`0.0025 s`; its log has no face-to-face iteration-limit or contact-stiffness
reduction message. The deck contains no `*CONTROLS` card, so CCX defaults
apply. `ini_cal.c:323–324` sets `kscalemax=100` and `itf2f=60` (also
`controlss.f:93–94`). In `checkconvergence.c:725–795`, reaching
`iit==itf2f` requests a retry and sets `kscale` to 100. Thus a longer run of
the same deck could reach a qualitatively different retry once the increment
reaches iteration 60; iteration 34 did not test it.

On that first face-to-face fallback, the increment duration stays at
`0.0025 s`. The source applies the default cutback fraction only when
`mortar!=1` or `icutb!=0`; the initial face-to-face retry has `icutb==0`, so
that condition skips multiplying `dtheta` by `dc`. The default `dc` is 0.5
(`ini_cal.c:254`), and later fallback retries with a nonzero cutback count can
halve the increment. The branch prints that the increment size is decreased
even on the first face-to-face retry, although that particular source path
does not change it.

The reduction is a solver recovery aid, not an accepted softened-contact
state. `springstiff_f2f.f:180` divides the linear normal penalty stiffness by
`kscale` (the tangential stick slope is likewise scaled at line 274). If the
iteration test reports convergence while `kscale>1`,
`checkconvergence.c:180–187` restores `kscale=1`, clears the convergence flag,
and continues iteration. Any accepted increment therefore has to converge
again at the original contact stiffness; the `kscale=100` result alone cannot
be treated as converged.

An unchanged rerun with more wall time could expose this fallback, but must be
allowed to continue through restored-stiffness convergence. It is not a
guaranteed recovery, and this source review does not justify changing the
contact model or loosening convergence criteria. Given the checkpoint's 34
iterations in roughly ten minutes, reaching iteration 60 alone would require
substantial additional runtime, with the softened retry and restored-stiffness
iterations beyond that. Pair-level contact diagnostics remain useful before
spending that runtime.

Source archive provenance: [CalculiX 2.21 source archive](http://www.dhondt.de/ccx_2.21.src.tar.bz2), SHA-256 `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`. The archive and extracted source tree used for this review are not included in this repository.
