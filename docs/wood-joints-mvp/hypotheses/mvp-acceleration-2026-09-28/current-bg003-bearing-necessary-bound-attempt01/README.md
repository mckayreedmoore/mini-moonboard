# BG003 necessary bearing bounds

This calculation supplies minimum projected bearing peaks required by the
three receivers' stored force and first moment. It uses all seven increments
of both BG003 bolts in each of the three authenticated rear cases: 126
receiver states. It needs no timber stiffness, bolt modulus, gap homotopy or
assumption that the two shear planes act independently.

Consider any signed transverse line traction p(s) over a modeled receiver
length L, with s measured from its midpoint. For a unit transverse direction,
let F be its integrated force and J its integrated first moment. If
|p(s)| ≤ P, the largest possible |J| at a given F is

```text
|J| ≤ P L²/4 − F²/(4P),  with |F| ≤ P L.
P ≥ (2|J| + sqrt(4J² + L²F²))/L².
```

The maximizing scalar field switches between opposing flanks: +P on one
side of a switch station and -P on the other. This follows by filling the
largest positive moment arms first while retaining the prescribed integral
force. Uniform and sign-reversing fields are independently integrated in
the producer's known-answer checks. A vector field with magnitude bounded by
P must obey this scalar inequality in every direction. We evaluate 180 unit
directions plus the source force and first-moment directions; each reported
winning projection is a valid necessary certificate. This finite set is not
a proof of the sharp biaxial optimum or deformation compatibility.

The source receiver midpoint wrenches give F=[Fy,Fz] and J=[Mz,-My]. The
bearing traction balances their negatives; reversing both signs leaves the
bound unchanged. The modeled intervals are 38.1 mm for the spine and 88.9 mm
for the side member and inner block. Dividing P by the modeled 6.35 mm bolt
diameter gives a projected bearing-pressure bound, consistent with the
usual force/(diameter × engagement length) measure. Full interval engagement
and bore-only transverse transfer are explicit idealizations.

| Receiver | Largest necessary projected peak (MPa) | Controlling stored case / bolt | Force-only average at that state (MPa) |
| --- | ---: | --- | ---: |
| Spine | 4.8292 | A12 rear, bolt 1, full load | 2.0003 |
| Side member | 1.9855 | A12 rear, bolt 1, full load | 0.9520 |
| Inner block | 0.4385 | A1 rear, bolt 1, full load | 0.1816 |

These are **lower bounds on required projected peaks**, not upper bounds on
actual demand, allowable bearing values or capacity ratios. A capacity below
an applicable necessary bound would be incompatible with that source wrench
and idealized transfer mechanism. A capacity above it would not establish a
pass: actual concentration, grain-dependent engagement, contact compatibility,
steel bending, shared two-bolt timber, splitting and axial/thread/washer
transfer still matter. Face-contact compression values such as Fc⊥ are not
automatically bolt embedment strengths and must not be compared interchangeably.

The source input and all three case reports are hash-checked on every replay.
The calculation uses their stored rounded wrench centers, with no propagation
of native-output uncertainty; it therefore remains conditional on those
numerical values and modeled geometry. It does not rate actual stock or
hardware and makes no geometry, native-run or construction change.

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-bearing-necessary-bound-attempt01/produce.py --verify
```

See [bounds.json](bounds.json) for every signed input and its projection
certificate. The next resistance comparison needs an applicable directional
embedment basis and complete-joint treatment, rather than another arbitrary
foundation stiffness.
