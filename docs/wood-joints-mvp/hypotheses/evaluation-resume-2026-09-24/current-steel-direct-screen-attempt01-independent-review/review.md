# Independent review — `steel_direct` attempt01

**Reviewed:** 2026-09-28  
**Scope:** source, method applicability, arithmetic, and packet integrity for
[`current-steel-direct-screen-attempt01`](../current-steel-direct-screen-attempt01/).

## Conclusion

The attempt supports the **bounded method-gap conclusion**: within the reviewed
source set, no applicable design procedure was authenticated for the current
timber joint's simultaneous through-bolt tension, transverse shear, and
bending. Keep `steel_direct` pending. This finding does not prove that no
acceptable method exists; it says the screened sources do not establish one
for this product, timber-joint configuration, section changes, and combined
actions. The screen correctly makes no criterion result, capacity, or pass
claim.

## Integrity and source recheck

All three files listed in the attempt's `terminal-hashes.json` match their
recorded SHA-256 values. All seven local candidate-source pins in
`source-pins.json` also match the current file bytes. The Chapter 11 and
Chapter 12 AWC PDF review copies match their recorded digests, as does the
March 2026 NDS errata copy. The attempt04 manifest's raw file hash matches its
pin. Its embedded digest also reproduces when the preimage restores the
attempt03 digest that attempt04 copied before rebuilding; simply removing the
final digest field is not the producer's construction. These checks are
recorded individually in `integrity-manifest.json`.

The criteria-method-map file was marked modified in the shared working tree at
review time, but its bytes match the SHA-256 pinned by attempt01. This review
therefore assesses the exact pinned bytes; the hash does not establish their
commit ancestry.

The official ASTM pages were reopened. [ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html)
identifies a static test method for bending yield moment and calculation of
fastener `Fyb`, and describes that value as an input to lateral connection
design. [ASTM F606/F606M-26a](https://store.astm.org/f0606_f0606m-26a.html)
states that product standards specify property requirements and applicable
tests. These are property/test routes, not bolt resistance or a combined
tension/shear/bending rule.

The pinned AWC Chapter 11 PDF's local copy was digest-checked; its extracted
text for §11.2.3 directs metal fasteners and parts to applicable metal design
procedures for tension, shear, metal-on-metal bearing, bending, and buckling,
but names no procedure for this bolt-in-timber configuration and gives no
combined-action equation. The official AWC PDF endpoints were inaccessible in
the web review. Chapter 12's pin and clause location are retained from the
attempt; its official PDF endpoint was likewise inaccessible in this review.
The Appendix-commentary digest is inherited from the earlier source review
and was not independently re-fetched here. That limitation does not change the
method-gap conclusion: the `Fyb` estimate is not relied on as direct bolt
resistance.

Official AISC scope pages identify [AISC 360](https://www.aisc.org/aisc/publications/current-standards/aisc-360/)
with structural-steel buildings and structures and [RCSC](https://www.aisc.org/aisc/publications/current-standards/rcsc-standard/)
with bolted structural-steel connections. The current AISC 360 text was not
accessible, and no equations were adopted. Those scope statements do not
establish applicability to this timber connection or a combined bolt
tension/shear/bending check. The [Goel AISC Engineering Journal paper](https://ej.aisc.org/index.php/engj/article/view/467)
is a 1986 discussion of tension/shear stress interaction, including a
von-Mises-related empirical proposal; it is not a current normative rule, a
timber-joint method, or a treatment of fastener bending under this load
combination.

## Method and arithmetic assessment

Keep the three quantities separate:

1. **NDS lateral yield:** NDS Chapter 12 `Fyb` is used in the wood-fastener
   lateral-yield route to derive reference lateral connection values `Z`.
   It is not direct bolt tension, shear, or bending resistance.
2. **`Fyb` as a test input:** ASTM F1575 tests bending yield moment/strength;
   ASTM F606 is a mechanical-property test method whose applicable properties
   and tests are specified by the product standard. Neither standard supplies
   the candidate's delivered bolt properties or a combined design resistance.
   The Appendix commentary estimate based on tensile yield/ultimate values is
   an estimate for the `Fyb` input, not a tested product value or a bolt
   design capacity.
3. **Material first-yield arithmetic:** the helper's `A·Fy`,
   `A·Fy/√3`, and optional same-section average-shear von Mises calculation
   are unadjusted material references. They are not design resistances.

The known-answer arithmetic is correct for its synthetic, co-located
100 mm² section: tension reference 60,000 N; shear reference 34,641.016 N;
`σ = 300 MPa`; nominal average `τ = 100 MPa`; and von Mises equivalent stress
346.410 MPa. The corresponding unadjusted ratios are 0.5, 0.288675, and
0.577350. This verifies arithmetic only. The helper explicitly leaves bending
unevaluated and omits section stress distribution, thread/fracture limits,
design factors, load sharing, and connection effects. A real bending moment
would require the section geometry and location-specific stress state at each
controlling shank/thread section; the example supplies neither.

The pinned current-frame manifest identifies the reviewed candidate and
revision, but its six case records are applied force/wrench inputs and each
marks `reactions_or_joint_demands` false. It says solver model inputs and
body/element/DOF material mapping are incomplete, no product is selected, and
no native solve was executed. Thus the screen has neither simultaneous
per-bolt actions nor a fit-qualified product against which to run a resistance
check. No solver or native run was performed for this review.

## Disposition

Retain the method-gap status and the existing `pending` disposition. The
screen's distinction between NDS lateral-yield `Fyb`, test-derived/property
inputs, and material first-yield arithmetic is technically appropriate. A
future criterion-resolving producer still needs an applicable reviewed metal
design procedure and product/property basis; actual thread and shank sections,
shear planes, and bending sections; signed simultaneous per-bolt forces and
moments; and an independently checkable benchmark. No source reviewed here
supports inferring a capacity or acceptance result.
