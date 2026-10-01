# Fixed-reference applicability counterexample

The successful four prescribed coupled states do not prove solvability for
arbitrary applied loads under the preceding-open-stage reference rule. This
parent check isolates one cell, using the coupled fixture's top-left carrier
matrix `[[20,5],[5,100]] N/mm`, normal penalty `100 N/mm`, fixed episode
reference `x=0 mm`, and applied tangent/normal load `(4,+0.5) N`. These are
mathematical fixture devices and loads, not candidate support properties.

For the open branch, both contact forces must vanish. Solving `K q = W`
gives `x=0.201265823 mm`, `z=-2/395 mm=-0.005063291 mm`. The gap is negative,
so the branch is inadmissible. For the bearing branch, stick imposes `x=0`;
normal equilibrium gives `z=0.5/(100+100)=0.0025 mm` and candidate normal
force `N=-100 z=-0.25 N`. Positive gap and negative force make this branch
inadmissible. Both branch equations balance exactly as rational numbers,
but neither meets the original normal law. There are only these two branches.

The sign-reversed load `(-4,-0.5) N`, with the same reference, has **two**
admissible branches: open at `(-0.201265823,+0.005063291) mm` with zero
contact force, or stuck at `(0,-0.0025) mm` with `(T,N)=(+3.9875,+0.25) N`.
Thus a positive-definite elastic carrier and correct local complementarity do
not establish unique support states for this conditional fixed-reference law.
Both existence and selection require treatment beyond picking one valid mask.

This proves a limitation of the **fixed discrete episode reference** with
normal/tangent coupling. It does not prove any reviewed frame case fails,
that physical timber fails, or that a differently defined continuous-contact
history cannot resolve engagement. It also does not authorize a new law.
Do not repair it by enabling tangent restraint at zero normal force, relaxing
normal signs, tuning stiffness, or selecting a different reference without
stating its physical/mathematical basis. The next applicable support-method
work must address when the reference is captured and the load-history or
bounded unresolved-state policy before general frame reactions are adopted.
The passing four-state fixture remains useful known-answer coverage.

Reproduce with standard Python:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/parent_reference_counterexample.py
```

The output pins the coupled fixture input and records both rejected branches.
No native or frame solve, geometry change, or candidate acceptance occurs.
