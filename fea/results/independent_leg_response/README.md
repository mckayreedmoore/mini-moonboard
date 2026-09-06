# Actual bent-leg independent-ply response

All four solver jobs completed normally; all 24 load cases passed the frozen
global equilibrium and native-energy checks. The largest relative compliance
change between the two meshes was **0.1681%**, below the predeclared 5% diagnostic.
This is an isolated **fixed-bore linear compliance experiment**, not a complete
frame response, physical loose-bolt/contact simulation, material capacity,
buckling calculation, or construction approval.

## Result and design implication

Fine-mesh work-conjugate compliance, mm/N (unit load work divided by force²):

| Construction/loading | X, out of ply plane | Y, in plane | Z, in plane |
| --- | ---: | ---: | ---: |
| Bonded reference | 0.22448507 | 0.010345689 | 0.0014395830 |
| Independent, evenly shared | 0.88048813 | 0.010348933 | 0.0014399508 |
| Independent, inner only | 1.76097120 | 0.020697510 | 0.0028798531 |
| Independent, outer only | 1.76098130 | 0.020698225 | 0.0028799502 |

Evenly shared independent plies have **3.9223×** the reference's out-of-plane
compliance, while their two in-plane compliances differ by less than 0.04%.
The one-ply-loaded cases are approximately 7.8445× out of plane and 2.0006×
in plane. These are compliance ratios, not reductions in allowable load or
buckling resistance. They are consistent with the mechanism isolated in the
[straight-strip control](../independent_ply_control/README.md), without forcing
the bent, drilled, ν=0.3 specimen to follow that control's exact ratios.

The practical recommendation is to **resolve leg composite action and lateral
restraint before substituting deeper perimeter rims**. An unqualified glue
joint cannot be credited as the bonded reference merely because it matches its
CAD envelope. Conversely, a no-adhesive-credit two-ply assembly is not ruled out:
its actual connectors and restraints must be designed and checked. This study
does not establish which leg mechanism governs the complete frame or show that
2×8 rims have sufficient resistance.

Do not multiply these isolated linear values by a climber's weight and call
that a predicted board deflection. The imposed unit loads, fixed fixtures,
generic material, absent inter-ply contact and geometric linearity limit that
interpretation. Real frame load allocation remains a separate question.

## What was modeled and verified

- Current drilled right `2x8-foot100` leg, split in global X into two 19.05 mm
  plies, with the knee, four bores and flat floor edge preserved.
- The [verified matched meshes](../independent_leg_mesh/README.md) are reused
  without changing element geometry. Bonded nodes remain shared; independent
  interface nodes are duplicated. All four cylindrical bore surfaces are fixed
  in XYZ. Full floor faces receive distributed unit forces in X, Y and Z.
- Generic homogeneous E=7000 MPa, ν=0.3; no gravity, inter-ply contact, stitches,
  connector slip, friction, material nonlinearity or geometric nonlinearity.
- Equal sharing and both single-ply load cases. Single-ply loading shifts the
  traction centroid by ±9.525 mm; the corresponding Y/Z force moments are
  recorded rather than hidden with a corrective couple.
- Force and moment balance uses undeformed coordinates, appropriate to this
  linear experiment. The largest whole-specimen residual components across
  the study were 1.37e−6 N and 0.002524 Nmm. Independent-ply balances also pass.
- Native `ELSE` energy is reported per ply. Its sum agrees with total half
  external work; each independent ply's energy also agrees with its own half
  work. The bonded ply energies are **not** inferred by dividing external work.
- Complete finite outputs, fixed/unloaded motion checks and the frozen gates
  are replayable. Max-displacement values are included in the JSON, but the
  mesh comparison concerns work-conjugate compliance, not peak stress.

## Provenance and replay

Original run: `fea/generated/independent-leg-response-c_big87g`. Docker image
ID `sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`,
CalculiX 2.21, two OpenMP threads and a 120-second cap per job. The predeclared
runner and mesh artifacts were committed as `b844b0e` before launch.

`evidence.tar.gz` preserves exact launch-source snapshots, decks, mesh inputs,
fixture metadata, raw outputs and terminal records. `report.json` includes
hashes and all per-case results. `publisher.py` is the exact later publication
source: publication/replay code was added after the solver run, without
altering the launch snapshots or original outputs. The replay regenerates every
deck exactly, binds the selections to the separately verified mesh archive,
checks raw hashes, and recomputes the energy/balance/compliance comparisons.

Independent pre-run review identified and resolved incomplete fixture-data
authentication, missing per-ply energy accounting and an omitted source
dependency snapshot. Subsequent implementation, archive-replay and result-prose
reviews found no substantial remaining findings within this experiment's scope.
The session's agent limit prevented a fresh three-agent parallel review; these
reviews are not represented as that full protocol or as structural approval.

```sh
uv run pytest -q tests/test_independent_leg_response.py
```

Next compare an actual mechanically connected or qualified laminated leg using
identified panel properties and real connector behavior. Then evaluate its
global/lateral stability and frame load allocation; do not select a stitch
schedule or advertise a climber rating from this control experiment.
