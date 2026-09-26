# Current finite-actuator work audit: five accepted increments

This corrected audit covers the immutable progress snapshot through `0.0025 s`.
The snapshot was captured from a live process and is non-atomic across files;
the five accepted `.sta` rows define the included states. Each accepted time
has a complete matched block with 339 physical `PILOT_MONITOR` displacement
rows and both `ACTUATOR_DRIVER` nodes' displacement and reaction rows. The
audit does not read live case outputs.

The parser evaluates the serialized MPC
`q_P + Σ aᵢUᵢ = 0` and independently forms `q_A = Σ(−aᵢ)Uᵢ` from all 662
physical terms. It matches the serialized terms to the frozen source unit
pattern within each coefficient token's decimal half-quantum. It deliberately
does not trust `actuator-driving.json.source_unit_pattern.mpc_coefficient_max_rounding_error`:
that metadata value is `0.05970879193580837` because it compares a coefficient
with the opposite sign convention. The parser derives signed `−aᵢ` weights
from `pilot.inp` and checks them against the source terms directly.

At every accepted state, target RF agrees with `200(q_T−q_P)` within the
propagated DAT print bounds, and emitted `q_A` agrees with `q_P` within the
physical-coordinate projection bound. The source-weight projection also
agrees within the serialized-MPC rounding and DAT print bound. At the final
state, `q_A=3.41335137597e-5 mm`, `q_P=3.413351e-5 mm`, `q_T=1.730166e-4 mm`,
and target RF is `0.02777662 N`; the spring relation gives `0.027776618 N`.

The endpoint-trapezoid work partition for each accepted interval separates
target work into actuator-spring storage and proxy work. Proxy work is
independently compared with physical work using the emitted-MPC coordinate.
All five target/spring/proxy identities close within propagated print bounds.
At `0.0025 s`, cumulative target work is `2.49829673288e-6 N·mm`, actuator
spring-energy increase is `1.92885126879e-6 N·mm`, proxy work is
`5.69445292251e-7 N·mm`, and physical work is `5.69445401525e-7 N·mm`.

The first interval begins from the checked input-defined zero spring state.
No physical or contact energy is assigned to that driver state, so the first
continuum `ELSE+ELKE` change is unavailable. Later continuum energy changes
between adjacent accepted rows remain diagnostics, not energy-closure tests.
The native global log reports zero external work and is not the prescribed
target-work oracle. DAT CELS sums match CNUM counts but remain diagnostic only
because of the pinned sparse writer/printer limitation; they are excluded
from closure. The large `.cel` and `.frd` artifacts were not read.

The accepted-status parser requires contiguous increment numbers and strictly
increasing accepted times. It refuses to bridge a missing accepted increment,
and the focused synthetic regression checks that a `1 → 3` sequence fails.
An accepted time without complete, unique physical and driver observations
also fails. This remains a prefix accounting result; it does not establish a
complete-joint response, time accuracy, a seated state, capacity, or
mechanical acceptance.

The report is in [report.json](report.json), generated from the immutable
[progress snapshot](../ordinary-finite-actuator-progress-snapshot-attempt02/snapshot.json)
whose manifest SHA-256 is
`e315511717f1da5ea94deeee6b582db0f454280487fc19a1ef6698177c3e2051`. The
corrected gap-aware parser is [audit.py](audit.py), SHA-256
`c43341d3a72904641a973b017e591b02fdc32bc342f192f5148de5746cf212c6`; its
source hash and input/output pins are also recorded in the report.

Reproduce from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-finite-actuator-work-audit-attempt03/audit.py \
  docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-progress-snapshot-attempt02 \
  --expected-snapshot-sha256 e315511717f1da5ea94deeee6b582db0f454280487fc19a1ef6698177c3e2051
.venv/bin/pytest -q tests/test_current_finite_actuator_work_audit.py tests/test_current_finite_actuator_work_audit_attempt03.py
```
