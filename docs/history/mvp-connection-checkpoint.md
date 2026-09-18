# Panel retention and base-angle checkpoint

The next two investigations produced a panel-attachment prototype and a mapped
base-angle resistance screen. They did **not** establish build readiness. The
checkpoint describes the preserved angle-base candidate. The current
`horizontal-service-development` uses a different panel/frame load path; these
preceding results do not qualify its hardware schedule.

## Panel attachment trial

[Local section render](../exports/panel-plate-trial/section.png),
[local STEP](../exports/panel-plate-trial/panel-plate-trial.step), and
[replayable calculation and placement report](../exports/panel-plate-trial/report.json).

The trial uses a documented SPAX XFU10-3500 #10 ×3½-inch flat-head screw through
a 1¼ ×2 ×5/16-inch steel plate (31.75 ×50.8 ×7.9375 mm). The plate is proud of
the climbing face; the plywood is not recessed. A 5.8 mm hole and 90-degree
countersink are explicit geometric placeholders pending the actual head drawing.
The STEP is a local joint cutout, not a replacement frame or fabrication release.
The render removes half of the local wood solely to expose the screw.

The [DrJ product report](https://www.drjcertification.org/report/download/1936),
Tables 4, 10 and 19, supplies the selected screw dimensions and conditional
references. The modeled stack leaves 62.706 mm gross wood penetration, enough
for its full 60.325 mm thread length including the tip. The DF-L SG 0.50
unadjusted withdrawal reference is 1,859.357 N. No duration or other adjustment
increase is applied. Material applicability and the custom plate seat remain
unverified.

| Diagnostic | 250 lb normal-only case | 300 lb sensitivity |
| --- | ---: | ---: |
| Existing ideal screw tension | 1,725.586 N | 2,022.908 N |
| Conditional withdrawal reference | 1,859.357 N | 1,859.357 N |
| Reference exceeded | No | Yes |
| Assumed strip bending stress | 95.541 MPa | 112.003 MPa |
| Required steel yield at assumed divisor 1.67 | 159.554 MPa | 187.046 MPa |
| Nominal average plate/plywood pressure | 1.124 MPa | 1.317 MPa |

These are calculations at the previous ideal point-restraint peak, not the
redistributed demands of an installed plate. The strip model assumes simple
end supports and subtracts the full countersink diameter from its net width.
Actual plywood contact, punching, steel seat resistance and screw combined
loading remain to be established. The computed pressure is a required material
check, not an assigned plywood capacity. Steel grade has not been selected.

The 250 lb reference has only a 7.75% margin over that diagnostic, before
unresolved adjustments and other force components. This is not enough evidence
to adopt the attachment throughout the frame. A longer screw does not increase
capacity if its documented embedded thread remains unchanged.

All 119 interior panel/principal locations were screened. The proposed plates
remain within their individual panel boundaries and clear the nominal 40 mm
service corridors extended to the front. Actual hold bodies and tool access
still need checking. The existing `timber_panel_upper_right_2` location fails
the selected screw's 57.15 mm toward-end reference. Lower sloping-end resistance
and any relocation are not qualified. The remaining 32 perimeter/kicker screws
are outside this prototype; no capacity improvement is assigned to them.

All 119 longer nominal shaft envelopes also clear retained fasteners and brackets
and have full cylindrical coverage in their raw receivers. This checks the deeper
62.706 mm reach rather than reusing the shorter screw clearance. It does not
qualify complete plate/driver/hold fit, threads or installation access.

Ordinary ¼-inch through-bolts were also considered. Their centered axis has
only 19.05 mm side-edge distance in a 38.1 mm principal, below the 25.4 mm
[reversible cross-grain 4D screening distance](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf). A plate does not remove that wood
splitting issue. Larger screws likewise require their own product spacing.

## Base-angle check

[Directional analysis](angle-base-connection-screen.md) and
[recorded screen](../fea/results/angle-base-connection-screen-v1.json).

The current two ML24Z angles have conditional single-direction references of
2,646.69 N fore/aft, 2,001.70 N outward, and 3,336.17 N inward per angle under
the stated bearing-installation interpretation. The manufacturer table has no
bearing-installation uplift value. The inspected reference also supplies no
mixed-direction or independent moment rule for this detail. Unsupported cases
remain unassessed, even if their individual components are small.

Current individual joint demands cannot be recovered from floor equilibrium
or the old gusset model. The current redundant frame needs a fresh compliant
member/connection model, including separated panels, actual screw positions,
compression-only bearing and floor support. A checked reduced beam/spring
model with restraint and slip sensitivities is the faster first calculation;
a full solid-contact model is not required to start. Arbitrary equal sharing
or rigid connections would conceal the behavior that needs checking.

The shortest defensible route to construction is to resolve that load path and
its supported connection detail before multiplying custom plate assemblies.
The panel product/grade and actual floor/foot interface also remain required
inputs. A small joint prototype can establish installation and contact behavior;
it cannot provide a whole-board load rating.

## Inspecting bolt nuts

The current viewer now places **Inspect bolt** near the top of its controls.
Choose a leg bolt to show its head, nut and both washers together. Wood is hidden
and the actual hardware stays at its modeled positions. Choose **Full assembly**
to restore the frame and prior camera view. This resolves hidden nut ends without
changing the fabrication geometry or coloring unqualified hardware as a pass.

Verification: 11 focused tests passed, including archived source/artifact replay,
a deliberately obstructed longer screw, mirrored angle mapping and rejection
of unsupported loads. Browser checks covered all eight complete bolt stacks,
unchanged hardware transforms, both-end selection, view restoration and hidden
controls on older models without separately modeled bolt ends.
