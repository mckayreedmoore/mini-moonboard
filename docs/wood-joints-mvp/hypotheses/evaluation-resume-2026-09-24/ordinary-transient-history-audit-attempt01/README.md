# Accepted-history work and forcing-impulse audit

This folder records a read-only audit of accepted output from the current-joint transient diagnostics. The helper reconstructs the signed generalized displacement

`q = Σ_nodes F_unit,node · U_node`

from complete `PILOT_MONITOR` blocks. The frozen force pattern is normalized as a 1 N reference field, so `q_mm` is a signed mm-equivalent virtual-work coordinate. It is not a center-of-mass displacement. For each accepted increment, the reconstructed discrete work is

`ΔW = 0.5 (A_prev + A_i) (q_i - q_prev) load_scale`.

`load_scale` is recovered from the serialized `*CLOAD` rows and checked for exact support and proportionality to the frozen unit field. The helper refuses to form a work history if any accepted `.sta` time lacks a complete monitored displacement block; it does not bridge a missing increment. It ignores rejected `.sta` attempts when building accepted histories.

The impulse values are integrals of the scalar coefficient `load_scale × A(t)` in N·s, multiplying the frozen unit-load nodal pattern. They are not net-resultant vector impulses and are not contact-force or transferred impulses. The exact integral splits intervals at every serialized tabular-ramp knot; the companion endpoint-trapezoid value shows the error from integrating across each entire accepted interval. Reported print bounds include printed q precision, DAT time-label precision propagated through the piecewise-linear ramp, and native external-work print precision. They exclude solver integration error and the difference between continuous solver work and this incrementwise trapezoidal reconstruction.

## Attempt 04 terminal run

[`pilot-attempt04-audit.json`](pilot-attempt04-audit.json) audits only the terminal, hash-pinned outputs of [`ordinary-transient-pilot-attempt04`](../ordinary-transient-pilot-attempt04/). Its execution status is `bounded_timeout`: the run stopped after eight accepted increments at 0.003129826 s of the requested 0.025 s step. It did not finish the step.

All eight accepted times have complete monitor blocks and matching native external-work summaries. At the last accepted state, `q = 1.19207456e-5 mm`; reconstructed cumulative discrete work is `1.87554098e-8 N·mm`, compared with CCX external work `1.875541e-8 N·mm`. Each of the eight differences is within the combined printed-value bound. This confirms accounting consistency for the observed increments; it does not establish contact equilibrium, energy closure, stiffness, quasi-static response, or capacity.

Through 0.003129826 s, the exact piecewise-linear scalar pattern impulse is `3.16559350e-6 N·s`; integrating the same accepted intervals with one endpoint trapezoid each gives `3.89498909e-6 N·s`. The first interval spans 0–0.0025 s and crosses ramp knots: its exact value is `1.66475e-6 N·s`, versus `2.39375e-6 N·s` from the whole-interval trapezoid. The accepted increment from 0.002912626 to 0.003016055 s also crosses the 0.003 s ramp knot. These differences document why accepted endpoints alone do not justify treating the sampled ramp as linear over every increment.

The execution manifest SHA-256 is `b2092585ac3910fc209a01d4f123c80703be9556ae3b0c336f5fb6c41ad38d10`; the audit JSON carries the input-freeze hash, every one of its fourteen artifact pins, the `.sta`/`.dat`/`.log` output pins, and the audit implementation pins.

## Aligned first-knot snapshot

[`aligned-first-knot-snapshot-audit.json`](aligned-first-knot-snapshot-audit.json) audits the immutable first accepted state captured from [`ordinary-transient-aligned-first-knot-snapshot-attempt01`](../ordinary-transient-aligned-first-knot-snapshot-attempt01/). The snapshot SHA-256 is `a91a8412e25c92952ab414e5b65e29cb89a6364a9f114a49fa1ef6c7e81d272e`. Its input freeze and all eighteen serialized input artifacts were checked against the still-running source folder before parsing; only the immutable snapshot's `.sta`, `.dat`, and log-prefix files were read as results. The snapshot records that the source process was still running at capture. This is one accepted point, not a terminal run.

At t = 0.001 s, the DAT monitor projection is `q = 2.31868671e-5 mm`. The reconstructed discrete work is `3.45484320e-7 N·mm`, matching the captured native external-work print `3.454843e-7 N·mm` within the combined print bound. The exact pattern impulse to this first ramp knot is `1.49e-5 N·s`. The captured native energy report gives a nonzero 1.230541% energy residual at that state; agreement in this discrete-work check does not close that energy discrepancy.

## Reproduction and pins

From the repository root, run the focused tests and terminal audit with:

```sh
.venv/bin/python -m pytest -q tests/test_wood_joint_current_transient_history.py
.venv/bin/python -m fea.wood_joint_current_transient_history \
  docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt04
```

The helper requires a terminal `execution.json` and verifies its frozen input and output SHA-256 pins. The aligned snapshot was audited with the same text-level helper because its source execution was live at capture; `audit_directory()` was deliberately not used on that folder.

Frozen audit implementation copies and SHA-256 pins:

- `wood_joint_current_transient_history.py.snapshot`: `7c8d3ff46161576f3ed13605e666c9ea3aba14bdeaa439ede52a7cab562f374c`
- `wood_joint_current_transient_launch.py.snapshot` (including the lazy monitor-block parser): `664251cec9197d6c4a6ee2993eb493fe5024e9191ac5007c9dc44ddbe2eed142`
- `test_wood_joint_current_transient_history.py.snapshot`: `bc7f8699cb2ad95cca09c08d54016fcca3db928a8d73f261c9318949b593df77`

The JSON reports carry the full relevant input, terminal-output/snapshot, and implementation hashes. The audit code and focused tests are also maintained at [the helper](../../../../../fea/wood_joint_current_transient_history.py) and [its tests](../../../../../tests/test_wood_joint_current_transient_history.py).
