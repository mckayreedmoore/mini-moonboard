# Mortar gap history source screen

## Finding

The pinned CalculiX 2.23 source contains a strong candidate mechanism for the
MORTAR coupon's force while its faces are geometrically open. It scales the
current projected gap by the current step-time fraction before assembling the
dual gap. In the coupon's second step, the first accepted increment has step
time fraction 0.1. The preceding open state has a +0.001 mm interface gap, so
the source scales its projected integration-point gap to about +0.0001 mm
before dual-gap assembly.

This confirms the code path and its timing, not the complete cause of the
40 N force at total time 1.1 or the 448.44 N compression peak. No instrumented
native run has exposed the integration gaps, assembled dual gaps, and corrected
gaps needed to close that force balance. Keep the known-answer failure and all
acceptance gates unchanged.

## Conditional gap path

The coupon has no `*CLEARANCE` card. `contactpairs.f:64–66` initializes
`tietol(3)` to the no-clearance sentinel `1.2357111317`; `clearances.f:96`
replaces it only when a clearance card is read. In
`treatmasterface_mortar.f:206–221`, the baseline-gap subtraction and clearance
addition run only when the value is outside the sentinel interval
`(1.2357111316, 1.2357111318)`. Thus this coupon skips that baseline correction.
The path computes the current projected gap at lines 197–204, then at lines
222–225 applies `spm=reltime*spm` and stores it in `gapmints`.

`slavintmortar.f:90–93` unconditionally sets `shrink=.true.`. Its six-node
triangular master-face branch passes `shrink` and `reltime` to
`treatmasterface_mortar.f` (lines 430–651). In `nonlingeo.c:1634–1638`,
`reltime=theta+dtheta` is the end fraction of the current step; the accepted
`.sta` record for step 2, increment 1 reports a 0.1 step fraction. The source
sequence is therefore sensitive to step history and the current increment's
fraction, rather than only to the physical endpoint geometry.

`contactmortar.c:118–125` performs its geometry/segmentation update at the
first iteration of each increment. `bdfill.c:139–140,207–213` resets and then
assembles the dual nodal gap from integration-point contributions. In
`stressmortar.c:341–342,578–580`, the normal displacement increment is formed
and subtracted from that gap. These sites establish the ordering, but the
retained coupon output does not expose those internal values.

## Small discriminator

The one-step monotonic packet from initially touching geometry also fails the
frozen oracle: both MORTAR and surface-to-surface penalty first fail at step
time 0.2. The recorded force magnitudes are 39.9952 N for both at 0.1, then
67.188 N (MORTAR) and 72.87379 N (penalty) at 0.2 versus the 80 N reference.
At 0.5 they are 158.032 N and 150.88817 N versus 200 N. At the endpoint,
MORTAR is 441.009 N versus 400 N; penalty is 399.5199 N. All ten increments
were accepted. These records show opening/reversal is not necessary for the
intermediate-force mismatch, but they do not prove which source path causes it.

Penalty contact has a separate clearance adjustment. In the static branch,
`gencontelem_f2f.f:562–585` labels its contact detection algorithm as
“more sophisticated.” At `iit<=0`, when the step is 1 or the tie tolerance is
positive, a negative current projected clearance sets
`springarea(2)=clear/(1-theta)` (:570–577); the old `iinc==1` guard is commented
out (:574–580). It then uses `clear=clear-springarea(2)*(1-reltime)` (:585).
`springstiff_f2f.f:147–152` applies the same adjusted clearance for static
contact. This source records a clearance/ramp rule, not evidence of a solver
bug. It can run at the start of each qualifying increment when the current
state is overclosed. Penalty and MORTAR therefore have distinct source paths
that both depend on step fraction; the penalty correction is zero at
`reltime=1`, consistent with its matching endpoint here.

A possible path-sensitivity discriminator is the same ten displacement
endpoints applied as ten `*STATIC` steps with one full increment per step.
The parent first prepares the smaller original three endpoint sequence
(open, compress, reopen), each with `*STATIC,DIRECT` and a single full increment.
It exercises opening/contact/reopening at step endpoints only; it does not
reproduce or validate the ten-state monotonic path.
`nonlingeo.c:859–872,1634–1638` resets `theta` for a new step and computes
`reltime=theta+dtheta`; the one-increment endpoint has `reltime=1`. That makes
the explicit `reltime*spm` MORTAR scaling a no-op and the penalty
`(1-reltime)` correction zero at each accepted state. The step-count change also
changes step-gated logic, so a changed result would identify dependence on
step-fraction/step handling as a group, not isolate one coefficient. This is
only a discriminator. Keep the frozen oracle and every acceptance gate
unchanged.

## Evidence identities

Source archive: [pinned archive][source-archive] and extracted copy
`/tmp/ccx_2.23.src.tar.bz2`, SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The files below are from its `CalculiX/ccx_2.23/src/` tree.

| Source file | SHA-256 |
| --- | --- |
| `nonlingeo.c` | `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f` |
| `contactpairs.f` | `e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488` |
| `clearances.f` | `dc5a8fecd824c5e6f539f445027bc395e36744bb865b70ef8917a2dd0c0e65de` |
| `slavintmortar.f` | `a993c9a84202b7ce642073e52994269697eb487afbc51c86ff61c303b4f6e808` |
| `treatmasterface_mortar.f` | `045dd09aea90d5dd92e03c299b76da72069ccb657b961c9818d1dc052d31e48b` |
| `contactmortar.c` | `67ef7ea5f3353eb1d5a009ebce289b22b0c8e0f8542c038a30392c676186f001` |
| `bdfill.c` | `135e13339b2d3e4688cc8a86b3b9044f24ef10626a72850b6714a71ffdbc6c8a` |
| `stressmortar.c` | `c62c65de7aba91260320a3c548ebc513a436e4243151ca0441dcc5d309dce621` |
| `gencontelem_f2f.f` | `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe` |
| `springstiff_f2f.f` | `bfa17fa023dc806f3c0776a965c72497590edb72cdfbc48f67ee16ed3d75da2a` |

The original retained result is in [RESULTS.md](RESULTS.md). The monotonic
packet's [execution record][monotonic-execution] and [failed audit][monotonic-audit]
record the later discriminator. No input, binary, native output, or verifier
was changed for this source screen.

[source-archive]:
  ../ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2
[monotonic-execution]: ../contact-mortar-c3d10-monotonic-attempt01/execution.json
[monotonic-audit]: ../contact-mortar-c3d10-monotonic-attempt01/verifier.json
