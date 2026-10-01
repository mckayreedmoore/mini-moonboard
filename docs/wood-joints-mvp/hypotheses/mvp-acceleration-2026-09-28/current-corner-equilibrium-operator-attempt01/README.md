# Complete corner: equilibrium and relative-motion operator

This parent-scoped input calculation assembles all internal carriers among
post, spine, side, inner block and header. It is the complete five-body
BG001/BG003/BG045 abstraction, not another isolated post/spine response.
The pinned carrier-map hash is
`c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8`.
The map itself binds the frozen input; no C11 force or active state is read.

The operator has 30 body force/moment rows and 50 carrier columns: 16 lateral
components at eight bolt planes, six outer-seat ties, and 28 compression
contact cells across seven pairs. Each column applies a unit action on one
member and its opposite on the other at the physical points. Moments use
the explicit descriptor-midpoint datums and are divided by 100 mm for numeric
scaling. These datums are not support stations or actual cut locations.

| Algebraic carrier set | Columns | Rank | Relative motion nullity after six common rigid modes | Force-sharing nullity |
| --- | ---: | ---: | ---: | ---: |
| Bolt carriers only | 22 | 18 | 6 | 4 |
| Bolt carriers plus all potential bearing cells | 50 | 24 | 0 | 26 |

These ranks treat carrier actions bilaterally for linear-algebra purposes.
Contacts and ties remain physically unilateral; potential cells are not
proven active. The full rank therefore **does not prove stability, engagement,
sign feasibility or capacity**. Conversely, the six bolt-only modes are
relative motions in this rigid abstraction when all bearing is removed,
not a finding that the installed corner is unstable. They establish why the
complete joint must include bearing/contact instead of summed bolt capacities.

For a consistent prescribed balanced member-wrench set, the full operator
has 26 algebraic directions along which carrier forces can change without
changing equilibrium. These are stored in [operator.json](operator.json).
They need not obey positive contact/tie signs and are not physical preload
states. Thus force balance alone does not select a joint response. Compatible
member/seat deformation and unilateral engagement must determine sharing.

Source-pinned reproduction passes. Independent global force/moment summation
cancels every internal carrier column to 1.99e-15 in the scaled components.
The stored force nullspace closes to 2.53e-15. The smallest counted singular
values are 0.11289 (full) and 0.14555 (bolt-only); excluded singular values
are about 3.48e-15 and 2.25e-15, so this rank result is well separated from
floating-point noise at the declared relative cutoff 1e-10.

**Result unlocked:** a reproducible whole-corner equilibrium/recovery matrix
that retains the three-member bolt stacks, seven bearing pairs, actual
application points and each member separately. The next mechanics step must
supply simultaneous boundary/member actions and an applicable compatible
unilateral response; neither aggregate loads nor single-bolt references do
that. The current operator omits boundary carriers deliberately because it
maps internal actions; the companion carrier map retains all outward routes.
Those routes and external loads remain necessary in an actual corner solve.

No original leg/runner resistance work, geometry, mesh, native execution,
run budget, criterion or physical-work disposition changes. There is no
accepted signed demand or assembly-capacity result.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-equilibrium-operator-attempt01/produce.py
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-equilibrium-operator-attempt01/produce.py --verify
```
