# Outer-header/post barrel clearance: bounded negative screen

The [reproducible probe][probe] evaluates 24 detached, mirrored poses for the
two outer-header/post duties. It uses the exact kerf-right assembly wood,
including center posts at X = ±180 mm and kicker backers. It does not alter
the 66 panel/kicker screws, 12 frame bolts, or other barrel-trial producers.
The existing straight top-entry pose is still **REVISE**. None of these 24
poses clears every nominal geometry gate; this is not a proof that every
possible barrel-nut arrangement is impossible.

The source header spans Z = 238.9–277.0 mm and each outer post spans
Z = 0–238.9 mm. The left post spans X = −1219.2 to −1181.1 mm; the right
spans X = 1177.925 to 1216.025 mm. The same-side side rim occupies the
projection above each post, blocking straight top access. Exact candidate
parameters and all finite hits are in the probe's `search()` result.

- Existing vertical top: Y = −135/−75 mm; post midpoint X = −1200.15 mm
  left or 1196.975 mm right; axis 70 mm below post top. Each shaft hits the
  side rim by 52.285878 mm³ and each 20 × 40 mm bolt-access cylinder by
  12566.370614 mm³.
- Six translated vertical-top pairs per side: Y = −145/−85 or −125/−65 mm,
  post midpoint X ±8 mm, same 70 mm depth. Every shaft and access path
  retains the same rim hits. At midpoint X with the −125/−65 pair, the rear
  row also intersects fixed `round_kicker_*_rim_2` panel screw.
- Four oblique top-inboard pairs per side: Y = −135/−75 mm; top seats at
  X = −1120.3/1117.125 mm; axes at post midpoint or 12 mm from inner face;
  depths 45 or 70 mm. Shaft and straight access avoid the side rim, but
  the bolt line crosses the header/post butt plane outside the post. The
  70 mm cases also have nominal bolt-reach deficits of 4.9792–9.0446 mm.
  These cases need an unmodeled angled washer seat and intersect existing
  other-trial paths.
- Reverse vertical-bottom pair: Y = −135/−75 mm; post midpoint X, header
  barrel axis Z = 257.95 mm. The nominal 5-inch bolt falls 132.601 mm
  short of the barrel axis; one row per side also crosses a retained frame
  bolt.

For example, the left 45 mm oblique trial with its axis 12 mm inside the
post's inner face reaches the butt plane at X = −1153.6776 mm, while the
post ends at X = −1181.1 mm. The mirrored right trial reaches X =
1150.5026 mm, while its post begins at X = 1177.925 mm. Thus removing the
rim access collision alone does not create a post/header connection.

The probe constructs full provisional bolt shafts, barrel bodies, 7.5 mm
machine and barrel bores, 20 mm × 40 mm straight access cylinders, a 13 mm
diameter × 5 mm head envelope, and a **provisional** 19.05 mm washer OD
with 1.651 mm thickness. The 19.05 mm OD is a sensitivity input, **not a
verified Hillman 811070 dimension or retail fit**; the online table and
same-page Q&A conflict. It checks source-wood coverage, unrelated timber,
the protected T-nut/hold/electrical/fixed-connection inventory, both rows,
and the other 22 integrated barrel-trial stations' physical and path solids.
The other trials remain diagnostic poses, not accepted hardware.

No alternative is adopted in the viewer. A different access strategy,
head pocket, bolt length, member topology, or assembly sequence would be a
new design to model and screen, not a release inferred from this search.
Delivered head/washer dimensions, thread engagement, tolerances, insertion
sequence, wood capacity, and joint loads remain open. **No drilling,
fabrication, or structural release.**

[probe]: ../../scripts/owner_barrel_outer_header_clearance_probe.py
