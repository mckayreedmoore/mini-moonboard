# Explicit zero-SPC displacement interval proof

The replay checks one pinned CCX 2.23 case and two existing native known-answer
fixtures. Its narrow conclusion is valid: for an explicitly serialized
homogeneous zero `*BOUNDARY` DOF that is not the dependent term of a serialized
MPC, a native zero U token can have representation radius zero. Source and
coupon pins are recorded in `zero_spc_replay.json`.

That SPC-only change is insufficient for the current SPRINGA branch gate. On
K12-rear at time `0.1`, setting the numerical ground U radii to zero changes
endpoint geometric elongation from a zero-crossing interval to a strictly
negative interval, but the separate free source-projection token still carries
radius `5.00000005e-7 mm`; the projected `q` interval remains ambiguous. The
initial replay therefore does not clear the required projected-coordinate
gate by itself.

The subsequent source-backed format proof at
[`current-springa-zero-u-token-response-audit-attempt01`](../current-springa-zero-u-token-response-audit-attempt01/README.md)
shows why a canonical all-zero CCX E13.6 U token can receive zero
representation radius regardless of SPC status. Its separate K12 screen then
checks both projected `q` and geometric elongation intervals. The SPC replay
is retained as the narrower diagnostic record; it does not change native
inputs, outputs, or the frozen response auditor.
