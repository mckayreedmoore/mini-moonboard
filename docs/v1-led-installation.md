# V1 MoonBoard V5 LED installation and routing

V1 uses the user-selected **MoonBoard LED System, SKU 60-201-V5**, not a
third-party substitute. Moon's current build guide identifies this V5 family
as 50-LED strings and says that a Mini uses **three strings** (a Standard uses
four); the user-selected Standard kit supplies 200 LEDs. V1 has 132 scheduled
centres, so install the first 132 LEDs in the documented order: that consumes
two complete strings and 32 LEDs of the third. Retain the remaining 18 LEDs on
that third string and the wholly unused fourth string: **68 LEDs total** remain
uninstalled (Moon identifies the last two as replacement spares; the other 66
are the standard-kit excess for a Mini). The guide also requires Moon's
supplied control box and 5 VDC power adaptor only.

Source of record: [MoonBoard build and LED guide](https://moonclimbing.com/build-your-moonboard).
The guide, the labels on the received kit, and its V5 installation PDF control
if they conflict with this routing aid.

## Physical provisions already in V1

- The generated drill schedule has 132 LED centres at 13 mm / 1/2-in diameter.
  The LED is installed below the T-nut/hold it illuminates, flush with the
  climbing side, as Moon specifies.
- The opposite, support side has a tested 36 mm service gap between panel and
  support rails. It is the only allowed route for LED wire across the main
  surface; never route cable on the climbing face.
- The 20 bearing-block locations are kept at least 20 mm beyond the CAD bore
  edge. Do not add a cable clip, screw, or controller fastener in a bore,
  T-nut, or LED clearance area.
- The V1 model intentionally leaves controller dimensions unmodeled because
  the received V5 box has not been measured. Its mounting footprint is a
  required offcut/fit-test record, not a license to drill the panel.

## Install order

1. Before mounting anything, connect the supplied LED strings, supplementary
   power-feed cable, control box, and supplied power adaptor on a protected
   bench. Confirm the startup sequence, then disconnect power.
2. From the support side, begin with the LED labelled A1 and push it into the
   scheduled A1 hole until the LED is flush with the climbing face. Continue
   in Moon's specified zig-zag column sequence; do not infer the string order
   from cable length.
3. Continue through two complete 50-LED strings and 32 LEDs of the third
   string, using the push-fit connectors. At the end of the second string,
   connect the supplementary power feed to PWR1 on the control box as directed
   by the V5 guide. Do not cut the third-string tail: label and retain its 18
   uninstalled LEDs, plus the entire unused fourth string, for future repair.
4. Mount the control box on the support side only after measuring its actual
   bracket/footprint. Choose a rear rail/tie location with switch access,
   a 30 mm clear perimeter, no panel bore behind it, no sharp bend in the
   supplied leads, and no interference with leg or tie fasteners.
5. Route each string inside the 36 mm service gap. Use screw-mounted,
   insulated cable saddles fixed to rail faces—not the climbing panels—and
   place a saddle at every direction change and at a maximum provisional
   spacing of 300 mm. Do not pinch wire between any bearing block and panel.
6. With mains power disconnected, perform a complete rear-side tug/visual
   check: no conductor may rub an edge, cross a structural fastener, sit in a
   panel seam, or be exposed on the climbing face. Then power up with only the
   supplied adaptor and test every scheduled LED before holds are installed.

## Required received-kit audit

Record these before drilling controller or cable-mount holes:

| Item | V1 status |
| --- | --- |
| String count and LEDs per string | Verify four 50-LED strings in SKU 60-201-V5; V1 installs 132 LEDs, retaining 68 uninstalled LEDs |
| Control-box mounting footprint and fastener holes | Measure actual received component |
| Switch access and mains-adaptor lead direction | Verify at selected rear location |
| Cable outer diameter, connector size, and minimum bend radius | Measure or use the supplied V5 guide |
| Every saddle/clip location | Mark on rear rails only; verify against structural schedules |

This LED plan does not alter the board's separate crash-pad/impact-surface
scope, and it does not authorize substitution of power, LEDs, or control-box
components.
