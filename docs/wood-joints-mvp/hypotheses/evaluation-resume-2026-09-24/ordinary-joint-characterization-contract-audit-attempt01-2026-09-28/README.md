# Ordinary-joint characterization contract audit — attempt01

Date: 2026-09-28  
Candidate: `led-clearance-2x6-runner-seated-blocks-v1`  
Disposition: **NO-GO for an ordinary-joint freeze or response run**

This read-only, append-only packet tests whether one bounded non-service
characterization history can be frozen from existing evidence. The closest
exactly pinned history is the attempt03 1 N N+ external-force diagnostic: its
202 amplitude pairs ramp over 0.100 s, hold through 0.125 s, and use
`*DYNAMIC,ALPHA=0` with 0.001 s initial, 0.0025 s maximum, and 0.000001 s
minimum increments. The deck has a 3600 s wallclock bound, a 600 s accepted
state/monitor no-progress watchdog, and sampled diagnostic stops at 1.3 mm
force-dual travel, 5 mm loaded-node displacement, or 0.05 rad controller
rotation. The 1.3 mm value remains a geometry-only diagnostic stop; it is not
service demand, a load case, or a predicted bearing event.

Attempt03 accepted only the startup state at 0.001 s. Its amplitude was
9.8506e-6 of the 1 N reference; the input force and reported energies were
below their frozen numerical floors. It produced no bearing or post-bearing
response and stopped after the no-progress watchdog. Therefore this record
supports only the existence and exact contents of a past bounded diagnostic,
not a validated response history or acceptance contract.

The pinned CalculiX 2.23 manual supports the input/output mechanics described
in `contract-audit.json`: §7.1 `*AMPLITUDE`, PDF pp. 407–408; §7.46 `*DYNAMIC`,
pp. 482–484; §7.20 `*CONTACT FILE`, pp. 434–436; and §7.23 `*CONTACT PRINT`,
pp. 439–441. §§6.10.2 and 6.10.5 (pp. 386–391) describe solver convergence
controls. Those controls govern solver iteration and increment decisions; they
do not define WJCP bearing, near-zero, post-bearing, or joint-response
acceptance limits. The attempt03 force/energy percentages and floors are
frozen analyst-selected diagnostic gates, not manual-prescribed tolerances;
the moment residual normalization and matched-response comparison norm are
also not fully specified for reuse.

The exact current active map set is A00, A01, A02, and A03. Each is a distinct
rank-six source map. The known-answer fixture supports A00/M03 only under its
small global-Y body-force history. Exact transformed equivalence for A01–A03
is not established, and the A00 result does not transfer to the N+ history.
The handoff requires map applicability for maps actually used, frozen signed
and near-zero thresholds for WJCP_020–027, complete accepted-state outputs,
and two accepted states after first resolved bearing. No supported numeric
near-zero or first-bearing threshold is present. A finite resolved resultant
can witness some compression; a zero curved-face resultant cannot prove no
local bearing or identify exact first local touch.

The smallest next evidence step is the parent-owned, pinned-runtime T02
attempt09 contact-capture known-answer coupon, after fresh parent readiness,
coupon authorization, durable run-once registration, and the serialized slot
are available. It can verify capture, state joins, output signs and
known-answer behavior; it cannot alone set WJCP acceptance thresholds. The
separate T03 shared-slave penalty coupon remains required. Then bind either an
exact transformed equation/carrier equivalence record for the active maps or
matched direct, map-only, and map-plus-carrier qualification for each distinct
active map under the frozen diagnostic. Only after those observations can a
unit-aware near-zero rule and complete response/stop contract be frozen.

This packet changes no source, geometry, solver input, queue, ledger, or
readiness record; it runs no solver. It closes planning only, never joint
response, capacity, criterion acceptance, or readiness. The parent has now
confirmed that the pinned Docker runtime is accessible; this supersedes the
older status note that recorded permission denial. Fresh T02/T03 readiness,
authorization, queue, and run-once fields are transcribed from the companion
live snapshot rather than inferred from that older note.

`contract-audit.json` is the supported/unsupported contract table.
`current-readiness-ledger-snapshot.json` records the live parent gates at the
snapshot time. `source-pins.json` gives source roles and full SHA-256 values;
`SOURCE-SHA256SUMS` is checked from the repository root. Check this packet from
its directory with `sha256sum -c SHA256SUMS`.
