# CCX 2.23 MORTAR source screen

Pinned source: [official 2.23 archive](https://www.dhondt.de/ccx_2.23.src.tar.bz2),
SHA256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The paths below are within `CalculiX/ccx_2.23/src/`.

- `contactpairs.f:62-66` initializes the no-clearance sentinel;
  `clearances.f:90-96` changes it only for an explicit clearance.
- `slavintmortar.f:90-93` reads that value and unconditionally sets
  `shrink=.true.`. In `treatmasterface_mortar.f:195-225`, `spm` is the
  projected signed gap. The initial-geometry correction at lines 206-221
  runs only for a non-sentinel clearance; it is not a general gap rule.
  Lines 222-224 then multiply `spm` by `reltime`.
- `contactmortar.c:235-241` passes `reltime`. In `nonlingeo.c:856-873`,
  `theta` resets at step entry; lines 1607-1612 report the step-local elapsed
  fraction; lines 1634-1638 set `reltime=theta+dtheta`, with
  `dtheta=tinc/tper`.

The original open-to-compression deck uses 0.1 increments in 1.0 steps
([input](input/mortar_c3d10.inp), lines 122-139). The source therefore scales
the projected gap by 0.1 at the first increment of a step. For its +0.001 mm
step-boundary gap and -0.0006 mm first boundary change, the source path is
consistent with a candidate 0.0005 mm closure and the observed 39.9952 N
reaction. This is an inference from the source, schedule, and recorded output,
not an isolated causal proof or a general MORTAR defect claim. The manual says
MORTAR satisfies the pressure-penetration relation weakly (§6.7.8, pp. 248-249),
so an averaged positive gap alone does not establish that every integration point is
open. Here the independent nodal audit also finds all nine matching interface
gaps equal to +0.000800012 mm at time 1.1; the failure is therefore supported
by the uniform nodal geometry and support reactions, independently of contact-field
sign conventions. See the [official 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf).

No input-controlled switch to disable this scaling appears in the pinned path.
An input-only discriminator is one fixed full-step increment: the manual's
`*STATIC,DIRECT` holds the increment fixed; `1.,1.` in a 1.0 step gives
`reltime=1` if it converges. That tests partial-step scaling; it does not turn
off `shrink` and may fail without automatic subdivision. The subsequent
monotonic result from both formulations also means this source finding alone
does not explain the shared intermediate mismatch. Upstream
[issue #162](https://github.com/Dhondtguido/CalculiX/issues/162) concerns
another unit-scale-dependent convergence case and is not diagnostic for this
force transient. The GitHub path-history endpoint was unavailable in this
lookup; this note makes no claim about later fixes.
