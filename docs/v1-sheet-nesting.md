# V1 sheet purchase and cutting layout

Buy **nine** nominal 3/4-in, 48 x 96-in birch plywood sheets. This layout is
for the user-selected stock route and the current `1219.2 mm` V1 panel size.
It assumes an actually measured minimum raw sheet of **1219.2 x 2438.4 mm**.

Each main panel uses the full **1219.2 mm factory width** of one sheet. Do not
attempt to produce two full-width main panels from one 4 x 8 sheet: even a
thin saw kerf makes that route impossible. Crosscut each of sheets 1–4 once at
1219.2 mm, keeping the square factory edge on the panel. If the measured sheet
is smaller than 1219.2 mm, stop: revise `V1_PANEL_SIZE_MM`, regenerate all
artifacts, and recalibrate the official template before cutting a production
panel.

For sheets 1–4, use the coordinate convention `X = 1219.2 mm factory width`
and `Y = 2438.4 mm factory length`. The main panel is `X=0–1219.2`,
`Y=0–1219.2`; the crosscut kerf is `Y=1219.2–1221.6`. In the remaining field,
each face-rail blank runs its **1219.2 mm length along X**, not along the
shorter remaining Y dimension. Cut the five 180 mm-wide strips at Y spans
`1221.6–1401.6`, `1404.0–1584.0`, `1586.4–1766.4`,
`1768.8–1948.8`, and `1951.2–2131.2`. The named 2.4 mm gaps are kerfs.

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
| 5 | 2 kicker panels, 1219.2 x 225; 4 blank-kicker backings, 1219.2 x 75; 6 rail-cross-tie laminations, 1309.2 x 180 | First crosscut the full-width kicker/backing strips (750 mm plus six 2.4 mm kerfs, including the separation to the tie field), then set six 180 mm lanes in the remaining 1674.0 mm-long field and crosscut each at 1309.2 mm. |
| 6 | 6 rail-cross-tie laminations, 1309.2 x 180 | Set six 180 mm lanes across sheet width; crosscut each at 1309.2 mm. |
| 7 | 4 lower-leg laminations, 1495.2 x 180; 4 upper-leg laminations, 400 x 180 | Use the explicit sheet-7 map below; transfer the lower-leg trim profile only after cutting its rectangular blanks. |
| 8 | 40 bearing-block laminations, 4 side-gusset laminations, 10 rail-splice-cover laminations, 4 knee-plate laminations, 2 kicker-backing seam-splice laminations | Use the explicit sheet-8 lanes below. Mark gussets before trimming their CAD profile. |
| 9 | 6 rail-cross-tie center-splice laminations, 400 x 180; 10 main-seam bearing-block laminations, 180 x 60 | Use the explicit sheet-9 lanes below. Pair the six 400 x 180 blanks into three 36 mm splice plates. |

## Crowded-sheet cut maps

Coordinates below are measured from one factory corner of the raw sheet. They
are **layout zones**, not a replacement for the finished dimensions in the cut
list: leave a saw kerf of no more than 2.4 mm between every adjacent blank,
and retain any surplus at the far edge as waste. The maps fit inside the
minimum 1219.2 x 2438.4 mm raw-sheet assumption.

### Sheet 7

| Zone | X span mm | Y span mm | Finished cuts | Capacity/use |
| --- | ---: | ---: | --- | --- |
| A | 0–727.2 | 0–1495.2 | 1495.2 x 180 | Four lower-leg blanks in four 180 mm lanes, separated by three 2.4 mm kerfs. |
| B | 0–727.2 | 1497.6–1897.6 | 400 x 180 | Four upper-leg blanks in four 180 mm lanes. The 2.4 mm gap after zone A is the separating kerf; retain all remaining material as waste. |

### Sheet 8

| Zone | X span mm | Y span mm | Finished cuts | Capacity/use |
| --- | ---: | ---: | --- | --- |
| A | 0–902.4 | 0–902.4 | 450 x 450 | Four knee-gusset blanks in a 2 x 2 array |
| B | 904.8–1219.2 | 0–900 | 80 x 60 | Forty regular bearing-block laminations: three 80 mm columns by fourteen 60 mm rows provides 42 positions; retain two as optional defect/spare blanks |
| C | 0–802.4 | 904.8–1847.2 | 400 x 470 | Four kicker/main side-gusset blanks in a 2 x 2 array |
| D | 804.8–1204.8 | 904.8–1267.2 | 400 x 180 | Two face-rail splice-cover laminations stacked vertically |
| E | 0–1204.8 | 1849.6–2394.4 | 400 x 180 | Eight face-rail splice-cover laminations in a three-column, three-row array; leave one position unused |
| F | 804.8–1204.8 | 1269.6–1422.0 | 400 x 75 | Two kicker-backing seam-splice laminations stacked vertically |

### Sheet 9

| Zone | X span mm | Y span mm | Finished cuts | Capacity/use |
| --- | ---: | ---: | --- | --- |
| A | 0–802.4 | 0–544.8 | 400 x 180 | Six rail-cross-tie center-splice laminations in a two-column, three-row array |
| B | 0–1092 | 547.2–669.6 | 180 x 60 | Ten main-seam bearing-block laminations; six columns by two rows gives 12 positions, leaving two optional defect/spare blanks |

Before drilling, label every blank with its generated part name and orientation.
The drill schedule/template controls holes; this nesting layout never changes
their datum mapping. Do not use a cut edge as a template datum until its actual
trim and the template calibration have been recorded.

This is a cut/purchase plan, not structural approval. The connection hardware,
adhesive, floor interface, and final template calibration remain the explicit
human-audit items in the V1 build package.
> Historical rail-and-spacer revision. For the current box frame, use
> [box-frame-revision.md](box-frame-revision.md) and regenerated schedules.
> The dimensions and analysis below do not describe the current assembly.
