# PB-02 combined center cleats: shortened principal cleat, small socket body

**Nominal socket-body geometry is feasible in this bounded trial.** This is an
independent alternative to the rejected combined pose, not a revision to its
result. The inherited upright bolt remains on its original X axis at
Y = −147.3, Z = 350 mm. The header/post cleat and its two bolts are unchanged.
The principal side cleat keeps its X and Y footprint (−20…50.95,
−190…−45 mm), but its top drops from Z = 380 to 338 mm. Its nominal finished
size is 70.95 × 145 × 61 mm, with grain along Y. All coordinates are global
millimeters.

The header/cleat Z bolt stays at X = 15.475, Y = −145.3; its cleat exit moves
to Z = 338. The cleat/principal X bolt stays at Y = −95 and moves from Z = 330
to 307.5. Both bolts retain full modeled bore reception in their two intended
woods and full 10-mm-radius illustrative washer bearing at both ends. The
serial routes remain post → post cleat → header and principal → principal
cleat → header. The original 66 panel/kicker screw axes (48 + 18), all ten
header receiver fractions (0.7125), all four center receiver fractions (1.0),
and both inner kicker supports are preserved.

For the conditional 1/4-in bolt markers, 4D + 5 mm is 30.4 mm and the cleat
7D grain-end marker is 44.45 mm. The limiting transverse distances are
30.4 mm at the header rear edge and 30.5 mm at each cleat Z edge of the
principal bolt. The limiting cleat grain-end distance is 44.7 mm at the
header/cleat bolt. These are centerline distances, with only 0.1 and 0.25 mm
of nominal excess at the two closest cleat limits. They are conditional
markers, not an engineering determination of loading direction or capacity.

[GEARWRENCH 80112](https://www.gearwrench.com/all-tools/ratchets-sockets/chrome-sockets/80112-14-drive-6-point-standard-sae-socket-716)
lists 0.618-in Dim A and B and 0.965-in overall length for an ordinary
1/4-drive 7/16-in socket. The probe conservatively represents its **body**
as a 7.8486-mm-radius, 24.511-mm-long outward cylinder at all 16 exposed
bolt ends. It finds no socket-body collision with modeled wood, fixed screw
envelopes, another socket body, or another end's 10-mm-radius by 5-mm hardware
envelope. The 0.01-mm outward washer face disks and hardware envelopes also
clear wood; all eight bores avoid unintended wood, each other, and fixed
screws. The two new wood solids avoid neighboring members and fixed screws.

The earlier illustrative 20-mm-radius, 20-mm-long straight tool cylinder
still intersects the shortened principal cleat at the inherited upright-left
end by 3,578.36174 mm³. That cylinder is a larger tool-access screen, not the
catalog socket body. This trial establishes neither the space for a ratchet
head and handle sweep nor an extension, hand clearance, assembly sequence,
or purchased washer/nut/bolt stacks. The 0.1-mm nominal cleat edge margin is
especially sensitive to machining and placement tolerance. Joint actions,
contact retention, splitting, strength, and six-case structural response are
also unverified. **This is no cut, drilling, fabrication, or rating release.**

Reproduce with `.venv/bin/python scripts/simple_center_combined_small_tool_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_combined_small_tool_probe.py`.
