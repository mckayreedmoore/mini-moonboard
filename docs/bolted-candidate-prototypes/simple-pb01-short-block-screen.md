# PB01 152.4 mm corner block trial

The **bolted solid-wood corner block** is the rectangular part still identified as
`cleat_*` in machine records. This development screen compares the preserved
300 mm prototype with a 152.4 mm corner block using the maintained PB01 pose
producer. It is not a selected joint, cut list, or drilling instruction.

| Quantity | Preserved prototype | Length-only trial |
| --- | ---: | ---: |
| X × T × N, mm | 139.7 × 57.15 × 300 | 139.7 × 57.15 × 152.4 |
| Front N, mm | 209.841 | 209.841 |
| Rear N, mm | 509.841 | 362.241 |
| Last upright center to rear grain end, mm | 199.841 | 52.241 |
| Reserve beyond conditional 7D = 44.45 mm, mm | 155.391 | 7.791 |
| Gross volume, L | 2.395 | 1.217 |

The four centers remain upright N=265/310 and rail N=290 at X=70/110 mm.
The diagnostic bore stays 7.5 mm. All 66 fixed panel/kicker axes remain in
the geometry check; the trial reports no wood, panel, or parent clash. The
nominal 139.7 mm contact overlap at both interfaces remains, as do the
measured contact areas. The 7D comparison is a conditional marker, not a
classified loaded-end requirement or a fabrication tolerance.

The member comparison reuses the same X/T section, bolt count, bore and
front-facing row geometry. Its isolated Appendix E reference components are
therefore unchanged; this does **not** check the shorter rear end, bored
critical sections, splitting, group action, combined stresses, or adjusted
resistance. The old native force archive describes the 300 mm part and is
not applied to this trial. A fresh connected model and bolt/contact law are
needed before demand or gravity effects can be interpreted for the trial.

Wood grips remain 177.8 mm upright and 95.25 mm rail. The diagnostic envelope
adds 5 mm to each. The existing nominal 5 in partially threaded rail pattern
still fails its assumed full-nut seating check; shortening the corner block
does not shorten a bolt running through X or T. Purchased hardware, stack
tolerances, actual tool motions with the relevant panels removed, bolt
insertion/removal sequence, and permanent installed hardware clearance still
need verification. The 40 mm straight tool cylinders in the pose are only
diagnostic envelopes.

Gross block volume falls 49.2%, but purchase cost is undetermined: stock
yield, kerf, grade after ripping, delivered dimensions, waste and hardware
packs have not been priced. The 152.4 mm trial uses one ordinary crosscut and
keeps X/T; a narrower width trial would move bolts and change mechanics, so
it is deferred. The machine-readable comparison is produced by
`uv run --no-sync python scripts/simple_pb01_short_block_screen.py`.
