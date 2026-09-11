# Horizontal-service drilling references

The new `horizontal-service-development` candidate has its own drilling
references. These describe nominal modeled geometry and **are not released shop
instructions or climbing approval**. Use dimensions, not print scaling.

The generated [PDF](horizontal-service-drilling/drilling.pdf) and individual
[SVG pages](horizontal-service-drilling/drilling.html) pair named physical
faces/edges with hole-center coordinate tables. The machine-readable
[coordinate schedule](horizontal-service-drilling/drilling.json) and
[source/artifact manifest](horizontal-service-drilling/manifest.json) identify
the exact model behind each page.

## Face-panel holes

Look at the climbing face, with TOP upward. Measure horizontally from each
individual panel's left edge toward its right edge. Do not mirror this front
view when working from the rear. Lower-panel row dimensions are measured DOWN
from the lower panel's TOP edge; upper-panel row dimensions are measured UP
from the upper panel's BOTTOM edge. These two reference edges meet at the
horizontal seam.

The schedule follows the project's existing `panel_grid_v2` adaptation of the
[official Mini metric template](https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf),
linked from [Moon's build guidance](https://moonclimbing.com/build-your-moonboard).
The official nominal panel dimension is 1220 mm. This project's actual 48-inch
stock dimension is 1219.2 mm; the grid is not scaled. Consequently lower LED1
is 19.2 mm above the bottom, lower LED7 is 20 mm below the top, and T-nut rows
6–7 retain the 220 mm spacing. LED7 belongs to the lower panel despite serving
an upper-panel hold. The right panel's first column G is 180.8 mm from that
panel's left edge; it is not a mirrored copy of column A.

The drawings label current CAD through-bore diameters: 11.1125 mm for hold
T-nut holes and 13 mm for LEDs. Actual supplied hardware must establish final
fit. These are not panel-fastening screw pilots or T-nut mounting-screw
instructions. Hold hardware, mounting screws, recesses and LED seating still
require their applicable installation details.

## Structural leg/rim bolts

Four pages cover the four bores in each left/right rim and leg, corresponding
to eight assembled through-bolt axes. Each member receives its own dimensions:
the crossing rim and leg use different grain directions and are not identical
drill patterns. The nominal clearance diameter is 11.1125 mm (7/16 inch),
through the 38.1 mm stock thickness.

The measuring plane is the member's broad face. Measure down along its length
from the top end, then across from the named long edge. The printed enlarged
region is a local-axis projection, not a photographic outside-face view. Its
width/down world vectors remove ambiguity when identifying a loose member.
The actual outside faces are the smaller-X face of the left assembly and the
larger-X face of the right assembly. Drilling toward the center therefore runs
+X on the left and −X on the right. The local coordinates do not authorize
mirroring a pattern or transferring leg dimensions onto a rim.

Tables include both long-edge distances and the nearest end distance measured
along grain at each hole. These are geometric center-to-boundary dimensions;
they do not establish connection resistance, drill tolerance, bolt group
capacity or approval of a retrofit with pre-existing holes. Panel screws and
manufacturer bracket holes are separate operations.

## Reproduce

After the candidate source is frozen:

```sh
uv run python -m mini_moonboard.horizontal_service_drilling
node scripts/print_horizontal_service_drilling.cjs /path/to/installed/playwright
```

The generator refuses to overwrite a package. The PDF printer authenticates
the SVG/HTML source package before adding the PDF hash to its manifest.

## Prewired lighting access

The owner measured approximately 304.8 mm between adjacent bulb bases. This
is the available segment-length assumption, not a cable bend-radius or connector
size measurement. Any route crossing a horizontal rail must remain compatible
with placing the already wired harness. A small closed bore that requires
threading every bulb or connector through solid timber is not the selected
approach. The current service detail uses open-front grooves: place the harness
from the panel-contact side before closing the face panel. Groove dimensions,
remaining timber section, wire clearance and retention require their own checks;
the panel LED bore diameter does not define a suitable timber wire passage.

Each generated groove page names its individual timber member and shows the
panel-contact face with the panel removed. Measure groove start/end positions
RIGHT from that member's left edge and DOWN from its top edge. Measure depth
perpendicular into timber from the panel-contact face, N=0. The start/end
coordinates describe the actual rectangular CAD cut bounds, including detours;
they are not measurements from the assembled floor or another rail. Groove
pages use an exaggerated schematic aspect ratio so narrow cuts remain legible.
The dimension table governs. Long schedules continue onto numbered pages.
