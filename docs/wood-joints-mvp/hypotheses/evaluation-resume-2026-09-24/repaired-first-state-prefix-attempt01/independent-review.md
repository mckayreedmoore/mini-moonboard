# Independent review: corrected first-state prefix

This review covers only the immutable files in this directory. It does not
read the live run directory, invoke the capture program, or run CCX. The
capture was taken while attempt03 was still running; it is not a terminal
record or a full-trajectory result.

The reviewed pins are `capture.json` SHA-256
`7423133652ecb58b2698a7bb66f5b5956f5810e34d2b6dd646913452052269a0`,
`analysis.json` `23fefcf88712c08b84439747afbc49905e57604d468a64bf72e1c5e275c3d5cf`,
`capture_and_audit.py` `0dca6ca71586a374602adf45a6ae0b08067e3269e380083251dfa9886ed43483`,
and `reader_helper.py`
`607742ec48228a473923031dacccab1062478cdef43c28e886aaeb621f65b716`.
Captured run identity is execution status `running`, container
`e104dafd66343b264759bbc0eb38772344d9ba4ab7ef0430de058452fed79051`,
binary SHA-256 `3b63e1590b143be79c4c869c218286fc83c081fd89802a63658cd13776b60ab0`,
and source-index SHA-256
`b55323a611704378ad84f1e688075e284859bdbd09b75d853c0bb8ef0b9ef19f`.
The copied execution and capture manifests agree on all eight input hashes;
the copied `pilot.inp` also matches its recorded hash. The frozen files match
all captured byte lengths and SHA-256 values. The other seven input byte
streams are not copied here, so offline verification of those inputs relies
on the capture producer's before/after hash checks and the parent-authenticated
manifest.

I independently replayed the frozen parser's pure STA, point-join, CELS, LOG,
and acceleration-row readers. The first accepted state is step 1, increment
1, attempt 1, at 0.0005 s after 23 iterations. All 104,245 writer point rows
join one-to-one with the DAT point identities; there are no unmatched rows or
duplicate DAT point keys. The DAT CELS table has a terminating boundary and
104,245 parsed rows. Its energy is `3.478602937091854873853287e-11 N mm`,
versus writer sum `3.4786029442674645207833417000531865e-11 N mm`; the
difference `-7.1756096469300547e-20 N mm` is within the combined printed-token
bound `6.7386076046921624e-18 N mm`. The accepted-increment LOG value is
`3.478603e-11 N mm`; its difference from the writer sum
`5.5732535479216658e-19 N mm` is within the combined bound
`5.0000000035253614e-18 N mm`.

The separately reported source-formula checks replay as recorded: maximum
writer/formula point difference `6.310887241768095e-30 N mm`, and zero
C/DAT differences at printed precision for clearance, pressure, and area.
These are pointwise/output arithmetic observations; the bounded sum checks
are reader-equality evidence. Neither establishes contact-law validity or
mechanical acceptance. The legacy compact-index CSV energy and FRD CELS are
not used in the reader verdict; the attempt03 source index identifies LOG
and DAT CELS as point-slot readers and excludes FRD CELS as an energy
authority.

The acceleration stream has one complete framed state at 0.0005 s, with
ascending IDs 1–116,162, 116,162 records, and finite X/Y/Z acceleration
components. The JSON field `finite_xyz` refers to those acceleration
components, not spatial coordinates. This verifies the emitted first-state
record coverage and finite values; it does not verify a momentum or
equilibrium balance.

One material completeness boundary is visible at the end of the captured
DAT: after the completed energy table, output ends immediately after the
`WJ_ANGULAR variable=CFS, role=master` header for tie 35, without its numeric
row. Thus this prefix supports the completed CELS energy comparison, but does
not establish complete angular-resultant output or angular closure. The
partial angular tail does not change the independently parsed, terminated
CELS table.

I found no inconsistency in the bounded first-state reader comparison. The
result remains a live-run prefix only: it says nothing about later contact
states, full-run completion, time accuracy, joint resistance, or any formal
acceptance criterion.
