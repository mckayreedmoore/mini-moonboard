# Parameterized case-bound floor input adapter, attempt 02

This packet contains an input-only a12-left selected-floor proposal. It binds the fresh a12-left source model and load-register row to the a12-left all-bearing controls and the rejected all-bearing screen. The screen has 10 strictly positive floor cells and 90 strictly separated cells at all seven recorded states, so the prepared branch contains 20 active tangent rows and 180 inactive rows. The selected transform is full rank. The screen forces and active states are not adopted as response.

The prepared model/deck and their case-local audit, pin ledger, and context are in `a12-left/`. The local read-only case-bound input validator passed. Geometry, materials, source loads, normal SPRINGA carriers, retained bilateral SPRING2 rows, and INC=40 controls remain bound to the selected case controls. This proposal establishes no floor qualification, accepted support, mechanical acceptance, or corner demands. No freeze, native run, or response ledger was created.

The first emission is retained under `first-emission-rejected-by-input-contract/` as a superseded input draft. Use only the case-local artifacts under `a12-left/`.

The exact source-bound invocation was:

```bash
./.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt02/prepare.py \
  --case-id a12-left \
  --control-dir docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-a12-left-all-bearing-attempt01 \
  --screen docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-a12-left-floor-screen-attempt01/screen.json \
  --register docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-six-case-source-load-register-attempt01/register.json \
  --fresh-case-model docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-six-case-frame-input-adapter-attempt01/a12-left/model.json \
  --output-dir docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt02/a12-left \
  --diagnostic-stage all-bearing \
  --expected-control-model-sha256 4794fb54a8761db8a14b8058bc517e9f5b8b69ffcedea574c1911f79657e9781 \
  --expected-control-deck-sha256 7543c3500d185f21c1a27ac7d949235832210dea2a2c802114dd3d6376e62487 \
  --expected-control-dat-sha256 3dc673b0d33048ed421e4677988b5ac9b63bf5b9ed753b7f96fa35b4cb79cb13 \
  --expected-control-execution-sha256 510366c340fa5007af446efb0fc1a436344a7ed276392f8418cdeb3193e38c7a \
  --expected-control-freeze-sha256 9dca9e49aac519b818fb9017ad69e8d6675b8e7b087c487d789cfaf2d4bebc57 \
  --expected-control-authorization-sha256 ba8bb6d2fa18316938ebc484e2c0b04b3efcd233a0780a4da0175655b69ae51a \
  --expected-control-parent-audit-sha256 6c40c26f078b22f9a0a0f2deecfdfb5c1dcad6e29d629e2c638cd41dea7faf86 \
  --expected-screen-sha256 0a04bfad5068b4f20cdb69eab5198e57d25052d1a1db84c70af4b2b67677fdf6 \
  --expected-register-sha256 7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508 \
  --expected-fresh-case-model-sha256 4d56602abb6a2325b4cf08d2adbbc92b405cf1435eaf0c356a0e1da9d50a0473
```
