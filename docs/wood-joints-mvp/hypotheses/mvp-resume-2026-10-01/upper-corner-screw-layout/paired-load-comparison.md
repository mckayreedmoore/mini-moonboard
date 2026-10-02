# One finite hand/foot load comparison

October 2, 2026. This is a diagnostic stance sensitivity, not a replacement
for the owner's 250 lb dynamic requirement or the original single-hold cases.
It changes applied load placement only. The four-moved-screw geometry,
connector laws, timber references, 66 screw axes, bolt clearances, no-slip
assumption, dead weight and 25 kg accessory allowance stay unchanged.

## Declared load

For each of the five upper-hold cases, half of the 2224.111 N downward
climber force stays at the original hold and half moves to the saved
lower-left A1 hold. The original signed 300 N horizontal force stays at
the upper hold. The sixth, A1-rear, remains unchanged. Both contacts retain
the inherited 100 mm face standoff. The lower-left placement in right-hand
cases is explicit; it is not a mirrored or measured stance.

[`paired_loads.py`](paired_loads.py) combines the frozen applied-load columns:

```text
new live column_i = old live column_i
                  + 0.5 (A1 vertical column - original_i vertical column)
```

This changes `e`, `W` and `F` live columns, using the authenticated vertical
decomposition. It never averages solved joint forces. `H`, `D`, body geometry,
row identities and all dead-load columns are preserved. Each resultant
force matches the original; five global moments change. Direct sums of
the declared contact wrenches reproduce the six new load columns within
1.82e−12 N and 1.87e−9 N·mm. No physical stance, body acceleration history,
contact allocation or dynamic upper bound is established by that arithmetic.

## Actual result: eight accepted states, then STOP

The parent ran one serialized batch with the original force/contact/domain
gates. All six zero-gap states return, followed by A12-rear and A12-forward
at nominal gaps. A12-left nominal gap then stops on `normal active-set cycle`.
The final iterate is unaccepted. There is no complete six-case nominal-gap
envelope and no physical frame-failure claim. No seed search or law relaxation
followed this finite run.

| Returned case | Gap scale | Original peak T (N) | Paired peak T (N) | Same-state V at paired peak (N) |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 0 | 1923.816 | 1057.462 | 327.758 |
| A12 forward | 0 | 1602.367 | 734.409 | 256.624 |
| A12 left | 0 | 1861.156 | 992.280 | 321.515 |
| K12 right | 0 | 1545.067 | 805.962 | 327.909 |
| K12 rear | 0 | 1626.535 | 890.506 | 326.540 |
| A1 rear, unchanged | 0 | 1162.709 | 1162.709 | 338.275 |
| A12 rear | 1 | 1871.251 | 980.172 | 400.859 |
| A12 forward | 1 | 1513.849 | 621.723 | 306.279 |

The two returned nominal states retain bounded, nonunique fixed-force
seating. Representative positions establish no motion envelope or strict
tangent stability. Peaks remain simultaneous signed-response demands;
separate case maxima are not added.

## What changes the next decision

The A12-rear nominal head demand drops about 48%, from 1871 to 980 N.
Single-hold concentration therefore materially changes this modeled local
demand. It was not a duplicated climber force. The change also shifts the
body wrench; it is not an alternative equilibrium allocation for the same
original single-hold load.

The reduced 980 N is still above the declared 594 N normal-duration head
reference and its favorable 951 N short-duration scenario for a standard
No. 10 head, G=.50 plywood and the stated countersink reduction. It is below
the extreme 1006 N scenario that omits the reduction. Neither adjustment
is newly adopted. The unchanged A1 zero-gap case still exceeds even 1006 N.
See [head-reference basis](head-reference-basis.md) for material/geometry
and duration limits. These partial results do not close head, withdrawal,
lateral or combined attachment acceptance.

A useful next change needs a stated physical load/stance basis or a
defensible resistance/load-sharing detail. Additional arbitrary stiffness
or stance sweeps do not establish either. The original complete 250 lb
packet remains intact; this comparison supplies no transferred member,
bolt, washer or assembly acceptance.

## Retained local evidence

The raw packet is `rawlocal/paired-load-attempt01/`, ignored and preserved.
All 109 preparation source pins and 140 stopped-frame source pins match
after execution. Existing authority, 47 pending criteria and eight false
release flags are unchanged. No geometry rebuild, native solve, software
tests or review loop ran.

| Artifact relative to the raw packet | SHA-256 |
| --- | --- |
| `operators/operator-assessment.json` | `ca5c2db1f6a84811fac95b3e5c53e60750efcc9b679c5e52773fbabbf0bcb177` |
| `operators/operators.npz` | `aafbf598a2cffcb5e39e660f477526978860df02b1544e782de7d1c7a9ef4adf` |
| `operators/producer.py.snapshot` | `6e5a2fca37d5d8c278199d2b538f6bb7ea4e06dcfa61267c1974e1d547c3ca8b` |
| `frame/stop.json` | `fce6a6d680154f5262b4dbd14cbe2681869c36ba771c900ac4da968baa5b5f4e` |
| `frame/partial-response.npz` | `5a57f4559791335c668e637ca9d61c8853ae65f0dc0e726503e093c4881fcb07` |
| `frame/unaccepted-iterate.npz` | `6028ab7cae5a882ab49215526648a67af614ec12903ab171c060ed8274bd5f3a` |

Reproduce only in the parent's serialized analysis slot, with NumPy 2.2.6,
SciPy 1.15.3 and OSQP 1.0.4. `paired_loads.build(fresh_output / 'operators')`
prepares the columns; `--run` calls the unchanged frame method. Choose a
fresh destination. Existing packet children are refused. The STOP receipt
retains accepted states separately from the last unaccepted iterate.
