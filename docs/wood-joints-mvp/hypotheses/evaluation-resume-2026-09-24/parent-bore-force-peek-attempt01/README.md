# Finite cleat-bore force observation

The parent read one bounded prefix from the live third trajectory attempt.
`observation.json` records the consumed DAT byte count and SHA-256, accepted
STA text, exact native container, matching contact-fragment/manifest hashes,
and source byte offsets for each observed record. The source manifest maps
ties 20, 22, 24 and 26 to the four bolt-shank contacts with the ordinary cleat.

All 76 complete CFN slave records through the 19th accepted increment
(0.0095 s) have zero printed resultant force components. This is an
observation of net normal force. It does **not** prove absence of local
contact: opposing point forces can cancel. Establishing first local contact
requires pointwise pressure/contact-state evidence. The general observation
monitor should likewise distinguish a first nonzero resultant from a proven
first contact time.

The peek does not validate complete angular, acceleration or point-map
framing for these states, does not stop the solver, and does not establish
time accuracy, whole-joint equilibrium, capacity or acceptance. Its source
is preserved in `capture.py`; repeat observations must use new artifacts or
the separately prepared incremental monitor, not overwrite this record.
