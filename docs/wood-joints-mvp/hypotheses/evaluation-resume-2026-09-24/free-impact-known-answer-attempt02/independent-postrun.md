# Independent post-run audit

This read-only audit records attempt02's frozen native result. The note is post-run and outside the frozen local inventory; no frozen packet file was changed. This method fixture does not qualify the joint or authorize release.

## Freeze, provenance, and raw-file integrity

The freeze is SHA-256 `5efc117c64a614eb73c07a75e8f539bde3315f9b92cd9969e2dee640a890c656`. I independently compared every recorded file hash: all 12 local frozen files and all 27 external dependencies match. Its `native_execution`, `mechanical_acceptance`, and `joint_acceptance` false flags are the pre-run freeze scope; the later execution record below documents the two completed native cases.

The input is unchanged from attempt01, SHA-256 `2b253f63f9e8cee1bcb471ba3fb6b8150e72df781432bcfe6a1019e66d44caea`; expected contract SHA-256 is `d9364226a70cd3085b2b23eb7234ddaccfa6d33c57eccb5084cb0a73adc7a72d`. `correction.json` is `3bd2b5c29cb7f3186143ee1a36b5835487ac2274f05f6d4c677dd287f10bb5f3`; acceptance SHA-256 is `9641c84087f6fa13907f6d9561d8bd9c4a60aab704d3b6b9b29eb22c07c00b0a`. The correction changes only the predeclared pressure-law identity to source-defined code 2; it does not change input, solver, fixture, numerical gates, or tolerances.

Top-level execution record `output/execution.json` is SHA-256 `f91676d630acbb961838bb0df21d3beb37daca336be8f2e348ffd0c871435bf4`. It binds the same input for both cases and the attempt02 freeze, and records serialized `baseline` then `trace` captures. Each native case exited normally with code 0 under the pinned image and binary. Per-case output hashes in each execution manifest match the files on disk:

| Case | Case record SHA-256 | FRD SHA-256 | stdout SHA-256 |
|---|---|---|---|
| baseline | `716d2ae7940adcb103e1c50e65b9f648634e5a8b9317d2b49f450b46a59fb02a` | `99094a2326f8728a178a6ee5e954f62a18a994f1cbd2f37dea8c07ddfc3b9d49` | `d8869ca3e1ddbfe87eec43304df679b4b4cf2f4866a3f5db30636af1df70c8bd` |
| trace | `a16323a2aaa2068d16372e477fcb30ec084ac44007dadb5f1f4bbc001c57f6fd` | `c22a59547c109ea7b728f22108eeee593469b67e50514524dfed4cdbdd5f9f53` | `8739cc23bd940ea61aa19ac32c868060278b5804ae57514a222a29d271c7d5da` |

Both cases also have matching DAT SHA-256 `2b0fe3d61ba8aa67e40a0a845235bdf8da94cf409b670182706f1a2757b6d996`, CVG SHA-256 `eb9798fe5fe2aa071989e07f1f9ec6f711c92f8edf7d566609f000fc4ca4a883`, and STA SHA-256 `b0409c83c04b9b230d8a1abf8cd5b28858cd363d24713eac0ea5335606b164d2`. The input copy hashes match the prepared input. `coupon.12d` and `solver.stderr` are empty in both captures.

## Verifier replay and trace results

The saved [verifier result](verifier.json), SHA-256 `9b77b85a508740c004d2f531eda0e70932c1a80207ed1c378c720774e62a6fba`, reports `PASS_FREE_IMPACT_KNOWN_ANSWER`; baseline, trace, and their comparison all pass. I reran its read-only `--audit-dir output` path: the regenerated JSON exactly equals the saved result. Each case has 70 accepted states from 0.0001 s through 0.007 s, 70 FRD frames, zero unaccepted FRD frames, and 141 CVG iterations.

Raw trace counts independently agree with the verifier: 7,896 MAP rows and 5,544 TRIAL rows, with zero UNMAPPED rows. Every MAP identity is `(tie=1, nmethod=4, pressure_law=2)`. Of the MAP rows, 2,352 have positive signed gap and all are filtered (`isol=0`); 5,544 are generated rows. Trial rows cover every nonzero CVG contact count, while 42 zero-count CVG identities correctly have no TRIAL rows. The 56 positive-gap TRIAL rows occur only at step 1, increment 50, attempt 1, iteration 1; the frozen contract treats those old-set observations as diagnostic and does not require them. The overall trace coverage and numerical checks pass without changing any gate.

## Source and acceptance boundary

The freeze pins the CalculiX source archive SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` and trace diagnostic patch SHA-256 `8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff`. Relevant archive member hashes are `surfacebehaviors.f` `f0088a364b9b069aa10be9c4b4f38d72df875295f339830d7e2df6762ad9e161`, `contactpairs.f` `e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488`, and `gencontelem_f2f.f` `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe`. `surfacebehaviors.f` lines 66–67 select the LINEAR branch and lines 194–200 assign 2.5; `gencontelem_f2f.f` lines 554–560 use `int(elcon(3,1,imat))`, and the trace patch records that same integer, yielding code 2. `contactpairs.f` lines 115–118 assign `mortar=1` to `TYPE=SURFACE TO SURFACE`, a separate contact-pair field. The raw trace therefore matches both the pinned implementation and corrected frozen expectation.

The saved verifier keeps `mechanical_acceptance`, `work_energy_acceptance`, `joint_acceptance`, and `release` false. This passing result closes the narrowly scoped free-impact known-answer and trace-classification fixture only; it does not accept the wood joint or broader contact mechanics.
