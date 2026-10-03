# Parent disposition of resumed STI17 source review

All three independent source reviewers completed against target SHA-256
`8bec53f223af3d770ea8df541d2b0cb47eeac89fee721103ae046ca55703f7e8`.
Each authenticated all 15 inputs. The original target and its source archive
remain unchanged. No build, freeze or native coupon was launched.

## Confirmed findings and fixes

- The coupon preparer contained a mistyped manual digest. The actual manual
  and already authenticated stock profile agree. Preparation now checks the
  manual against that profile's recorded digest. A regression exercises the
  real pinned inputs through this gate and stops at absent terminal receipts.
- The launcher could accept a relabeled, self-hashed deck/model under the
  coupon scope. It now requires the canonical attempt directory and the
  exact retained deck and model before any Docker call. Independent negative
  tests cover a relabeled deck, model and directory.
- The invocation used a PATH-resolved timeout name. It now names
  `/usr/bin/timeout`, verifies its known hash during binary preflight, and
  records that path/hash in authorization and execution. The result checker
  requires both bindings and the absolute command. Final-image runtime
  qualification remains required.
- The freeze could change between initial review verification and locked
  reservation. The locked check now revalidates scope/payload and requires
  the same reviewed freeze hash before authorization. The payload deck has
  an additional read-only bind mount. Source-only tests replace the freeze
  during preflight and verify that no run is reserved.
- Build readiness and the build-input freeze now carry the exact final
  source target and three independent report hashes. Both the freezer and
  builder verify these records and require each frozen target input to have
  its reviewed hash. A synthetic test covers source, frozen-map and report
  drift. Parent retains responsibility for reading and dispositioning the
  reviews before writing readiness.

Architecture's statement that the freezer omitted its own source was
incorrect: its `INPUT_PATHS` already included
`freeze_sti17_build_inputs.py`. That portion is rejected. The missing explicit
binding to the final reviewed target was confirmed and fixed as described.

The read-only mount prevents container writes to the deck. The parent still
owns the frozen directory and must preserve it without host edits during
execution; no claim of a cryptographically immutable host filesystem follows.

Focused checks after these fixes pass 26 tests, 47 subtests and Ruff. A fresh
three-role review of the final bytes remains required before build readiness.
All 47 criteria remain pending; the original A12 STOP and physical release
flags are unchanged.
