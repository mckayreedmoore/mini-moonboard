# Body-restricted `FORC_NODA` known-answer

This fixture checks Code_Aster 17.4's `CALC_CHAMP(FORCE='FORC_NODA',
GROUP_MA=...)` route on a flat, fully active PENTA15/TRIA6 contact coupon. The
deck calculates the field on only `S_SOLID`, writes it to a separate result
concept, and sums it at the existing nine-node `SLNOD` interface. It does not
change the mesh or physical solution block.

The flat coupon has an analytic pressure resultant of `3000 N`. The frozen
audit finds the body-restricted surface resultant matches that value, the
full-domain interface field, the opposite slave `RN` action, and the same-body
cut force within `4.8e-13 N`; its first moment about the patch center is
`7.9e-12 N·mm`. The attempt and audit are in
[`contact-body-restricted-forc-noda-known-answer-attempt01`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/contact-body-restricted-forc-noda-known-answer-attempt01/)
and its `parent-audit.json`.

Prepare the fixture from the hash-checked flat baseline with:

```sh
.venv/bin/python fea/code_aster_trial/contact_body_force/prepare_body_force_known_answer.py
```

The parent serialized execution uses `run_frozen.py` and the pinned image
recorded in `readiness.json`. The offline audit is:

```sh
.venv/bin/python fea/code_aster_trial/contact_body_force/audit_body_force_known_answer.py
```

This validates one integrated resultant and first moment. The coupon fixes
`DX` and `DY` at all nodes, so pointwise tangential nodal forces are not a
contact-traction distribution. This result does not validate TETRA10 assembly,
curved pressure, joint behavior, or candidate acceptance.
