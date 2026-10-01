# Coupon known-answer attempt02

**Status: PASS.** Parent executed this preflight on 2026-09-27 using a fresh copy
of the frozen instrumented coupon and the existing build-attempt02 image.

- Execution: `execution.json`, SHA-256
  `69b7d733f07946d12ce88f86d0bccb36b12a0d6b7e31c838d7ec3844c09e1095`
- Verifier: `verifier.json`, SHA-256
  `d1addc19d8961325f54a45b9c2bdd8914732168a9b91f998a84363be369cf356`
- Runner used: SHA-256
  `49b4755f5ee2b10b71e5fb260f330aa537b6c1a02f6927813e618081d9b1bab4`

## Pinned input and binary

- Input: `input/coupon.inp`
- Input SHA-256: `73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab`
- Image: `mini-moonboard-fea:ccx-attempt04-output-trace-build02-20260927-v1`
- Image ID: `sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa`
- Patched binary: `/usr/local/bin/ccx-attempt04-diagnostic-2.23`
- Patched binary SHA-256: `3aec6cfe0ca72a463d87c648ed6b4a83ee1bb6a08bf604a144c8a6553d2f439f`

The runner verified the image ID, the patched executable, both preserved
unpatched executables, the full source manifest, the source-member hashes, the
diagnostic patch, and the build context inventory before this execution.

## Trace acceptance rationale

Attempt01 passed numerical output comparison but failed trace alignment because
its validator required contact events for all 16 `.cvg` keys. The saved attempt01
execution and verifier remain unchanged and are hash-bound here:

- `../coupon-known-answer-attempt01/execution.json`:
  `66b9cc4404b9b58ea27f0a6bdc1566ff7d3a034eefd601a00621972eb7f6d797`
- `../coupon-known-answer-attempt01/verifier.json`:
  `e114ca152d9b0cb22f0366b2ecf8291d971fd7ffccaf702fcfc89d4cb95c7c88`
- Preserved attempt01 failure: numerical equivalence `true`, trace alignment
  `false`, error `contact trace identities do not match .cvg records`.

The revised expectation follows the pinned CalculiX source and this coupon's
procedure. In `nonlingeo.c`, contact-element generation is at lines 1738–1921,
with the `contact()` call at lines 1883–1895. The output-only contact event was
added after the existing contact-count branch at lines 2352–2360. That branch is
inside the outer iteration guard at line 2228, whose `iit!=1` condition skips
the branch for iteration 1. Initial contact generation still appears in the
iteration-1 `.cvg` and `.cel` records; the contact event is emitted at iteration
2. `checkconvergence.c` emits one convergence event per iteration.

For this frozen mechanical, surface-to-surface mortar1 coupon, which has no
`SMALL SLIDING` option, the validator therefore requires:

- Exactly 16 `.cvg` iteration keys and 16 `.cel` keys, for step 1, attempt 1,
  iterations 1 and 2 across increments 1–8.
- Exactly 16 convergence events with keys equal to the `.cvg` and `.cel` keys.
- Exactly 8 contact events, with keys equal to those same keys whose iteration
  is greater than 1.
- Each contact event's `contact_new` equals both current `.cvg` and `.cel`
  counts; `contact_old` equals the preceding iteration's `.cvg` count in the
  same step, increment, and attempt; and `delcon` equals the pinned `0.001`.

The validator rejects duplicate JSON keys, extra or missing event fields,
incorrect JSON value types, and non-finite numbers. It compared `.12d`, `.cel`,
`.cvg`, `.dat`, `.sta`, and `spooles.out` by byte hash; all six were identical
to the instrumented known-answer outputs. For each FRD file, it normalized only
the generated clock value on its single `1UTIME` line; both files then matched
the known-answer data. The raw FRD hashes differed because of that clock value.

Byte-identical output SHA-256 values:

- `coupon.12d`, `spooles.out`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `coupon.cel`: `0b6dc846387e97c18464eab5ce7ee0709c2cdfde85620496e479dd99e5b1988c`
- `coupon.cvg`: `1eb0375a197b8a49921475cd3e5f4ff67bb583cce24a0f8a2584d66187de637d`
- `coupon.dat`: `0377ac55cc4c55cc6e5c35b48ab906a4386dd2f9b52e827fcb095b4848027c17`
- `coupon.sta`: `62cd9c24c1fb208d227c0afc5970741a0bfaa41b73c1d6a39ab98acc4999d32d`

Normalized FRD SHA-256 for `coupon.frd`:
`895802fdfea54628b0789b050bdf9d0d1245422dab33264f6705a29fd604d796`.
For `ResultsForLastIterations.frd`:
`a724f885890c9ff14caebef1e0d2bde52cdc838026379087c3c55954d67c8738`.
Per-file raw and normalized hashes, and all six byte-identical output hashes,
are recorded in `verifier.json`.

Execution completed with return code 0 in 0.313 seconds, without timeout or OOM.
Captured stdout was 24,180 bytes (under the 1 MiB cap); stderr was empty. Trace
alignment passed with exactly 16 `.cvg` and `.cel` iteration records, 16
convergence events, and 8 contact events. All eight contact records matched the
current counts and preceding iteration counts, with `delcon=0.001`.

This is a coupon preflight only: `mechanical_acceptance` and `joint_acceptance`
remain false.
