# Dynamic contact-point known-answer verifier

This packet adds an offline output auditor for the prepared, prescribed-motion
C3D10 contact coupon. It does not run CalculiX. The parent fixture binds the
input, source archive and members, diagnostic patch, trace format, and separate
geometry-only audit by SHA-256 before any capture is audited.

Run the synthetic preflight with:

```sh
python3 verifier.py --self-test
```

To audit an already captured native output directory, use
`python3 verifier.py --audit-dir PATH`. The directory must contain
`solver.stdout`, `coupon.frd`, `coupon.sta`, `coupon.cvg`, and `coupon.dat`.
The verifier requires 50 accepted 0.1 s increments, matching convergence and
CVG identities, all 58 displacement records in each FRD state, complete
CVG/TRIAL contact-element counts, final MAP-to-state gap coverage, and a
positive-gap active corrected TRIAL checked against observed area and time.
Zero-contact CVG identities legitimately have no TRIAL records.

The energy and force fields remain narrowly interpreted: pressure, area, and
master normal are emitted; the normal resultant is derived as `p*A*n_master`.
The patch emits neither `fnl` nor `CFN`. Trial energy is valid only when
`energy_enabled=1`, and the frozen fixture requires `kscale=1`. DAT CELS is
reported as secondary output. Passing this coupon does not accept a joint,
equilibrium, physical transient, reaction force, inertia, external work, or
wood-joint method.
