"""Map frozen obligations to saved evidence without running mechanical methods.

Import is inert. build(output) authenticates saved bytes, copies comparisons and
records missing modeled checks. It does not reclassify criteria or select a
candidate. Authentication utilities are imported from the frozen splitting
producer; none of that producer's mechanics or build functions are called.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/qualification-register"
CRITERIA = "docs/wood-joints-mvp/criteria.json"
HELPER = "all-joint-splitting/closure.py"
SPLITTING_COMMIT = "af6e03b069324df1063b5e89e7f11af0987f6411"

# These paths and hashes are literal frozen inputs, populated at preparation.
FROZEN = {
    "docs/wood-joints-mvp/criteria.json": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/hardware-length-fit.md": "40ec79f3193c60acb718a351bde8db24f67ccacf83a11f86c6e583b1a51d2e4b",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/knee-bridge-fit.md": "881b4a4c8e3c2dfb5be1f3690de287fb21863817c14f02b3b4484a8e2ff5d867",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/knee-bridge-order.md": "d9546eb9b48d802e27ed33d8fd9cd82ca270e3cc03345ae4951a99fe5a52dfc9",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/knee-bridge-shop.md": "2f738d0acf7dc3dc93dd8c783a3545b33514b0319cbbb644012b845e024452fa",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/shop-guide.md": "b3d13e0b90004f3c150a7d5756173bd203ab41dc27a79ee11420aca5c4ed1bd8",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/washer-coverage.md": "2ca6f8ce992aebf6a33f347a18150cc2a59fb2f8b3d58800cf9aef023ddf3e86",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/four-screw-layout01/geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/README.md": "e474d0668d9962e4504c8dce0d37a8da05440f01921e8d641b612469194e4056",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/closure.py": "095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/attempt01/checks.json": "91124cdd68bd440d5221047f77d81b47f13cbcf06e68093f3ebc6c5091a74fb9",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/attempt01/receipt.json": "1c037ed5f138cf738f4f4ca8628e377ef2ffbcf332419f496a5b03aab7d759b9",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/bolted-replay.md": "a08553ee1cc86126efb690f9e32ffb6db41e2af06671f2064f5f097c8d09c040",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/central-seat-transfer.md": "9845de69182525f9249038b40cdb385afc25d3d7e6316cf6c6ab5bb274383c9b",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/dead-load-check.md": "b0ad09f528262b529ec75fb41b1a942c2868d4da68dc80abee82d15e6e01ff2c",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/head-reference-basis.md": "577f75fa32889fdb5ee53f1076ebec924132b5251d6e92e571ab0b49e96588d3",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/header-traction-map.md": "d1a1f1af6036551b420ef8c52f01887184d4e43f730483dde290a6258c823a76",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-hardware.md": "7af4755444e6da7ebea43e02583362c34fe792985348e79f217159fed384a025",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-members.md": "ccb2452650787fbfef0e5dc6e50763d2f0a88f2aeeee23311532a871d6c95b35",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-remaining-sections.md": "d5654b78b05251ab361986325aa2863cb7df1c49e0496adc271563ead8800730",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-top-rail.md": "9e5255c2b8a70db02739580e195aebd61d1b01faa5609185f0f0db14d50a289f",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md": "cfda3c960c6cc79009016b89e6328afdc704e4597cdb75921eb7360f7114ca0f",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/mvp-joint-disposition.md": "ad762bb4db00783416ec15ed219f14b96620a75167f7e6e2a23090b8e0ac3a98",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-material-fidelity.md": "5c411432f0c0f6abddaefa9ba2c27fe46a2c0b990e2513f3fe65f2f03f2e361f",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-path-reconciliation.md": "90e349cdc27b41c9641f7646d7a1ed9ce605798c7ca8c4e6795d5a40cf2a1508",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/central-seat-transfer/coupon-attempt01/coupon.json": "bdc35b60ca03039f6e5acad8c5c81784086368a3472183ae7515f66335fe41bb",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/central-seat-transfer/preparation-attempt01/receipt.json": "a1ac28b3b358e1a03a5bd26511774128804a9d45a46e4057cd006bafab1e9ad0",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-continuous-shafts/attempt02/receipt.json": "5496190db02ec1ed8fca6ced59f7538526503ab6735f946e651394ab225d1ffa",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-continuous-shafts/attempt02/suite.json": "ec3b5bbc6d2c80c38bfcbe5877a4ea9ca6ac89f926f5f22fa799bfb9c76a701f",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-corner-references/attempt01/receipt.json": "fcd986b018bb121df464292449cedcb23f1c069bd5ec611dd49b654c6d840288",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-corner-references/attempt01/worksheet.json": "c7c2bbde84cf48bd5042e06cbe218b741da684fa7477eed56da2add4f132c051",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-frame/attempt02/response/comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-joint-replay/attempt01/checks.json": "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-joint-replay/attempt01/receipt.json": "10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-members/attempt01/checks.json": "0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-members/attempt01/receipt.json": "fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-other-bolts/attempt01/receipt.json": "ee67b7e042a8fcf88d1c37eaaaaac8aebcb815e2cf73b8f1a22a61f44283da83",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-other-bolts/attempt01/summary.json": "317fd50ce080862f42bdd57c36994a71bfe499f7d069688571524a803c54e630",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-remaining-sections/attempt01/checks.json": "f519ecc04af7622ec5637162b7a86d6a88e6478e2b15332bf566e6d0e5a3d4c3",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-remaining-sections/attempt01/receipt.json": "e1796242c3ede025927db911af73b69d226ddd7b7e03aa621f77a548a4f322d0",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-response/attempt02/summary.json": "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-top-rail/attempt02/checks.json": "9af1574d785466cdb8de36d3f0cd13dd92cd554ca6e374999f59d20adee5a744",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-top-rail/attempt02/receipt.json": "80ed0f8af4dee1e9cf4d006728a33fdb049c97b3bc0d4ccb904610e7b6b679a1",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-washer/attempt02/receipt.json": "041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-working-package/attempt02/manifest.json": "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-working-package/attempt02/receipt.json": "5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/retail-washer-suite/attempt01-fine/checks.json": "3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/working-joint-register/attempt03/receipt.json": "026fe56a606e453a16faa94aecb4a9302c30ed970260e587ac36061e0104279b",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/working-joint-register/attempt03/register.json": "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/remaining-block-duties.md": "bfe7c2281337e0f606d47ef8182e43cd2286b66e5a0aeb4bbed514e4afcd75f3",
    "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/shop-addendum.md": "4583b946a278d84b75f21de2508cad0dcfd8d590d29486a51af71bc2eb2859e1"
}

EVIDENCE = {
    "reviewed": "rawlocal/working-joint-register/attempt03/register.json",
    "proposal": "rawlocal/knee-bridge-working-package/attempt02/manifest.json",
    "splitting": "all-joint-splitting/rawlocal/attempt01/checks.json",
    "other": "rawlocal/knee-bridge-other-bolts/attempt01/summary.json",
    "members": "rawlocal/knee-bridge-members/attempt01/checks.json",
    "corners": "rawlocal/knee-bridge-corner-references/attempt01/worksheet.json",
    "sections": "rawlocal/knee-bridge-remaining-sections/attempt01/checks.json",
    "rail": "rawlocal/knee-bridge-top-rail/attempt02/checks.json",
    "shafts": "rawlocal/knee-bridge-continuous-shafts/attempt02/suite.json",
    "bridge": "rawlocal/knee-bridge-joint-replay/attempt01/checks.json",
    "response": "rawlocal/knee-bridge-response/attempt02/summary.json",
    "frame": "rawlocal/knee-bridge-frame/attempt02/response/comparison.json",
    "washer": "rawlocal/retail-washer-suite/attempt01-fine/checks.json",
    "geometry": "../member-screen-attempt02/four-screw-layout01/geometry.json",
    "head_note": "head-reference-basis.md",
    "split_note": "all-joint-splitting/README.md",
    "proposal_note": "knee-bridge-working-package.md",
    "disposition": "mvp-joint-disposition.md",
    "methods": "bolted-replay.md",
    "duties": "remaining-block-duties.md",
    "partial_seat": "central-seat-transfer.md",
    "contact": "header-traction-map.md",
    "fit": "../assembly-package/knee-bridge-fit.md",
    "shop": "../assembly-package/knee-bridge-shop.md",
    "order": "../assembly-package/knee-bridge-order.md",
    "washer_inventory": "../assembly-package/washer-coverage.md",
    "shop_axes": "shop-addendum.md",
    "panel_path": "panel-path-reconciliation.md",
    "panel_material": "panel-material-fidelity.md",
    "member_note": "knee-bridge-members.md",
    "rail_note": "knee-bridge-top-rail.md",
    "section_note": "knee-bridge-remaining-sections.md",
    "profile": "knee-bridge-hardware.md",
    "shop_guide": "../assembly-package/shop-guide.md",
    "length_fit": "../assembly-package/hardware-length-fit.md",
    "old_permanent": "dead-load-check.md",
}

# id, owner, exact absent comparison or applicability decision, evidence ids.
# Actual material/product/build observations are limits, not invented numerical tasks.
GAPS = (
    ("N01", "parent", "Fresh nominal lateral references for the twelve end-grain axes (72 states), with the existing Ceg method and its separate group/detailing limits. Current other-bolt output deliberately keeps these references null; the 104-source Ceg result is historical comparison evidence.", "other methods"),
    ("N02", "parent", "Fresh adopted additional group-reduction sensitivity and applicable group resistance for all current bolt groups, including six retained pairs and the two new internal pairs. Existing row-factor hypotheses do not qualify oblique/crossed groups.", "reviewed other corners methods"),
    ("N03", "parent", "Signed spacing/end/edge applicability on both finished hosts for all 108 axes, including existing header oblique/end-grain cases and the four proposed transverse axes. Zero-direction first-ray nulls and geometric bore clearances are not resistance passes.", "reviewed corners bridge methods"),
    ("N04", "splitting peer", "Supported simultaneous transverse boundary transfer and applicable splitting/anchorage comparisons for all 30 duties and 44 timber sides using current force scopes. The 104-source census is complete; its 27 compression envelopes, 13 aligned positive cleat envelopes, eight unaligned cleat envelopes and 40 receiver point envelopes are not complete 108 resistance checks. New all-joint leaves require their own completed receipts before inclusion.", "splitting bridge split_note"),
    ("N05", "parent", "Current base/contact average bearing and adopted quarter-active-area sensitivity from signed contact actions and supported areas. Mean washer-seat and spine-band comparisons do not supply this contact inventory.", "frame proposal corners"),
    ("N06", "parent", "Current floor-runner wood bearing from signed no-slip reactions and the recorded footprints. No friction coefficient, anchor qualification or floor test is required by this register.", "frame geometry"),
    ("N07", "parent", "Current rear-leg recess/base-end notch shear and taper net normal/shear/torsion checks at the actual retained sections, including bore/runout applicability. Geometry records preserve the 38.1 mm depth and 457.2 mm run, but gross rectangular references exclude disturbed profiles.", "geometry members member_note"),
    ("N08", "parent", "Residual finished-opening and end-profile section checks outside the explicit current 144 top-rail, 4,344 header/remaining-block and two-spine finite limits. Reconcile actual bore/passage intervals to section results; do not call all 19,872 gross-method exclusions either passed or uncomputed. Stale-STEP section matches and local concentration/ligament transfer retain null applicability.", "geometry members sections rail bridge duties"),
    ("N09", "parent", "Fresh supported washer/wood pressure and washer-metal T/M comparisons for endpoints not covered by the fresh corner references and the M=0 bridge envelope. The 104-source 48-end top-retail suite and central supported-ring construction remain complete at their own loads; their fresh 108 T/M applicability/envelope join is absent. Mean annulus pressure alone cannot qualify short-block anchorage.", "washer washer_inventory partial_seat corners proposal"),
    ("N10", "parent", "Simultaneous axial/lateral/shaft-bending steel comparisons for the 84 other existing axes using the chosen partial-thread 92 ksi model. Their fresh 504-state worksheet compares lateral action only. The 96 corner, 24 continuous-shaft and 24 new axial states are already separately covered by their stated proxies.", "other corners shafts bridge"),
    ("N11", "parent", "Whole-frame stability/motion and full-length header/member restraint applicability for the current proposal. Six bounded nominal seating states do not prove a unique pose, a displacement envelope, strict tangent stability or stiffness of assumed timber restraints.", "frame members member_note"),
    ("N12", "parent", "Permanent-load C_D=0.9 member/contact/joint comparison at the current 108 proposal gravity and geometry. The completed 104-source permanent result cannot be relabeled current.", "members old_permanent proposal"),
    ("N13", "common knee deformation peer", "Common two-shaft, three-receiver deformation compatibility for both knees, including the proposed internal ties and changed six-bore stiffness. All 24 isolated loaded shaft fields and 96 geometric placements are complete; these do not supply shared timber poses or frame displacement feedback.", "shafts bridge proposal"),
    ("N14", "parent", "Complete panel/screw numerical resistance and compatible transfer under the recorded Hillman/plywood hypotheses: head pull-through, timber withdrawal, lateral/steel interaction, panel/contact sharing and relevant panel bending. The 396 fresh actions and one complete saved governing path are not all these resistance comparisons. Preserve the completed head-reference exceedance.", "response head_note panel_path panel_material"),
    ("N15", "parent", "Current 66-axis supported receiver/backer and both kerf-right inner kicker edge load paths under simultaneous actions, including owner-moved axes. Receiver inventory and unchanged outlines alone do not establish strength/transfer of every support.", "reviewed shop_axes panel_path proposal"),
    ("N16", "parent", "Complete modeled turning/counterhold and installation/reverse-removal stroke envelopes for the stated hardware and sequences, including the four proposed stacks. Saved straight paths, captured-nut alternatives and wire staging remain complete within their scopes; actual operation remains an observation limit.", "fit shop shop_guide length_fit"),
    ("N17", "parent", "Datum-bound connector and finite installed-hardware local-N measurements against 139.7 mm, with explicit dimensioned exceptions. Whole-body extents, stock blank sizes and nominal bolt lengths are not this comparison.", "shop_guide profile proposal"),
    ("N18", "parent", "Modeled tolerance-aware installed/flush/taper-top clearance for the current complete inventory. The saved 58,296 proposal fit pairs and 1,176 mutual paths cover nominal enclosures, not all tool/tolerance or motion envelopes.", "fit frame length_fit"),
    ("N19", "parent", "Machining completeness and exact finished/native taper surface/volume identity, with affected sampling and the unbored-torsion applicability decision. Saved STEP bindings and gross filled-bore native compliance expressly differ; no exact finished-mesh comparison can be inferred.", "geometry proposal member_note"),
)

# id, comparison disposition, applicability, evidence ids, absent check ids, result.
# supported_pass is scoped evidence only; every source criterion remains pending.
ROWS = (
    ("actual_angle_lateral_CD_1", "supported_pass_with_nulls", "applicable_bolts", "other corners shafts bridge", "N01 N02 N03", "432 other-axis and 96 corner lateral comparisons are below their declared references; 72 end-grain ratios remain null. Four new ties are axial only; continuous shafts require their own multi-interface method."),
    ("additional_group_reduction_sensitivity", "source104_only", "applicable_groups", "methods corners", "N02", "The 104-source retained row-factor sensitivity peaks at 0.962538. Fresh corner adjusted references exist; no whole-current group sensitivity acceptance follows."),
    ("local_parallel", "supported_pass_partial", "grain_specific", "corners sections bridge", "N08 N09", "Fresh corner finished-path peak 0.160370; grain section and spine comparisons are complete at named cuts. Neither is all-host local bearing/ligament coverage."),
    ("supplemental_EC5_splitting", "applicability_null", "replacement_method_required", "splitting split_note bridge", "N04", "EC5 single-loaded-edge scalar does not qualify opposing/crossed complete groups. Finite normal-transfer demands and applicable compression witnesses are distinct from missing splitting resistance."),
    ("sampled_net_member", "supported_pass_with_nulls", "finished_sections_partial", "members sections rail bridge geometry", "N07 N08", "33,912 bore-free traces, 4,344 opening limits, 144 rail traces and both spines retain scoped references. Gross-method 19,872 exclusions and stale geometry matches remain explicit."),
    ("header_gross_full_length_stability", "supported_pass_partial", "assumed_restraints", "members frame", "N11", "Fresh member stability kernels retain full strong/beam spans and assumed weak restraints; no complete-frame/restraint acceptance."),
    ("base_bearing_average", "no_comparison", "applicable_contact", "frame corners", "N05", "Local seat means do not supply the base contact-area comparison."),
    ("base_bearing_quarter_area_sensitivity", "no_comparison", "applicable_contact", "frame proposal", "N05", "No current adopted quarter-active-area result is bound."),
    ("base_end_notch_shear", "applicability_unresolved", "retained_cut_inventory", "geometry members", "N07 N19", "Retained recess/profile geometry exists; fresh notch-specific shear comparison is not supplied by intact rectangles."),
    ("group_spacing", "applicability_partial", "all_108_groups", "reviewed bridge methods", "N03", "Existing/new geometric axes are enumerated. Complete applicable spacing rules and host boundaries are not replaced by fit or a first-ray null."),
    ("catalog_washer_bounds", "supported_geometry_partial", "all_216_endpoints", "washer_inventory profile fit", "N09", "Catalog/model families and nominal lands remain recorded. Central partial ring is distinct from full annulus; installed geometry does not assign metal resistance."),
    ("directional_edges", "applicability_partial", "signed_both_hosts", "methods corners bridge", "N03", "Finished corner paths and bridge edge facts are available; universal oblique/header edge acceptance is absent."),
    ("steel_direct", "supported_pass_partial", "partial_thread_model", "corners shafts bridge other", "N10", "Fresh corner and shaft smooth-steel proxies and internal axial references are complete. Other 84 axes have fresh signed T/V but lateral-only references."),
    ("washer_bearing", "supported_pass_partial", "supported_area_only", "corners proposal partial_seat washer_inventory", "N09", "Fresh corner mean pressure peak 0.768962; bridge fixed-land envelope is retained. Central supported-ring route and other annuli retain original force scopes."),
    ("washer_bending", "supported_pass_partial", "fixed_geometry_T_M_scope", "washer proposal", "N09", "104-source top-retail proxy 0.828821; fresh bridge M=0 envelope 0.697914. No general fresh-load metal pass is transferred."),
    ("receiver_fit", "supported_geometry_partial", "nominal_installed", "fit profile reviewed", "N18", "Nominal receiver, shaft and hardware routes are bound; fit does not establish tolerance or loaded movement."),
    ("overlap_contact", "supported_pass_partial", "unilateral_laws", "frame corners bridge", "N04 N05 N13", "Twelve frame law states and named local wrench/contact constructions complete under declared laws; full simultaneous timber transfer remains scoped."),
    ("all_machining_represented", "geometry_bound_approximation", "STEP_vs_gross_native", "proposal geometry", "N19", "50 effective STEP bindings include both modified six-bore spines. Frame compliance retains filled-bore gross solids; this is an explicit approximation."),
    ("sampled_member_stability", "supported_pass_with_nulls", "assumed_restraints", "members member_note", "N11", "C_D=1.25 restrained normal peak 0.518822. End-only kernel retains 8,293 outside-slenderness-domain traces; null domains do not pass."),
    ("all_bolt_centres_sampled", "inventory_bound", "all_108_axes", "proposal response shafts", "N08", "648 unique bolt/case records include 24 internal tie records. Force coverage is not finished-section/resistance sampling at every bore."),
    ("angle_rated_force_components", "replacement_partial", "no_ML24Z_resistance", "proposal corners shafts bridge splitting", "N02 N04 N09 N10", "Map angle duties to complete timber/bolt resistance. Zero angles cannot pass the legacy obligation; completed components retain their scope."),
    ("floor_rail_wood_bearing", "no_comparison", "no_slip_conditional", "frame geometry", "N06", "Frame floor-law checks do not supply floor-runner wood bearing."),
    ("actual_kicker_cutouts", "geometry_bound_partial", "kerf_right_current_66", "reviewed shop_axes proposal", "N15 N19", "Current panel geometry/screw policy is retained; reconcile both inner supports and owner-authorized moves rather than imposing stale fixed-axis wording."),
    ("taper_native_actual_taper", "geometry_bound_approximation", "retained_recess", "geometry members", "N19", "Both rear-leg recess recipes remain saved; gross native compliance is not exact finished taper identity."),
    ("taper_native_matches_cad_taper", "no_comparison", "exact_identity_required", "geometry proposal", "N19", "Pinned finished STEP and gross native model are distinct; no exact surface-match pass is supplied."),
    ("taper_actual_mesh_volume", "no_comparison", "finished_mesh_not_bound", "geometry proposal", "N19", "Drilled STEP and filled-bore retained volumes are saved; exact finished native-mesh volume comparison is absent."),
    ("taper_taper_at_least_one_in_ten", "supported_geometry_partial", "geometric_slope_only", "geometry", "N19", "Saved recess depth/run 38.1/457.2 mm records 1:12. This is geometric identity, not a taper resistance or finished-mesh pass."),
    ("taper_intended_stock_and_runout", "supported_geometry_partial", "recorded_stock", "geometry shop_guide", "N19", "Saved 4x6 rear-leg stock and runout are distinct from 2x6 blocks; delivered cuts remain unobserved."),
    ("taper_taper_bounds_sampled", "inventory_partial", "recorded_cut_stations", "geometry members", "N07 N08", "Saved taper start/end and trace inventory exist; disturbed-profile exclusions do not establish complete applicable section bounds."),
    ("taper_actual_net_section_normal_resistance", "applicability_null", "disturbed_sections", "geometry members", "N07 N08", "Fresh intact profile rectangles do not supply all retained tapered/notched net-section normal comparisons."),
    ("taper_sampled_rectangular_shear_torsion", "supported_pass_partial", "intact_rectangles_only", "members geometry", "N07 N08", "Applicable intact rectangular references are retained; newly bored/disturbed taper slices need their own applicable comparison."),
    ("taper_taper_region_unbored_torsion_applicable", "applicability_unresolved", "bore_runout_inventory", "geometry members", "N07 N19", "Do not apply unbored torsion treatment across retained/new bores merely because taper dimensions persist."),
    ("component_layouts", "inventory_bound", "24_blocks_30_duties", "proposal splitting reviewed", "N02 N04 N17", "All block duties and six retained pairs have named physical sides; this replaces the old 24-angle inventory without transferring its capacity."),
    ("flush_face_normal_contact", "supported_pass_partial", "reconciled_contact_graph", "frame corners bridge contact", "N04 N05", "Current normal-law/wrench witnesses exist; old six-interface counts do not define current supported transfer completeness."),
    ("flush_face_wood_bearing", "supported_pass_partial", "signed_actual_support", "corners bridge rail", "N05 N09", "Named fresh seat/band pressure references complete; full flush/base active-area bearing census remains absent."),
    ("flush_sampled_taper_top_clearance", "supported_geometry_partial", "nominal_vs_full_envelope", "fit frame geometry", "N18", "Saved finite fit and bounded seating are scoped; old 18 monitors cannot become full current tolerance/motion coverage."),
    ("complete_load_path_coverage", "inventory_bound_partial", "all_24_legacy_duties", "proposal splitting panel_path", "N04 N10 N14 N15", "24 block duties and six retained pairs are mapped; a connected graph and balanced components are not complete resistance of all paths."),
    ("center_kicker_receiver_paths", "inventory_bound_partial", "both_inner_edges", "reviewed shop_axes panel_path", "N15", "Current fixed-count screw receivers are named; both edge-support paths need current supported transfer, including top-rail receiver moves."),
    ("connector_body_behavior", "supported_pass_partial", "solid_timber_blocks", "sections bridge corners splitting", "N04 N08", "Finite block section/normal-transfer references complete. Plywood-layer connector behavior is inapplicable to solid timber blocks; panel behavior stays separate."),
    ("housing_and_finished_sections", "supported_pass_with_nulls", "actual_cuts_only", "geometry sections bridge", "N07 N08 N19", "Current bore/recess/relief section scopes are explicit. No new housing experiment or primary-member notch is commissioned."),
    ("complete_joint_actions", "supported_transfer_partial", "simultaneous_six_components", "corners bridge shafts frame", "N04 N09 N10 N13", "Fresh corner transfer, isolated shaft closure and bridge static allocations preserve signed simultaneous wrenches; compatibility and complete resistance remain distinct."),
    ("joint_stiffness", "assumption_unqualified", "gross_frame_rigid_local", "proposal frame shafts bridge", "N11 N13", "Filled-bore gross compliance, declared contact laws and rigid local timber are explicit. Changed-hole stiffness/shared-pose effects are not accepted."),
    ("installed_clearance", "supported_geometry_partial", "nominal_scene", "fit length_fit profile", "N18", "58,296 proposal pairs plus 1,176 mutual paths have zero overlap/undecided; tools, tolerance and loaded motion retain separate limits."),
    ("assembly_and_removal_access", "supported_geometry_partial", "straight_paths_only", "fit shop shop_guide", "N16", "Recorded captured-nut/wire sequences and straight withdrawal paths remain usable assumptions; full turning/counterhold/stroke envelope is absent."),
    ("demountable_transport", "supported_inventory", "metal_nut_removal", "proposal shop shop_guide", "", "50 individual bodies/44 timber blanks retained. Four same-spine ties join no transport bodies; routine structural wood-thread removal stays zero. 66 panel screws are counted separately."),
    ("ordinary_n_envelope", "no_comparison", "named_datum_needed", "proposal profile shop_guide", "N17", "The 139.7 mm datum-bound installed hardware comparison is not supplied by the nominal 6.5-inch length or stock dimensions."),
    ("hardware_source_count_cost", "supported_inventory_partial", "dated_conditional_order", "proposal order profile", "", "108 bolts/nuts, 216 washers and 66 Hillman screws are bound. Dated prices and unknown purchase terms remain explicit; no current complete delivered cost/rating is invented."),
)


def build(output):
    """Authenticate and publish a saved-data map to a fresh owned child."""
    if not FROZEN:
        raise ValueError("STOP: producer remains unfrozen pending parent source restoration")
    output = Path(output).resolve()
    if output.parent != RAW.resolve() or output.exists():
        raise ValueError("STOP: fresh immediate qualification-register child required")
    helper_path = HERE / HELPER
    with helper_path.open("rb") as stream:
        helper_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if helper_digest != FROZEN[str(helper_path.relative_to(ROOT))]:
        raise ValueError("STOP: authentication helper changed")
    spec = importlib.util.spec_from_file_location("qualification_saved_auth", helper_path)
    auth = importlib.util.module_from_spec(spec)
    bytecode_setting = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(auth)
    finally:
        sys.dont_write_bytecode = bytecode_setting
    pins = {ROOT / name: digest for name, digest in FROZEN.items()}
    auth.bind(pins, Path(__file__), auth.sha(__file__))
    auth.bind(pins, HERE / "qualification-register.md", auth.sha(HERE / "qualification-register.md"))
    auth.authenticate(pins)

    # Reuse receipt/source closure readers. Do not execute any mechanical API.
    for path in list(pins):
        if path.name == "receipt.json":
            auth.receipt_sources(pins, path)
    evidence = {}
    documents = {}
    for name, relative in EVIDENCE.items():
        path = (HERE / relative).resolve()
        auth.require(path in pins, "unbound evidence: " + name)
        evidence[name] = {"source": auth.key(path), "sha256": pins[path]}
        if path.suffix == ".json":
            document = auth.read(path)
            documents[name] = document
            for field in ("source_sha256", "classifier_source_sha256"):
                for source, digest in document.get(field, {}).items():
                    auth.bind(pins, ROOT / source, digest)
    auth.authenticate(pins)

    criteria = auth.read(ROOT / CRITERIA)
    frozen_rows = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    ids = [row.get("legacy_id", row.get("id")) for row in frozen_rows]
    auth.require(len(ids) == len(ROWS) == 47 and ids == [row[0] for row in ROWS],
                 "frozen obligation inventory/order differs")
    auth.require(all(row["status"] == "pending" for row in frozen_rows), "criterion status changed")
    gaps = [{"id": gid, "owner": owner, "missing_modeled_check": check,
             "evidence_ids": sources.split(), "disposition": "missing",
             "result": None, "execution_requested_by_this_register": False}
            for gid, owner, check, sources in GAPS]
    rows = []
    for definition, (rid, comparison, applicability, sources, missing, result) in zip(frozen_rows, ROWS):
        auth.require(set(sources.split()).issubset(evidence), "unknown evidence id")
        auth.require(set(missing.split()).issubset({g["id"] for g in gaps}), "unknown missing check")
        rows.append({"id": rid, "frozen_definition": definition, "formal_status": "pending",
                     "comparison_disposition": comparison, "applicability": applicability,
                     "evidence_ids": sources.split(), "missing_check_ids": missing.split(),
                     "evidence_result": result, "formal_acceptance": False})

    def saved(name):
        return documents[name]

    proposal, reviewed, splitting = saved("proposal"), saved("reviewed"), saved("splitting")
    auth.require(proposal["status"] == "CONDITIONAL_WORKING_PACKET_BOUND", "proposal incomplete")
    auth.require(len(proposal["existing_bolt_axes"]) == len(reviewed["axes"]) == 104
                 and len(proposal["proposed_internal_bolt_axes"]) == 4, "104/108 axis split differs")
    auth.require(proposal["case_ids"] == reviewed["case_ids"], "case inventory differs")
    auth.require(proposal["census"]["bolt_case_records"] == 648
                 and proposal["census"]["screw_case_records"] == 396, "proposal force census differs")
    auth.require(splitting["coverage"]["joint_duties"] == 30
                 and splitting["coverage"]["timber_bodies"] == 44
                 and len(splitting["states"]) == 528, "splitting source census differs")
    auth.require(not proposal["proposal_adopted"] and not proposal["complete_joint_acceptance"]
                 and not splitting["splitting_resistance_established"], "source claim boundary differs")

    comparisons = []

    def copy_metric(name, pointer, disposition, scope):
        value = saved(name)
        for part in pointer.strip("/").split("/") if pointer else ():
            value = value[int(part)] if isinstance(value, list) else value[part]
        comparisons.append({"evidence_id": name, "record_pointer": pointer,
                            "comparison_disposition": disposition, "source_scope": scope,
                            "saved_value": value, "formal_acceptance": False})

    for name, pointer, disposition, scope in (
        ("other", "/peak_92ksi_same_state", "supported_pass", "fresh108_lateral_only"),
        ("other", "/census/status_states", "applicability_null_separate", "fresh108_72_end_grain_states"),
        ("corners", "/component_summary", "supported_pass", "fresh108_96_corner_states"),
        ("members", "/global_peaks", "pass_and_exceedance_separate", "fresh108_CD1_and_CD1_25"),
        ("members", "/scenario_exception_counts", "applicability_null_separate", "fresh108_gross_method"),
        ("rail", "/duration_comparison", "pass_and_exceedance_separate", "fresh108_physical_pressure"),
        ("shafts", "/peak_same_state_same_position_smooth_proxy", "supported_pass", "fresh108_isolated_shaft"),
        ("bridge", "/all_named_reference_screens_satisfied", "supported_pass", "fresh108_two_spines_static"),
        ("proposal", "/concentric_washer_envelope_reuse", "supported_pass", "fresh108_fixed_geometry_M0"),
        ("response", "/peak_screw_axial_same_state", "exceedance_against_documented_head_references", "fresh108_head_force_only"),
        ("splitting", "/coverage", "demand_census_complete_resistance_null", "reviewed104_only"),
        ("splitting", "/opening_path_counts", "demand_diagnostic_only", "reviewed104_only"),
        ("washer", "/maximum_envelopes", "supported_pass_original_scope", "reviewed104_retail_48_end_suite"),
    ):
        copy_metric(name, pointer, disposition, scope)
    for family in saved("sections")["families"]:
        for field in ("evaluated_limit_count", "same_state_peaks", "finite_index_counts_above_one"):
            copy_metric("sections", f"/families/{family}/{field}", "supported_pass",
                        "fresh108_finite_nominal_sections")
    for index in range(len(saved("frame")["states"])):
        for field in ("case_id", "gap_scale", "status"):
            copy_metric("frame", f"/states/{index}/{field}",
                        "supported_conditional_laws_not_stability", "fresh108_frame_laws")

    # List exact saved exclusions; later finite families overlap them and are not
    # subtracted without a station/method match. No new section calculation occurs.
    geometry = saved("geometry")
    section_inventory = {
        "gross_method_status_counts": saved("members")["section_status_trace_counts"],
        "matching_finished_sections": geometry["saved_matching_finished_sections"],
        "inapplicable_finished_sections": geometry["saved_non_applicable_finished_sections"],
        "scope": "Saved geometry/method exclusions; not a count of residual failures or completed resistance checks.",
        "current_finite_families": {name: {k: family[k] for k in
                                   ("body_ids", "evaluated_limit_count", "geometry_recipes", "worksheets")}
                                   for name, family in saved("sections")["families"].items()},
    }
    duty_map = []
    for duty in splitting["joint_duties"]:
        added = [axis["axis_id"] for axis in proposal["proposed_internal_bolt_axes"]
                 if axis["body"] == duty["joint_id"]]
        duty_map.append({**duty, "geometry_extension_108_internal_axis_ids": added,
                         "mechanics_scope": "reviewed104_splitting_source_only",
                         "fresh108_splitting_resistance_n": None})

    result = {
        "schema": "existing_evidence_qualification_register/v1",
        "status": "FROZEN_47_OBLIGATION_MAP_WITH_EXPLICIT_MISSING_CHECKS",
        "candidate": criteria["candidate"], "criteria_sha256": pins[ROOT / CRITERIA],
        "formal_pending_criteria_count": 47, "obligations": rows, "missing_checks": gaps,
        "release_flags": saved("other")["release_flags"],
        "evidence": evidence, "comparisons": comparisons, "section_inventory": section_inventory,
        "source104": {"register": evidence["reviewed"], "frame_authority": reviewed["frame_authority"],
                      "accounting": reviewed["accounting"], "splitting_source": evidence["splitting"],
                      "splitting_readme_commit": SPLITTING_COMMIT, "force_acceptance_transferred": False},
        "source108": {"manifest": evidence["proposal"], "census": proposal["census"],
                      "frame_response": proposal["frame_response"], "loads": proposal["source_load_identity"],
                      "modeled_mass_kg": proposal["modeled_mass_kg"],
                      "dead_load_factor": proposal["dead_load_factor"], "limits": proposal["limits"],
                      "internal_axis_ids": [axis["axis_id"] for axis in proposal["proposed_internal_bolt_axes"]],
                      "proposal_adopted": False},
        "joint_duties": duty_map,
        "head_reference_exception": {"demand": evidence["response"],
                                     "reference": evidence["head_note"],
                                     "favorable_documented_reference_range_n": [930.222, 984.128],
                                     "reference_kind": "documented_conditional_arithmetic_not_product_rating",
                                     "physical_failure_claimed": False},
        "applicability_decisions": [
            "No ML24Z resistance transfers; complete timber/bolt duty checks replace that method.",
            "72 end-grain lateral nulls are method exclusions, not zero ratios or completed fresh checks.",
            "New internal ties are axial; a global lateral interface is inapplicable, not missing.",
            "Crossed/opposing groups lack an applicable universal EC5 loaded-edge scalar.",
            "Splitting lower bounds and zero normal bounds are demand diagnostics, not timber capacities.",
            "Nominal ligament sharing is a declared finite comparison hypothesis, not a local stress bound.",
            "Gross rectangular references do not apply at excluded bore/profile traces.",
            "C_D=1.25 requires the recorded seven cumulative full-peak days assumption; C_D=1 results persist.",
            "104-source retail washer/partial-seat/permanent results retain their original loads.",
            "Bridge washer scaling is valid only for its fixed linear plate, zero gap/no preload and M=0.",
            "Plywood-layer connector checks are inapplicable to solid timber blocks; panels remain applicable.",
            "Delivered material/profile, wood/floor and actual installation are unobserved limits, not compulsory new numerical experiments.",
            "Finite floor friction is not adopted; no-slip support remains conditional.",
        ],
        "ownership": {"owned_paths": [auth.key(Path(__file__)), auth.key(HERE / "qualification-register.md")],
                      "parent": "Frame stability, permanent load, heavy-check serialization and integration.",
                      "peers": "Common knee deformation and new all-joint splitting leaves.",
                      "helper_agents_used": 0},
        "authority_mutated": False, "criteria_mutated": False, "formal_acceptance": False,
        "complete_joint_acceptance": False, "physical_release": False, "fabrication_release": False,
        "native_CAD_frame_or_test_executions": False, "review_loop_run": False,
        "source_sha256": {auth.key(path): digest for path, digest in sorted(pins.items())},
    }
    auth.authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    auth.write(output / "qualification-register.json", result)
    auth.authenticate(pins)
    receipt = {"schema": "existing_evidence_qualification_receipt/v1", "status": result["status"],
               "source_sha256": result["source_sha256"],
               "output_sha256": {path.name: auth.sha(path) for path in sorted(output.iterdir())},
               "obligation_count": len(rows), "missing_check_count": len(gaps),
               "physical_release": False, "authority_mutated": False,
               "native_CAD_frame_or_test_executions": False}
    auth.write(output / "receipt.json", receipt)
    auth.authenticate(pins)
    return {"status": result["status"], "obligation_count": len(rows),
            "missing_check_count": len(gaps), "source_pin_count": len(pins),
            "producer_sha256": auth.sha(__file__),
            "register_sha256": auth.sha(output / "qualification-register.json"),
            "receipt_sha256": auth.sha(output / "receipt.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(build(parser.parse_args().output))
