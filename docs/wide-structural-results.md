# Wider-principal structural diagnostics

These are completed numerical diagnostics of `wide-principal-development`, not
connection capacity FEA or construction approval. Both meshes use the same
source-bound geometry and loading. Results from the narrower timber model are
preserved separately; its asymmetric cases have not been transferred here.

## What changed and what the calculation says

The two wider principals and their matched post blocks increase the included
model mass from 176.36 kg to **200.04 kg**, approximately 23.68 kg (52.20 lb).
Both estimates assume wood density 600 kg/m³ and bracket steel 7850 kg/m³;
they exclude fasteners, inserts, holds, LEDs and glue. Display insert reservations
also differ from actual installation pilots. These are not measured build weights.

| Diagnostic | 60 mm mesh | 40 mm mesh |
| --- | ---: | ---: |
| Nodes / quadratic tetrahedra | 76,195 / 40,645 | 153,552 / 82,839 |
| Maximum loaded-point displacement, 1.2 kN downward | 0.879 mm | 0.879 mm |
| Maximum loaded-point displacement, 2.4 kN downward | 1.759 mm | 1.757 mm |
| Downward 1.2 kN plus 0.3 kN outward | 1.128 mm | 1.124 mm |
| Downward 1.2 kN plus 0.3 kN inward | 0.631 mm | 0.633 mm |
| Normal load, either sign | 1.326 mm | 1.316 mm |

The 2.4 kN loaded-point displacement changes approximately 0.071% between
these meshes. This is a two-mesh displacement comparison, not local stress or
joint convergence. The preceding timber model reported 2.075 mm under the same
five-point 2.4 kN loading; the wider model reports about 15.3% less displacement.
Neither small displacement establishes adequate strength.

The 60 mm mesher warned about one ill-shaped tetrahedron. The accepted mesh has
positive minimum sampled Jacobian 0.4223; the 40 mm mesh gives 0.9400. Both
straight-sided quadratic meshes pass the existing element, midpoint and global
force/moment replay checks. Volume differences from CAD are approximately
0.0353% and 0.0369%. These checks do not establish accurate local stresses.

## Model limitations

Wood is isotropic elastic material with E = 7000 MPa and Poisson ratio 0.3.
All touching wood, including separate leg plies and leg-to-upper-panel edges,
is ideally bonded. Floor nodes are fixed in all three directions. Fasteners,
clips and their holes are omitted from the bulk model; service pockets and
housings remain. There is no gravity, slip, separation, material strength,
buckling, real connector compliance or unanchored contact analysis.

Each load is shared equally among corrected-grid A12, C12, F12, H12 and K12
face nodes. Reported displacement is the maximum at those five loaded nodes,
not the whole mesh or a single loaded hold. The normal cases and force vectors
are recorded explicitly in the archived inputs. Do not interpret an upward
diagnostic case as a claimed real climbing load combination.

The separate rigid moment screen covers 96 envelope cases at 150/200/250/300 lb.
Minimum moment ratios are approximately 2.159 / 2.088 / 2.022 / 1.960 against
the selected illustrative 1.5 screen. Added assumed mass helps those ratios;
the screen does not resolve sliding, yaw, local lift-off or joint resistance.

## Decision

Keep the wider version as an inspectable **edge-clearance alternative**, not a
proven minimum-weight requirement. It clears the selected lateral backing-bolt
edge-distance screen, but adds considerable mass and does not enlarge the
washers or the backing's counterbore ligament. A defensible local joint demand
and resistance comparison must decide whether that tradeoff is justified.
The [connection qualification ledger](connection-qualification-ledger.md)
identifies the missing evidence rather than treating it as passed.

## Reproduction and provenance

The [40 mm](../fea/results/wide-principal/mesh40.json) and
[60 mm](../fea/results/wide-principal/mesh60.json) records include compressed
input decks, displacement/reaction output, context, solver logs and status
files. The [moment record](../fea/results/wide-principal/stability.json)
retains its assumptions and source hashes. All were generated on 2026-09-08
using the existing `mini-moonboard-fea:box-v1` Docker toolchain and two OpenMP
threads; no new solver dependency was added.

```bash
uv run pytest -q tests/test_publish_wide_structural.py tests/test_wide_evidence.py
```

Fresh generation uses `python3 -m fea.wide_structural prepare`, followed by
`python3 -m fea.wide_structural solve --size 60` and `--size 40` in that Docker
environment. Run heavy jobs sequentially. Preparation and publication refuse to
overwrite existing evidence; use a fresh checkout/work location for reproduction.
The publisher is `python3 -m fea.publish_wide_structural <60mm-result> <40mm-result>`.

The frozen input records the original local geometry commit `893bf52` and exact
source hashes. The user's evening publication policy may later change that
unpublished commit's timestamp and ID. Preserve the original provenance and a
commit mapping if that occurs; do not relabel an old solve as a new execution.
