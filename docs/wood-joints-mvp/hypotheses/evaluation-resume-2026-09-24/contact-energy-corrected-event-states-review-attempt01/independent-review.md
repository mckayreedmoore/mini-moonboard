# Independent review: corrected contact-energy states 39 and 40

This review is bounded to the two accepted-state output slices selected by the author. It does not rerun CalculiX or rehash the multi-gigabyte outputs in full.

## Frozen evidence reviewed

The author’s attempt folder is `../contact-energy-corrected-event-states-attempt01/`.

- Producer `audit_two_state_contact_energy.py`: `2a3ca9f4c316b53da284cce2a15bda58fceb0aae48f8f8948d6f70ca777351db`
- Result `analysis.json`: `658c16682e7553d53e555288574ec9d64b57d3dc5f6e0da08d369aa7359d4694`
- Focused tests: `5e12bf9c72f0882e98bb36544151ca90e12cb8ee81b7005833a17dcef597b28d`
- README reviewed: `f74712b9d9a1d6310a4fefd6fa55a625d4f954845ef788bc1bdfd0e6405ff46b`
- Terminal execution: `fef69a37664f9dea002394270547f6c3e3adec0cb53669daa2b0b2f4de9d0052`; source index: `b55323a611704378ad84f1e688075e284859bdbd09b75d853c0bb8ef0b9ef19f`; binary: `3b63e1590b143be79c4c869c218286fc83c081fd89802a63658cd13776b60ab0`.

I independently re-read the recorded byte ranges from the frozen terminal CSV, DAT, and LOG files and recomputed their hashes. All selected CSV, CEP, CELS, and LOG slices match their extraction hashes. I separately parsed the two CSV/CEP slices using Decimal arithmetic and checked the small STA/LOG identity records.

## Findings

The selected states are step 1, increment 39, attempt 1 at 0.0195 s and increment 40, attempt 1 at 0.01975 s. These identities match the accepted STA rows and the corresponding CSV, DAT CEP/CELS headers, and LOG segments. Each state has one complete STATE/END block: 72,045 point rows at increment 39 and 79,174 at increment 40. All C point keys are unique and exactly match the DAT CEP keys; DAT CEP and CELS row counts equal the corresponding point counts. The CEP energy record has 23 pair tags at increment 39 and 21 at increment 40; the audit does not claim omitted pair tags are zero.

Area, pressure, native-clear, and projected-clear tokens match across the keyed C/DAT point records within the printed-token bounds. The writer sums are 0.0375142917434256061263 N·mm and 0.00587031359657693340880 N·mm. Both writer sums agree with the complete DAT CELS sums and same-state LOG energy under the propagated per-row CELS and aggregate LOG token bounds. The report correctly excludes FRD CELS, whose source path retains the legacy compact address.

The report also exposes a distinct per-point diagnostic: writer energy-slot tokens versus the DAT `printer_energy` expression exceed their energy-only token bounds at 5,244/72,045 and 5,692/79,174 points, with maxima 6e−20 and 4e−21 N·mm. I reproduced those counts and maxima. This is consistent with the pinned source’s different evaluation paths (`senergy = -elas*clear/2` for the stored slot versus `-0.5*(pressure*area)*clearproj` in the point printer). The separate source-law reconstructions pass with propagated input and arithmetic bounds, and the actual corrected-reader CELS/LOG aggregates pass against the writer sums. The report keeps these claims distinct; this is not a mechanics or acceptance result.

The parent-stopped terminal record is consistent with the README: return code 137, no timeout/OOM, accepted output through 0.0203 s, requested 0.025 s endpoint unverified, and `mechanical_acceptance=false`. Increment 41’s later partial DAT tail is outside the selected states.

## Required wording correction

The reviewed README says the join key is `(slave, master, igauss)`. That is not the implemented key and the CSV has no slave/master fields. The producer uses the exact key `(element_fortran_number, igauss, jfaces)`; DAT `tie/slave/master` tags are retained metadata on the matched CEP rows. Correct that sentence before treating the README as final. This documentation issue does not change the independently reproduced numbers or reader conclusion.

The two focused tests pass. No native, CAD, or full-output rescan was performed.
