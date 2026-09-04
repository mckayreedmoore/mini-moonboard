# V1 sheet purchase and cutting layout

Buy **eleven** nominal 3/4-in, 48 x 96-in birch plywood sheets. This layout is
for the user-selected stock route and the current `1219.2 mm` V1 panel size.
It assumes an actually measured minimum raw sheet of **1219.2 x 2438.4 mm**.

Each main panel uses the full **1219.2 mm factory width** of one sheet. Do not
attempt to produce two full-width main panels from one 4 x 8 sheet: even a
thin saw kerf makes that route impossible. Crosscut each of sheets 1–4 once at
1219.2 mm, keeping the square factory edge on the panel. If the measured sheet
is smaller than 1219.2 mm, stop: revise `V1_PANEL_SIZE_MM`, regenerate all
artifacts, and recalibrate the official template before cutting a production
panel.

All dimensions below are finished blank dimensions from the generated cut list.
Add the measured kerf between adjacent parts; keep factory long edges where
practical. Every support part is cut twice for its two-ply lamination unless
the listed quantity already includes both plies.

| Sheet | Cuts | Layout rule |
| --- | --- | --- |
| 1 | 1 main panel, 1219.2 x 1219.2; 5 face-rail laminations, 1219.2 x 180 | Crosscut the panel from the factory-width sheet. From its 1216.8 mm-long remainder, rip five 180 mm rail strips across the factory width. |
| 2 | 1 main panel, 1219.2 x 1219.2; 5 face-rail laminations, 1219.2 x 180 | Same as sheet 1. |
| 3 | 1 main panel, 1219.2 x 1219.2; 5 face-rail laminations, 1219.2 x 180 | Same as sheet 1. |
| 4 | 1 main panel, 1219.2 x 1219.2; 5 face-rail laminations, 1219.2 x 180 | Same as sheet 1. |
| 5 | 2 kicker panels, 1219.2 x 225; 4 blank-kicker backings, 1219.2 x 75; 6 rear-tie laminations, 1309.2 x 180 | First crosscut the full-width kicker/backing strips (750 mm plus five 2.4 mm kerfs), then set six 180 mm lanes in the remaining 1676.4 mm-long field and crosscut each at 1309.2 mm. |
| 6 | 6 rear-tie laminations, 1309.2 x 180 | Set six 180 mm lanes across sheet width; crosscut each at 1309.2 mm. |
| 7 | 6 rail-cross-tie laminations, 1309.2 x 180 | Same layout as sheet 6. |
| 8 | 6 rail-cross-tie laminations, 1309.2 x 180 | Same layout as sheet 6. |
| 9 | 4 lower-leg laminations, 1495.2 x 180; 4 upper-leg laminations, 400 x 180 | Make four 180 mm lanes for lower legs; use the remaining width/length for upper-leg laminations. |
| 10 | 40 bearing-block laminations, 4 side-gusset laminations, 10 rail-splice-cover laminations, 4 knee-plate laminations, 2 kicker-backing seam-splice laminations | Use the explicit sheet-10 lanes below. Mark gussets before trimming their CAD profile. |
| 11 | 12 tie-center-splice laminations, 400 x 180; 10 main-seam bearing-block laminations, 180 x 60 | Use the explicit sheet-11 lanes below. Pair the twelve 400 x 180 blanks into six 36 mm splice plates. |

## Crowded-sheet cut maps

Coordinates below are measured from one factory corner of the raw sheet. They
are **layout zones**, not a replacement for the finished dimensions in the cut
list: leave a saw kerf of no more than 2.4 mm between every adjacent blank,
and retain any surplus at the far edge as waste. The maps fit inside the
minimum 1219.2 x 2438.4 mm raw-sheet assumption.

### Sheet 10

| Zone | X span mm | Y span mm | Finished cuts | Capacity/use |
| --- | ---: | ---: | --- | --- |
| A | 0–902.4 | 0–902.4 | 450 x 450 | Four knee-gusset blanks in a 2 x 2 array |
| B | 904.8–1219.2 | 0–900 | 80 x 60 | Forty regular bearing-block laminations: three 80 mm columns by fourteen 60 mm rows provides 42 positions; retain two as optional defect/spare blanks |
| C | 0–802.4 | 902.4–1844.8 | 400 x 470 | Four kicker/main side-gusset blanks in a 2 x 2 array |
| D | 804.8–1204.8 | 902.4–1264.8 | 400 x 180 | Two face-rail splice-cover laminations stacked vertically |
| E | 0–1204.8 | 1847.2–2392.0 | 400 x 180 | Eight face-rail splice-cover laminations in a three-column, three-row array; leave one position unused |
| F | 804.8–1204.8 | 1267.2–1419.6 | 400 x 75 | Two kicker-backing seam-splice laminations stacked vertically |

### Sheet 11

| Zone | X span mm | Y span mm | Finished cuts | Capacity/use |
| --- | ---: | ---: | --- | --- |
| A | 0–1204.8 | 0–727.2 | 400 x 180 | Twelve tie-center-splice laminations in a three-column, four-row array |
| B | 0–1092 | 729.6–852.0 | 180 x 60 | Ten main-seam bearing-block laminations; six columns by two rows gives 12 positions, leaving two optional defect/spare blanks |

Before drilling, label every blank with its generated part name and orientation.
The drill schedule/template controls holes; this nesting layout never changes
their datum mapping. Do not use a cut edge as a template datum until its actual
trim and the template calibration have been recorded.

This is a cut/purchase plan, not structural approval. The connection hardware,
adhesive, floor interface, and final template calibration remain the explicit
human-audit items in the V1 build package.
