# Separated-pose stationary evidence

The two-free-body posed fixture passes the complete stationary output gates:
20 fixed increments of 1e−7 s through 2e−6 s. Every state has zero displacement,
velocity, kinetic/internal/contact energy, penetration, and pair force/moment.
Native CNUM is explicitly zero, with empty contact tables and complete
zero-area statistics for both pairs; missing output was not inferred as zero.

This establishes only a quiet numerical baseline. Moving contact, momentum
transfer, joint capacity and board safety remain unqualified.

## Frozen experiment

- Preparation: `posed-control-p8c_gk9h`; the earlier preparation
  `posed-control-x41m3ebv` was not launched and remains preserved locally.
- Solve: `quiescent-w_xxkfbo`; native exit 0, cleanup exit 0, no wrapper
  exceptions. Native elapsed time: 92.953257 seconds, within the frozen
  180-second inner/200-second outer limits.
- Audit: `quiet-audit-0tz5hrg9`; existing gates unchanged.
- Mass cache: `mass-cache-omcrgm_t`, Gmsh 4.12.1; separate complete native
  four-point and physical Gauss8 element operators for both bodies.
- Washer-only translation: `(0.001, 0.7356, 0)` mm; exact frozen serialized
  coordinates, unchanged core/connectivity. Fixed angular reference:
  `(1.001, 0.7356, 0)` mm.
- Full quadratic selected-surface gap lower bounds: radial
  0.0007702642876363796 mm; axial 0.0009999999999999998 mm.

No loads, restraints, gravity, preload, friction or artificial initial motion
were added. Material and penalty parameters remain provisional diagnostic
choices, not product or structural resistance values.

`posed-quiet.tar.gz` retains complete `prepared/`, `solve/`, `audit/` and
`mass/` trees. `members.json` pins every member; `references.json` pins the
earlier fourth archive and its original geometry/two STEP identities.
Preparation includes the nested centred inputs and frozen pose proof.
All earlier archives are unchanged. The portable regression pins this archive
and checks raw audit replay, provenance and both native body masses.

Preparation and mass integration used bounded Gmsh workers with image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`.
Their exit-zero and subsequent container-absence checks were session-observed,
not archived runtime provenance. The solver's command, image/build identity,
exit, owned-container probe and cleanup records **are** archived under `solve/`.

Replay without CAD, Gmsh or a solver:

```sh
uv run pytest tests/test_posed_quiet_publication.py -q
```

Next: freeze a moving two-interface experiment and its force/momentum,
moment/angular-momentum, energy and timestep-refinement gates before launch.
Keep the physical Gauss8 operator distinct from CalculiX's native mass operator.
