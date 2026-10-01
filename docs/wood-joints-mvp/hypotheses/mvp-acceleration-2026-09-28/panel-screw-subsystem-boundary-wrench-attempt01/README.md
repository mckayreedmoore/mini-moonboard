# Panel/screw subsystem boundary wrench — attempt01

## Result and stop condition

This packet derives the signed aggregate wrench that the remainder of the
frame must apply to the selected panel/screw subsystem to balance each frozen
climber load and that subsystem's source-assigned own weight. The subsystem
contains six panel bodies, 142 T-nuts, and 66 modeled panel/kicker screw-axis
mass proxies. It is a source-bound static free body, not an installed or
mechanically accepted assembly.

At the conditional mass scenario, the included subsystem is **74.044731 kg**
with a computed center of mass at `(-1.873, 678.050, 1106.366) mm`. Its
source-assigned gravity is `(0, 0, −726.131) N`. The table gives the required
reaction **from the remaining frame onto the subsystem**, resolved at that
center of mass:

| Case | Global force `(Fx,Fy,Fz)` (N) | Global moment `(Mx,My,Mz)` (N·mm) |
|---|---:|---:|
| `a12-rear` | `(0, −300, 2,950.242)` | `(2,203,161.767, 2,262,648.896, 305,198.224)` |
| `a12-forward` | `(0, 300, 2,950.242)` | `(1,673,481.350, 2,262,648.896, −305,198.224)` |
| `a12-left` | `(300, 0, 2,950.242)` | `(1,938,321.558, 2,527,489.104, −261,451.213)` |
| `k12-right` | `(−300, 0, 2,950.242)` | `(1,938,321.558, −2,450,412.928, 261,451.213)` |
| `k12-rear` | `(0, −300, 2,950.242)` | `(2,203,161.767, −2,185,572.720, −294,801.776)` |
| `a1-rear` | `(0, −300, 2,950.242)` | `(−1,480,804.363, 2,262,648.896, 305,198.224)` |

These are aggregate receiver/bearing resultants only. They give no individual
screw, face, block, or member action and no connection resistance check. The
net reaction follows from whole-subsystem equilibrium; internal panel-panel
actions cancel because all six panel bodies are included.

**Stop:** Do not partition these resultants among receivers until a supported
attachment/bearing law and force-sharing basis exist. The panel-withdrawal,
receiver-transfer, floor-support, and member-demand gates remain open. The
separate 25 kg accessory allowance is excluded because its body split and
placement are unresolved; it must be added to the appropriate subsystem once
that assignment is supported.

## Reproduce

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-subsystem-boundary-wrench-attempt01/produce.py --verify
cd docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-subsystem-boundary-wrench-attempt01
sha256sum -c SHA256SUMS
```

The producer pins the current six-case load contract, mass/centroid record,
attempt04 full-frame manifest, and governing `AGENTS.md`. It recomputes each
included mass and gravity wrench, checks the standoff load wrench and reference
translation, then closes all six aggregate force/moment balances. It also
recomputes each reaction moment by summing about the global origin first and
translating the result to the subsystem centroid; the maximum difference from
the direct reference-point calculation is `4.66e−10 N·mm`. `--verify` does not
write files.

## Scope and limits

- Panel mass uses the source's conditional `600 kg/m³` density. T-nut masses
  and the 66 screw-axis masses are source-assigned CAD values/envelopes, not
  observed hardware weights or delivered lengths.
- The climber loads remain the frozen direct-to-panel wrenches. This bypasses
  physical hold/T-nut force transfer, as in the registered load contract.
- The 25 kg accessory allowance, 20 frame timbers, 24 blocks, candidate block
  bolts/nuts/washers, and retained frame bolts are outside this subsystem.
- This boundary resultant is not a local contact or fastener demand, does not
  prove the system is connected, and cannot be checked against a single-bolt
  capacity. No force-sharing or non-interaction is inferred.
- The result is not a full-frame response or a six-case acceptance. No
  geometry, criterion, native input, mesh, or solver run changed.

## Source pins

| Source | SHA-256 |
|---|---|
| [Governing AGENTS.md](../../../../../AGENTS.md) | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| [Six-case load contract](../../evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| [Mass/centroid record](../../evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json) | `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a` |
| [Attempt04 full-frame manifest](../../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json) | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |

The generated result pins the producer and these inputs. Packet hashes are in
[`SHA256SUMS`](SHA256SUMS).
