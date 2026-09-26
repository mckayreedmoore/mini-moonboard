# SPOOLES MT output-parity benchmark, attempt 01

## Result

All six strict audits pass, and every requested numerical output compares
exactly across the serial reference, the MT-enabled binary at one thread, and
the MT-enabled binary at a four-thread request. The requested four-thread
setting reached the MT dispatch branch, but both factorizations in both tiny
fixture cases used one SPOOLES worker. The benchmark therefore demonstrates
output parity and environment dispatch; its actual-multithreading gate fails.

The 100 N fixture is only a solver-output probe. It does not establish a wood
property, connection response, capacity, or candidate acceptance.

## Frozen inputs and provenance

The input contract is `parent-input-contract.json` (SHA-256
`52c5736290625c5510cd3bb64633d0cc6232197fcd70ca0cab0170e7cddb0e0e`). It
pins the two original contact benchmark decks, the strict re-audit parser and
manifest, the solver image, and three binary/configuration arms. The serial
reference is `ccx-wj-contact-energy-map-2.21` at
`af0da93038dda93e7d9807f392a5fe6c4fd5f2b9d0b47d0de5d107936795d174`; the MT
binary is `ccx-wj-contact-energy-map-mt-2.21` at
`8f6f15cfc3887310cf71e4b6d661f7a1701c96c1cee0664faccbd514f9f9c38e`. Both
executables use the same frozen point-map `results.c` and
`printoutcontact.f` source inputs. The strict parser snapshot is pinned at
`2034ab0e368c1f4661c306f86c4540821571519e14459f134b1a0ac1fcb9e8f7`; the
matching current authenticated source and frozen re-audit manifest were
verified before comparison.

The exact numerical tolerances were frozen before these native outputs in the
input contract. They reuse the existing expected-result force, moment,
centroid, area, mean-normal, and time limits, with comparison-only limits for
contact gap/stress and pointwise/aggregate energy. Since all DAT files are
byte-identical across the three arms, their observed numerical differences
are zero and are inside every frozen tolerance.

## Comparison

`compare_frozen_arms.py` is a read-only-output comparator; it never starts a
solver. It rechecks each execution artifact hash, verifies the six preserved
strict-audit records, reruns the authenticated `reaudit02` parser against each
DAT/STA/LOG/input-deck set, and checks the parser's ordered CF/CFN/CFS groups
against accepted status times. It compares the complete DAT contents,
including final nodal U/RF, all printed CDIS/CSTR rows, every requested
CF/CFN/CFS wrench, WJ angular wrenches, pointwise contact energy, and the
aggregate contact-energy print. Each case has one accepted state, 28
pointwise energy records, nine angular records, and one aggregate energy.
The pointwise energy sum matches the aggregate to floating-point roundoff.

For both cases, `.dat`, `.sta`, `.cvg`, and empty `.12d` files are byte-for-byte
identical among arms. `.frd` differs only in its single `1UTIME` run-clock
header; after replacing that metadata line, all remaining FRD bytes match.
Equation-count and matrix-nonzero histories match. The logs differ where they
report requested CPU counts and timing.

The upper-slave aggregate elastic contact energy is
`0.0012499999999999818 N mm`; the lower-slave value is
`0.0012500000000000010 N mm`. In both cases the 28 printed point-energy values
sum to the printed aggregate within `1e-8 N mm` absolute / `1e-8` relative.

The MT4 logs report `Using up to 4 cpu(s) for spooles`, while each associated
`spooles.out` records `Using 1 threads` twice. CCX selected the MT-capable path
but the one-front fixture limited the actual factorization worker count to
one. Do not treat this as a parallel-speed result. The larger translated
multi-pair fixture is prepared separately to exercise multiple independent
fronts and must satisfy the same explicit worker-count gate.

The comparison result is `numerical-comparison-attempt01.json` (SHA-256
`b8eb134afc0cdf663730768b9cb3b2d44a1a1b9e21b10f4d36cb30c2b7679ad4`), made
with comparator SHA-256
`68fdd17be75e4299bb476bafd01ddc491702ae55dde1a9fa2f5f161eeceff2a8`. Parent
execution and strict-audit summaries remain preserved separately; original
parser-rejection history is unchanged.
