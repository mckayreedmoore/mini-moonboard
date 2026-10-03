# Bottom-outer architecture and ownership review

## Assessment

The bottom producer is a focused, read-only adapter for the four selected axes. It validates candidate and case identity, reuses the two secondary methods by exact content hash, keeps the six planes/eight memberships and 63 body/252 cut state counts explicit, and marks section resistance and joint acceptance false. Repository-root resolution is relative to the script location, so it does not depend on the author's checkout path. The project lock covers CadQuery/OCP, and the section method records the runtime kernel versions in each section result.

No substantial architecture or ownership finding was identified. The README correctly distinguishes public-checkout verification (synthetic tests and lint) from full extraction, which uses intentionally local frozen JSON and STEP evidence. Its commands and stated boundary are consistent with the source: synthetic tests import the code methods and generated fixtures, while `produce.py` verifies and reads the local inputs only when invoked.

## Reproducibility and claim boundary

The reviewed code uses `Path(__file__).resolve()` and repository-relative paths (`produce.py:14`), hashes its JSON and method inputs (`produce.py:27`, `produce.py:77`), and verifies the finished STEP and frozen case files before extraction (`produce.py:263`, `produce.py:298`, `produce.py:312`). It performs no native solve and does not rewrite source responses. Its output is printed to stdout and includes the method/source pins, case sources, kernel versions, and explicit false flags for actual traction, common strain, resistance, criterion pass, and joint acceptance. The method and geometry notes preserve those limits.

The project requires Python `>=3.12,<3.13`; `uv.lock` resolves CadQuery 2.8.0 and CadQuery OCP 7.9.3.1.1. The secondary helper identities match the producer pins exactly: `section_geometry.py` SHA-256 `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` and `host_actions.py` SHA-256 `39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b`.

## Reviewed working-tree hashes

| File | SHA-256 |
| --- | --- |
| `produce.py` | `662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7` |
| `test_sections.py` | `2632083c4e393b0d212426522405463f642f11cf488155a50617579eb6517aad` |
| `method-review.md` | `54cc0b7e72482cb63954468d9d58438ee0be3c97da92ffe0e66079a870b868a8` |
| `finished-geometry-review.md` | `b0b6d281a604e8ea9db6897e3838e077c768f750255f86915c412d2aa7558029` |
| `../upper-outer-finished-sections-2026-10-01/section_geometry.py` | `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` |
| `../upper-outer-load-path-2026-10-01/host_actions.py` | `39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b` |

These are working-tree identities. The bottom folder and upper section helper were untracked when reviewed, so the final published revision needs to include the code required by the README's test/lint commands and retain the reviewed hashes or update this review after changes.

This review did not rerun the producer or perform any CAD/native mechanics run. It is limited to code ownership, dependency and path behavior, source availability, and the stated result/claim boundaries.
