# BG001 conditional axial/contact sharing

This is a parent-scoped, bounded calculation of the existing post/spine
normal-transfer idealization under imposed interface actions. It is not the
six climber cases, a full corner response, a native run, or a resistance check.
Reviewed geometry and native budgets are unchanged. No C11 forces or active
states are inherited.

Inputs are frozen C11 model SHA-256
`d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0`:
two outer-seat ties of 4,670.054 N/mm and four post/spine contact-centroid
cells, each with stiffness 100 N/mm³ times its modeled area. The local timber
bodies are rigid; initial gaps and preload are zero. Other corner contacts,
member flexure, lateral actions, friction and washer metal bending are absent.
Therefore these are conditional mechanism results, not actual bolt actions.

At face datum `(-1219.2,-137.6,192.475) mm`, write opening as
`g = a + b*dz + c*dy`. Ties engage for positive opening and contacts for
negative opening. The prescribed joint action **on the spine** is
`Fx = sum(T-C)`, `My = sum(dz*(T-C))`, `Mz = -sum(dy*(T-C))`.
The external balancing action is its opposite. The producer enumerates all
64 unilateral spring branches, rejects singular stiffness matrices and
inconsistent gap signs, and checks force/moment closure. Different compatible
displacements stop the affected probe rather than being silently selected.

| Imposed joint action on spine | Conditional total bolt tension (N) |
| --- | ---: |
| My = +1 N·m; Fx = Mz = 0 | 22.622 |
| My = −1 N·m; Fx = Mz = 0 | 23.489 |
| Mz = +1 N·m; Fx = My = 0 | 16.152 |
| Mz = −1 N·m; Fx = My = 0 | 207.169 |
| Fx = −1 N; My = Mz = 0 | 0 |
| Fx = +1 N; My = Mz = 0 | UNRESOLVED: different compatible displacement states |

The large reverse-Mz result comes from the sampled contact lever arm.
For that sign, contact centroids lie only about 4.827 mm from the bolt row in
Y, requiring approximately `1000 / 4.827 = 207.169 N` compression and equal
total tie force. The earlier unrestricted-pressure footprint bound is only
26.247 N for the same sign. The sampled-cell response is about 7.9 times that
necessary ideal bound. This does not prove a physical failure, a true pressure
field or that the ideal bound is attainable. It demonstrates that four fixed
centroid carriers constrain redistribution and can materially affect this
conditional axial mechanism. Their areas do not turn point reactions into a
verified distributed-pressure solution.

Pure positive Fx has compatible states that the displacement-uniqueness guard
does not resolve. No force result is adopted for it. Independent one-dimensional
known answers (`+10/2=+5`, `−9/3=−3`) reproduce, and parent separately recovers
the five reported wrenches using physical 3D cross products: maximum closure
residual is 1.46e-11 in the stated N / N·mm components. These checks validate
the bounded arithmetic, not its applicability to the deformable complete joint.

Exact next issue: establish suitable pressure/contact resolution or a supported
distributed-pressure representation before interpreting these sampled-cell
ties as local demands. Then retain the full seven-pair corner inventory and
actual simultaneous boundary actions. Do not continue the C11 branch, alter
reviewed geometry, or infer a capacity/pass from this calculation.

Reproduce from the repository root:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-conditional-sharing-attempt01/produce.py
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-conditional-sharing-attempt01/produce.py --verify
```

The complete per-tie/contact actions, gaps, active branches and residuals are
in [conditional-sharing.json](conditional-sharing.json), generated afresh
from prescribed actions, not recovered from the rejected frame response.
