# Original-state gravity quadrature replay

Replacing archived Gauss5 gravity weights with the source-reconstructed,
untransformed CalculiX 2.21 four-point weights leaves all seven failed times
unchanged: 1.0625, 1.125, 1.1875, 1.25, 1.3125, 1.75 and 1.8125.

Across the original 32 accepted states, the maximum gravity-force correction
is `2.53063767e-9 N` and the maximum gravity-moment correction is
`0.000819322755 Nmm`. The peak moment residual changes from
`30.2845690039871` to `30.28374970307231 Nmm`. The original `0.1 N` and
`1 Nmm` gates remain in effect. This untransformed quadrature difference
does not explain the failures. Mortar basis transformations remain
unqualified; these results do not establish contact or physical acceptance.

`retained-replay.tar.gz` contains the launch-time source snapshot, launch/input
provenance, mesh, integrated native weights, Gmsh log, complete original and
corrected rows, and output hash manifest. The publication `report.json`
hashes every archive member and links the existing original `.0625` archive
and published refinement report by digest. Those originals are not duplicated.
The original run did not record imported module origins; its snapshots alone
do not prove which module paths were executed. That archive remains unchanged.
Original DAT displacements are used throughout; observer displacements are
not mixed into this replay. The retained computation ran Gmsh only, with
a 110-second inner and 120-second outer bound, two CPUs, 2 GB memory,
disabled networking and a read-only container root. No FEA solver ran.

The portable verifier independently reconstructs the signed correction from
the recorded native weights, original archived weights, and original DAT
displacements at every accepted time. It checks the original mesh and
published residual identities, all retained source/output hashes and the
unchanged failed-time list. No Gmsh, Docker or solver is needed:

```sh
.venv/bin/python -m fea.publish_native_gravity_replay
.venv/bin/python -m pytest -q tests/test_native_gravity_replay_publication.py
```

`strict-origins-supplement.tar.gz` separately preserves a fresh, bounded
Gmsh-only integration of the exact same original mesh. All **62,020 recorded
native weights match exactly**. This launch clears inherited `PYTHONPATH`,
uses a regular frozen `fea` package, and checks all four imported source files
against the frozen files by file identity and loaded/current/snapshot hashes
at integration entry and completion. Its integration output records the
verified `/sources/fea/...` origins. `supplement.json` hashes this separate
archive and its members and links the unchanged original archive. The
supplement includes its own source snapshot, launcher, launch record,
mesh, integration output, log and comparison report.

The supplementary import checks corroborate the retained numerical weights;
they do not retroactively establish the original run's import paths. The
portable replay independently establishes the original-state correction
arithmetic. The competing-package regression reproduces the original
namespace override and proves the hardened launcher rejects or isolates it.
Verify the supplement without Gmsh or a solver:

```sh
.venv/bin/python -m fea.native_gravity_supplement
```

See [operator qualification](../../../docs/dynamic-momentum-qualification.md)
for the separate physical and source-reconstructed mass operators and their
bounded native dynamic controls. This static gravity replay does not qualify
either dynamic operator.
