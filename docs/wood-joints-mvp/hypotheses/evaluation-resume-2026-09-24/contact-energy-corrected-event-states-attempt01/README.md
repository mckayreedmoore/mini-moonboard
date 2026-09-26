# Corrected contact-energy accounting at accepted states 39 and 40

This bounded audit checks corrected contact-energy output accounting at step 1,
increments 39 and 40. It uses the accepted state identities from the parent
framing audit, the contact-energy point-map CSV, the corresponding DAT point
records and complete DAT `CELS` tables, and each state’s accepted energy line
from `pilot.log`. It does not use FRD `CELS`: the pinned output source identifies
that path as the legacy compact-address reader.

The native run was explicitly parent-stopped (return code 137, no OOM or
timeout). Its accepted endpoint is 0.0203 s; the requested 0.025 s endpoint was
not verified. This audit therefore covers only the two selected accepted
states. The report is output-accounting and source-law evidence, not equilibrium,
contact validation, capacity, or joint acceptance.

## Method and result

The producer streamed the 1,695,720,152-byte DAT once and retained only the
selected point records and CELS blocks. For each state it joined the CSV energy
slot and DAT `WJ_CEP` records by the exact
`(element_fortran_number, igauss, jfaces)` key. The DAT `tie/slave/master` tags
remain matched-record metadata, not join keys. The producer checked pressure,
area, and native clear against the CSV tokens, and reconstructed each output’s
own energy expression with propagated printed-token bounds. It then
compared the CSV writer sum, DAT `CELS` sum, and accepted `LOG` energy using the
sum of their printed-token bounds. All selected point-key sets and counts match.

| Accepted increment | Points | CSV writer sum (N·mm) | DAT `CELS` sum (N·mm) | `LOG` energy (N·mm) | Writer−CELS / bound (N·mm) | Writer−LOG / bound (N·mm) |
|---:|---:|---:|---:|---:|---:|---:|
| 39, t = 0.0195 s | 72,045 | 0.0375142917434256061263 | 0.0375142918666575592231 | 0.03751429 | −1.23232e−10 / 6.92512e−9 | 1.74343e−9 / 5.00001e−9 |
| 40, t = 0.01975 s | 79,174 | 0.00587031359657693340880 | 0.00587031362395516794923 | 0.005870314 | −2.73782e−11 / 1.11820e−9 | −4.03423e−10 / 5.00001e−10 |

Both aggregate comparisons are within the combined printed-token bounds. The
CSV writer’s source-law reconstruction also passes pointwise and in aggregate
for both states using the pinned operation order
`-0.5 * (pressure * area) * native_clear`. The DAT point records independently
pass their own projection-law check using
`-0.5 * normalforce * clearproj`; pressure, area, and projected/native clear
tokens agree with the CSV tokens at all selected points.

There is a separate pointwise token diagnostic: comparing the CSV sparse
`ener` slot directly with the DAT `WJ_CEP_VALUE` `printer_energy` field exceeds
the combined energy-token-only bound at 5,244 of 72,045 points in increment 39
and 5,692 of 79,174 points in increment 40. The largest differences are
6e−20 N·mm (increment 39) and 4e−21 N·mm (increment 40); the largest per-row
excess over the combined bound is 5e−20 and 3e−21 N·mm, respectively. This
compares two distinct output calculations: a stored sparse energy slot and the
direct `-0.5 * normalforce * clearproj` DAT expression. It is an output
operation-order diagnostic, not a corrected-reader equivalence verdict. Each
calculation passes its own formula check, and the actual DAT `CELS` and `LOG`
reader aggregates pass against the CSV writer sum above.

The complete per-point counts, formula checks, tolerances, worst keys, exact
selected byte ranges, and extracted-file hashes are in `analysis.json`. Its
`terminal_point_map_stream_verification` confirms that the selected CSV ranges
were checked against the terminal CSV hash and byte size.

## Frozen evidence

The run, source index, binary, inputs, output files, framing evidence, and
relevant reader/writer source hashes are recorded in `analysis.json`. Principal
pins are:

- Producer `audit_two_state_contact_energy.py`: SHA-256
  `2a3ca9f4c316b53da284cce2a15bda58fceb0aae48f8f8948d6f70ca777351db`.
- Focused tests `test_audit_two_state_contact_energy.py`: SHA-256
  `5e12bf9c72f0882e98bb36544151ca90e12cb8ee81b7005833a17dcef597b28d`.
- Result `analysis.json`: SHA-256
  `658c16682e7553d53e555288574ec9d64b57d3dc5f6e0da08d369aa7359d4694`.
- Run DAT: SHA-256
  `bfcc73d49159936a24fe3d90579733388d1b8e637b3ea30ce3e722c11c167459`;
  run CSV: SHA-256
  `56b4228237044623e2e32da5d0d74e6be592bec85f319b400f34cc7aa3d29f60`.
- Terminal status: `parent_stopped`, solver/Docker return code 137,
  `oom_killed=false`, `timed_out=false`, `mechanical_acceptance=false`.

The selected DAT CELS blocks are exact source slices: increment 39 occupies
bytes `[1597194265, 1599787986)` and has SHA-256
`c9085a5ff160726c8ade92de5105e5c3ee67a7cfd9f29d3a802d8814a54c360b`;
increment 40 occupies `[1625790300, 1628640665)` and has SHA-256
`675679b82470ece4df2261e5456451ce2b43ae0278ac1d2a16fef68cf922b015`. The
matching accepted LOG segments and point-map/CEP slices are hash- and
byte-range-pinned in `analysis.json` and preserved under `extracted/`.

The focused tests cover the exact selected CELS block boundaries and reporting
of a metric that exceeds its declared bound. Run them with:

```sh
python3 -m unittest docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/contact-energy-corrected-event-states-attempt01/test_audit_two_state_contact_energy.py
```
