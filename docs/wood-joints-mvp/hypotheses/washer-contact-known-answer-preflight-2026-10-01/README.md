# Washer/contact known-answer preflight

**Status: preparation only.** This packet prepares two small, independent
CalculiX 2.23 method jobs for later parent review and serialized execution.
It has not been frozen or run. It does not change candidate geometry, select
a washer, qualify a material, or establish washer stress or resistance.

The source-method review says a conditional washer scenario needs three
dimensional solids, compression-only contact, and a finite receiver. Its
literature comparisons validate assembly load–embedment response for the
published setup; they do not validate local metal stress/plastic-strain
recovery for this candidate. The ordinary washer has no pinned numerical
yield minimum, and the printed Teranishi wood Poisson pairs do not define a
consistent reciprocal tensor. Accordingly, this packet uses declared
isotropic, linear-elastic software diagnostic values only. The receiver value
is not a wood model, and the metal value is not an ordinary-washer product
property. No Teranishi tensor or material result is copied.

The upstream input decks and contracts are generated under `prepared/` by
`prepare.py`. It makes no solver or Docker call and refuses to overwrite a
nonempty output directory. `verify.py` contains the offline result audits;
`tests/test_preparation.py` exercises the analytic contracts and output
parsers using synthetic data. `verify_preparation_receipt.py` checks the
generated-file and supporting-code SHA-256 values. Those checks do not require
CalculiX.
The current `prepared/` directory is disposable generator output with no
freeze or execution record. Regeneration may remove only this unexecuted
directory; parent-created attempt and freeze directories are separate.

The first job, `prepared/annular-affine/model.inp`, is a C3D10 annulus patch
with a homogeneous axial affine boundary field. The diagnostic material uses
`nu = 0`, so the exact field has only `sigma_zz = -E epsilon`. It checks
integration-point stress, top and bottom reaction resultants, global reaction
wrench closure, and elastic strain energy. Its area and volume oracles come
from the actual straight-sided FE mesh: C3D10 midside nodes are placed at
edge midpoints, so the annular faces are polygonal and the quadratic surface
geometry is planar. The ideal circle is recorded only as a comparison, never
as the force/volume oracle. Exterior nodes receive the affine boundary
displacements; interior nodes remain free. This is an elastic patch check,
not a contact or washer-bending check.

The second job, `prepared/finite-sector-contact/model.inp`, uses two
geometrically matched annular C3D10 solids with separate node IDs, an initially
touching interface, and frictionless face-to-face linear penalty contact. A
positive `*DSLOAD` pressure acts inward on an eccentric finite sector of the
upper annulus. The initial force and first moment are independently integrated
from the actual loaded triangular FE faces. Because the nonlinear step uses
follower pressure, the offline audit also reads the loaded face's six-node
displacement field and integrates pressure over the deformed TRI6 geometry.
It compares this applied wrench with the slave `CF`/`CFN`/`CFS` resultants and
the lower support reactions, with the gauge wrench included explicitly in
each free-body balance.

The audit follows the CalculiX 2.23 manual's “Forces obtained by selecting
RF” discussion, pinned as `node212.html`: `RF` reports total external nodal
force, including applied nodal and consistent distributed-load contributions.
The upper gauges are on the lower face of the upper body, and their node IDs
are checked to be disjoint from the pressure-face node IDs, so their fixed x/y
RF components are constraint reactions. The free z RF values are reported
separately and are not treated as reactions. The lower support nodes are
unpressurized and disjoint from the pressure nodes, so their RF values are
support reactions. The gauge restraints and every fixed support DOF are
recorded in the job contract. This job checks integrated load transfer
and output extraction; it does not predict the pressure distribution,
indentation field, washer stress, plastic recovery, or capacity. The penalty
coefficient is a numerical enforcement value, not contact-material
compliance. The full-area spring scale in `expected.json` is explicitly not a
response oracle for the eccentrically loaded contact field.

At the declared mesh resolution, the affine job has 800 nodes and 384 C3D10
elements; the two-body contact job has 1,600 nodes and 768 C3D10 elements.
The frozen gates are in each `expected.json`: affine stress uses
`5e-5 MPa + 1e-5 × reference`, reaction force uses `0.001 N + 1e-5 ×
reference`, top/bottom moment uses `0.02 N·mm + 1e-5 × reference`, and energy
uses `1e-9 N·mm + 1e-5 × reference`. Affine whole-boundary closure is bounded
by `0.02 N` and `0.05 N·mm`. Contact-resultant force uses `0.02 N +
2e-4 × reference`, moment uses `0.05 N·mm + 2e-4 × reference`, frictionless
shear is bounded by `0.01` in force and moment, and gauge force L1 by
`0.02 N + 1e-4 × pressure-resultant magnitude`. Upper-body and whole-model
equilibrium each use `0.1` absolute force and moment bounds. Affine boundary
and free-interior displacement use `1e-8 mm` absolute. These limits are fixed
before any run; no result-dependent widening is allowed.

The verified prior
[`contact-penalty-touch-work-known-answer-attempt01`](../../evaluation-resume-2026-09-24/contact-penalty-touch-work-known-answer-attempt01/README.md)
already covers an exact-touch C3D10 penalty path through open, touch,
compression, unloading, and reopening, with validated `CF`, `CFN`, and `CFS`
formats. This packet binds it as source history and does not rerun it. The
contact-sector job has one compressive state; duplicating the earlier path
would add little to these narrowly scoped annular and finite-wrench checks.

## Pinned 2.23 basis

`source-pins.json` binds the profile, local manual PDF, official source and
HTML archives, source members, prior exact-touch deck/parser, and the reduced
native runner. Key pins are:

- Solver profile: `fea/calculix_223/solver-profile.json`, SHA-256
  `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c`.
- Runtime: immutable image
  `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`,
  executable `/usr/local/bin/ccx-upstream-2.23`, SHA-256
  `c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.
- Official 2.23 manual PDF: `fea/generated/ccx_2.23.pdf`, SHA-256
  `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
- Official source archive: SHA-256
  `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
- Official manual HTML archive: SHA-256
  `ed14b31b51972d5492209a42fcd52a062e36cbc7843bcd358617cb3aee0da736`.

The preparation follows the pinned manual's C3D10 element definition
(§6.2.7), face-to-face penalty formulation (§6.7.7), `*BOUNDARY` (§7.4),
`*CONTACT PAIR` (§7.22), `*CONTACT PRINT` (§7.23), `*DSLOAD` pressure
(§7.45), `*ELASTIC` (§7.47), `*EL PRINT` (§7.53), `*NODE PRINT` (§7.99),
`*STATIC` (§7.123), C3D10 `*SURFACE` face labels (§7.129),
`*SURFACE BEHAVIOR` (§7.130), and `*SURFACE INTERACTION` (§7.131). The
manual defines C3D10 tetrahedron faces as 1-2-3, 1-4-2, 2-4-3, and 3-4-1;
the deck uses those labels for the annular pressure and opposed contact faces.
The same pinned manual explains that RF contains applied and reaction forces;
the fixture therefore audits only gauge DOFs with no direct pressure load.
The pinned 2.23 `contactprints.f` and `printoutcontact.f` source members bind
pair selection and integrated contact resultants. `dloads.f` binds the
distributed-pressure input path. The earlier exact-touch contact fixture
records the accepted `CF`/`CFN`/`CFS` output layout and independent parser.

## Parent-owned next step

Review both generated input/oracle pairs, the offline tests, and
`prepared/preparation.json`. The first native attempt is the affine annulus
job only: create a separate exact freeze and independent readiness receipt for
that job, then use the parent-only
[`fea/wood_joint_reduced_native.py`](../../../../fea/wood_joint_reduced_native.py)
protocol with one reserved run ID, one launch, 60-second timeout, 1 GiB
memory, and one CPU. Do not freeze or launch the contact job until the affine
job passes its frozen gate and the parent reviews the contact job separately.
Stop after any failed launch or method gate. Subsequent hypothetical washer
scenarios should use the existing signed primary-corner, upper-cohort, or
remaining-54-axis three-case outer-seat action/scenario join and state
physical assembly/preload bounds; this packet calls for no new demand solve.
It creates no freeze, readiness record,
authorization, ledger entry, or solver output.

After a parent-owned attempt writes `model.dat`, the read-only result check is
invoked with the generated parser on `PYTHONPATH`:

```sh
PYTHONPATH="$PWD/docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01/prepared" \
python3 docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01/verify.py \
  affine docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01/prepared/annular-affine/expected.json \
  <attempt-directory>/model.dat \
  docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01/prepared/annular-affine/model_coordinates.json
```

For contact, use `contact` and the `finite-sector-contact` expected and
coordinate files. `preparation.json` lists SHA-256 for each generated file;
check every listed path before review or freeze, then verify the expected.json
and deck hashes also recorded under each job. The receipt explicitly says no
freeze and no native run.

The read-only receipt check and offline tests are:

```sh
python3 docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01/verify_preparation_receipt.py
python3 -m unittest discover -s docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01/tests -v
```

A passing patch or contact-resultant check would qualify only those bounded
numerical methods. It would not transfer properties or capacities from
Teranishi's square SS400/Japanese-cedar specimens, qualify the present
ordinary washer, represent wood crushing, or validate local washer stresses.
Published specimen reproduction remains an optional validation path. A
clearly declared hypothetical conditional scenario can proceed independently;
no blanket physical test or external sign-off prerequisite is created here.
