# CCX 2.21 restart continuation review

This is a source-bound review of the current transient checkpoint deck, not a
continuation deck or a solver result. The reviewed
[`pilot.inp`](ordinary-transient-checkpoint-attempt01/pilot.inp) is SHA-256
`b5b7268e27d4f8a78c8035b935bc086271be836d5c6b18b7df149b930e176924`; its
freeze is `3bf365efa368dadf3e9c7c90b5ddd585e1622427bdffcf4c52b8d24c968d8fd2`.
It requests a single `0.0025 s` NLGEOM implicit-dynamic step and
`*RESTART,WRITE,FREQUENCY=1`. The parent reports that this run terminated on
timeout while still unconverged, and no `.rout` exists. There is no usable
step-end checkpoint to continue from; contact diagnosis must come first.

The pinned CalculiX source archive is CCX 2.21, SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`. The
matching manual is §7.110, pp. 573–574, and §7.1, pp. 397–398. The manual
requires `*RESTART,READ` as the first non-comment line of a continuation input.
It reads the last stored step by default. The source reads the selected binary
`.rin` record in `restarts.f:84–129` and `restartread.f`; for a different continuation
job name, the `.rout` must be copied or renamed to that job's `.rin` name. The
writer is called after a step returns from the solver (`ccx_2.21.c`), so a
converged increment within a step is not itself a restart point.

For a completed checkpoint, the restart record carries the mesh, constraints,
loads and amplitudes, current nodal fields, material integration-point state,
energy variables, and mortar-contact state. Specifically, `restartwrite.f`
and `restartread.f` store/restore `vold`, dynamic `veold`, `sti`, `eme`,
`xstate`, `ener`, and (for mortar contact) `islavsurf`, `pslavsurf`, and
`clearini` (`restartwrite.f:404–481`, `restartread.f:390–467`). The force records and their amplitude references (`xforc`,
`xforcold`, `iamforc`) and the tabular amplitude are also stored, as is the
accumulated `ttime`.

There is one important state distinction. The step driver documents `veold`
as the first time derivative and `accold` as the second derivative. The
restart format stores `veold` but has no `accold` field. For this NLGEOM
dynamic procedure, CCX frees `accold` at step return and allocates it with
`NNEW` (zero-initialized) when the next dynamic step begins
(`ccx_2.21.c:1824`, `ccx_2.21step.c:1210–1220`). Thus a restarted next step does not preserve
the prior acceleration. This is also the ordinary CCX behavior at a
non-restarted NLGEOM dynamic step boundary. A restart continuation must
therefore be compared with an uninterrupted **two-step** control using the
same `0.0025 + 0.0225 s` step split. It is not a strict same-step Newmark
continuation and must not be presented as equivalent to one uninterrupted
`0.025 s` step without evidence.

The global-time ramp itself can continue across that boundary. The frozen deck
defines `RAMP_N` with `TIME=TOTAL TIME` and applies its stored CLOAD pattern
through that amplitude. CCX stores total-time amplitude IDs as negative and
retains those IDs at the next step; step-time amplitudes are detached at a step
transition (`amplitudes.f:57–73`, `ccx_2.21.c:1738–1753`). With no `TIME RESET`, the manual
defines total time as the time accumulated before the new step plus its local
time. The local step clock restarts at zero, while the total-time amplitude
does not. The existing ramp factor is `0.001915` at total time `0.0025 s`
and `0.15625` at `0.025 s`. Do not restart the table at zero or add a second
copy of the stored CLOADs.

CCX also resets its nonlinear-dynamic work reference at each solver-step
entry: `nonlingeo.c:168` initializes `allwk` to zero and `nonlingeo.c:1454`
takes `energyref` from the starting state. Integration-point energy state is carried, but continuation
log work and balance are step-local; compare their changes from the checkpoint
state rather than expecting a cumulative work total. Contact state variables
are serialized, but the continuation re-enters nonlinear/contact solution, so
the prior Newton active-set iteration is not a continuation invariant.

If a successful `.rout` later becomes available and the parent elects to test
the route, the minimal new input shape is:

```text
*RESTART,READ
*STEP,NLGEOM,INC=250
*DYNAMIC,ALPHA=0
<initial increment>,2.25e-2,1e-6,2.5e-3
...step-level output requests...
*END STEP
```

Use a new job name and a byte-preserving copy of the exact `.rout` as its
`.rin`; omit the mesh/material/contact includes, duplicate CLOADs, and a new
amplitude definition because those are already in the restart state. Keep the
same solver image. The continuation should then be checked against a
same-mesh, same-load, same-two-step no-restart control: total time and ramp
force at the seam; nodal displacement and velocity; contact status/tractions
and energy; and step-local work and energy balance. This is a method-equivalence
check only, not a joint acceptance result. No continuation input was prepared
or run for this review.

Source paths inspected under `/tmp/ccx221-source/CalculiX/ccx_2.21/src/`:
`restarts.f`, `restartwrite.f`, `restartread.f`, `ccx_2.21.c`,
`ccx_2.21step.c`, `amplitudes.f`, and `nonlingeo.c`. Extracted manual text
SHA-256: `118fc7e79e1961b713e4cd3c7cf653cf15f92b137b476ad4db3e47e405883f39`.

Source archive provenance: [CalculiX 2.21 source archive](http://www.dhondt.de/ccx_2.21.src.tar.bz2), SHA-256 `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`. The archive and extracted source tree used for this review are not included in this repository.
