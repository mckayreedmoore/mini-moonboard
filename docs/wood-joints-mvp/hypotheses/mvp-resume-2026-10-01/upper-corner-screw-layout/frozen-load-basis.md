# Actual frozen load basis

This note identifies the existing loads consumed by N15
[kicker-path completion](kicker-path-completion.md),
`rawlocal/kicker-path-completion/parent-attempt01`. It authenticates saved
inputs and external vectors; it introduces no geometry, load variant,
measurement prerequisite, test, solve or CAD execution. The analytical
no-slip floor, frame/contact/material assumptions and release flags remain
unchanged.

## Loads represented by the saved six cases

| Input | Actual frozen assumption |
| --- | --- |
| Modeled self weight | 225.19791414318078 kg at g = 9.80665 m/s²: 2208.4371247322238 N downward |
| Planning equipment | 25 kg once: 245.16625 N downward, distributed proportionally to modeled gravity through dead-load factor 1.1110134616260479 |
| Climber demand | One 250 lb source weight × dynamic factor 2; 250 × 0.45359237 × 9.80665 × 2 = **2224.11080763025 N downward** |
| Horizontal demand | One signed global X/Y component of **300 N**, simultaneous with the downward climber force; comparison horizontal and climber scales are both 1.0 |
| Hold application | One loaded hold per case; 20 mm square patch at the frozen hold-face datum and 100 mm outward-normal standoff |

The factor 2 is an equivalent downward dynamic-demand assumption. It is
already present in the saved force and is applied once. It specifies neither
a second climber nor a separate second 250 lb load. The six cases are
alternative hold/direction cases, not six concurrent loads. The horizontal
300 N is the recorded component; it is not doubled again.

The source [load contract](../../evaluation-resume-2026-09-24/current-load-cases.json)
records exactly these numbers. Fresh gravity updates retain its live forces
and moments. The current frame comparison records source/comparison weight
250 lb, climber scale 1.0, horizontal scale 1.0, and the same gravity factor.

## Saved external-vector check

N15's `body-balances.json` contains **300 records: 50 distinct bodies for
each of six cases**. Its producer forms each body's external wrench as
`dead_load_factor × W_gravity + W_live`, converting moments to Nmm. Summing
the first three components once per body gives:

| Case | Loaded hold/panel | Summed Fx, N | Summed Fy, N |
| --- | --- | ---: | ---: |
| `a12-rear` | A12 / `main_upper_left` | 0 | +300 |
| `a12-forward` | A12 / `main_upper_left` | 0 | −300 |
| `a12-left` | A12 / `main_upper_left` | −300 | 0 |
| `k12-right` | K12 / `main_upper_right` | +300 | 0 |
| `k12-rear` | K12 / `main_upper_right` | 0 | +300 |
| `a1-rear` | A1 / `main_lower_left` | 0 | +300 |

Horizontal entries above are rounded from saved sums; deviations are below
1.2e-12 N. All six saved Fz sums lie between **−4677.714182362475 and
−4677.714182362472 N**, matching:

```text
Fz = −[(225.19791414318078 + 25) × 9.80665 + 2224.11080763025]
   = −4677.714182362473 N
```

This agrees with the parent's −4677.71418236247 N to rounding. No supported
load discrepancy was found. Describing these results as two simultaneous
climbers would contradict the single applied-force record and its explicitly
named dynamic factor. Panel/receiver, contact and screw grouping views reuse
the same simultaneous actions; they add no external load.

## Lever and equivalent moment

The frozen outward normal is
`[−0.0, 0.7660444431189781, −0.6427876096865394]`.
Every saved force point is the hold-face/patch center plus 100 mm along that
normal: displacement approximately `[0, 76.60444431189781,
−64.27876096865394]` mm. Read-only scalar reconstruction gives 100 mm to
floating-point precision, with maximum component discrepancy below
1e-13 mm. A12 and K12 share the upper-panel height; A1 uses its separate
lower-panel datum.

The equivalent moment is `(force point − panel-midplane reference) × force`.
The 100 mm standoff starts at the face datum; the panel-midplane reference
is a different saved point. Thus the moment retains that face-to-reference
offset as well as the standoff. For A12 rear, the saved local moment is
`[−164885.11528647266, 0, 0]` Nmm. All six saved source moments reconstruct
exactly from their recorded points and force vectors in the scalar check.
This moment represents the same offset force, not another applied force or
an additional independently chosen hold couple. Moments at different body
datums must be shifted to a common origin before summation.

## Strength duration and 140 lb context

N15 retains the saved timber-reference comparisons at **C_D=1.0** and
conditional **C_D=1.25**, with the existing hypothesis of at most seven
cumulative days at full peak load. That conditional duration basis remains
unadopted. It changes only Fb, Ft parallel, Fc parallel and Fv references;
Emin, Fc perpendicular, applied demand, elastic stiffness and hardware
references are unchanged. **C_D is a wood-strength modifier, separate from
the dynamic factor 2 already included in downward demand.** Neither factor
implies climber count.

The separately executed [permanent comparison](knee-bridge-permanent-resolve.md)
uses gravity plus the same 25 kg allowance, once, with **C_D=0.9** and zero
climber, horizontal and hold-moment components. It does not replace the six
live-load cases. A contextual **140 lb** person does not change the frozen
250 lb basis or create a 140 lb response variant. These existing planning
assumptions are retained without a new personal-weight or equipment-placement
measurement gate. Documenting loads establishes no complete joint capacity
or climber rating.

## Authenticated evidence

The consumed N15 load leaves match its receipt source hashes; its saved
balance/report/snapshot outputs match the receipt output hashes. The load
contract matches the hash in fresh model inputs, and its producer matches
the contract's provenance hash. The saved timber-duration helper also matches
the member-result source pin. No source or raw result was changed.

Paths below are relative to this directory except the explicitly linked load
contract. The existing receipts preserve the wider source/output closures.

| Evidence | SHA-256 |
| --- | --- |
| `rawlocal/kicker-path-completion/parent-attempt01/receipt.json` | `c589a8227000b2afe9ac536cbb7b99e4000f7b6e8b1024066a7e8b43109da402` |
| `rawlocal/kicker-path-completion/parent-attempt01/body-balances.json` | `753679d69ed192eeee475811746852032bff5c49af23ff9f4bec481fa17483ad` |
| `rawlocal/kicker-path-completion/parent-attempt01/report.json` | `ed568d974c649e052cdde4c604482c23e611900cea7314f26e9426192a1f03e8` |
| `kicker-path-completion.py` and executed snapshot | `a1483fc420f463d0b5b692b231258c904f849b696851b7b3e227efa30b4256ff` |
| Source load contract linked above | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-gravity/attempt01/model-inputs.json` | `b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `rawlocal/knee-bridge-members/attempt01/checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| `member-duration.py` | `4407e780ade7a5f4f08eb586b6aea15130a6dd81ef747f535562a812f4a10c6d` |
| `rawlocal/knee-bridge-permanent-resolve/attempt02/comparison.json` | `3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a` |
