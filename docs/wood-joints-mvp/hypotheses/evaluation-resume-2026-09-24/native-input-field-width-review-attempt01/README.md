# Preserved native input field-width review

Status: read-only audit complete. No historical input, result, or producer was
changed; no build, native solve, or freeze was performed.

The pinned CalculiX 2.23 readers consume CLOAD values from the first 20
characters of their value textpart (`cloads.f:267`, F20.0) and BOUNDARY
values from the first 20 characters (`boundarys.f:355`, F20.0). I compared
each scalar's full text token with the value parsed from its first 20
characters in all preserved `.inp` files containing either card under
ordinary external-force transient attempts 01–03, attempt 04 diagnostic and
its replay, and current port-motion attempt 09.

The audit covers 78 input/working-copy files and 17 unique deck contents.
Across file copies it found 12,452 CLOAD value rows and 134 BOUNDARY value
rows (146 expanded constrained DOFs). Across unique deck contents these
counts are 2,800 and 29 rows (32 expanded DOFs). Every scalar token is at most
20 characters. There are zero over-width fields, zero parser/full-token
numeric differences, and zero parse errors. Per-file deck paths, SHA-256,
field counts, maximum widths, numeric difference summaries, and value-sequence
hashes are in `audit.json`.

The producer snapshots match the emitted fields. The external-port load
formatter uses `.13e` and explicitly rejects a formatted value longer than 20
characters. The transient force runner also emits `.13e`; the actual CLOAD
values in its frozen decks fit the reader width. The port-motion boundary
producer writes `.13e` control values; the actual imposed values fit as well.
Attempt 04's two coupon input/working copies contain only short BOUNDARY
values, including `-0.001`, and no CLOAD rows. Producer paths, hashes, and
relevant formatting lines are captured in `audit.json`.

The first-20-character comparison is distinct from ordinary coordinate
rounding. Across five identical copies of `mesh.inp` (SHA-256
`117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`), 18 of
348,486 coordinate components exceed 20 characters. None uses exponent
notation. The largest difference between a full coordinate token and its
first-20-character parser value is `6.94e-18 mm` (`1.45e-15` relative). The
five identical `nut-coupling.inp` copies have 24 coordinate components with no
over-width fields; all 18,420 MPC coefficient fields also fit within 20
characters and parse without numeric change. These tiny fixed-decimal
coordinate-prefix effects are not exponent truncation of a load value.

Source reader evidence is pinned to the attempt 04 diagnostic CalculiX source
archive, SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The exact source-member hashes and the `nodes.f` / `equations.f` field checks
are recorded in `audit.json`. `audit.py` reruns this bounded scan and writes
the deterministic JSON report.

Conclusion: the discovered F20.0 CLOAD truncation hazard does not appear in
these preserved external-force or port-motion inputs. Their CLOAD and
prescribed BOUNDARY values reach the pinned reader unchanged. Keep the
20-character check on future generated values; this result is limited to the
files and source pins listed in the audit.
