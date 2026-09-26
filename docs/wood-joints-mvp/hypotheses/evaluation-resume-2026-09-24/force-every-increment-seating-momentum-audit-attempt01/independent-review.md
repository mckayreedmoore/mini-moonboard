# Independent review: bounded momentum audit

The frozen postprocessor and result are internally consistent for their stated
scope: the global assembly and the bottom-center-right cleat over the accepted
`.019 → .020 s` interval. All three components pass the reported output
rounding and time-token bounds under both mass operators. This is linear
momentum bookkeeping for two states, not a joint acceptance result.

The successful execution record pins `audit.py`
(`3771729a6e032a49b594ed922d8864241003bb045b9aa962fcc853a5b9474760`), the
six-test file (`5ba510900d93e8591d810fe0597cd3ab1fa59821be3c89b7b0369f1849d1a238`),
and `momentum-audit.json`
(`b04030fda49f15d7fc7df3e6ade8265caa69f94386667311e6c3354b06aef5a4`). The
execution record itself is
`de7e9fa76897146daf5f3acde03a21e0404a3dc954a004d7cfd401ffd6ff87e4`. It records
the bounded one-CPU postprocess, no native solver run, and
`mechanical_acceptance: false`. The earlier failed preflight remains separately
identified as unauthenticated and is not the producer run for this result.

I independently read the pinned current input deck and manifest. The actual
`*CLOAD,AMPLITUDE=RAMP_N` has 662 terms over 331 nodes; its 101-point table is
piecewise linear in the solver, with amplitudes `.094582` and `.104000` at the
two accepted endpoints. The interval integral is `.000099291 s`. The cleat
force resultant at unit amplitude is `(0, -76.6044443, 64.2787610) N`; the
principal receives the equal-and-opposite vector and the global resultant is
within `1.75e-13 N` of zero. These source-derived resultants reproduce the
reported applied impulses.

The manifest assigns ten and only ten direct contact interfaces to this cleat:
indices 1, 2, 5, 9, 13, 17, 20, 22, 24, and 26. I parsed their raw DAT `CF`
vectors at both endpoints and applied the owner-side sign (`CF` on slave,
negated when the cleat is master). Each required interface has all three
`CF`/`CFN`/`CFS` reports at both states. The resulting cleat forces are
`(-.477808, .073833, .088726) N` at `.019 s` and
`(-.812605, 39.125100, -33.148849) N` at `.020 s`, matching the audit. `CFN`
and `CFS` are not added. At `.020 s`, pair 034 is partial and pair 035 is
missing; neither is incident to the cleat. The report preserves these states
as partial/missing and does not use them as zero-valued evidence.

The two independently assembled mass operators give `11.7756010 kg` globally
and `.558187221 kg` for the cleat; CalculiX 2.21 four-point reconstruction and
physical Gauss8 consistent mass differ by about `1.11e-9` and `2.49e-10`
relative, respectively. The positive-mass scope is the three wood bodies and
twelve steel bodies; zero-density display carriers and massless controls are
excluded. FRD velocity bounds use the pinned helper’s source-derived
binary32-cast and decimal-print quantization. Each endpoint time bound combines
STA, FRD, and DAT token half-quantums to `1.05e-7 s`; the contact impulse uses
these combined endpoint bounds and includes the second-order `qdt*qF` term.
Its componentwise time/CF print bounds are
`(1.41e-7, 4.12e-6, 3.47e-6) N·s`.

The largest global residual is `1.36e-8 N·s`, below the smallest corresponding
global component bound (`4.53e-7 N·s`). The largest cleat residual is
`2.25e-9 N·s`, below the smallest corresponding cleat component bound
(`1.72e-7 N·s`). All 12 component checks pass. The focused tests also pass
(`6 passed`), including reversed owner-side signs, incomplete incident-pair
rejection, the nonincident 034/035 exception, and the second-order impulse
bound.

The contact impulse is a trapezoid between two accepted endpoints. The bounds
cover printed-value and time-token representation only; they do not cover
between-increment contact-force variation, solver equilibrium residual, or
solver arithmetic. The snapshot is a non-atomic live-output prefix and only
the pinned `.019` and `.020 s` rows were used. No other owner balance, angular
momentum, stiffness, capacity, or contact qualification is established.
