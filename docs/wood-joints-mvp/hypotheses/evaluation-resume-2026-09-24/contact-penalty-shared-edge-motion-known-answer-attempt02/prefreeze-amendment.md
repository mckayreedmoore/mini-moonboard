# Separate numeric-format correction

The preserved attempt01 stopped while reading its first node card. Its
formatter emitted 22-character positive scientific values and 23-character
negative values. Pinned CalculiX 2.23 reads node coordinates, equation
coefficients and boundary values from the first 20 field characters using
`f20.0`; the truncated exponent is invalid for the observed failing cards.

This packet changes only `format_float()` to Python's shortest round-trip
representation, with a 20-character guard. The separate lexical audit compares
every old/new numeric value exactly, all nonnumeric tokens, card ordering and
line inventory. No geometry, mesh, equation coefficient, support, contact,
load, material, oracle or numerical tolerance is changed. The earlier output
corrections remain as frozen in attempt01. Native compatibility remains to be
tested on these bounded known-answer cases. No current-joint run is selected.
