# Correctness review

**Result: no current producer, raw-oracle, or reported-value correctness
defect found** in producer
`af0a9569da228a8858f23107c16c7c8b3d9e0dbb50769733b5a399743eea6e24`, report
`f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1`, and raw
oracle `9d04a698227d42207533e23b33afa08b7031518d8c80499251cdf4d4e791e758`.
The canonical raw-oracle receipt is
`c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9` and
records `PASS_RAW_TOKEN_FORCE_AND_WRENCH_RECONCILIATION` for report SHA
`f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1`.
This review covers the current retained-frame-bolt join; it does not establish
capacity or acceptance.

I independently checked all 143 report input pins against the current source
bytes and sizes. Across the 21 case/factor states, all 756 retained scalar
channel records map to the frozen model group, inventory index and element;
their signed scalar values and rounding radii match the frozen response
components, and their direction-projected vectors and component bounds
reconstruct the reported physical interface actions. The README's twelve
largest-lateral rows and same-state axial values reproduce from the report.

The 168 receiver-body references and residual force/moment vectors agree with
the corresponding all-body audit entries within the documented arithmetic
tolerances. I also reconstructed all 504 retained receiver endpoint wrenches,
reporting-datum and origin moments, and their rounding radii from the reported
points and signed actions; the body-wrench origin transports also agree. No
historical demand, capacity, bolt-bending resistance, or acceptance is implied.

The oracle uses its own standard-library parser for native DAT `RF` tokens and
does not import the producer or a response parser. It pins the freeze,
projection, three source models, three DAT files and three all-body audits; the
freeze digest is also required in the report input pins. Its receipt covers 21
states, 504 SPRING2 and 252 SPRINGA channel states, 504 endpoint wrenches, and
168 authenticated receiver datums. The oracle's sign and rounding calculations
match the source conventions: it uses the first SPRING2 endpoint reaction with
the documented sign, and the SPRINGA qghost action projected along the frozen
physical axis while checking its numerical ground is opposite and not a
physical receiver.

As a separate data check, I compared all 36 retained SPRINGA model bindings
across the three cases to the pinned projection's qghost/ground nodes and
physical owners; all match. I also checked the 252 retained qghost raw force
vectors against their axis projections. The largest component residual was
`1.54e-12 N`, and every residual fit within its propagated native-token
rounding interval. Thus the scalar projection matches the current frozen
records. The oracle itself does not separately assert zero transverse qghost
force or compare the SPRINGA projection node list to the model binding; those
additional refusals would matter if this oracle were adapted to re-pinned
source. They reveal no mismatch in the present artifact, whose source bytes
are pinned and whose producer checks the SPRINGA projection node mapping.

The raw-token cross-check confirms force and wrench arithmetic for these frozen
conditional cases only. It does not extend the source envelope or qualify
another model, establish a bolt resistance, or change any acceptance flag.
