# Preserved bottom-center retained-host replay failure

The first retained-g18 run stopped before producing a diagnostic report. It
found a 10090.034566930073 mm³ symmetric difference at
`base_principal_center_left`: the producer replayed all canonical native source
cutters, restoring source SDS cuts already removed by the WJ18 composition.
Bottom rails also require separate source-overlay and retained-host checks:
their additional finished source parts contain native and purchase cuts, while
the WJ18 finished hosts also contain retained candidate bores.

The [producer snapshot](producer.py.snapshot), [focused tests](tests.py.snapshot),
and [failed-attempt record](failed-attempt.json) preserve this pre-fix state.
The run stopped during geometry reconstruction; no diagnostic report, native
solve, or geometry change resulted. Do not treat the failed reconstruction as
an acceptance result.
