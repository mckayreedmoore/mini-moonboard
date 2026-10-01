# Energy-method review — 2026-09-27

This is a post-run, read-only method note. It records the work/energy audit gap
and a bounded known-answer route; it does not alter the frozen full-step coupon,
accept an energy channel, choose the missing work floor, or authorize another
native run.

## Attempt09 work contract

The [attempt09 contract](../ordinary-port-motion-attempt09-common-map/README.md#L62)
defines incremental prescribed-boundary work as
`Σ 0.5*(Q_i + Q_i+1)·(q_i+1 − q_i)`, compares it to the change in reported
elastic plus frictionless-contact energy, and sets a 5% relative difference.
It specifies the absolute work floor only as “from the same unit-wrench scale”
([lines 67–72](../ordinary-port-motion-attempt09-common-map/README.md#L67)); no
number is frozen there. The [static-schedule proposal](static-schedule-proposal.md#L73)
correctly requires resolving that floor before any launch. This review does not
select or infer the floor.

Attempt09's output requests already show the intended candidate fields:
`ELSE,ELKE,EMAS,EVOL` and `CDIS,CSTR,CELS,CNUM` in
[`response_rt_minus.inp`](../ordinary-port-motion-attempt09-common-map/response_rt_minus.inp#L181).
That syntax is a request, not validation that `CELS` represents stored MORTAR
contact energy.

## Pinned 2.23 source evidence

The audited source is the official 2.23 archive
[`source.tar.bz2`](../ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2),
SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The [source-manifest verification](../ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source-manifest-verification.json)
records all 1,197 members matched. Full source-member hashes below are over the
archive member bytes after removing the archive's leading `./` path component.

| Pinned source member and relevant lines | SHA-256 | Finding |
| --- | --- | --- |
| `contactpairs.f:115–118` | `e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488` | `TYPE=SURFACETOSURFACE` sets `mortar=1`; `TYPE=MORTAR` sets `mortar=2`. |
| `getcontactparams.f:73–79` | `03384b3d55deb22010f19a4521f3b10380caaf16441d270bf35f886ec0aadbaa` | Linear pressure-overclosure regularization uses `regmode=1` and `fkninv=1/K`. |
| `resultsmech.f:423–441` | `15fccc9fb553f259af5d33bc78e8d3808f1f9f338ee266ce92192bae33026fa6` | Contact spring energy is assigned in the `mortar.eq.1` face-to-face branch; the audited routine has no corresponding `mortar.eq.2` assignment. |
| `printout.f:426–438,477–505` | `ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32` | CELS is labelled “contact spring energy”; its print branches and traversal cover `mortar.eq.0` and `.eq.1`, not `.eq.2`. |
| `noelfiles.f:595–599` | `ed85b45d6987882e484f11a0be3dc9c2d716afba07d59483d364e0709107a59f` | Parsing `CELS` sets the output flag and `nener=1`; that alone does not establish MORTAR values. |
| `springforc_f2f.f:186–201` | `3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4` | For linear face-to-face overclosure the stored spring term is `−stiff*clear/2`; this supports the penalty coupon oracle only. |
| `calcenergy.f:189–196` | `5f705ac94653c9a80b492fa9d1424c57ac04263f1b4bce260310b296c0b01a9e` | Generated contact-element energy is read from `ener`; this does not by itself establish a MORTAR 2.23 energy producer. |
| `results.c:397–405` | `9113a4984342355ff15bb16a609c5bdb034183c951719b064037b3858eac24dd` | The audited global energy calculation is guarded for dynamic method `nmethod==4`; it is not an audited static MORTAR energy route. |

Together these source paths do not establish a standard stored-energy `CELS`
channel for `TYPE=MORTAR` in pinned 2.23. They do not show that physical
frictionless contact energy is zero. Any MORTAR energy quantity used by the
work gate needs an independently validated output or integration method; the
penalty `CELS` result cannot be transferred to MORTAR.

## Bounded known-answer route (proposal, not acceptance)

Reuse the existing two-body C3D10 coupon and its matched penalty/MORTAR inputs
as the method fixture; request per-body element strain energy (`ELSE`) and
contact spring energy (`CELS`) as output-only additions. Preserve the mechanics,
loading, existing U/RF/SOF/stress-style gates, and trace checks. Assess the
energy channel separately from those mechanical gates: a missing or unsupported
MORTAR CELS result is “unavailable/unvalidated,” never a zero-energy pass.

The fixture gives a dimensional analytical reference. Each body has
`E=100,000 N/mm²`, area `A=4 mm²`, and thickness `L=2 mm`; the compression
endpoint shortens each body by `0.002 mm` under the frozen linear `400 N`
reference. Thus each body has
`0.5*(EA/L)*δ² = 0.4 N·mm`, and the pair has `0.8 N·mm` bulk energy. At
`K=100,000 N/mm³` and interface overclosure `g=0.001 mm`, the linear normal-law
contact energy is `0.5*K*A*g² = 0.2 N·mm`. The reference total is therefore
`1.0 N·mm`; in the open and reopened `+0.001 mm` states the expected bulk and
contact energies are zero. These are linear analytical reference values: the
existing full-step fixture records the nonlinear endpoint near `399.5199 N`,
so any output tolerance must be declared against the fixture's nonlinear
approximation and discrete output before a separate freeze. This note does not
set that tolerance or claim observed energies.

For penalty, compare observed `ELSE` per body and `CELS` against those analytical
components. For MORTAR, first determine whether the requested output exists and
matches the independently computed contact-law integral; otherwise keep its
contact-energy channel unavailable. Do not infer contact energy solely as a
work-balance residual, since that would make the work/energy acceptance check
circular. This coupon route validates only the small method fixture, not joint
response or acceptance.

The work-floor issue remains separate: attempt09's path has `0.1 mm` prescribed
increments, so its unit-force increment work scale is `1 N * 0.1 mm =
0.1 N·mm`; the prior `1,000 N·mm` moment diagnostic scale does not define work
on a zero-rotation path. Parent must state the work floor explicitly in any
future reviewed contract. This note does not extend the coupon schedule to add
touch states or claim that its existing opening/compression endpoints validate
pathwise trapezoidal work.

## Parent clarification of endpoint work quadrature

The existing top motion goes from `+0.001 mm` with zero force to `−0.005 mm`
with the linear reference force `400 N`. Endpoint-only trapezoidal work is
`0.5 * 400 N * 0.006 mm = 1.2 N·mm`, whereas the independently derived stored
energy is `1.0 N·mm`. The difference is caused by applying a single trapezoid
across the initial open gap; it is not evidence of contact-energy loss.
A separate work-method fixture could include the exact zero-force touch state
at displacement zero, giving touch-to-compression work
`0.5 * 400 N * 0.005 mm = 1.0 N·mm` and the negative value on reversal.
That is a proposed later fixture, not a change to the output-only energy packet
or the existing frozen schedule. The current coupon endpoints cannot validate
a 5% pathwise work gate by themselves.

## Acceptance boundary and current branch status

The missing MORTAR stored contact-energy validation blocks attempt09's proposed
5% work/energy consistency gate and broader response characterization. By
itself, it does not invalidate an independently converged static equilibrium or
independently validated force/moment actions. The [static-schedule proposal](static-schedule-proposal.md#L84)
separates the action-output validation requirement from work/energy.

The separate [shared-edge attempt02 result](../contact-mortar-shared-edge-known-answer-attempt02/RESULTS.md#L3)
reports that its first `shared_slave_mortar` case reached 201 CVG iterations,
ended with native exit 201, and accepted no state; the other three cases did not
run. That unresolved method failure is independent of the source-based energy
finding here. This energy note neither explains that failure nor authorizes a
follow-on native run.
