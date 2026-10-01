# Pre-execution clarification

The frozen preparation narrative calls attempt01's missing records "penalty
stress coverage." This is a wording error: attempt01 requested no `STRESS`
field. Its penalty FRD omitted nodal `DISP`, `FORC` and `CONTACT` records,
with no records at the open/reopened endpoints and only 14 of 54 model nodes
at compression. The detailed [attempt01 result](../contact-section-force-known-answer-attempt01/RESULTS.md)
records the correct distinction.

This clarification changes no deck, oracle, required output, verifier or
acceptance threshold. Attempt02 adds `S` output and requires both complete
inherited nodal output and three complete, finite 54-node `STRESS` datasets
per case. Its frozen preparation files retain their original bytes.
