# C3D10 native section-resultant coupon

## Status and scope

Prepared for parent review. This packet has not launched CalculiX. It adds
only two `*SECTION PRINT` output requests to the previously passing C3D10
full-step pair. Mesh, material, contact, constraints, target motions, static
steps, and every mechanical gate stay unchanged.

The base pair passed the opening, compression, and reopening endpoint gates
for both MORTAR and matched surface-to-surface penalty contact. Its immutable
input freeze is `978f8e49e79d6569dc033595ce565ce8587e36c4c5845c5615f120582634e8b0`,
execution is `a485410aada87d2e149b39ee77b78d3efcada065c833a0c7e91acf1a60312574`,
and the `PASS_METHOD_FIXTURE` verifier result is
`813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14`.
`expected.json` pins these along with the verifier source and result summary.

This is a small output-method check, not a contact-force qualification or a
joint assessment. `SOF` integrates bulk stresses extrapolated to and averaged
at nodes. Across contact stress jumps, its result is a section proxy, not the
exact MORTAR traction resultant. No joint qualification follows.

## Output-only change and source basis

Each of the three steps requests:

```text
*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1
SOF
*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1
SOF
```

The deck uses no `GLOBAL` option. These are existing element-face surfaces:
upper elements 1 and 2, S1; lower elements 11 and 12, S3. Each surface has two
quadratic C3D10 triangular faces and area `4 mm2`. There are six section
reports per case: the two surfaces at each of the three step endpoints. No
additional stress `*NODE FILE` or FRD output is requested.

The pinned 2.23 source archive and the reviewed
[`mortar-output-method-screen`](../ordinary-external-force-transient-attempt04-diagnostic/mortar-output-method-screen.md)
are hash-bound in `expected.json`. `sectionprints.f` parses the `SURFACE`,
required `NAME`, and `FREQUENCYF` parameters; its default coordinate system is
global. `SOF` writes the force, origin moment, centroid/normal, centroid
moment, area, and derived normal/shear/torque/bending values. The C3D10 face
integration path is in `printoutface.f`.

## Predeclared section-resultant checks

The inherited mechanical oracle remains `400 N` compression, zero open and
reopened force, and all prior displacement, interface, compliance, closure,
and iteration gates. The additional section checks are:

- At compression, slave force is `(0, 0, +400) N`; master is
  `(0, 0, -400) N`. Each vector error is at most `4.001 N`.
- Each open/reopened section-force norm is at most `0.001 N`. The opposed
  force-sum norm is at most `4.001 N` in compression and `0.001 N` when open.
- With deformed centroid reference `(1, 1, z) mm`, origin moments are
  `(400, -400, 0) Nmm` for the slave and `(-400, 400, 0) Nmm` for the master.
  The z coordinate does not affect the expected moment from axial force.
- Origin-moment and centroid-moment vector errors use `0.01*F + 0.001 Nmm`;
  at compression this is `4.001 Nmm`, and at open/reopen it is `0.001 Nmm`.
  Opposed origin-moment sums use the same compression/open bounds.
- Each reported area is `4 mm2` within `1e-5 mm2`; reported normal and
  deformed centroid match the face geometry within `1e-5`.
- Normal force, shear, torque, and bending outputs obey the same state-scaled
  `0.01*F + 0.001` component bound.

The extension verifier also requires exact parity with the base run for
nodal `U/RF` data and `.sta`/`.cvg` row tokens. Any mismatch means the new
output request changed or disturbed the existing fixture response.

## Records and next action

`prepare.py` verifies the passed fixture freeze, execution, verifier, result,
source archive, source-member and manual hashes. It inserts only the two
section requests before each `*END STEP`; removing those blocks must restore
each base input byte-for-byte. It records the expected section reports,
resultant signs, tolerances, and proxy interpretation.

The parent owns review, immutable input freeze, bounded serial execution, and
the result audit. Do not run the decks before that review and freeze.
