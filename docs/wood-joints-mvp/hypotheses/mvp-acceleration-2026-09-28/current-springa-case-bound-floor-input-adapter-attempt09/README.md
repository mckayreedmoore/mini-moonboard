# A12-left strict-normal screen and one input proposal — attempt09

**Status:** input proposal ready for parent review; no selected-branch response
or corner actions are available from this packet.

The direct a12-left selected-floor attempt02 is the rejected 10-cell run. Its
terminal assessment reports the strict exception “Inactive floor normal is
not strictly separated with zero endpoint RF: SPR1302.” The source-bound 711
zero-U interval replay classifies all 100 normals at all seven printed
increments through load factor 1.0. The same 11 cells are strictly positive,
the other 89 strictly separated, and no interval is unresolved at any state.
`SPR1302` (`floor_lumber_leg_left_1`) is the only branch mismatch: it is
strictly positive while inactive in the rejected 10-cell input.

The one new input proposal selects that case-specific 11/89 strict set. It was
prepared with the immutable attempt02 adapter API from the original a12-left
all-bearing controls and fresh a12-left case record. The adapter's source
preservation audit and an independent serialized-deck/source-wrench audit
both pass. A separate case-context audit also passes. The audited deck keeps
the 50 bodies, 92 new bolt axes, 12 retained leg/runner axes, and 66 Hillman
axes; it reports no geometry, law, load, or material changes.

The rejected attempt02 model, DAT, and execution are used only as same-case
normal-classification lineage. No rejected connector forces, a12-rear or
A1-rear response states, or screen forces are adopted. The new 11/89 proposal
does not establish accepted floor support, a selected-branch equilibrium
response, usable connector forces, corner demand, resistance, or joint
acceptance. No freeze or native run was performed.

## Pinned artifacts

- [Strict 711 interval diagnostic](../current-springa-a12-left-normal-interval-diagnostic-attempt01/a12-left-normal-intervals.json), SHA-256 `029244c02a57ddbe2dff9abd1c2afd3533e39f23a387e37e472b742c9ba53f86`.
- [Case-bound screen](a12-left-screen.json), SHA-256 `9cfad72bcae52d1023b7281321de92f05bde0c3dfa54f2122be12e67018a1139`.
- Proposed [model record](a12-left/model.json), SHA-256 `9e1347fcd5168a465d0994eca361dfd16f7ffc81dfaabf138f7a1fa11f310fd0`, and [deck](a12-left/model.inp), SHA-256 `bda415108a68af5dadd2f8cfecf542c2ab3f3d96ea9f79925b96f48e63823d0d`.
- Adapter algebra/source-preservation audit: [audit.json](a12-left/audit.json), SHA-256 `0bb7bfbd404eba6ef7f03576c7673872e4c8b848b34f9931290d2f7bd9ffdee0`.
- Independent serialized-deck/source-wrench audit: [independent-deck-audit.json](a12-left/independent-deck-audit.json), SHA-256 `ee7935d4bb3f28a32c122d04ed3ed88727a3ebc21dcfb82a6b5b29a48b11d9be`.
- Independent case-context audit: [independent-context-audit.json](a12-left/independent-context-audit.json), SHA-256 `a8bc362b569ba1880cbcb95cdfed5db010e416ee9ffbb4a4355d49f9f24b255d`.
- [Adapter source-pin ledger](a12-left/source-pins.json), SHA-256 `e28e98c7bb6d5d01da447d7f7f6df206ff50cba5f1a489f711f328136eb05243`.

The interval method is the pinned [zero-U wrapper](../current-springa-zero-u-token-response-audit-attempt01/response_audit.py), SHA-256 `711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0`. The new model/deck were emitted by the immutable [adapter attempt02](../current-springa-case-bound-floor-input-adapter-attempt02/prepare.py), SHA-256 `1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc`.
