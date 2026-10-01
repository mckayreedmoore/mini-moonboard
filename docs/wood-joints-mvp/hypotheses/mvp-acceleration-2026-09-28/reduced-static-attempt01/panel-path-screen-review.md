# Panel-path screen review

Independent read-only review of `panel_path_screen.py` and
`panel-path-screen.json`. No native solve was run.

The sign and load-direction checks agree with the frozen geometry. The nominal
outward panel normal is `n = (0, cos 40°, -sin 40°)`. It matches the imported
STEP main-upper/frame contact normals to less than `4e-13` component error.
For frame-first/panel-second contacts, compression acts on the panel as
`+normal_on_first`; its projection onto `n` is nonnegative (minimum `0`). The
side and seam contacts have zero nominal outward-normal projection. The panel
screw axes are `-n` to numerical precision, so their permitted lateral
reactions are tangent to the panel in the nominal geometry.

The external force rows conserve the source cases and assigned wood/T-nut
gravity. All-case assigned gravity is `216.692463 kg`, or `2125.027139 N`
downward. Each case adds the source `250 lb × 2` load, with horizontal
components of `±300 N` and vertical component `-2224.110808 N`, to the same
assigned-gravity resultant. The resulting all-body force is therefore
`[0, 300, -4349.137947] N` for rear cases, `[0, -300, -4349.137947] N` for
forward, `[-300, 0, -4349.137947] N` for left, and
`[300, 0, -4349.137947] N` for right. The screen's upper-panel loads also
match: gravity alone contributes `+104.424048 N` and `+104.078261 N` along
`n` for the left and right upper panels. The loaded-panel case adds `+1659.444203 N`
(rear), `+1199.817537 N` (forward), or `+1429.630870 N` (side), reproducing
the six reported positive normal demands.

The global moment sum also matches. For `a12-rear`, summed body wrenches give
`[-5534129.845, -2270360.243, -305760.000] N·mm`; this is the source applied
wrench about the origin `[-4043129.321, -2266813.735, -305760.000] N·mm` plus
the same assigned-gravity moment in every case,
`[-1491000.524, -3546.508, 0] N·mm`.

All six nominal screen cases are infeasible with the permitted reaction set.
The concrete model omission is axial screw restraint: upper-panel gravity and
the applied climber load have a positive outward-normal component, while
compression-only contact and lateral-only screw reactions cannot balance it.
This identifies missing restraint in that idealization; it does not show
failure of an installed Hillman screw, the frame, or the physical joint.

The reported certificates are numerical-tolerance/nominal-geometry checks,
not exact-arithmetic LP dual proofs. The script accepts screw-normal
projections below `1e-8` as zero while screw reaction variables are unbounded;
the recorded nonzero roundoff maximum is `3.56e-17`. An arbitrarily large
unbounded reaction could amplify any truly nonzero projection. The source
axis/normal relation supports treating the nominal projection as zero, but
this should remain explicit in interpreting the certificates. Compression
projections in this dataset are nonnegative; the same tolerance caveat would
apply if a negative projection were accepted. Contact forces at patch
centroids and vertices relax pressure over the actual contact hull. Moments
are divided by `1000` to scale N·mm to N·m, without changing equilibrium
feasibility. Deferred hardware and accessory loads are excluded as stated in
the screen limits.
