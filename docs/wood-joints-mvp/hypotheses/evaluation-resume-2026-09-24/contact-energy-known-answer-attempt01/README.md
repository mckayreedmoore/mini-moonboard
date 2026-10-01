# Contact and body energy known-answer output fixture — attempt01

## Status and scope

Prepared for parent review. No solver was launched, and there is no input freeze
or execution record. The two decks derive from the passing
[`contact-section-force-known-answer-attempt02`](../contact-section-force-known-answer-attempt02/RESULTS.md)
pair. The only input changes are output requests for per-body internal energy
(`ELSE`) and total contact spring energy (`CELS`).

The source fixture has two 2 mm C3D10 bodies, `E=100,000 N/mm²`, interface area
`4 mm²`, and a linear frictionless normal slope `K=100,000 N/mm³`. It retains
the original open (`+0.001 mm`), compression (`−0.005 mm`) and reopen
(`+0.001 mm`) endpoints and all existing displacement, reaction, section-force,
stress and solver-trace requirements. The analytical compression reference is
`0.4 N·mm` in each body, `0.2 N·mm` at the contact law, and `1.0 N·mm` total.
The open/reopen reference energies are zero.

## Output requests and source basis

Before each existing `*END STEP`, each deck requests:

```text
*EL PRINT,ELSET=UPPER,TOTALS=ONLY,FREQUENCY=1
ELSE
*EL PRINT,ELSET=LOWER,TOTALS=ONLY,FREQUENCY=1
ELSE
*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1
CELS
```

The requests appear in the first step as well as the later steps, as needed for
nonlinear internal-energy accumulation. Pinned CalculiX 2.23 manual
`fea/generated/ccx_2.23.pdf` (SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`) documents
the `*EL PRINT` and `*CONTACT PRINT` keyword entries. Source parsing in
`elprints.f:82–145,237–287` and `contactprints.f:99–104,176–222` accepts the
sets, `TOTALS=ONLY`, `FREQUENCY`, and `ELSE`/`CELS` labels. `printout.f:341–363,
552–559` and `printoutelem.f:519–521` implement per-body and total `ELSE`
output. `contactprints.f:192–222`, `printout.f:426–438,617–623`, and
`printoutelem.f:522–528` implement `CELS` output.

The pinned source maps `TYPE=MORTAR` to `mortar=2`, but the audited CELS storage
and printing branches cover only mortar modes 0 and 1
(`contactpairs.f:115–118`, `resultsmech.f:423–441`, `printout.f:429–438,477–505`,
and `printoutelem.f:522–528`). Therefore absence of MORTAR `CELS` is recorded as
`UNAVAILABLE_UNVALIDATED`; it is never substituted with zero or treated as an
energy pass. It does not fail inherited mechanical gates. Any present MORTAR
CELS data stays separately identified and must match the analytical oracle
before anyone uses it as stored contact energy.

The archive, manual and source-member SHA-256 pins are in `expected.json` and
checked by `prepare.py`. The preparation pins the passing section-force
attempt02 result, execution and input freeze. It does not freeze this new packet.

## Energy checks and interpretation

Use the proposed predeclared tolerance `|observed − reference| ≤ 1% ×
reference + 1e−6 N·mm` for nonzero compression energies, and `|observed| ≤
1e−6 N·mm` for open/reopen zero-energy states. The 1% relative tolerance
matches the inherited force/compliance numerical tolerance and exceeds the
known small-strain versus nonlinear force difference in the passing fixture
(about 0.120%). The `1e−6 N·mm` absolute term is one last-place unit of the
2.23 total-energy text format at order `1 N·mm` (`printout.f:559,623`). These
are method-fixture tolerances, not structural allowables; parent review is
required before input freeze.

Report four independent result categories: inherited mechanical/trace status,
body `ELSE` status, penalty `CELS` status, and MORTAR `CELS` availability and
known-answer status. The inherited gates remain the exact attempt02 contract:
accepted state and trace parity, complete U/RF/SOF/STRESS coverage and checks,
the MORTAR iteration cap, and all endpoint mechanical checks. A missing MORTAR
energy channel cannot upgrade the work/energy gate; it leaves that gate and
broader MORTAR response characterization unresolved. Missing or incomplete
penalty `CELS` data is also `UNAVAILABLE_UNVALIDATED`; an observed mismatch is
an energy-channel failure, while neither outcome changes the inherited
mechanical result. Missing/incomplete `ELSE` is reported as an energy-output
failure, separately from mechanics. This fixture does not validate pathwise
trapezoidal work or a joint model.

See [`energy-method-review-2026-09-27.md`](../contact-mortar-c3d10-fullstep-attempt01/energy-method-review-2026-09-27.md)
for the source-based limitation, dimensional derivation, work-floor gap, and
separation from the unrelated shared-edge attempt02 failure.
