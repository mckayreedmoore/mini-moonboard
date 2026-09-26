# First accepted-state contact output audit

This report checks the frozen instrumented joint output at step 1, increment
1, `t = 0.0005 s`. The native run later failed with return code 201 after one
accepted increment; this is a first-state output audit, not a completed
trajectory. The parent terminal-validation record authenticates the exact
input/output files and accepted state.

The producer reads the frozen pilot and contact fragment to build the expected
35-pair sequence. It verifies exact identity and time for all 315
`WJ_ANGULAR` records (35 pairs × `CF`/`CFN`/`CFS` × slave/master/pair-offset
couple), plus one finite `WJ_E_IF_FRICTIONLESS_LINEAR_DYNAMIC` energy record
per pair. It checks all 525 `CF = CFN + CFS` components, 315 slave/master
force action-reaction components, and 315 pair-offset-couple components
against the printed origin-moment sums. All checks pass using the
printer-fixture comparison bound: each formatted value's half quantum plus
`128 × binary64 epsilon × max(1, sum(abs(operands)))`. This is an output
arithmetic bound, not a mechanics tolerance.

The contact-energy records do not agree with the native aggregate. The 35
pair-level `WJ_E_IF` values sum to `3.47860364458171215650e-11 N·mm`; the
104,244 displayed CELS rows sum to `1.091529611754608990186507413e-9 N·mm`,
and the native LOG reports `1.091530e-09 N·mm`. The CELS row sum differs from
the LOG's displayed total by `-3.88245391009813492587e-16 N·mm`, less than
the LOG field's `5e-16 N·mm` half quantum. The WJ_E_IF sum is lower than the
LOG value by `1.0567439635541828784350e-9 N·mm`, far beyond the combined
printed bound (`2.972170943040451013484497070e-14 N·mm`). The result preserves
this as an unresolved diagnostic discrepancy. These are alternative reports
of contact energy and must not be added or subtracted twice. CELS values are
individually printed at `E13.6`; the displayed-row sum is not treated as a
strict true-energy bound across all rounded rows.

Reproduce from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/first-state-contact-output-audit-attempt01/audit_first_state_contact_output.py
```

Frozen inputs and authentication:

| Artifact | SHA-256 |
| --- | --- |
| Instrumented `pilot.inp` | `7542af582f91215a3759292726211e15911387640b0f76514946681b8f623da3` |
| Instrumented `contact-fragment.inc` | `e70fc43593e8e5a5b8e445f88122fb5e675dc788207be6e6031aae9c1f71cac5` |
| Native `pilot.dat` | `1e2340c1f73b2be58db3969aeac64d7e7b01cd2f50f103fe0824f6863b7407ba` |
| Native `pilot.log` | `4c9970493923b23d961979105bc79b147a569bbd2b64487972dabe650ce76eee` |
| Native execution record | `bb103133a63954751e926cde03c2f92299280cbe8d3ae89600da11343eba98a9` |
| Parent terminal input/output validation | `2cc3888588e6b3e2a7094713f2eee59c6ce8dd7469c4de7fb8d5fab2cb612708` |
| Built `printoutcontact.f` | `4cf339d0b041034279ccbd9da9724b73ee8e1848005a63cb2bc6895f348d2af6` |
| Printer fixture execution | `d0272182a8478b2b54ebf0f58af57875d67ec5237a6d996fedec75801f8b4418` |

Producer SHA-256:
`9be21ca6856dd9892629c6e8dddec2120cf2e4ab5279dcb32f2c9372a00a22cb`.
Result SHA-256:
`ae44acf254748eb0c4ee01531ff62bc9ea41a41fd2d602f9168a7494c6608b13`.

The focused printer fixture validates output arithmetic and formatting, not
the live joint contact law. Exact emitted identity and resultant closure do
not prove physical contact completeness, explain the energy discrepancy,
establish solver convergence, or imply capacity or mechanical acceptance.
