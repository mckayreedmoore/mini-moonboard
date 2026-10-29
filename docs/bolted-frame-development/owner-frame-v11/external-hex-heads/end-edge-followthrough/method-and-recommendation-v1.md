The end/edge follow-through leaves four cleat-post minimum-end locations as
the priority for this detail. The current bank supports a completed planar
reduced-depth shear comparison at both lower rear feet. The outer-top 7D
marker is a conservative principal-direction reference; it is not another
established minimum-end violation for the saved oblique actions. All results
use fixed geometry `fe77d1be…`, bank `8106a0a1…`, eight bolts per cleat and
zero spacers. This paper changes no model, hardware, forces or release status.

Each new cleat-post near-row axis has 23.8125 mm to the post end, with nominal
D = 9.525 mm. The maxima below are the existing supplemental oblique end
comparison against half the full end requirement, not a resistance index.

| Axis | Case | Available mm | Supplemental minimum mm | Minimum-end index |
|---|---|---:|---:|---:|
| v11_cleat_left_post_1 | a12-rear | 23.8125 | 30.448947 | 1.278696 |
| v11_cleat_left_post_2 | a12-rear | 23.8125 | 29.715203 | 1.247883 |
| v11_cleat_right_post_1 | k12-rear | 23.8125 | 30.444173 | 1.278495 |
| v11_cleat_right_post_2 | k12-rear | 23.8125 | 29.734525 | 1.248694 |

All 18 net-action and 16 primitive-action flags remain at those four axes.
The worst primitive minimum is 28.567907 mm, index 1.199702. The local force
points toward the short end in the governing cases. Calling the whole post
compressed does not change that fastener-bearing direction. The principal
softwood tension minimum is 3.5D = 33.3375 mm. The available distance meets
the separate 2D compression/perpendicular minimum, so direction and moment
applicability matter.

NDS 2024 §12.5.1.2(a) permits an end geometry factor only between the table's
half and full distances. Primary 2018 Commentary C12.5.1.2 supplies the saved
linear interpolation for oblique tension ends and prohibits distances below
half the full value. Full 2024 commentary interpolation wording has not been
directly verified; this remains an explicitly supplemental method. Granting
that method still leaves available/full ratios only 0.3910–0.4007 at the four
governing net cases. Those values cannot be adopted as Cdelta by extending
its permitted range below 0.5. A factor reducing connection strength cannot
supply missing minimum geometry. Edge reductions and a favorable oblique-edge
interpolation are not provided by that commentary.

The lower-foot follow-through reuses the exact tested `planar_application`
function from the earlier rear-joint work. It uses all 48 saved foot cuts and
all raw bearing/capture ports. In each of the three former envelope flags,
the load has one bolt line, zero explicit in-plane couple, zero resultant
moment about the width axis, and coherent signed cut shears. Figure 3E fixes
the unloaded edge from the applied bolt-load direction. The resulting indices
are 0.602533 and 0.652940 at the left foot and 0.654661 at the right foot;
all 12 foot cases meet this component reference. The former 1.008896,
1.093297 and 1.096180 two-edge envelopes remain saved diagnostics. This is a
supported planar branch selection, not a favorable factor choice. The full
width/grain forces, out-of-plane couples and local splitting duties remain
recorded separately. The seven existing selector tests pass, including
negative controls for a couple, line offset, cut reversal and zero net force.

At the four retained outer-top beam bolts, 65.0875 mm is 1.5875 mm below full
7D = 66.675 mm. It is well above the principal half minimum. Under a declared
principal end envelope, the end-only ratio is 0.976190476; NDS propagates the
smallest applicable factor through the connection. No actual factor is
adopted here. With the existing supplemental oblique interpolation, all 24
net and primitive full-end comparisons already meet: worst full index
0.837757 net and 0.893368 primitive, the latter requiring 58.147090 mm.
A standalone top-angle translation is not justified by this marker. Complete
row, fitting, coupled strength and splitting scope remains separate.

The source review directly reread NDS 2024 §3.4.4.1(a), Eq. 3.4-6 and Figure
3E; §12.5.1.2 and Tables 12.5.1A/B; 2018 Commentary C12.5.1.2–.3; and the
March 2026 errata. The errata confirms the Chapter 3 shear locator and does
not relax minimum ends. The commentary's reported 5D Douglas-fir metal-side
single-bolt study does not qualify this plywood/wood/steel multi-fastener
joint or authorize halving an alternative full-distance assumption.

The physical review confirms that the post end bears against the header.
The saved model has compressive contact in all 12 pairs, but nine patches
have some open cells. Those reactions do not establish uniform full-face
restraint, a crack-closure mechanism or an end-distance waiver. An admissible
local end-block compression/load-transfer proof would be a distinct method
requiring its complete signed force and moment mapping; no such capacity is
assigned by this review. Existing E2/E3/E4 and connected-path parallel
comparisons do not supply a general transverse splitting law.

Keep the four-bolts-per-member requirement. The next practical design review
is a compatible factory fitting/hole pattern or an explicit post/header detail
that supplies the missing end distance while retaining seating, four bolts
per member and no packers. The geometry worker's exact extension/translation
checks are in `geometry-review/`; they must control feasibility. Moving a
hole alone is not an approved factory-hole or timber remedy. The earlier
rear-foot centering value 0.835124 held historical forces fixed and remains
unadopted; it is not needed to erase a planar flag now resolved by its
applicable signed branch. Smaller cleat bolts and the 102-bolt deletion study
are not selected. Any owner-selected changed detail needs its own matched
geometry, grip/clearance and force checks. Further convergence runs on the
unchanged geometry will not resolve these four minimum-end limitations.

Detailed current actions and comparisons are in
`saved-method-followthrough-v1.json`; source editions, hashes, test command
and scope are in `method-source-receipt-v1.json`. The contact observations are
in `saved-post-header-end-contact-v1.json`. Actual Cg, Cdelta and complete
connection capacities remain null. Fabrication and climbing remain on hold.
