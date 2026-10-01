# Upper-block conditional lateral references

This packet recomputes the six unadjusted single-bolt lateral-yield modes for
the 32 axes in the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` revision. It combines the two
authenticated upper-joint action records without changing their state forces:
8 blocks, 32 axes, 3 rear cases, 7 states per case, and 672 same-state bolt
action rows (4,032 mode values). Each output row retains the source lateral
force vector and rounding radius, and the coincident axial force and tension.

The governing sampled states are the outer top blocks. Under the frozen
partial-thread scenario, the thread selector returns nominal `D = 0.25 in.`
for both members of these axes. The conditional DF-L No. 2 / `G = 0.50`
bearing inputs come from the pinned materials packet. The `Fyb = 106 ksi`
value is the existing unadopted commentary estimate, not a tested, guaranteed,
or received bolt property. The numbers below are component references, before
end-use adjustments and before any group or complete-joint treatment.

| Block and same-state source | Lateral demand | Six-mode minimum at `Fyb=106 ksi` | Governing mode | Demand / reference | Required common total multiplier for unity |
| --- | ---: | ---: | --- | ---: | ---: |
| Top outer left, `a12-rear`, factor 1.0 | 1,074.79 N | 924.08 N | IV | 1.1631 | 1.1631 (+16.3%) |
| Top outer right, `k12-rear`, factor 1.0 | 1,264.69 N | 925.36 N | IV | 1.3667 | 1.3667 (+36.7%) |

The final column is the algebraic factor product a single common resistance
multiplier would need to reach before it brings the unadjusted component to
unity. It is not a selected NDS adjustment or a pass. No duration, group,
wet-service, temperature, treatment, or other factor is adopted here. A factor
product of 1.0 leaves both outer states above unity; a smaller product raises
the ratios.

The six nominal-diameter values for those two axes are:

| Mode | Top outer left | Top outer right |
| --- | ---: | ---: |
| `Im` | 4,377.10 N | 4,382.16 N |
| `Is` | 3,480.14 N | 3,485.55 N |
| `II` | 1,804.61 N | 1,807.03 N |
| `IIIm` | 1,832.76 N | 1,835.04 N |
| `IIIs` | 1,594.43 N | 1,596.80 N |
| `IV` | 924.08 N | 925.36 N |

For left, the same-state lateral force is approximately `(0, -846.6104,
662.131) N` and the axial tension is `362.7086 N`. For right, it is `(0,
-1004.524, 768.3592) N` with `423.0656 N` axial tension. The computed
block/host load-to-grain angles are 1.971/88.029 degrees on left and
2.588/87.412 degrees on right. Their rounded `D=0.25 in.` bearing inputs are
about 5,598/4,451 psi (block/host) on left and 5,597/4,452 psi on right,
using the source `G=0.50` equations and each member's recorded angle.

The additional sensitivities keep these limits explicit:

- A hypothetical 45 ksi Fyb sensitivity gives unadjusted Mode IV references of
  602.09 N left and 602.92 N right, with demand ratios of 1.7851 and 2.0976.
  The source's Table I1/TR12 45 ksi example is limited to `D ≥ 3/8 in`; the
  Table 12A basis does not qualify a quarter-inch bolt. These figures are
  arithmetic only, not a table-qualified quarter-inch property, delivered-bolt
  qualification, or adopted design value. See the boundary in the pinned
  [fastener materials note](../hardware-material-specification-2026-09-30/fasteners.md).
- The separate `Dr = 0.189 in.` sensitivity treats all wood-bearing length as
  threaded in both members, with the same unadopted 106 ksi Fyb estimate. Its
  Mode IV references are 684.74 N and 685.69 N, giving ratios 1.5696 and
  1.8444. This is not the frozen partial-thread case: that case has 21.082 mm
  of thread-bearing length in the block and zero in the host, within the
  quarter-member rule for nominal D.
- Solving `CD × min(six unadjusted modes) = demand` gives the following minimum
  conditional Fyb values. These are non-group arithmetic illustrations using
  the declared CD multipliers only; no CD value is selected or applied to the
  672 output rows.

| Illustrative `CD` | Minimum Fyb, left | Minimum Fyb, right |
| ---: | ---: | ---: |
| 1.00 | 143.4 ksi | 198.0 ksi |
| 1.25 | 91.8 ksi | 126.7 ksi |
| 1.60 | 56.0 ksi | 77.3 ksi |

In the hypothetical 45 ksi sensitivity, even the illustrative `CD=1.60`
values remain below demand: 963.35 N left and 964.68 N right. This is not a
quarter-inch table qualification or an automatic Grade 5 bolt guarantee, and
no load-duration factor is adopted.

The original same-state steel records are carried into the machine output as
separate conditional references. For the two governing states they use the
pinned hypothetical Grade 5 material note, a typical 0.189 in. circular root
at the shear plane (not a delivered-part bound), and nominal 1/4-20 tensile
stress area. The source first-yield utilization values are 0.162/0.191 in
shear and 0.028/0.033 in tension, but the source leaves their interaction
unresolved because it lacks one co-located section area and basis. The
washer values compare only against an ideal annulus; they do not establish
actual washer or wood-seat capacity. No nut capacity comparison is made, and
no bolt bending demand is inferred from the lateral resultant.

## Replay and pins

The producer fails closed if any pinned source hash, schema, row count, axis,
case, thread selection, or replayed mode changes. It also runs the existing
partial-thread packet's own `--verify` check. The complete SHA-256 map is in
[`lateral.py`](lateral.py). Its primary inputs are the two action records
(`../upper-frame-joint-review-2026-09-30/upper-joints.json`,
`0fc5f9ce…c1994a6`; `../service-upper-frame-joint-review-2026-09-30/upper-joints.json`,
`f4c92d87…a2be9f`), the
local `../service-upper-frame-joint-review-2026-09-30/thread-scenario-freeze.json`,
the [DF-L No. 2 material note](../hardware-material-specification-2026-09-30/materials.md),
the [fastener Fyb scope note](../hardware-material-specification-2026-09-30/fasteners.md),
and the pinned
[2024 NDS Chapter 12 source PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
(SHA-256 `5fc83752…fe4ee2a`; §§12.3.3–12.3.4 for the conditional wood
embedment inputs). The exact original action and material pins are embedded
in the producer. The action JSON and thread freeze are local-only evidence,
excluded from the published source packet.

Run from the repository root:

```sh
./.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/lateral.py --write
./.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/lateral.py --verify
./.venv/bin/python -m pytest -q docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/test_lateral.py
```

The generated `lateral.json` is ignored local machine output. The packet
establishes no group resistance, splitting resistance, complete-joint pass,
geometry change, drilling/fabrication release, structural release, or climbing
release. Native solves are outside this calculation.
