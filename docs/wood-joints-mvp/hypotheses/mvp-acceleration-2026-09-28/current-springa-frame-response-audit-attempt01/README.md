# Current SPRINGA frame response recovery, attempt 01

This packet adds an input-only postprocessor for the parent-owned `a12-rear`
SPRINGA adapter. It recovers physical forces from every isolated native spring
endpoint, transfers them through the recorded body ownership and connector
bases, recovers exact-floor tangent reactions from the 200 transformed MPC
reference channels, and checks each physical body's and the complete frame's
force and moment balance. Numerical SPRINGA grounds never enter a physical
balance.

The adapter schema, complete source-row join, native `U`/`RF` output, and
single linear load ramp are required inputs. The checker rejects records that
lack the revised nonlinear-carrier inventory, or that retain floor tangent
SPRING2 elements in place of the exact-MPC reference channels. It checks all
MPCs at every printed increment, checks each of the 1,292 unilateral force
tables and endpoint pairs, verifies the 348 retained bilateral SPRING2
components by their unchanged law, and requires every floor normal to remain
strictly compression-positive for this conditional all-bearing branch. Each
increment reports explicit MPC, SPRINGA, bilateral, floor-normal, raw-balance,
and output-rounding-interval gate flags. The source model JSON hash, emitted
deck hash, and native DAT hash bind each later report to its inputs.

`verify_method_fixtures.py` replays three already-passed method coupons without
launching CalculiX or modifying their packets. It checks the nonlinear SPRINGA
endpoint sign and two-body force transfer at all 18 relative-coordinate
states, exact-floor `RF(reference,1) - dependent source CLOAD` recovery at all
12 printed states, and the nonidentity, permuted matrix transfer at all 12
states of the transformed-floor coupon. It checks body closure and
source-to-physical support force and moment preservation while excluding
nonzero numerical-ground reactions from physical equilibrium. The written
`method_fixture_check.json` binds each replay to its previously recorded DAT
hash. These coupons establish method behavior only; they do not validate a
frame response or joint demand.

For nonlinear SPRINGA geometry checks, the postprocessor reads the actual node
coordinates emitted in the native deck and compares
`norm(current)-norm(initial)` to the relative-coordinate MPC. It retains the
100 mm nominal-span/axis audit and applies a small, explicit floating-point
cancellation bound at the endpoint length scale, since emitted `.14g`
coordinates can shift the initial norm by about `1e-10 mm`.

The frame report deliberately preserves 92 new block bolt axes separately
from 12 retained leg/runner axes and retains the source IDs for all recovered
carrier rows. Historical C11 forces and active states are not consumed.

Run the method replay from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-response-audit-attempt01/verify_method_fixtures.py
```

For a later parent-authorized native result, the postprocessor can be called
without launching a solver:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-response-audit-attempt01/response_audit.py MODEL.json MODEL.dat MODEL.inp --output RESPONSE.json
```

The output is a numerical response audit, not frame qualification, a capacity
comparison, a floor or anchor qualification, or joint acceptance. It covers
only the supplied `a12-rear` load case and the recorded all-bearing exact-stick
floor hypothesis. It does not supply contact release/recontact handling,
friction, other load cases, historical C11 states, physical inspection, or
design resistance.
