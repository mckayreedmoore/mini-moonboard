# Print-only master-wrench and contact-energy instrumentation

This is a review artifact only. The diff is not applied to the local CCX
source tree, built, or used in a solver run. It targets
`printoutcontact.f` SHA-256
`2c4d1da25da0ba5f3157a7d591bf262c388fc652dae05b4de0da2c4a36954c01`.
The patch file SHA-256 is
`aa3adbc8b515ac40f9a7291a307cbf2924955ace53208af0662cadbc2f5d0183`.

The addition evaluates each master contact point with the stored
`pmastsurf(1:2,igauss)` parameters, current master node coordinates, and the
same `shape*` calls and `shp2m(4,:)` weights used by
`springforc_f2f.f`. It accumulates `-df` at that current master point, while
leaving the existing slave `CF` arithmetic and its arrays untouched. Each
supplemental record explicitly includes `CF`/`CFN`/`CFS`, side role, tie
index, slave/master names, and time; the following high-precision row carries
the force and origin moment (or the three-component pair-offset couple).
The couple is emitted as `M_slave + M_master`, which equals
`sum((r_slave-r_master) x df)`.

For the frozen frictionless LINEAR contact law, the patch also computes one
per-pair normal spring-storage diagnostic on the total `CF` request:

```text
E_pair = -0.5 * (CPRESS * darea) * current_clearance
```

This is the source form `senergy = -elas*clear/2`, using
`CPRESS=elas/darea` and the current implicit-dynamic clearance
`(r_slave-r_master) dot n`. It uses actual solver pressure and area, so any
active `kscale` is reflected rather than assuming a nominal penalty
stiffness. The output label is intentionally conditional:
`WJ_E_IF_FRICTIONLESS_LINEAR_DYNAMIC`. `printoutcontact.f` has no material-law
context; input readiness must verify that every pair covered by this
diagnostic uses frictionless LINEAR behavior and the current dynamic
clearance convention before treating the values as that energy. The field is
only an output diagnostic. It does not repair CELS indexing, LOG energy
control, `checkimpacts`, or total-energy accounting.

The local checks performed were a patch dry-run against the pinned source and
application to a scratch copy. The resulting fixed-form source had no new
lines beyond column 72. No compiler, native solver, or model input was run.
The useful algebra checks for review are: aligned normal contact gives zero
pair-offset couple; a tangential offset produces `M_slave+M_master` equal to
the direct cross-product sum; and `CPRESS*darea=10 N`, clearance `-0.1 mm`
gives `0.5 N mm` stored normal-spring energy. These examples are not solver
results.
