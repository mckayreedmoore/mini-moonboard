# Outer-rail 6 in bolt / 60 mm setback sensitivity

The [detached source-bound probe](../../scripts/owner_barrel_outer_rail_setback_probe.py)
tests a nominal alternative to the current barrel viewer at its six bottom,
lower, and upper **outer-rail** stations (two rows each). It retains the current
kerf-right frame, Y = −85 mm outer-header pose, 66 fixed panel/kicker screws,
12 retained frame bolts, both ±180 mm center posts and two kicker backers.
It changes **no** viewer or selected-candidate geometry.

At these six stations only, the trial moves the barrel center from 70 to
60 mm along its rail from the butt face and substitutes a 152.4 mm (6 in)
nominal bolt for the current 127 mm (5 in) shaft. The 6 in shaft still starts
at the same modeled washer seat. All twelve tips are nominally **1.849 mm
past the assumed barrel thread axis**, **3.1548 mm before the barrel body's
far cylindrical wall**, and **5.1548 mm before the end of the modeled 7.5 mm
machine-bore envelope**. This is a narrow nominal length window, not a
verified engagement or tolerance allowance. The potential axial overlap
from the near barrel wall to the tip is 6.8528 mm; it is *not* a count of
effective threads, because the delivered internal thread geometry and axis
are not controlled by this model.

The exact current assembly's source screen reports direct butt geometry,
both barrels contained in receiving wood, machine-bore/cross-bore
intersections, and no >1 mm³ hits against unrelated wood or protected
features at all six stations. A separate pairwise finite-solid check found
no >1 mm³ clashes between their trial barrels/shafts and other candidate
hardware (including the retained 18 stations). The matching bolt/barrel
contact is intentionally excluded. Tool sweeps, actual head/washer dimensions,
drill tolerance, thread engagement, wood net sections and structural loads
are not passed by those zero-hit results.

[Home Depot lists an Everbilt 1/4-20 × 6 in galvanized hex bolt, model 805436](https://www.homedepot.com/p/204633311),
as fully threaded and A307. This is an ordinary-retail **lead**, not selected
hardware. The listing alone does not establish the delivered shank length,
head/washer stack, fit to the Hillman cross dowel, bolt-to-barrel resistance,
or repeated demounting behavior. No manufacturer was contacted and nothing
was purchased.

The result supports *further development* of a shorter-setback, 6 in outer-
rail layout; it does not replace the current viewer, set drilling dimensions,
approve any joint, or release fabrication. All 24 barrel duties, backer
attachments, changed-topology force cases and complete joint capacities
remain open.
