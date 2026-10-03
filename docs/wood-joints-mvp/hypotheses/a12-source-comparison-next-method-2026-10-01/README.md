# A12 row 1586 next-method discriminator

This is an additive, arithmetic-only check after the reviewed endpoint recovery.
The retained result is **method pass / native RF miss**: both owning-body
elastic quotient screens passed, while the unchanged raw-H comparison remains
stopped with 27 source force-interval failures. Row 1586 is still outside its
native RF interval by `8.90334638e-8 N` at the recovered table force; no force
or interval is adopted or changed.

The compared values come from distinct operators and states:

| Path | Operator/state | Row 1586 quantity |
| --- | --- | --- |
| Pure-solid export | The unloaded physical-body `K` from the authenticated `.sti`, 37,647 DOFs; connectors and contact are absent. | Input for both the compliance reduction and the later two-body endpoint recovery. |
| Raw-H branch | The fixed 734-bound reduced connector system uses the unsymmetrized `H` from compliance attempt04, the original `D/e/W` and fixed active rows. This is a linear scalar-projection state, not a nonlinear native equilibrium. | Raw-H force `0.00363391098709315 N`; its scalar spring-law value is `0.00363391034036805 N`. |
| Recovered endpoint state | The two target body blocks of the same serialized pure-solid `K`, with the unmodified raw-H body loads and saved rigid coordinates; the emitted MPCs then recover SPRINGA endpoints. | Body-load projection `B*u = 9.140036990846884e-7 mm`; emitted-endpoint linear projection `q_emit = 9.14003697060809e-7 mm`; exact emitted-endpoint `dd-dd0 = 9.14003706498079e-7 mm`; table force `0.00363391036978350 N`. |
| Native state | The separately saved nonlinear CalculiX A12 state with emitted springs, MPCs and contact; the RF center is the native endpoint internal force projected onto the emitted axis. | RF center `0.00363382063190370 N`, unchanged interval `[0.00363381992748767, 0.00363382133631972] N`. |

The recovered table force differs from raw-H force by `6.17309650e-10 N`, but
it remains `8.90334638e-8 N` above the RF interval. In the recovered state,
the body-load projection `B*u` differs from emitted-endpoint projection
`q_emit` by `2.02387945e-15 mm`, equivalent to `8.0466e-12 N` at the emitted
table slope. The table force exceeds the force from that emitted linear
projection by `3.7521e-11 N`; relative to the body-load `B*u` projection the
finite-endpoint-geometry delta is `2.9474e-11 N`. These are distinct recorded
quantities. In the separate native state, the geometric table force
exceeds the native linear projection force by `1.58278824e-5 N`; that is a
different state and operator comparison, not a correction to raw-H. The
emitted table slope `3975.8157914987996 N/mm` differs from the projection
contract stiffness `3975.8157914988024 N/mm` by `-2.7285e-12 N/mm`, an effect
of about `2.5e-18 N` at this recovered body-load `B*u`.

The observed numerical residuals also separate cleanly from a forward-error
claim. The raw-H bordered solve had a minimum/maximum singular-value ratio of
`1.08523e-7` and relative linear residual `1.01479e-17`. Compliance attempt04
reported maximum reciprocity error `9.3832e-11` and maximum body-chunk nodal
relative residual `9.2617e-11`. The two recovered bodies then passed their
quotient checks with KKT relative residuals `2.94e-15` and `4.37e-14`, and
original-K force residuals `6.18e-13 N` and `1.50e-11 N`. Those are measured
backward/operator diagnostics; none maps to a rowwise force uncertainty.

The pinned CalculiX 2.23 source makes two precision facts observable. In
`springforc_n2f.f`, the endpoint operation is `pl=xl+vl`, then `dd0`, `dd`,
and `val=dd-dd0`; `calcspringforc.f` computes the table slope and force from
the displacement/force pairs. In `matrixstorage.c`, the upper-triangle
physical solid matrix is written as one-based indices plus `%20.13e` per
double, or 14 significant decimal digits. The pure-solid assessment records
the `.sti` SHA-256 as
`7d22d2b013fcdc9fddfeab589b456615f0671db989a034e091bac855f3a93c01`, with
2,320,506 stored upper pairs and 4,601,263 reconstructed symmetric
nonzeros. The two reduced methods share this serialized operator; the native
nonlinear response uses its own assembled solve. No pre-format matrix values
or rowwise response bound to `.sti` quantization are retained here. Export
rounding or conditioning amplification is therefore possible but unmeasured,
not an evidenced explanation.

The smallest bounded discriminator supported by these records is the saved
row arithmetic replay in [audit_saved_row_arithmetic.py](audit_saved_row_arithmetic.py).
It checks source order against a high-precision rationalized length difference
from the same recovered binary64 endpoint coordinates, and validates the new
identity on a separate synthetic known answer. The replay takes about
`0.57 s`; it reads pinned reports, the deck and selected CalculiX source
members. It does not read `.sti`, parse stiffness triplets, reconstruct a
body, factor, solve a state or run native CalculiX. Expected result:

- The Python binary64 mirror of the pinned source order reproduces
  `0.0036339103697834957 N`.
- High-precision arithmetic on the same rounded endpoints gives
  `0.0036339103661339461 N`, a shift of `-3.65e-12 N`.
- The half-ULP scale from the two final near-equal computed lengths is
  `5.65e-11 N`, about 1,576 times smaller than the `8.90e-8 N` interval miss.
  This scale excludes coordinate-addition, norm-input arithmetic and state
  forward error, so it is not an end-to-end force error bound.
- The original RF miss and all 27 raw-H interval failures remain.

This discriminator checks only endpoint norm/subtraction arithmetic for the
saved recovered coordinates. It does not bound the displacement-to-position
addition, source-K forward error, effect of `.sti` serialization, or difference
between the reduced and native states. No further causal discriminator is
supported by the present records without an unrounded assembled operator or
a rowwise perturbation bound. The raw-H stop remains in force.

Reproduce the check with:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/a12-source-comparison-next-method-2026-10-01/audit_saved_row_arithmetic.py \
  --report /tmp/mini-moonboard-a12-saved-arithmetic-replay.json
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/a12-source-comparison-next-method-2026-10-01/audit_saved_row_arithmetic.py
```

The explicit `/tmp` report path preserves the retained `arithmetic-result.json`.
`elapsed_seconds` varies between replays; compare the replay to the retained
receipt after removing that field. `output-pin.json` binds this packet's code,
retained result and source receipts.

Pinned source evidence includes parent result `79b97a8191bcbdc5d9cbc3a806998fcdc741283717d9c3922b2330bd102bc908`, endpoint result `560352a02ab4e01291f1c0d73db5f9001a71a38d8f9c3212962fb0cd586432b3`, raw-H diagnostic `7542ce827f79bcdfe93c018e6b6f869f6435e8190a5ca0d5d492158961412658`, projection contract `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3`, and native emitted deck `e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff`. The pinned source archive SHA-256 is `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the checker verifies the exact writer and SPRINGA source-member hashes.
