# Centered Y-face HL35/common post — rejected

This is an isolated nominal installed-geometry screen, not a connection
selection, load rating, purchase list, or drilling plan. Regenerate its JSON
with `uv run python -m scripts.hardware_first_center_yface --output
docs/bolted-candidate-prototypes/hardware_first_center_yface.json`.

The [Simpson HL catalog](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
gives HL35 a 5-in bend length, 3.25-in flange reach, four total 1/2-in
bolts, and a 3.5-in minimum wood thickness for the `3`/`5` series. It
requires centering the angle on a member face at least as wide as the angle;
both faces are needed for F1 resistance in both directions. The model uses
an illustrative 4.55-mm plate thickness for a nominal 7-gauge envelope,
not measured delivered steel or a factory-hole tolerance.

The trial replaces the two separate center posts with a single conceptual
solid receiver spanning X = −92.075..92.075, Y = −175.7..−36 and
Z = 0..238.9 mm. It retains both original post footprints, has no modeled
overlap with the other original timber, backs both kicker inner edges at
X = −1.5875 mm, and intersects all four fixed center kicker screw occupied
envelopes. This is *not* proof of adequate screw embedment or a stocked
nominal 6×8 supply. All 66 protected kerf-right panel/kicker axes were read
without changing them.

The front face of a directly supporting post is at Y = −36 mm, exactly
where both kicker panel backs begin. A centered HL35 front vertical flange
of any nonzero thickness therefore enters the immutable panels. The
illustrative envelope overlaps the left and right kicker solids by about
23,254 and 24,447 mm³, respectively. Its horizontal seat adds about 5,143
and 5,407 mm³. These are nominal rectangular-overlap volumes, not measured
bracket collisions; holes, bend radius, coating, and tolerances are omitted.
The rear vertical flange has no panel-solid overlap in this screen. No
protected screw shaft intersects these modeled flange volumes, which does
not cure the panel clash.

There is no feasible centered, face-mounted front bracket position while
the common post itself continuously supports the fixed panel backs and
inner edges. Moving the post rearward, adding independent panel blocking,
recessing the steel, or choosing another connector is a distinct concept;
none is covered by this rejection. Because the plate cannot be installed,
post/header/principal bores, washer/head/nut grip, tool access, neighboring
joint loads, and catalog resistance are intentionally **not** approved or
assigned fabrication coordinates. Do not drill or build from this trial.
