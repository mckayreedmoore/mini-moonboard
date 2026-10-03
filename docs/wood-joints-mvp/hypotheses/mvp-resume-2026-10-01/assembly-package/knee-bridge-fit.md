# Knee-spine bridge: saved-scene fit

**Parent run complete: 58,296 query/obstacle pairs; zero overlap or undecided pair. The four new axes remain a proposal.**

The proposal adds two through-bolts to each outer knee spine at local
`(grain,u)=(100,0)` and `(250,0)` mm. Each proposed bore envelope is 7.5 mm
through the saved 139.7 mm local-`v` depth. Existing 104 axes and 66 Hillman
screws remain unchanged. The four new axes stay unadopted.

The selected nominal stock lead is K.L. Jack `25C650HCS5Z`, 1/4-20 Grade 5,
6.5 in (165.1 mm) under head. The 203.2 mm length is retained only as an extra
conservative occupancy and straight-path bound. The exact delivered thread
transition and full-form interval remain conditional. Head and nut use
conservative cylinders with radius `maximum across flats / sqrt(3)`; nut height
comes from the matched K.L. Jack `25CNFH5Z` lead and current Grade 5 catalog
envelope. Proposed washers are 25.4 mm OD, 8.3058 mm ID, 2.5 mm thick.
Washer fit uses filled OD cylinders, with each annular land separately checked
against the saved stock edges, existing bore cutouts, and proposed bore.

Nut direction is **positive local `v` on both spines**, taken from each frozen
source basis row 2. In this geometry that is world `+Y` for both; heads sit on
negative `v` faces. This is the selected fit orientation, not an access or
installation qualification.

The producer uses the frozen accepted top-washer-fit source set: 1,009 saved
obstacles plus the corrected eight top stacks and four Hillman translations.
It reuses the saved 589 source pins and snapshot references; the completed packet binds 596 pins. It does not
rebuild the scene. Preparation records four installed stacks and finite
straight axial installation/withdrawal envelopes for shaft, head, washers, nut,
and tip. It models no tools, nut turning, or handling envelope.

Only shafts centered on each named spine's proposed bore receive analytic host
clearance, with the 3.175 mm shaft radius inside the 3.75 mm bore radius. Every
other query remains paired with every saved obstacle. Positive AABB or finite
cylinder projection gaps are recorded; overlapping pairs with saved STEP use
parent-only exact intersection. Overlapping non-STEP pairs remain named
undecided.

The parent's [force-and-grain proposal](../upper-corner-screw-layout/knee-spine-reinforcement.md) is separate evidence. It does not supply
scene clearance, delivered hardware fit, installation access, turning fit, or
joint acceptance.

## API and parent command

`prepare(output)` writes `setup.json` and source-hash snapshot references to a
fresh child of `assembly-package/rawlocal/knee-bridge-fit/`. Parent owns
`directrun(output, setup)` and any exact saved-STEP intersections.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/knee_bridge_fit.py --prepare --output-dir docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/knee-bridge-fit/prepare-attempt02
```

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/knee_bridge_fit.py --run --output-dir docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/knee-bridge-fit/run-attempt01 --setup docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/knee-bridge-fit/prepare-attempt02/setup.json
```

Producer SHA-256: `fd69e5106fd5febe2cc85817f12fb6487f40d7524490b8f33de762284f2f4cfa`.

## Completed finite result

All 56 installed/path queries retain 1,041 current obstacles, including the
corrected top stacks and four relocated Hillman axes. **58,256 pairs** separate
by conservative boxes; **24** named host-shaft pairs have prescribed-bore
certificates. The parent checked the remaining **16** washer/host pairs against
two saved spine STEPs: no interpenetration. Face contact is retained; a zero
distance at a washer seat is not a collision. No scene was rebuilt.

Parent preparation first stopped on an undefined constant name. Original
source and STOP are preserved at `rawlocal/knee-bridge-fit/prepare-stop-attempt01/`.
Only that naming error and three unused variables were corrected; no geometry,
clearance tolerance or method was changed. Targeted Ruff passes. All 596 source
pins match after the run. No software tests or agent review loop ran.

| Saved artifact under `rawlocal/knee-bridge-fit/` | SHA-256 |
| --- | --- |
| `prepare-attempt02/setup.json` | `794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb` |
| `run-attempt01/result.json` | `5a2a2e3c886353d4a24262748d0169ba33826cdcca76e8fa01c0a1e0d2bfde8b` |
| Same run, `receipt.json` | `4c307065da48b557a94840fd86211dd439add4b8e392f7ac6231def4e95daf00` |
| Same run, `parent-authentication.json` | `44cc36a154a29b55e7fd511fba8f95faa20544ab465b31705585dbbc7019911c` |

The separate parent certificate checks every enclosure pair across distinct
new stacks: **1,176 pairs**, minimum positive separation **124.599998 mm**. Simultaneous additions do not inherit a single-stack fit claim.
Delivered profiles, actual tools/turning and elastic/global adoption retain
their stated limits. Current 104-axis geometry and all physical flags remain
unchanged; no drilling or fabrication is authorized.
