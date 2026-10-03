# BG001 three-case Appendix E parallel-component screen

This packet extends the prior A12-only Appendix E arithmetic across the 21
authenticated rear case/load-factor states: A1-rear, A12-rear and K12-rear,
each at seven factors. It reports signed grain-parallel receiver-group actions
against the same conditional one-row tear-out references, and the spine's
candidate net-section reference. Cross-grain lateral actions and outer-seat
axial ties remain explicit and separate. This is a directional component
screen, not a mixed-action interaction, DCR, pass/fail, or joint acceptance.

## Method and inputs

The calculation reuses the prior source-reviewed [A12 Appendix E screen](../current-bg001-appendix-e-parallel-row-screen-attempt01/README.md)
and its helper methods, geometry, DF-L No. 2 base values, and NDS-2024 Appendix
E source pin. It consumes the later authenticated [three-case paired-resultant
screen](../current-bg001-three-case-resultant-reference-attempt01/README.md),
which retains both physical bolts, both signed receiver actions, and each
same-state outer-seat tie. Its producer is run in read-only verify mode before
this screen is generated. Direct and inherited source hashes are listed in
[`source-pins.json`](source-pins.json).

For each state and receiver, the two source-signed bolt-plane forces are summed
and projected onto the proposed `+Z` grain. The sign selects the modeled
loaded grain end (`g−` for the spine and `g+` for the post in all 21 states).
Using the nearest pinned finished-profile ray, the spine end distance is
31.75 mm and the post end distance is 25.40 mm. The row pitch is 42.05 mm and
bolt-axis thickness is 38.10 mm. Thus `s_critical = min(end distance, pitch)`
is 31.75 mm for the spine and 25.40 mm for the post. The existing helper
computes the one-row, two-shear-line Appendix E.3 base references with
unadjusted `Fv = 180 psi`: 675 lbf (3002.55 N) for the spine and 540 lbf
(2402.04 N) for the post.

The existing candidate E.2 spine section is the XY plane through one modeled
7.5 mm X-bore, with pinned area 5036.82 mm². The helper's unadjusted
`Ft = 575 psi` reference is 4489.07 lbf (19,968.40 N). The same spine
grain-parallel group component is shown against it for every state. This is a
candidate geometry/reference comparison, not a recovered internal section
force. The source packet does not map a post net-section plane, so none is
calculated.

No adjustment factor is applied to either base value, including no `Cvr`.
The inherited [March 2026 AWC errata review](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
(SHA-256 `b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0`)
found §5.3.10's `Cvr` provision in the glulam chapter for `Fvx`/`Fvy`; it is
not transferred to these solid-sawn members.
Actual stock, cuts, bores, hardware and service conditions are unobserved; they
are not assumed verified by this conditional arithmetic. No capacity or
qualification follows from the model inputs.

## Full-factor state summaries

The table shows signed `+Z` parallel group force, the signed global-`Y`
cross-grain group component, and the signed global-`X` outer-seat tie
resultant. The cross-grain and axial values are not combined with the row or
net-section ratios. Tiny numerical `X` residuals in the lateral vectors are
retained in the JSON source records.

| Case | Receiver | `F_parallel` (+Z) N | `F_crossgrain,Y` N | Separate seat tie `X` N | E.3 reference N | Parallel/reference | Spine E.2 reference N | Spine net/reference |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 rear | Spine | -210.789 | -124.053 | +91.485 | 3002.550 | 0.07020 | 19968.400 | 0.01056 |
| A1 rear | Post | +210.789 | +124.053 | -91.485 | 2402.040 | 0.08775 | — | — |
| A12 rear | Spine | -519.461 | +61.973 | +83.439 | 3002.550 | 0.17301 | 19968.400 | 0.02601 |
| A12 rear | Post | +519.461 | -61.973 | -83.439 | 2402.040 | **0.21626** | — | — |
| K12 rear | Spine | -12.204 | +44.586 | +70.521 | 3002.550 | 0.00406 | 19968.400 | 0.00061 |
| K12 rear | Post | +12.204 | -44.586 | -70.521 | 2402.040 | 0.00508 | — | — |

Across all 21 states, the largest receiver-row parallel-component ratio is
0.21626 (A12-rear, factor 1.0, post). The largest candidate spine E.2
parallel-component ratio is 0.02601 (A12-rear, factor 1.0). These are raw
base-reference comparisons only. Every state retains each bolt's individual
cross-grain vector and axial tie in [`screen.json`](screen.json), so the group
sum does not replace the local actions at either bolt.

## Applicability limits

NDS Appendix E.1 describes groups loaded parallel to grain. BG001's actual
signed lateral vectors include cross-grain action and each physical bolt has
a separate axial outer-seat tie. This packet reuses the prior method only for
the parallel component; it does not assert that the complete E.1 loading
condition is met, define a mixed-action interaction, infer cancellation as a
splitting check, or combine component ratios. The row and net-section
references therefore do not establish the actual governing path or capacity.

Adjusted `F′v` and `F′t`, mixed cross-grain/axial interaction, splitting,
member stress, full member section actions, post net section, and complete
corner transfer remain outside this arithmetic. No group capacity is summed
or transferred to BG003, BG045 or other candidate joints. This result does
not qualify the retained LEG/RUNNER arrangements.

## Replay

From the repository root:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg001-appendix-e-parallel-row-three-case-attempt01/produce.py --write
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg001-appendix-e-parallel-row-three-case-attempt01/produce.py --verify
```

The replay checks 21 states and 42 paired bolt actions/ties, recomputes both
receiver E.3 references and the spine E.2 reference, and compares A12 factor 1.0
per-bolt actions, group vectors, ties, geometry, references and ratios to the
prior packet. It performs no native solve or geometry edit.
