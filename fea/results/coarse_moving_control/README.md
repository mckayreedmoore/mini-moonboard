# Coarse moving-control preparation

This bundle publishes the selected **inputs**, not a solver outcome or moving
qualification. Solver results and the numerical audit are not published here
yet. No joint capacity or permission to build/climb follows from preparation.

[preparation.tar.gz](preparation.tar.gz) contains:

- `prepared/`: `moving-event-tnev6k3a`, including the pinned passed posed-quiet
  archive, protocol, source snapshots and the coarse moving deck.
- `mass/`: `mass-cache-c4qwd4l5`, containing the separate native four-point and
  physical Gauss8 operators bound to that exact context and deck.
- `solve/`: only the freeze and frozen inputs of `moving-9gsvcbgg`. No active
  results or launch record are included.
- `members.json` and `references.json`: exact member hashes, selected paths,
  source commit `bd17eac78586d51b8d74945b12f7395671930198`, and prerequisite identity.

Archive SHA256: `053d6c06995cb76c666ec8eae85178be299747db96cadd220cabc8355bb5c9d1`
(58,838,330 bytes; 68 members).

The selected event has 200 DIRECT increments of 1e−7 s through 2e−5 s. Only
the washer initially moves, at `(-100,100,0)` mm/s; the core is initially
stationary and both bodies remain free. The frozen solver caps are 1800 seconds
inside / 1820 seconds outside, with 4 GiB memory and two CPUs. These are numerical
experiment settings, not structural design loads or acceptance.

Portable replay checks the archive inventory, preparation/source/cache/launch
input identity, coarse settings and full cached operators. It does not rerun
CAD, Gmsh, the prerequisite quiet proof, a solver or a moving audit:

```sh
uv run pytest tests/test_coarse_moving_publication.py -q
```

See the [moving protocol](../../../docs/moving-hardware-control.md) and
[passed posed quiet evidence](../posed_hardware_control/README.md). Earlier
evidence archives are unchanged.
