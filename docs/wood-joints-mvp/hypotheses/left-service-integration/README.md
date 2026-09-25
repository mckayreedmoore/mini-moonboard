# Left service-rail four-duty diagnostic

Status: local nominal geometry diagnostic, 2026-09-24. The
[report](geometry.json) proposes four cleats and sixteen complete modeled
through-bolt stacks for `clip_horizontal_lower_left_1/_2` and
`clip_horizontal_upper_left_1/_2`. It replaces their twenty-four source SDS
axes in this candidate overlay. No replacement is accepted.

All four actual left source members reconstruct from their native cuts at
zero reported symmetric difference. Left-native datums remain unchanged.
The candidate outer cleats undo the right-side kerf translation before
mirroring, meeting the left side member at X = −1130.3 mm. The inner upper
cleat retains its full 119.7 mm N depth; the right G7 crosscut is not copied.
Actual left protected geometry is included in the local screen.

All sixteen bores have their declared timber layers, and all thirty-two
modeled washer seats have full nominal support. Candidate-body, finished-wood,
installed-component, cross-bore, fixed/protected-geometry, and sampled
access-envelope intersection maps are empty. Intended host membership does
not waive finished-solid overlap. Envelope clearance does not establish a
working tool path, tolerance margin, or assembly sequence.

This local report combines left and right service families only. Its
forty-eight removed SDS axes and sixteen remaining legacy clips are local
scene counts, not the current twelve-duty composition's counts. Integration
with the compact outer and center/backer families must rebuild shared left
side/principal hosts from raw stock with the union of native cuts, candidate
bores, and purchased-length receiver cuts. Simply cutting new holes into a
finished host would incorrectly retain newly replaced SDS openings.

The intended sixteen-duty composition will have thirteen joint hosts,
twenty connector pieces, 72 candidate bolt axes and 360 modeled hardware
shapes, with eight legacy clips and 48 SDS axes remaining. Those are expected
integration counts, not completed evidence in this report. All 66 fixed screw
axes and twelve starting frame-bolt arrangements still require the combined
recheck.

Parent ran the local model in the retained serial CAD process in 39.27 s,
verified the exact producer and input hashes after execution, and reviewed
the raw intersection maps and all washer seats. Nine focused tests cover
exact duty/axis/stack identities, both reflection rules, native datums,
purchased-length cuts, full-depth stock, and fingerprint coverage. The
[manifest](sha256.json) binds the JSON and exact producer snapshot.
No source family was rebuilt, native solve run, or physical part inspected.

Full layout, installation, removal, individual-member transport, hardware
engagement, cost, actual demands, and connection resistance remain open.
All acceptance and release flags stay false.
