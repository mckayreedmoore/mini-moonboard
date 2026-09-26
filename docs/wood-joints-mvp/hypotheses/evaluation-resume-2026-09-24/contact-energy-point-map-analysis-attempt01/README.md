# First accepted contact-energy point-map audit, attempt 01

This read-only audit isolates the energy discrepancy in the first accepted state of `dependent-residual-contact-trajectory-run-attempt01`. It parses only the terminal run artifacts and the source-pinned output streams; it does not change the contact law, model, or solver and does not establish mechanical acceptance.

## Accepted state and provenance

The first `.sta` row is accepted step 1 / increment 1 at total time `0.0005 s`, with increment time `0.0005 s` and 23 iterations. The CSV `STATE` and `END` rows each declare 104,244 points, and the parser independently counts 104,244 complete `POINT` rows. This satisfies framing because all three counts agree; `END` itself repeats the producer's expected count and is not an independently accumulated write count.

The run stopped at the parent's request after the first accepted state exposed the energy mismatch. The native process returned 137, the requested `0.025 s` endpoint was not reached, and `execution.json` records no accepted endpoint verification or mechanical acceptance. The return code is the parent's bounded stop, not a solver acceptance result.

The accepted outputs are bound by the frozen run `execution.json` to instrumented executable SHA-256 `af0da93038dda93e7d9807f392a5fe6c4fd5f2b9d0b47d0de5d107936795d174`, solver image `sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`, and binary source-index SHA-256 `1b7db302ac72d4511c1a0697763a48b936b72e5c494228c22a7a34bcf4e01745`. The source index binds the built C/Fortran sources to the reviewed point-map proposal and declares mechanical acceptance false.

| Run artifact | SHA-256 |
| --- | --- |
| `pilot.wj-contact-energy-map.csv` | `227a60baca84fa400cf408b02e27a6826895d63d49f9cdacc7d7c6c9b554dbd2` |
| `pilot.dat` | `98582fc99ea1f4218275ab3d7ac4c60013446318fb5d94d094d4f9441b7e249c` |
| `pilot.sta` | `ccc90a7fc440241c1eb5c7096a001fe39557c7ba927b0471ecd73f14b54cbdfb` |
| `pilot.log` | `e47ac7adb24905a87bbc650dd1c0c8b8c19bbf2e25f15800585cfb9815437eb0` |
| `execution.json` | `aad5d6d3cf724525064b4bac20458165d6db83c31dc922d6a202113c3445dba8` |
| `binary-source-index.json` | `1b7db302ac72d4511c1a0697763a48b936b72e5c494228c22a7a34bcf4e01745` |

## Point-map result

| First accepted state, step 1 / increment 1 | Result |
| --- | ---: |
| C map rows / DAT `WJ_CEP_POINT` + `WJ_CEP_VALUE` rows | 104,244 / 104,244 |
| Unique C-to-DAT joins by CE element, `igauss`, `jfaces`, and time | 104,244; no duplicate or unmatched keys |
| `WJ_E_IF` pair summaries | 35 total; 19 pair IDs have CE point rows, 16 have no CE point rows and report zero pair energy |
| C writer elastic energy, writer slot `ne0 + igauss` | `3.478603644581715e-11 N·mm` |
| C writer viscous energy | `0 N·mm` |
| Native-clear linear-law reconstruction | `3.478603644581715e-11 N·mm` |
| Fortran CE point energy from `clearproj` | `3.478603644581715e-11 N·mm` |
| Sum of 35 `WJ_E_IF` pair totals | `3.4786036445817124e-11 N·mm` |
| C compact-index elastic sum, slot `nelem` | `1.091529615022061e-9 N·mm` |
| C compact-index viscous sum | `0 N·mm` |
| Printed CELS table | 104,244 rows; displayed sum `1.091529611754609e-9 N·mm` |
| LOG elastic contact energy | `1.091530e-9 N·mm` (rounded output) |

All 104,244 writer addresses differ from their compact addresses, and all 104,244 energy values differ. For the pinned build, the writer uses `ne0 + igauss`; the compact value uses `nelem`. The compact-index sum is within `3.27e-18 N·mm` of the sum of displayed CELS rows, and the LOG rounds to the same scale. The CELS and standard LOG paths share the compact-reader lineage, so their agreement does not independently validate the writer values.

For this accepted state, C map and Fortran records have identical area, pressure, and native clearance at their printed precision. `clearproj` also equals native clearance at printed precision for every joined point. Using the binary64 pressure-area reconstruction (first `force = pressure × area`, then `-0.5 × force × clearance`), the largest per-point difference between C writer energy and reconstructed native-clear energy is `6.31e-30 N·mm`. Re-evaluating the printed decimal tokens as exact real numbers instead gives a largest residual of `1.79e-29 N·mm`; that is a display-token versus binary64-operation comparison, not a different energy law. The largest writer-to-printer point-energy difference is `6.31e-30 N·mm`. Pair-energy summaries differ from reconstructed point sums only at printed/summation precision. The discrepancy is therefore localized to the distinct writer and compact-index paths in this exact uncorrected executable; this audit does not implement or certify a reader repair.

For the current pinned frictionless linear pressure-overclosure branch, native `springforc_f2f` computes `elas = -springarea × stiffness × clear / kscale`, then `senergy = -elas × clear / 2` and stores pressure as `elas / springarea`. The audit reconstructs energy from the recorded pressure and area as `E = -0.5 × (pressure × area) × clearance`; this matches the printer operation order and is mathematically equivalent for this branch, but it is not a bitwise replay of the native writer intermediate operations. C `stx(1)` and Fortran `clearproj` remain separate in the parser. This formula is not generic to other contact laws. Sixteen `WJ_E_IF` pair rows have zero reported energy and no emitted CE point rows; zero energy or absent point output is not evidence that those interfaces carry no force or have no contact.

The completed log/map are from the longer `0.025 s` horizon. Although the selected increment is `0.0005 s`, `clearini × reltime` can make its native clearance differ from that in the preserved shorter paired arm. This audit uses only this run's native clearance, pressure, energy, and matched point IDs; it does not import old per-point energies as expectations or require the short arm's values to match.

## Parser and artifacts

`parse_contact_energy_point_map.py` streams `.sta`, CSV, and `.dat` records, binds step/increment/time to a numerically accepted `.sta` row, rejects incomplete count framing, matches CE point IDs, and reports writer/compact sums and source-law reconstructions. The large per-point detail is retained as a separate CSV; `analysis.json` is the compact machine summary. Four focused tests pass against the actual C emitter and Fortran printer harness fixtures, including rejection of a truncated C block and a check that the separate fixtures cannot falsely join.

- [Machine summary](analysis.json) — SHA-256 `72dbfb3210fcf2abfc9892f2bb009e0efe4e01e890dd70492ec88caed182d1c9`
- [Matched point rows](matched-points.csv) — SHA-256 `fcccc25f1e80b7361a3e4056e7423044f5e02d01363ededd7072fc62e6a2cc42`
- [Parser](parse_contact_energy_point_map.py) — SHA-256 `78887f638b7d3bf8b200e12e03b3ad179f1d53226e285ed2a808b3de0cc3eb0f`
- [Focused tests](test_parse_contact_energy_point_map.py) — SHA-256 `6b72232662328db6ada1c13964d8578bd4aad171b7d368f35b2acba102e1d375`

Run command:

```sh
python3 parse_contact_energy_point_map.py \
  --csv ../dependent-residual-contact-trajectory-run-attempt01/pilot.wj-contact-energy-map.csv \
  --dat ../dependent-residual-contact-trajectory-run-attempt01/pilot.dat \
  --sta ../dependent-residual-contact-trajectory-run-attempt01/pilot.sta \
  --log ../dependent-residual-contact-trajectory-run-attempt01/pilot.log \
  --execution ../dependent-residual-contact-trajectory-run-attempt01/execution.json \
  --binary-source-index ../dependent-residual-contact-trajectory-run-attempt01/binary-source-index.json \
  --points-output matched-points.csv --output analysis.json
```

Run tests from this directory with `python3 -m unittest discover -p 'test_*.py' -v`. The full native attempt stopped after the first state because this audit identified a numerical/output-path defect; it is not a converged joint result or physical acceptance.
