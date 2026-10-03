# Final architecture and ownership review

**Reviewed:** October 1, 2026. **Outcome:** no substantial architecture or
ownership findings in the requested scope. This is a source and artifact
boundary review. It does not qualify resistance, validate a physical assembly,
run CAD extraction, or perform native mechanics. The root-owned final
status and receipt-index metadata remain parent-owned and pending.

The bottom packet has a clear, bounded owner: `produce.py` joins four axes,
three members, eight receiver memberships and six finished bore planes to the
existing three rear response families. It verifies frozen source and STEP
identities, preserves the simultaneous point-action cut states, and emits
explicit negative acceptance flags. Its repository root calculation
(`HERE.parents[3]`) resolves correctly from this packet; the README commands
use the same root-relative layout.

The dependency boundary is inspectable. The producer SHA-pins the feature
register, case freeze, contact geometry, point-action helper and section helper;
the case freeze transitively pins its model, response and audit inputs, and the
feature register binds the STEP files. The repository Python 3.12 project and
`uv.lock` pin the runtime, including CadQuery 2.8.0 and OCP 7.9.3.1.1. The
independent verifier uses only the standard library, imports neither the
producer nor its arithmetic/CAD helpers, and reconstructs source actions and
cuts from the frozen source records. Section extraction is intentionally a
separate responsibility; the verifier checks reported section identities and
internal consistency rather than claiming a second CAD extraction.

The publication boundary is explicit and consistent: public synthetic tests
exercise the producer contract without the local raw response or STEP inputs;
full extraction and raw-source replay use locally retained frozen evidence, and
the raw report is intentionally not required in the published packet. The
reviewed documentation does not make publication or receipt of that evidence
an engineering, inspection or fabrication prerequisite.

The updated integration fixture adds independent hand-calculated expectations
for a full-load body wrench, both bore-plane traces, rounding bounds, centroid
transports and local components; the force on the plane exercises the cut jump.
The expectations are constants in the fixture and do not call producer
arithmetic helpers. The validation index now records the current test and
verifier hashes. A path-only spot-check confirms the washer independent review
links to the existing primary corner axial-seat register; that review's
conclusions were outside this pass.

The resistance table keeps the existing bolt scenario unadopted and routes
finished-section, contact, splitting and combined-joint questions to further
source-bound evidence. The washer preflight also keeps the boundary open: its
primary comparator is a three-dimensional washer/bolt/wood contact study
validated against washer-embedment tests, with different materials and square
washers. The paper reports average stiffness underprediction and yield-load
overprediction, so the review properly treats it as method-family precedent,
not a transferred factor, candidate washer result or local-stress validation
([Teranishi et al., 2021](https://doi.org/10.1186/s10086-021-01973-9)). The CSV
keeps experimental and FEA values separate and identifies assembly yield load
as its output; no tolerance or design capacity is inferred.

No code or source-data change is recommended. The review did not rerun tests,
lint, extraction or native analysis; the supplied validation record reports
the twenty synthetic tests, Ruff and formatting, repeated local extraction and
independent source replay. Hashes below identify the exact artifacts inspected
in this review; `validation.md` is its current version before the parent-owned
final status and receipt-index update.

## Reviewed artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `README.md` | `e51fa673635d68f8674d7bdbbeaa00309f11f9412735afab430260aa6353334f` |
| `produce.py` | `662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7` |
| `parent_verify.py` | `7b1ceeaf8e68a6f92c6d78e993d781be792e73a31a5b35d0a781195e88cebb0e` |
| `test_sections.py` | `2632083c4e393b0d212426522405463f642f11cf488155a50617579eb6517aad` |
| `test_integration.py` | `739ec1d1b01ed2c85dc23e5254369ce88d660d3bfb515564161d72758827714c` |
| `resistance-disposition.md` | `39945e0cd3cfc2cc904d3880ae3019db6a92bd0512af075d0316700e937ae066` |
| `validation.md` (before parent final status/index update) | `75da22785f3c4476168abceddbe330b7b1e9e803e5103db1dc817fe03c5d6ca2` |
| Washer `source-method-review.md` | `20e85755030d56d14779bca0598aa3c057a58e8a188aa77693b8b3219bc85bf0` |
| Washer `benchmark-inputs.md` | `2d484a4eb04faa9b1f30752e9536474c15f2060d7c15696fdc3f7f190ff5d9da` |
| Washer `teranishi-2021-benchmarks.csv` | `3034e5e4d9cab165f3758e660defba87611e889deb0f81993e58591a1f838040` |

## Execution and source dependency fingerprints

| Dependency | SHA-256 |
| --- | --- |
| Root `pyproject.toml` | `84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452` |
| Root `uv.lock` | `5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3` |
| Root `.python-version` | `9ea280e4c89d3f302c1e8b3e5e7db91c46bec0fe761356ae90f32aaf0dbe0e8b` |
| Point-action helper `host_actions.py` | `39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b` |
| Section helper `section_geometry.py` | `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` |
| Feature register `axis-features.json` | `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19` |
| Three-case `freeze.json` | `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` |
| Source `contact-geometry.json` | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
