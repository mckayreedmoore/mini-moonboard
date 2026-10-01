# Exact-touch penalty capture qualification packet

This is a small, previously frozen CalculiX 2.23 exact-touch penalty coupon
for a future parent-owned serialized qualification of the output patch. The
input is [contact_touch.inp](input/contact_touch.inp), SHA-256
fffe98b9992ce22a7f9447d423be2fe9f7cf183066ef3f1d9c50b5a295888a0c.
The frozen analytical contract is
[reference-expected.json](reference-expected.json), SHA-256
053039f39b33c5e3c1f1d1d19e88e8fa9967d6da7aea42fd9450bf80b56d1a26.

The coupon has two elastic bodies in series with a 4 mm² planar interface,
100,000 N/mm² elastic modulus and a linear penalty stiffness of
100,000 N/mm³. Its prescribed states are open, touch, compress to 0.001 mm
overclosure, touch, and reopen. At compression the analytical slave-side
resultant is (0, 0, 400) N, its moment about the global origin is
(400, -400, 0) N·mm, each body stores 0.4 N·mm, and contact stores 0.2 N·mm.
The unmodified-source prior run is copied under
[reference-output](reference-output/); its files are hash-pinned in
../source-pins.json. That run is not output from the r5 binary and does not
qualify this instrumentation.

The future serialized check should bind the exact input, 2.23 source archive,
patch and r5 binary; require normal completion and accepted states; and compare
the captured in-loop map/trial force and stored-energy aggregates with the
pair output and body/contact energy channels in the frozen contract. It must
retain the explicit lifecycle boundary: the initial pre-loop seed contact
scan is excluded. The parent owns any future readiness, freeze, runner and
execution decision. No solver execution is performed by this packet.
