# Panel screw withdrawal preflight

Prepared 2026-09-28 for the reduced-static MVP. This is a bounded method and
input screen for the existing 66 Hillman/Fas-n-Tite 42605 axes. It changes no
geometry or hardware and establishes no resistance, stiffness, load share, or
acceptance.

## Finding

The six climbing cases have positive outward panel-normal resultants of about
1.20–1.66 kN before gravity. The reviewed rear panel/frame faces are
compression-only: they can support the panel when it bears inward, but open
under outward panel motion. No complete alternative tension restraint is
established in the contact topology. Therefore the current zero-axial-credit
screw model remains an omission diagnostic; it cannot supply a complete
six-case panel load path. These case resultants are global inputs, not screw
group or per-screw demands.

The current reduced-static input lists all 66 panel screws and their receiving
members. Its timber descriptors place all modeled screw axes perpendicular to
their receiver grain (absolute direction cosine no greater than 3.2e-10 for
the oblique axes; zero for the orthogonal axes). That is consistent with the
orientation premise of the NDS side-grain withdrawal provision in the modeled
geometry. It does not establish the grain or grade of delivered pieces. The
current input binds the four center-kicker axes to the two center posts; use
these current receiver IDs, not the separate historical WJ24 backer remap.
The purchase record identifies Lowe's 755741, Hillman/Fas-n-Tite 42605, #10 ×
2-1/2 in (63.5 mm), flat-head, coarse-thread; all axes enter the 139.7 mm
receiver dimension. The [listing](https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042)
does not provide structural design values, and [Hillman’s product Q&A response](https://www.lowes.com/questions/fas-n-tite-42605-deck-screws/999995042/f4fd545e-48c7-5ada-90ea-db1169f463ee)
says no tensile-strength rating is listed.
With the assumed 18.25625 mm panel, nominal overall length beyond the panel is
45.24375 mm (1.78125 in). This is an upper geometric envelope, not measured
thread penetration `pt`; the public product record supplies no root, thread,
head, steel, or design dimensions. See the [current model preparation](reduced-static-attempt01/README.md),
[current model inputs](reduced-static-attempt01/model-inputs.json),
[purchase record](../../../current-panel-screw-purchase.md), and
[fixed-receiver audit](../../wj24-fixed-screw-receiver-audit.md).

## Conditional NDS resistance scale

The [AWC 2024 NDS Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
provides a possible *conditional* wood-thread withdrawal route:

- NDS §12.1.5.1 scopes wood-screw installation provisions to screws meeting
  ANSI/ASME B18.6.1. Section 12.1.8 permits use of §§12.2 and 12.3 for other
  dowel-fastener types or differing installation when an allowance is made
  for the variation under §11.1.1.3, with spacing sufficient to prevent
  splitting. The public 42605 record does not establish B18.6.1 conformity or
  supply an allowance. Its “deck screw” name neither proves nor disproves
  eligibility.
- For a single cut- or rolled-thread wood screw in side grain with its axis
  perpendicular to fibers, §12.2.2.1–2 uses Table 12.2B or
  `W = 2850 G² D` lb/in of thread penetration, then multiplies by actual `pt`
  and all applicable adjustment factors to obtain design resistance. At
  `G = 0.50` (the assigned DF-L scenario) and wood screw number #10, Table
  12.2B gives `W = 135 lb/in`. Sections 12.2.2.3–5 prohibit wood-screw
  withdrawal from end grain and cap the result at adjusted screw net-section
  tensile resistance.
- **Illustrative upper-envelope arithmetic only:** if 42605 were eligible for
  this method and the entire 1.78125 in beyond the assumed panel were threaded
  penetration into side-grain DF-L, the unadjusted wood-thread reference value
  would be `135 × 1.78125 = 240.47 lbf ≈ 1.070 kN per screw`. Actual `pt` is
  unknown and cannot exceed that geometric envelope; the product, installation,
  adjustment factors, root-section tension, and group behavior are unresolved.
  This number is not an adopted 42605 capacity or a group rating.

For `G ≤ 0.50`, §12.1.5.2 says a withdrawal lead hole is not required. The
owner-selected 1/8 in lead pilot through the panel into the receiver remains
the recorded installation policy; the code text does not itself validate that
pilot against this screw's unknown root or establish that it may be omitted.
Reconcile the actual pilot and 3/8 in countersink with the selected method;
do not transfer another product's installation rules.

NDS §12.2.5.1 Table 12.2F / Eq. 12.2-6 is explicitly for **round heads**.
The purchased 42605 has a flat/countersunk head, and the side member is
plywood. That round-head value is not an applicable plywood head-pull-through
resistance here. Head pull-through, countersink breakout/net thickness, and
panel damage remain distinct from wood-thread withdrawal and screw-root
tension. NDS §12.4 combined lateral-withdrawal interaction also cannot be
completed without applicable adjusted withdrawal and lateral values and
simultaneous interface actions.

## Axial stiffness and shortest defensible next step

The NDS withdrawal tables provide reference **strength**, not an axial
load-slip spring constant. The [ASTM D1761-20(2025) scope](https://store.astm.org/standards/d1761)
is a basic procedure for evaluating withdrawal and lateral resistance of
fasteners in wood and wood-based materials. It does not publish a 42605
spring value, establish this countersunk plywood-head limit, or establish
66-screw group sharing.

No source-supported numerical `k_ax` or physical upper/lower stiffness bound
for 42605 was found. If needed for a diagnostic native response, represent
each axis as a **tension-only, parameterized** panel-to-receiver spring and
sweep stiffness values only after a measured or otherwise applicable range is
available. Keep the unilateral rear-face contact separate; do not credit
preload, friction, or compression through the screw. An arbitrary numerical
range may show model sensitivity but is not a defensible physical bound and
must not feed an adopted demand/resistance result.

The most direct evidence route is matched, instrumented panel-to-receiver
load-slip testing with the exact 42605, the current receiving wood and panel,
the recorded 1/8 in pilot and 3/8 in countersink, actual thread penetration,
and representative edge/row geometry. Measure the panel/receiver force versus
opening displacement through service range and failure. This can bound axial
stiffness and reveal the governing withdrawal/head/panel mode for the tested
configuration. Use ASTM D1761 as the withdrawal/lateral test-method starting
point where applicable; separately document the countersunk panel-head test
and define the statistical/design basis before treating measured peak loads as
design resistance. Single-screw coupons alone do not prove the 66-axis group
distribution or the complete receiver-to-frame path; use a supported group
method or a representative assembly if those effects govern.

## Inputs still needed before a screw-dependent six-case response is usable

1. Bind exact current receiver and grain per axis, including physical species,
   grade, specific gravity/moisture scenario, and any end-grain exception.
2. Establish exact 42605 thread form and dimensions, threaded length, root
   section and steel tensile properties, and either B18.6.1 applicability or
   an NDS §12.1.8 allowance for the product/installation variation. Do not
   presume lot testing is required; use applicable exact product data or
   bounded measurements/evidence.
3. Establish installed receiver thread penetration `pt`, actual pilot fit,
   head seating/countersink depth, head diameter and panel net thickness.
4. Select an applicable resistance basis for panel-head pull-through and
   plywood damage, separate from NDS wood-thread withdrawal and steel-root
   tension.
5. Obtain axial load-slip stiffness (or a source-supported bound) and a
   defensible group load-sharing method; then recover simultaneous signed
   panel-interface and per-axis/group actions for all six cases.
6. Continue the screw reactions through every receiving member to the frame.

If those values are unavailable now, the bounded outcome is a localized
panel-withdrawal exception and a diagnostic stiffness sweep explicitly marked
non-qualifying. The six-case solve may proceed only if its intended output is
clearly limited to that diagnostic question; do not publish full-frame joint
acceptance or per-screw demand/resistance from a no-axial-credit path.
