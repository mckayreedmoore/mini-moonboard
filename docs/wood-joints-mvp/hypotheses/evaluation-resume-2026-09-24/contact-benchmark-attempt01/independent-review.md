# Independent review of contact-wrench benchmark attempt 01

This is an independent read-only review of the two CalculiX 2.21 contact-output probes in `contact-benchmark-attempt01`. The run completed both decks, but the recorded audit rejected the contact report parser's duplicate-time condition. The equilibrium calculation below is a separate check from that parser and does not turn the attempt into a contact-method or joint-acceptance result.

## Frozen decks and fixture equilibrium

The input deck hashes are:

| Deck | SHA-256 |
| --- | --- |
| `upper-slave.inp` | `fa8459d004516c417234fe076d35ccbbddd1e37b63e69692602b2cb6116db64d` |
| `lower-slave.inp` | `12c7808982a88fc5c30d642ec432a2fed4a96a2d1fe4decb71470eb788431c19` |

I summed the four bottom-node reactions in each `.dat` output and independently formed their moment about the global origin from the deck's bottom-node coordinates. Each deck applies four `-25 N` z loads at the upper face, for a total CLOAD of `(0, 0, -100) N` and global-origin moment `(-1000, 1000, 0) N·mm`.

| Deck | Bottom reaction sum (N) | Bottom moment about origin (N·mm) | Residual force (N) | Residual moment (N·mm) |
| --- | --- | --- | --- | --- |
| `upper-slave.inp` | `(4.490542e-16, -4.317766e-16, 100.0)` | `(1000.0, -1000.0, -1.223904e-14)` | `(4.490542e-16, -4.317766e-16, 0)` | `(0, 0, -1.223904e-14)` |
| `lower-slave.inp` | `(-1.063403e-16, 7.673214999999999e-16, 100.0)` | `(1000.0, -1000.0, 9.707435999999998e-15)` | `(-1.063403e-16, 7.673214999999999e-16, 0)` | `(0, 0, 9.707435999999998e-15)` |

Both whole-fixture checks close to floating-point roundoff. The lower face of the lower C3D8 is fixed in all three directions; the upper body is fixed only in x and y. Those restraints do not directly carry the vertical force. The fixture has Poisson ratio zero, so its lateral restraint is decoupled from the vertical response in this diagnostic.

## Contact face and wrench interpretation

The decks select the matching z=0 faces with opposite outward normals. The lower body's C3D8 S2 face uses nodes 5–8 and points outward in `+z`; the upper body's C3D8 S1 face uses nodes 11–14 and points outward in `-z`. Reversing slave/master therefore changes which body's action is printed while preserving the same physical interface pair.

The `.dat` output for the upper-slave case reports the expected slave wrench `(0, 0, +100) N` and `(1000, -1000, 0) N·mm`. The lower-slave case reports the equal-and-opposite wrench `(0, 0, -100) N` and `(-1000, 1000, 0) N·mm`. These moments agree with `r × F` at the contact centroid `(10, 10, 0) mm`. The reported compressive normal force is `-100 N` on each slave surface, consistent with a contact-normal convention where positive is tension. The master-body reaction is inferred by action–reaction and is not independently printed as a master total in these reports.

Each case reports area `400 mm²` and centroid x/y `(10, 10) mm`. The reported z centroids are approximately `-0.002525938 mm` for upper-slave and `-0.002500938 mm` for lower-slave. These are consistent with the small compressed interface position; they fit the frozen acceptance interval `[-0.003, 0.0001] mm` that admits either nominal or compressed coordinates. The mean normals are respectively `(0, 0, -1)` and `(0, 0, +1)`, with zero shear. The moment about the reported centroid is at numerical zero.

## Duplicate report blocks and parser status

The deck requests `CF,CFN,CFS` in that order. CalculiX writes three blocks with the same slave, master, and step-time label. In both scenarios the CF block and CFN block report the expected complete force and moment; the CFS-only block has zero force and moment, while retaining the contact area. The attempt01 parser expected one report block per time and conservatively rejected the repeated labels.

Do not deduplicate these records solely by pair and time, and do not select the last block as the total wrench. Either parse complete, ordered CF/CFN/CFS groups and validate each quantity's expected meaning, or reduce the deck to a CF-only request and narrow the audit claims. In both approaches, require the exact expected pair and a valid strictly increasing step-time sequence, and reject missing, extra, or malformed groups. The attempt01 record remains `PARSER_REJECTED_DUPLICATE_TIMES`; its contact report has not passed the producer audit.

The attempt manifest declared force tolerances of `0.01 N` absolute and `1e-4` relative, moment tolerances of `0.1 N·mm` absolute and `1e-4` relative, normal/shear tolerances of `0.01 N`, centroid x/y tolerance `1e-4 mm`, area tolerance `0.01 mm²`, mean-normal component tolerance `1e-8`, and endpoint-time tolerance `1e-9`. Those checks are narrow output-probe gates, not a wood property, joint capacity, or structural acceptance criterion.

## Manifest integrity note

The first independent review identified that the producer's manifest loader trusted acceptance-defining centroid bounds and step-end time from the mutable manifest. The current source now compares `solver`, `units`, `fixture`, `load`, `contact_patch`, `result_tolerances`, and `solver_completion_contract` against `_manifest_data()` before returning the manifest; preserve this equality check so the declared gates cannot be relaxed by editing the manifest. This source-level fix does not change the frozen attempt01 inputs or its rejected parser status.

Attempt01's solver completion and the bottom reaction closure establish only that the two small fixtures solved and balanced under their known loads. They do not establish wood-joint behavior, capacity, accepted geometry, or any physical-build status.
