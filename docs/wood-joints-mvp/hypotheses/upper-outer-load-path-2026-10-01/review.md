# Upper outer load-path validation

This review covers the point-action, native-MPC transfer and host-section
calculators, their tests, and the splitting-source note at
`led-clearance-2x6-runner-seated-blocks-v1`. It covers reproducible extraction
and stated method boundaries. It does not accept a material resistance,
finished-section stress field, complete joint or six-case envelope.

## Review disposition

Two rounds of three independent Luna maximum-reasoning reviewers examined
the core calculators, with separate mechanics, testing and evidence/ownership
scopes. Confirmed findings were fixed: explicit source candidate/revision
binding, rejection of fractional or boolean node/DOF IDs, and durable producer
and ignored-result identities. The identity and malformed-ID fixes have
regression tests. Neither fix changes the replayed action values.

Parent inspection of the host draft also corrected its discrete load-factor
application and source-row name lookup before the completed replay. Its tests
now check scaled loads and a bored-section CAD known answer. The source note's
rail T/N labels were corrected against the frozen frame map and bolt axes;
rail Figure-plane projection is local `Vv`, and side projection is `-Vv`.

The final round of three fresh independent reviewers covered the complete
packet with separate mechanics, testing and evidence/architecture scopes.
All three returned no substantial findings. Parent verification completed
after the final code freeze. This closes the bounded software/publication
review, with the engineering limits below retained.

## Parent checks

The focused suite passes **55 tests**: seven point-action tests,
37 nodal-transfer tests and eleven host tests. They cover virtual work,
signed force couples and moment transport, receiver-specific seats, both cut
traces, source ownership and identity refusal, finite contact-footprint
coverage, competing loads, load factors and net CAD section area. The CAD
known answer ran with the installed kernel; it was not skipped.

All three canonical read-only replays pass against their exact ignored
outputs and source hashes. Ruff passes for the maintained packet files.
Public local links and producer/result hashes also match. Each public
calculation summary records its applicable consumed-source identities.
The CEN corrigendum and JRC Figure 8.1 reproduction were checked directly
against the cached primary-source PDFs; explanatory slides remain distinct
from full normative standard text.

The checkout's ignored frozen evidence is necessary for replay. A source-only
checkout cannot reproduce the raw reports without that evidence. Raw JSONs,
cached PDFs and STEP inputs remain local, in accordance with repository
publication policy. Public code, tests, summaries and provenance are the
review target.

## Integration limits

The packet preserves 42 block states, 672 receiver transfers, 84 host
interface states and 63 whole-host balances from three rear cases. Generalized
gross-element nodal loads and concentrated point actions do not identify
tractions in bored-section ligaments. Host shears and candidate edge distances
are inputs to a later applicable resistance calculation, with other signed
forces, couples and contacts retained. The orthogonal cleat groups and full
design conversion remain open. No new native solve or geometry change occurred.

The continuing assistance goal remains active after this bounded handoff.
The mechanics coordinator retains frame history and primary-corner work;
the main MVP owner retains integrated resistance and criteria closure.
No physical observation, candidate selection, fabrication or climbing release
is recorded here.
