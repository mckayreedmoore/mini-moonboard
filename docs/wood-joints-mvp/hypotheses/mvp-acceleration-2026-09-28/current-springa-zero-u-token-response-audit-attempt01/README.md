# CCX 2.23 exact-zero U-token parser proof

The pinned CalculiX 2.23 nodal writer passes `real*8` displacement values to
Fortran format `1P,6(1x,e13.6)`. For this output path, `0.000000E+00` is the
formatted value zero; it is not an absolute `±5e-7` rounding bin. E editing
places significant digits at the printed decimal exponent, so nonzero values
remain nonzero by shifting that exponent. The pinned build records GNU Fortran
13.3.0 and the exact CCX binary/image. The primary source excerpts, source
archive/member hashes, manual/profile hashes, and the Fortran E-editing clause
are recorded in `zero_u_token_replay.json`.

The fresh stable parser copy changes only U-token representation radii. A
canonical all-zero field matching signed `0.000000E+00` receives radius zero.
Every finite nonzero U field keeps the prior half-last-place formula at its
printed exponent. RF values and radii remain on the original path. The parser
rejects nonfinite, noncanonical-zero, and unrecognized token forms rather than
guessing their precision. It is deliberately limited to the observed E13.6
fields with two-digit exponents; a three-digit exponent written without `E`
needs its own parser evidence before use here.

The read-only replay compares three pinned method fixtures: the exact-floor
MPC fixture (12 increments), the nonlinear SPRINGA fixture (18 increments),
and the C3D10 penalty fixture (3 increments). Values are identical across old
and new parsing; all 449,547 RF components and radii in the K12 source stream,
all 358,071 nonzero U components/radii, and all other coupon RF/nonzero-U
radii are unchanged. The contact coupon retains tiny nonzero U values such as
`2.170390E-24` with radius `5e-31`. A separate completed CCX output shows
`-1.619282E-78` with radius `5e-85`; that packet's method verifier failed and
its stream also contains unsupported three-digit exponents, so it is cited
only as formatting evidence, not replayed as an accepted fixture.

The K12-rear normal-law diagnostic in the sibling
[`current-springa-k12-rear-zero-u-token-screen-attempt01`](../current-springa-k12-rear-zero-u-token-screen-attempt01/README.md)
uses this parser against the existing frozen response. At the first state,
SPR1110's projected `q` interval is `[-7.2589015e-8, -7.2589005e-8] mm` and
its geometric elongation interval is `[-7.25893635e-8, -7.25886430e-8] mm`.
Both are strictly negative with the original geometry arithmetic guard
retained. The zero endpoint RF token keeps its original `5e-7 N` radius. The
screen therefore classifies 16 cells positive and 84 strictly separated at
all seven states, with no interval-unresolved normal cells.

This is a DAT representation correction only. It does not bound solver
residual or convergence error, arithmetic before the output write, underflow
before formatting, transformations, or the exact continuum solution. The
screen remains diagnostic: the source all-bearing support branch is rejected,
corner demands are unusable, and no floor mask or support state is selected.
No native solve, freeze, ledger, geometry, or original response file was
changed or rerun.

The generic parser and case-bound wrapper are new copies. Their SHA-256 pins
and the three fixture replays are in `zero_u_token_replay.json`; the replay
producer is `replay_zero_u_tokens.py`.
