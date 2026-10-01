# Upper outer joint load-path implementation

This packet turns the two top outer joints' existing simultaneous actions
into replayable receiver/pair wrenches and explicitly conditional section
actions. It also audits how the native attachment equations distribute
those forces. The same whole-body wrench does not identify the local
traction through a bored section.

The reviewed revision remains `led-clearance-2x6-runner-seated-blocks-v1`.
Three authenticated rear cases supply seven increments each: two blocks,
eight bolts and 42 block states. All actions retain their source increment,
receiver, position, sign and RF rounding interval. There is no new solve or
geometry change.

The host extraction retains four interfaces, 84 interface states and 63
whole-host balances. Its cuts bracket the finite contact polygons, with
explicit terminal traces where the rail patches reach the member ends.

## Implemented evidence

| Calculation | Source-bound result | Use boundary |
| --- | --- | --- |
| [Block actions](actions.md) | Separate lateral, axial-seat, face-contact and discrete gravity actions; paired receiver wrenches and both traces at five cuts per block | Point-action equilibrium reference; no regional share or stress assigned |
| [Native load transfer](nodal-transfer.md) | 672 connection transfers and 42 complete block states preserve receiver and whole-body force/moment | Generalized gross-element nodal loads; selecting nodes across a cut is not stress integration |
| [Host actions](host-actions.md) | All incident source actions on the common top rail and left/right side hosts; two-sided section inputs around each transfer zone | Same-state point-action host model, with finite-patch and neighboring-load coverage stated |
| [Splitting applicability](splitting.md) | Member-specific first-generation EC5 source/figure and shear-input mapping | Characteristic-method scenario only where its arrangement fits; cleat interaction and design conversion remain separate |

The source native representation has one gross rectangular C3D20 element
per outer block. The finished STEP geometry includes four bores that the
source element omits. The nodal audit measures point-versus-node cut
selection differences up to 824.989 N and 28,615.447 N mm, while complete
connection wrenches still agree. Neither simple selection is accepted as a
finished-section traction field or as a strength failure.

The [previous upper-strength packet](../upper-block-strength-2026-10-01/README.md)
still records the two top outer unadjusted nominal-diameter lateral ratios,
1.1631 left and 1.3667 right. Those use an unadopted 106 ksi bending-yield
estimate. This packet does not resolve them by choosing a favorable factor,
combining independent maxima or transferring acceptance from another design.
The newer [Fyb disposition](../fyb-specification-basis-2026-10-01/README.md)
corrects the empirical estimate's attribution to nonmandatory Appendix I.4.

## Implementation handoff

Use complete pair and receiver force/moment records to retain the bolt
couples, contact and axial transfer. A resultant alone cannot replace the
two bolts' individual actions. Use the host's shear on each side of the
connection for an applicable splitting method; a sum of bolt cross-grain
components is not that input.

Bind any local strength calculation to its stated load-transfer model,
finished paths and applicable adjusted properties. The split regions at a
cut do not authorize equal or area-based load sharing. Complete oblique
cleat splitting, local bearing/tear-out, bolt/washer coupled behavior and
the remaining three frame cases remain integration dependencies.

The mechanics coordinator owns gravity/contact continuation, the full
six-case response and BG001/BG003/BG045. The main MVP owner retains the
washer resistance, hardware-fit and integrated criteria work. Root owns
this isolated upper implementation and final validation. Every completed
deliverable is handed to those owners before selecting the next disjoint
task under the continuing assistance goal. This packet alone does not end
that goal.

## Frozen consumed evidence

Raw JSON remains local. The public identities below identify the exact
source records rather than linking to ignored data. Model and response
paths are under
`hypotheses/mvp-acceleration-2026-09-28/`, relative to `docs/wood-joints-mvp/`.

| Case | Model / response folder | Model SHA-256 | Response SHA-256 |
| --- | --- | --- | --- |
| A1-rear | `current-springa-selected-floor-a1-rear-attempt02/`; accepted `response-zero-u-token.json` | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` |
| A12-rear | `current-springa-selected-floor-a12-rear-attempt03/` | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` |
| K12-rear | `current-k12-rear-spr489-direct-native-attempt01/` | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` |

| Parent all-body audit | SHA-256 |
| --- | --- |
| A1-rear `parent-all-body-response-audit.json` | `247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca` |
| A12-rear `parent-all-body-response-audit.json` | `3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5` |
| K12-rear `audit.json` | `66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee` |

The exact upper action and geometry report hashes are recorded in
[nodal-transfer.md](nodal-transfer.md); the executable point-action source
pins also bind the two block STEP solids and source producers.
The splitting note records primary-source editions, URLs, pages and hashes.
No historical-case acceptance, selected-baseline authority, received-part
observation or physical-work release transfers.

## Local replay

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/actions.py --verify
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/nodal_transfer.py --verify
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/host_actions.py --verify
uv run --no-sync pytest -q docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01
```

The source environment and ignored frozen evidence are required. Verification
means reproducible calculation, not accepted strength. Independent review,
test results and parent checks are recorded in [review.md](review.md).
No complete joint, fabrication operation or climbing is released here.
