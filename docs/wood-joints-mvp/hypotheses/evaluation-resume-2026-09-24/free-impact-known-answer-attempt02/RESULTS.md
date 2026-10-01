# Free-impact attempt02: bounded method check passes

Date: 2026-09-27. Both the unmodified CalculiX 2.23 executable and the
output-only point-trace build pass all 70 accepted states of the frozen
free-impact fixture. The [verifier](verifier.json) checks the scalar Newmark
answer, every requested physical/controller displacement and velocity,
mass, volume, strain/kinetic/contact energy, pair forces and origin moments,
accepted-state identities, trace coverage, and baseline/trace comparisons.
The completed [independent post-run audit](independent-postrun.md) confirms
the frozen and captured hashes, raw trace identities and exact verifier
reproduction. This is a method result, not a current-joint response or capacity.

The [correction](correction.json) changes the expected linear pressure-law
code from 1 to the source-defined 2, plus that literal in the verifier's
synthetic input. Native input, numerical tolerances, binaries, and limits are
unchanged. [Attempt01](../free-impact-known-answer-attempt01/RESULTS.md) remains
a frozen verifier failure. The corrected contract was independently reviewed
and frozen before this separate pair of native runs.

## Observed response

The upper 1-tonne toy mass begins at −0.1 mm/s, compresses the planar spring,
rebounds and separates. The following are printed DAT values:

| Increment | Time, s | Upper/controller U3, mm | V3, mm/s | Upper kinetic energy, N·mm | Contact energy, N·mm |
| --- | --- | --- | --- | --- | --- |
| 25 | 0.0025 | −0.0001581063 | 0.0009815615 | 4.817315e−7 | 0.004999518 |
| 50 | 0.0050 | 0.000003106924 | 0.1000428 | 0.005004282 | 0 |
| 70 | 0.0070 | 0.0002031925 | 0.1000428 | 0.005004282 | 0 |

The reference predicts the small 0.0856326% energy increase at the fixed-step
unilateral switch. The numerical gates compare against that discrete answer;
they do not assert exact energy conservation through the switch. The lower
body stays fixed, both body masses/volumes match, and strain energy stays
below 4.09e−34 N·mm.

The trace contains 7,896 MAP and 5,544 TRIAL rows, with no unmapped rows.
Every one of the 141 CVG iteration identities has complete coverage: 99 have
56 TRIAL rows and 42 have zero contact points and no TRIAL rows. At increment
50, iteration 1 has 56 positive-gap old-set trials satisfying the signed
pressure and spring-energy formulas. Iterations 2–3 have no active springs.
Accepted states 50–70 have zero CFN and CELS. This distinguishes an intermediate
tensile trial from accepted open contact behavior.

All measured baseline/trace comparisons have zero numerical difference.
DAT, STA, CVG and stderr are byte-identical. FRD differs only in its run-time
header; all numerical content is identical. Largest errors against the oracle
are 4.94e−11 mm in DAT displacement, 4.62e−10 mm in FRD displacement,
7.16e−9 mm/s in DAT velocity, 1.93e−7 mm/s in FRD velocity,
4.97e−10 N·mm in kinetic energy, 4.88e−10 N·mm in contact energy,
and 4.80e−6 N in a CFN component, all within the frozen gates.

## Provenance and limits

The [parent integrity record](parent-postrun-integrity.json) verifies all
12 frozen local files, 27 external dependencies and 16 captured file hashes.
The baseline ran from 22:33:53.031963 to 22:33:54.070279 UTC; the trace began
at 22:33:54.072452 and ended at 22:33:55.209679 UTC. Each used one CPU,
1 GiB and no network. Captured output was 1,174,592 and 5,989,151 bytes,
within the unchanged 60 s and 16 MiB limits. Neither timed out or exhausted
memory.

- Input freeze: `5efc117c64a614eb73c07a75e8f539bde3315f9b92cd9969e2dee640a890c656`.
- Execution: `f91676d630acbb961838bb0df21d3beb37daca336be8f2e348ffd0c871435bf4`.
- Verifier result: `9b77b85a508740c004d2f531eda0e70932c1a80207ed1c378c720774e62a6fba`.

This qualifies the tested one-coordinate implicit contact/inertia method and
its point-trace interpretation. Current offset/rotational nut maps,
zero-density carriers, full-joint state joins and bounded capture,
inactive-force/work bounds, joint resistance and six current-frame cases
remain separate obligations. The reviewed MoonBoard geometry and all full
structural-criterion dispositions remain unchanged.
