# Low-load Newton convergence readiness

This is a source-bound, nonterminal diagnosis of the half-step transient input. The initial numerical observations below were an unpinned parent progress report, not values independently read from a live log: first increment at approximately `0.0005 s`, iteration near 9, about 60,000–65,000 active contact spring elements, average-force print near `1e-6 N`, predicted/largest displacement increment `1.687624e-6 mm`, and largest corrections `6.5e-8` to `2.2e-7 mm`. The parent has since reported the first four increments accepted through `0.002 s` in 23, 5, 7, and 8 iterations, with no rejected attempts in the status file. That resolves the initial-increment question; this note explains the governing gates and does not infer anything from later unpinned live progress.

**Scope:** this README analyzes the mechanical Newton convergence test only. Overall increment acceptance in this implicit contact case also applies a possible `kscale` reset and conditional contact-impact checks; see [acceptance-gates.md](acceptance-gates.md). Neither this mechanical-gate analysis nor the unpinned progress estimates identify which path governed any observed increment.

## Frozen input and source scope

The reviewed input is `ordinary-transient-seating-100n-every-increment-k1e4-halfdt-attempt01/pilot.inp`. Its SHA-256 is `1763d0ad15c2d53d86bdcf25ea136f3a3d267739b682d0dcd5d3cb2167387485`, matching the `artifacts_sha256.pilot.inp` entry in that directory’s `input-freeze.json` (SHA-256 `ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56`). The card is `*DYNAMIC,ALPHA=0` with initial and maximum increment `0.0005 s`, minimum `1e-6 s`; the main input and its seven included model files contain no `*CONTROLS` card. The loaded model controls therefore remain the defaults initialized in `ini_cal.c`. This review uses the pinned CCX 2.21 source archive SHA-256 `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`. It is source analysis, not proof that the installed solver binary is bit-for-bit built from that archive.

Relevant source-file pins:

| Source | SHA-256 |
| --- | --- |
| `checkconvergence.c` | `a9f417fe198b0bc227a28f1f4775382d2bba22a7e436d60ba6d523ab91713e50` |
| `nonlingeo.c` | `0be7d7d6037868c364a621e12a3802a703f189b09ba200de95cf2e9d1b211f1b` |
| `ini_cal.c` | `1d195e679e6692d03da0b3bd48e7ea52f733c96328bedfef3f5f7da6f3dd0d1f` |
| `resultsstr.c` | `31f52e9621c607e8fb5dafb91a29b5741b2a676160f26b106b2cb16f7411a736` |
| `resultsmech.f` | `7aadd7376c5d6176dcfe61b9fa8b0d472e7cc3ca6627bd9a617f571f2461080c` |
| `prediction.c` | `79bc3e59c90d93c731409fc225a0ceee75006794f694fe47cba9c18a4fff9445` |
| `writecvg.f` | `983183b8186b51dd6b343e7b7448c1256962cbe8f5cd718958b677d97df4dd8d` |

## Effective gates

For the mechanical branch, `checkconvergence.c:105–114,134–147` first chooses its relative force and displacement limits from `qa[0] > ea*qam[0]`. With defaults `ea=1e-5`, `ran=0.005`, `rap=0.02`, `can=0.01`, and `cae=0.001` (`ini_cal.c:243–271`):

- If `qa > 1e-5 qam`, the force residual limit is `0.5%` while iteration `iit <= 9` and `2%` afterwards; the direct correction limit is `cam <= 1% * uam` in either interval.
- If `qa <= 1e-5 qam`, the limits tighten to `ram <= 1e-5 * qam` and `cam <= 0.1% * uam`.
- Acceptance also requires `iit > 1` and no significant contact-set change (`iflagact == 0`). For the face-to-face contact path, `nonlingeo.c:2337–2340` marks a change when the active contact-spring count shifts by more than the default `delcon=0.001` (0.1%; `ini_cal.c:318–323`).
- The displacement test has alternate small-residual/improvement branches when `ntg == 0`, plus an absolute `cam < 1e-8 mm` branch. Therefore `cam/uam` alone is not enough to infer the gate result.

The reported corrections are about `3.85%` to `13.0%` of the reported `uam`, above the direct 1% branch at iteration 9 and above the 0.1% low-force branch. This comparison alone does not establish nonconvergence: the force residual may hit the absolute clamp below, the alternate displacement branch may apply, and `iflagact` is not reported in the supplied excerpt.

## Absolute floor and missing observables

The source has an absolute residual floor that is relevant at this scale. `nonlingeo.c:3335–3341` forms `ram[0]` as the largest absolute mechanical equation residual. Then `nonlingeo.c:3366–3368` changes it to exactly zero whenever it is below `1e-6 N`. The same mutated value is printed, written to `.cvg`, and passed immediately afterward into `checkconvergence()` (`nonlingeo.c:3419–3430`). Thus the absolute floor is part of the convergence decision, not just display formatting. Once it fires, the force residual criterion passes for positive `qam`; the optional `ram <= ral*qam` displacement bypass (`ral=1e-8`) also becomes true, subject to `ntg==0` and the separate contact-stability gate.

Existing text output cannot distinguish the needed branches:

- `average force` and `time avg. forc` use `%f` (`nonlingeo.c:3369–3370`), only six digits after the decimal; at about `1e-6 N`, this does not resolve the `qa <= 1e-5*qam` switch robustly.
- `largest residual force` also uses `%f`, but a pre-print mutation has already erased every raw residual below `1e-6 N`. `.cvg` uses scientific notation for the residual ratio (`writecvg.f:80–81`) but receives that already-clamped value.
- `largest increment` and `largest correction` are printed in scientific notation, but the supplied data omit `iflagact`, the consecutive active-contact counts used to set it, `ntg`, the selected `c1/c2` branch, and the raw pre-clamp `ram`.

`qa` is not the maximum equation residual: `resultsmech.f:1253–1259` sums absolute internal nodal-force contributions per element node and `resultsstr.c:214–240` averages that sum. `ram` is instead the maximum assembled equation residual. Treating the parent’s average-force estimate as `ram` would conflate distinct quantities.

## Smallest informative diagnostic

If another run needs a mechanical-gate diagnosis, one additional read-only diagnostic line per Newton iteration is sufficient to audit that test; do not change the acceptance logic. Capture the raw `ram[0]` immediately before the `<1e-6` clamp, then record `qa[0]`, `qam[0]`, `cam[0]`, `uam[0]`, `iit`, `dt`, active contact count and previous count, `iflagact`, `ntg`, and the evaluated `c1[0]` / `c2[0]`. A computed boolean for each conjunct/disjunction of the mechanical test would make that gate directly auditable. This line alone does not audit the post-mechanical `kscale` and `checkimpacts` paths described in [acceptance-gates.md](acceptance-gates.md). The present approximation cannot show whether the residual floor or active-contact stability is decisive.

Reducing `dt` is not a guaranteed way to ease the correction test. For implicit dynamics, `prediction.c:42–78` scales predicted motion from velocity by `dt` and acceleration by `dt^2`; `nonlingeo.c:3307–3309` also lets `uam` grow to the largest correction in the increment. Since the correction gate is relative to `uam`, a smaller predicted increment can reduce its absolute allowance, while the actual correction may shrink at a different rate. Contact-set stability is a separate gate. Do not infer a better convergence ratio from smaller `dt`, and do not alter tolerances to obtain acceptance.
