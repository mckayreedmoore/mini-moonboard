# Bottom quarter-inch resistance basis

October 1, 2026. This source/method packet binds the bottom-left four-bolt
conditional lateral calculation to all 84 existing A1/A12/K12 bolt states.
It adds a 106 ksi sensitivity, source interpretation and adjustment budget.
The reviewed model, complete signed demands and selected baseline are unchanged.
No native solve, CAD change, hardware choice, criterion pass or physical
operation is performed.

The [source note](source-note.md) distinguishes an exact catalog lead from
unadopted `Fyb` scenarios. The [applicability note](applicability.md) explains
which service, group, geometry and complete-action conditions remain open.
The Appendix's diameter parenthetical is ambiguous for bolts; this packet
does not repeat a blanket quarter-inch exclusion as an unambiguous NDS rule.
Neither 45 nor 106 ksi is adopted as the actual quarter-inch bending yield.

| A1 full-load bolt | Lateral action, N | Separate axial tie, N | 45 ksi reference, N / ratio | 106 ksi reference, N / ratio |
| --- | ---: | ---: | ---: | ---: |
| `side_1` | 661.948743 | 197.1248 | 604.790663 / 1.094508867 | 928.221778 / 0.713136407 |
| `side_2` | 168.525602 | 231.1119 | 621.192072 / 0.271293871 | 953.394364 / 0.176763791 |
| `rail_1` | 249.671333 | 221.195777 | 605.909347 / 0.412060540 | 851.817614 / 0.293104215 |
| `rail_2` | 325.489346 | 52.197230 | 659.844034 / 0.493282244 | 963.319448 / 0.337883084 |

These are individual unadjusted smooth-quarter-inch references, using the
existing rounded SG=0.50 bearing scenario. The six modes are recalculated
at each actual angle; scaling every reference by `sqrt(106/45)` would miss
mode switches on the shorter rail receiver. Both main/side role assignments
are retained. Service factors are a declared dry/normal/≤100°F scenario;
`Cg`, `CΔ`, and adjusted references remain null.

The local report also preserves 168 member/bolt states, 84 interface
wrenches, 21 complete cleat-boundary states, 252 contact-cell states, eight
finished-placement records and the four existing hardware-requirement rows.
It neither redistributes the source forces nor replaces complete action with
the displayed lateral scalar. The original 45 ksi flag remains unresolved
as an adopted resistance question; the favorable 106 ksi sensitivity is
useful input evidence, not complete-joint acceptance.

## Reproduce

Run from the repository root with the existing local frozen reports and
AWC source cache. Raw JSON/PDF/STEP/native files stay local; the packet
contains calculation code, tests and review documentation only.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-quarter-inch-resistance-basis-2026-10-01/produce.py --reference-report /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json --placement-report /tmp/mini-moonboard-bottom-outer-placement-2026-10-01.json --joint-report /tmp/mini-moonboard-bottom-outer-joint-2026-10-01.json > /tmp/mini-moonboard-bottom-quarter-inch-resistance-basis-2026-10-01.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/bottom-quarter-inch-resistance-basis-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/bottom-quarter-inch-resistance-basis-2026-10-01
```

Seven focused tests independently compare 2,016 mode values from the
signed source vectors and pinned proposed grains, check complete action
preservation, the exact quarter-inch trigger, conditional threshold, mode
switches, missing/duplicate/corrupt source rejection and null acceptance.
The producer requires exact SHA-256 pins for all three upstream reports,
the six-mode helper, hardware requirements and inspected AWC source PDFs.
It authenticates archived report bytes; it does not independently replay
every native RF token or requalify upstream response fidelity.

Independent reviews and final hashes are recorded in `validation.md` when
the review cycle is complete. Receiving observations remain absent and no
Actual/Disposition cell is filled. Only three rear families exist in this
packet; the six-case and complete-joint development gates remain open.
