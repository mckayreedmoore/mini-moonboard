# Independent review: current station family classification, attempt 01

**Verdict: confirmed with scope limits.** The frozen T04 packet's source-bound counts and claim boundary are supported by its pinned inputs. It classifies 24 former duties into 22 physical station groups, covers 92 candidate bolt axes, 12 retained frame-bolt axes, and 66 panel/kicker Hillman axes. Its geometry families remain geometry templates only; it proposes no mechanical representative.

The packet verifier (`python3 verify_packet.py --verify`) and `sha256sum -c SHA256SUMS` both pass when run from the producer packet directory. I independently rehashed all 67 source pins, joined the 50 current member STEP files across the attempt04 manifest and member-solids descriptor, and checked the duty, station, axis, retained-bolt, and Hillman identities against the pinned manifest and attachment-topology records. The 24 duties resolve to 22 physical station IDs; the only shared-duty groups are the left and right outer six-axis chains, each shared by two former duties.

The geometry comparison is properly bounded. Fifteen horizontal stations use a common block-geometry template, two center-post cleats form the documented proper-rotation shape pair, and the only exact whole-patch match remains `clip_horizontal_bottom_right_1`. These are geometry findings. All 22 station acceptance flags are false, station response ranges are null, and the packet's `mechanical_representatives_proposed` list is empty. Similar solid shapes, bore patterns, modeled contact faces, and axis-to-grain cosines do not establish shared demand, load transfer, or mechanical equivalence.

The six applied load records are external panel forces and global wrenches; they contain no reactions or station demands. The separate gravity input has 778 mass rows and a 25 kg accessory allowance, while solver DOF mapping and station demand remain unimplemented. Delivered grain or ring orientation, selected material and element assignments, and panel layups are unassigned. The 12 retained frame-bolt arrangements remain subject to current-candidate recheck. The 66 Hillman rows preserve the 63.5 mm nominal purchase policy, including eight owner-moved axes, without asserting screw resistance or engagement.

The inspected WJ-03 interface proposal is recorded as a scope boundary and not applied to the current station classification. Its 12 interfaces include four body IDs absent from the current 50-member manifest. No interface or mechanics result is transferred into T04.

This review corroborates the pinned records and their deterministic joins. It does not reconstruct CAD, establish physical contact or delivered hardware, infer a load path, execute a solver, or accept any criterion or joint. `review-record.json` records the counts, source hashes, fail-closed states, and review limits. `SHA256SUMS` covers this review packet's README and JSON record.

## Reproduction

From the producer packet directory:

```sh
python3 verify_packet.py --verify
sha256sum -c SHA256SUMS
```
