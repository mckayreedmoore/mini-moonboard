# Header nominal net-section comparison

## Scope and readiness

The parent executed the frozen [producer](header-net-section.py) once, with
status `COMPLETE_HEADER_NOMINAL_SECTION_COMPARISONS`. The six existing header
paired-bore sections cover all six simultaneous cases and both saved
before/after traces: 72 cuts, 216 retained rectangle comparisons and 864
longitudinal corner comparisons. All reported nominal indices are below 1.0
under the declared hypotheses. Completion means the nominal arithmetic
finished; it does not declare a joint pass or qualification. The worker
performed no calculator execution, coupon execution or tests.

The original 100 mm frame lever, 250 lb × 2 and signed 300 N source remain.
The input contract retains all 394 header actions per case. Every section
wrench includes concurrent connections, contacts, body loads and saved free
moments. Each complete signed wrench is restored independently from those
actions before comparison. No local interface resultant substitutes for it.

## Frozen inputs and calculator

| Artifact | SHA-256 |
| --- | --- |
| `rawlocal/header-local-transfer/attempt01/inputs.json` | `cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b` |
| Same packet, `model.json` | `eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52` |
| Same packet, `header-sections.csv` | `f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953` |
| Same packet, `receipt.json` | `3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8` |
| `rawlocal/header-traction-map/attempt01/result.json` | `39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837` |
| Same packet, `receipt.json` | `1d454a949640a9b43d6ae3e3cf56ca20705e12ff6ae06f9bb51c1749623d96fd` |
| [Shared scalar calculator](corner-net-section.py) | `8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5` |
| Its existing `../member_stability.py` rectangle coefficient dependency | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |

The parent supplied the finalized helper pin after executing its rectangle
coupon and eight named corner cuts successfully (`rawlocal/corner-net-section/attempt01`,
checks prefix `691df118`). This header adapter imports `nominal_section`,
`area_properties` and `rectangular_known_answer` from that exact source.
It does not import corner geometry, cut indices, force fields or material
references. Only the existing scalar rectangle coefficient dependency is
needed; no manual, CAD or native mechanics package is loaded.

## Actual header geometry and six duties

Header grain is global X. Geometric section coordinates are Y/Z. The frozen
rotated material R/T axes are recorded unchanged, and are not relabeled as
Y/Z. The common equal longitudinal shear modulus hypothesis permits the
nominal transverse calculation in geometric Y/Z coordinates.

| Header duty | Station from left end (mm) | Bore diameter (mm) | Section suffix |
| --- | ---: | ---: | --- |
| Left inner knee | 133.35 | 7.5 | `2d69ffdf7163d5db` |
| Left center post | 993.49 | 7.3 | `f7ae23a71b2b45df` |
| Left center principal | 1103.20 | 7.3 | `cbb798b352fe0eb8` |
| Right center principal | 1335.20 | 7.3 | `babb38b034c22504` |
| Right center post | 1443.55 | 7.3 | `b2bc8028d24db3ff` |
| Right inner knee | 2301.875 | 7.5 | `91b7a2e2788bd266` |

The adapter joins each saved plane to its actual two connection axes. It
constructs the three retained rectangles by removing the two existing
full-depth cylindrical bore chords from the saved finished header envelope.
It checks their areas, centroids and section inertia against the saved exact
section properties. All coordinates come from the header contract; no top
corner geometry or geometric shortening is transferred.

## Nominal working hypotheses and comparisons

Use the finalized helper's common longitudinal strain plane, with continuous
wood beyond the bores providing end-bridge compatibility. Transverse forces
share in proportion to retained rectangle area, retaining centroid-offset
moments. Equal longitudinal shear moduli and common twist distribute centroid
torque by each rectangle's standard Saint-Venant torsion constant. No
prestress or balancing free couple is introduced.

For each same cut, trace and rectangle, record the conservative nominal shear
bound `1.5*hypot(Vu, Vv)/A + tau_torsion`. Compare it with unchanged longitudinal
Fv. Record tension/Ft, compression/Fc, absolute bending/Fb and the existing
axial-plus-bending reference sum at each retained rectangle corner. These
are nominal stress/reference comparisons, not new interaction capacities.

The header's existing nominal 2×6 DF-L No. 2 CF-only references are retained:
Fb 8.066866033 MPa, Ft parallel 5.153831077 MPa, Fc parallel 10.238714580 MPa,
Fv parallel 1.241056313 MPa. They come directly from the prepared header
evidence, including its recorded adjustment assumptions. The helper's corner
4×6 reference values are not used.

The complete A1-rear left-knee after trace stays
`[-3.319134, +151.378204, -155.117256, -12768.261359, +8240.562206, -12998.207201]`
in N/N·mm: full torque −12.768261 N·m. Both A1 traces are matched to the
completed traction-map witness and retained with their regional comparisons.
Zero sampled knee normal contacts do not remove header torque.

The supported boundary map remains the existing conditional washer/contact
construction. The saved source before/after cuts are nominal demands; this
adapter does not reinterpret a cut inside the distributed washer annulus as
a physical pressure-map center-plane stress. End-bridge sharing, common
twist and opposite-wall contact remain explicit MVP assumptions. Bore stress
concentrations, splitting, perpendicular tension and group qualification
are outside this finite nominal comparison; no new method chain is required
by this packet and no unavailable resistance is invented.

## Parent API, coupon and output

Python API: load this file with `importlib.util` and call
`build(output: str | pathlib.Path) -> dict`. The output must be a fresh child
of `rawlocal/header-net-section/`. The returned summary includes status,
counts, result/receipt hashes, same-state peaks and independent accounting
residual maxima. The helper's translated rectangle coupon is included once
in the same calculation, using the header references: known affine stress,
all six datum-shift components, transverse shear and standard rectangle
torsion. It is arithmetic readiness evidence, not a software test or solve.

Single parent command from the repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/header-net-section.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/header-net-section/attempt01
```

The fresh ignored child contains `checks.json`, `receipt.json`, the producer
snapshot and `.gitignore`. The result records all 72 full signed cuts, their
role accounting, rectangle forces and offset moments, normal/shear references,
per-duty and overall same-state witnesses, counts of comparisons above 1.0,
and independent source-restoration/regional-closure residual maxima. Wrench
accounting tolerances are 1e−7 N and 1e−5 N·mm; they are numerical tolerances.
Changed pins, missing actions, incomplete duty joins or mismatched geometry
stop the calculation. A comparison above 1.0 remains visible and is not
converted into a pass.

All formal qualification, native readiness, mechanics execution,
compatibility solved, new resistance, complete joint acceptance and physical
release flags remain false. Counterpart claim gates and the existing authority
remain unchanged. Parent owns execution, integration and publication.

## Completed parent result and frozen receipt

The parent inspected the calculator and documentation, reported Ruff passing,
pinned the producer below and completed the single serialized run in
`rawlocal/header-net-section/attempt01`. The parent authenticated all nine
source pins and both output pins. The worker confirmed the producer, result
and receipt hashes while annotating this document; no calculation was repeated.

| Artifact | SHA-256 |
| --- | --- |
| [Frozen producer](header-net-section.py) | `d413a2ae912df6bf56086ad6ddda59526db32cc6325f1b4bf2b71f984d86a328` |
| `rawlocal/header-net-section/attempt01/checks.json` | `f582f87a45b80e9f95b5344bad289ce9837d4088135b21fc26c15dfc3e1d462d` |
| Same packet, `receipt.json` | `dbb35782f1e028459ec6b13877f98d242e7cbb5e80d2de6df0a2c57e4e96c988` |

The completed census is six duties, 72 signed cuts, 216 regional comparisons
and 864 longitudinal normal corner comparisons. The following independent
maxima retain their own same-state identities in `checks.json`; they are not
combined into a synthetic load state.

| Nominal comparison | Maximum reported index |
| --- | ---: |
| Total tension / Ft parallel | 0.25571867 |
| Total compression / Fc parallel | 0.12806032 |
| Absolute bending / Fb | 0.16316026 |
| Axial-plus-bending reference sum | 0.16413409 |
| Same-state transverse-plus-torsional shear bound / Fv | 0.34858933 |

| Independent accounting residual | Maximum force (N) | Maximum moment (N·mm) |
| --- | ---: | ---: |
| Full source action restoration minus saved section | 4.55e−13 | 5.57e−10 |
| Reconstructed regional wrench minus full source section | 1.76e−13 | 1.46e−11 |

The complete A1-rear left-knee after-trace torque remains −12.768261 N·m,
with both full signed traces retained. These are finite nominal comparisons
under the existing end-bridge, common-strain, transverse-sharing and common-twist
hypotheses. The original 100 mm/250 lb × 2/signed 300 N source, all false
qualification/release flags and counterpart claim gates remain unchanged.
The bounded task is complete; producer and documentation ownership return to
the parent for integration and publication.
