# First measured dependent-node residuals

The source-pinned processor completed in 1.519 seconds with one CPU and a
2 GiB limit. It reconstructed 24 dependent-node components from the actual
instrumented hook at step 1, increment 1, time and timestep both 0.0005 s.
The hook contains all 24 expected MPC identities and all 337 exact support
node IDs. The reconstructed 21 scalar mass rows exactly match the previously
reviewed mass-row extraction.

The relation is `R_dep = -fmpc - (M a)_dep` under the frozen zero direct pivot
load and unit dependent-coefficient assumptions. The largest absolute
component is 8.836607039793088e-6 N. This is a constraint residual/reaction
component, not a convergence-error measure or evidence of joint capacity.
Complete joint force/moment balance and full-row constraint work remain open.

The native run accepted this state and then failed its appended end-of-step
contact cleanup with code 201. Its runtime status remains failed. Parent
[terminal validation](../dependent-native-instrumented-parent-review-attempt01/parent-terminal-validation.json)
authenticates the inputs, outputs, execution and hook. The separate complete
accepted-state output comparison remains pending; this calculation does not
establish output equivalence or authorize interpreting a longer trajectory.

Reproduction uses `driver.py` and the exact container command in
`execution.json`. The driver checks the processor, native execution record
and hook hashes before invoking the existing processor. Output
`residuals.json` has SHA-256
`47d0128c4e4cae4b2554431b132acff6b309a363e6b76ea8efb78213caa0a4d7`.
The hook hash is
`42e77159443284aba9149201377d5af04b06cc792ad86a8bdcb548b51ae21bc6`;
the native execution hash is
`bb103133a63954751e926cde03c2f92299280cbe8d3ae89600da11343eba98a9`.
The [independent arithmetic review](independent-review.md) recomputed all 24
components from the frozen mass rows and actual hook and found an exact
match at stored float precision. No physical joint acceptance is claimed.
