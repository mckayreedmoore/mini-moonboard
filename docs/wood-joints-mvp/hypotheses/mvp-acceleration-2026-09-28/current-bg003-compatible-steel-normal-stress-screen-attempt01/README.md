# BG003 compatible proxy smooth-section normal stress

This screen converts the **four saved 32-division A12-rear BG003 bolt-1
radial-clearance scenarios** into a conditional smooth, 6.35 mm circular
section normal-stress comparison. It adds no solver run. The signed-demand
register has two lateral rows for this one bolt at the same full-load state;
both rows carry the exact same 95.96739 N outer-seat tie. The producer checks
that the tie vectors, endpoints, role, case, axis and load factor match, then
uses that single physical tension action once.

For a solid circle, `A=πd²/4`, `I=πd⁴/64`, and `Z=I/(d/2)=πd³/32`.
The packet's hand check applies the signed pair `(My,Mz)=(3,4) N·mm` to the
linear stress field `(My·z−Mz·y)/I`; at the tensile extreme radius it equals
`hypot(My,Mz)/Z`. The saved signed middle-cut pair is retained in each row.
The separate sampled peak is the radial diagnostic's paired moment-vector
norm, sampled at its mesh nodes. The screen computes `T/A + |M|/Z` and compares
that proxy normal stress with the current hardware packet's conditional 92 ksi
SAE J429 Grade 5 machine-test yield reference (`634.317671 MPa`). It does not
add independent Y/Z stresses or capacities.

| Hypothetical line `k` (N/mm²) | Modeled radial gap (mm) | Signed middle-cut `(My,Mz)` (N·mm) | Middle-cut `|M|` (N·mm) | Saved sampled peak `|M|` (N·mm) | `T/A + sampled |M|/Z` (MPa) | Ratio to 92 ksi |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0 | `(2469.114, 1594.100)` | 2938.993 | 4401.575 | 178.131 | 0.280822 |
| 100 | 0.575 | `(1932.730, 1247.664)` | 2300.459 | 3497.620 | 142.170 | 0.224131 |
| 1,000 | 0 | `(127.014, 82.002)` | 151.185 | 2429.771 | 99.690 | 0.157161 |
| 1,000 | 0.575 | `(878.821, 599.001)` | 1063.546 | 1818.439 | 75.370 | 0.118821 |

All four saved sample-derived proxy stresses are below the conditional smooth
shank yield reference. The largest is 178.131 MPa (ratio 0.280822) for the
`k=100`, zero-gap scenario. This is only an elastic-proxy stress/reference
comparison. The foundation stiffnesses and gaps are uncalibrated hypotheses,
not physical bounds, and the nodal moment sample is not a proven continuous
maximum.

The Grade 5 basis is taken from the current
[hardware/material `fasteners.md`](../../hardware-material-specification-2026-09-30/fasteners.md)
and its pinned `fastener-inputs.json`: the supplier technical table attributes
92 ksi machine-test yield to the 1/4–1 in SAE J429 diameter band. The source
URL recorded there is [STS SAE J429 technical data](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j429-technical-data).
The current hardware packet says Ro-Brand `HC5127`, the BG003 catalog lead, is
not tied to exact J429 conformance. Therefore 92 ksi is a conditional material
scenario, not an asserted property of an actual BG003 bolt. The producer pins
the current hardware outputs, its source manifest and source cache, along with
the radial diagnostic's existing source chain and the signed-demand register.
It verifies the signed-demand and hardware/material packet replays without
rerunning the radial diagnostic.

The smooth full-diameter section excludes thread roots, thread runout,
transitions, notches and section loss. This does not evaluate shear, torsion,
preload, threaded engagement, combined steel resistance, fatigue, fracture,
steel design capacity, or physical contact bounds. It does not select a
stiffness or clearance, qualify delivered steel, or accept a joint.

Run from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-compatible-steel-normal-stress-screen-attempt01/produce.py --verify
```

`--verify` is read-only. `--write` regenerates only this packet's
`steel-normal-stress.json`; the one-time `--freeze-sources` mode refuses to
replace an existing source manifest.
