# Left LEG retained-bolt affected-demand screen

This bounded screen applies the existing selected-baseline individual bolt methods to the new A12-rear and A1-rear corner forces for `lumber_leg_bolt_left_1` and `_2`. It consumes the 56 signed actions in the parent [onward-transfer register](../current-corner-left-leg-onward-transfer-register-attempt01/register.json), paired by bolt ID and load factor. It records all seven load states for each of the four case/bolt combinations. It does not import historical response forces into the new calculation.

The reused lateral method is `fea.thick_leg_checks.bolt_check` with `fea.dowel_yield.single_shear`, the same one-plane nominal-diameter check used by the baseline clear-space workflow. The new signed lateral vector is resolved against each member's original grain direction. The original inputs remain 12.7 mm nominal bolt diameter, 88.9 mm bearing in both members, Fyb 90 ksi, SG 0.5, Fe-parallel 5,600 psi, the existing perpendicular-bearing equation, zero gap, and the original fixed yield-reduction terms corresponding to Ktheta 1.25. No new load-angle Ktheta branch is adopted. The axial tie and lateral-plane force are paired at the same increment for the existing direct steel interaction formula; washer bearing and bending use the same provisional Grade 5 and washer assumptions.

| Case | Bolt | Peak lateral demand | Conditional lateral reference | Lateral ratio | Governing mode | Peak axial tension | Peak steel ratio | Peak washer bearing | Peak washer bending | Minimum clearance beyond old edge-screen requirement |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| A12-rear | left 1 | 1,183.332 N | 3,335.025 N | 0.35482 | IV | 262.707 N | 0.07805 | 0.07820 | 0.18373 | 1.060 mm |
| A12-rear | left 2 | 1,723.082 N | 2,966.394 N | 0.58087 | IIIm | 529.439 N | 0.11435 | 0.15760 | 0.37028 | 0.873 mm |
| A1-rear | left 1 | 377.513 N | 2,953.651 N | 0.12781 | IIIm | 71.602 N | 0.02485 | 0.02131 | 0.05008 | 21.349 mm |
| A1-rear | left 2 | 276.079 N | 3,303.898 N | 0.08356 | IV | 178.438 N | 0.01910 | 0.05312 | 0.12480 | 1.536 mm |

The directional grain angles, bearing strengths, all six per-bolt yield modes, signed forces, seven-state results and method inputs are in `affected-demand-screen.json`. Values below one (and nonnegative external-edge margins) describe these individual component screens under the reused assumptions; they do not qualify a bolt pair or joint.

The edge column reports clearance margin after the old method's 7D grain-end and force-directed 4D/1.5D depth-edge requirements; it is not the bolt's actual distance from an edge. The margin computation retains only the original outside stock boundaries. It says nothing about clearance to the ten new bores.

The precise geometry change is ten new candidate bores in `base_side_left` and none in `lumber_leg_left`; the two retained axes, receiver pair and hardware record are unchanged. The old individual edge rays, lateral-yield reference method, direct steel formula and provisional washer checks can therefore be applied to these new forces as a conditional component screen. The old external-edge calculation does not represent the ten added bores. Their effect on local group spacing, net section, tear-out and splitting in `base_side_left` remains unresolved. The result does not inherit the old case status, group result or six-case pass, and does not blanket-qualify the twelve retained frame-bolt arrangements.

Nominal-diameter resistance still depends on actual thread/runout leaving no more than one quarter of either timber bearing length threaded under NDS 12.3.7.2. The schedule's thread dimensions and purchased length remain blank, and delivered parts are unverified. The axial component screens also do not establish wood withdrawal, pull-through, preload or prying resistance. No joint acceptance is claimed.

Only the original nominal-diameter branch is applied. The separate full-thread-root sensitivity remains non-adopted and is not transferred into this screen.

Reproduce and check the source pins and calculation from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-left-leg-affected-demand-screen-attempt01/produce.py
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-left-leg-affected-demand-screen-attempt01/produce.py --verify
sha256sum -c docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-left-leg-affected-demand-screen-attempt01/SHA256SUMS
```
