# K=10000 diagnostic: immutable first-knot snapshot

This preserves the first accepted state at 0.001 s from the live K=10000
aligned diagnostic, with DAT/FRD bytes read unchanged twice and log/status
prefixes ending before increment 2. The [snapshot record](snapshot.json)
pins those files and the child input freeze. It is not a terminal execution
record, and stable bytes do not by themselves prove complete contact output.

The first increment converged after 26 iterations with q=2.4159449446e-5 mm,
maximum loaded-node motion 1.9882482444e-5 mm and maximum controller rotation
5.6713459780e-8 rad. The actual force at the knot is 0.0298 N per side;
the exact first-segment forcing impulse is 1.49e-5 N·s per side.

The [matched motion/energy comparison](../aligned-first-knot-penalty-motion-comparison-attempt01/README.md)
flags changes in the full displacement and controller fields, plus an
increased native energy discrepancy of 3.905511%. Contact and momentum
accounting remain separate. This state does not establish bore seating,
time accuracy, a physical engagement law or joint acceptance. Raw output
files remain local evidence.
