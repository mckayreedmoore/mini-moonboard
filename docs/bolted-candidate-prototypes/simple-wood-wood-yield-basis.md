# PB-04: conditional wood-to-wood single-bolt yield component

[`wood_wood_single_shear_reference`](../../mini_moonboard/bolted_wood_wood_yield.py)
maps two solid Douglas-fir–larch member inputs to the existing
[`single_shear`](../../fea/dowel_yield.py) six-mode solver. It is a component
calculation, not a selected PB-02 joint, group capacity, rating, or drilling
release. No A307 delivered-bolt strength, shank length, or thread geometry is
assumed.

The companion `dowel_bending_yield_moment_lb_in` computes the plastic dowel
moment `M_y = F_yb D_effective³ / 6` from **separately sourced** bending-yield
strength and the diameter established for the delivered shank/thread
geometry. This is the round-dowel moment relation in [AWC TR12 §1.7][tr12],
not a product grade lookup or a shaft shear/tension rating. For illustration,
45,000 psi with 1/2-in effective diameter gives 937.5 lb·in; if effective
diameter is 0.4 in, it gives 480 lb·in. These numbers cannot be assigned to
an unverified store bolt or treated as a connection resistance.

## Source and applicability

- [AWC 2024 NDS Chapter 12, printed pp. 91–95][nds12], Table 12.3.1A,
  gives six single-shear modes. Section 12.3.1 requires contacting faces,
  lateral force perpendicular to the bolt, and qualifying edge/end distances
  and spacing. This wrapper requires an explicit `gap_in=0` but **does not**
  verify the other prerequisites.
- [Table 12.3.1B][nds12] gives `R_d`: `4Kθ` for Im/Is, `3.6Kθ` for II,
  and `3.2Kθ` for IIIm/IIIs/IV for effective diameter 1/4–1 inch, where
  `Kθ = 1 + 0.25 × max(two load-to-grain angles)/90`. The caller supplies all
  six values; the wrapper validates them against that table. If threads
  require an effective `D_r < 1/4 in` for a nominal bolt at least 1/4 in,
  every mode instead uses `R_d = K_D Kθ`. The rendered
  [2024 NDS erratum][errata] gives `K_D = 2.2` through `D=0.17 in`, then
  `K_D = 10D + 0.5` up to but not including `D=0.25 in`.
- [Sections 12.3.3–12.3.5][nds12] provide solid-wood dowel bearing,
  angle-to-grain interpolation, and actual bearing-length rules. The existing
  `dfl_dowel_bearing_psi` helper provides each member's conditional DF-L
  `G=0.50` value. For selected `D < 1/4 in`, Table 12.3.3's
  angle-independent `16,600 G^1.84` expression rounds to 4,650 psi for
  DF-L. This requires both members to actually be qualifying solid
  DF-L, not plywood, steel, an unknown species, or unverified damaged wood.
- [Section 12.3.7][nds12] distinguishes full shank `D` from thread-root
  `D_r`; full `D` for a threaded full-body fastener is permitted only when
  thread bearing length is no more than one-quarter of the bearing length in
  each member holding threads, absent a more detailed analysis. The caller
  supplies both **delivered** diameters and thread-bearing lengths in both
  members; the wrapper selects `D` only when both quarter-length limits hold,
  otherwise `D_r`. `bolt_bending_yield_moment_lb_in` must correspond to that
  selected diameter and the established bolt property, not a nominal grade
  or a shaft tensile/shear rating. The wrapper intentionally does not derive
  this moment from an assumed `F_yb`. The sub-1/4-inch route additionally
  requires an explicit sourced `F_yb` matching the supplied moment to the
  selected root diameter. This consistency check does not certify the
  source or the installed bolt.
- [Section 12.3.3.4][nds12] has a special main-member end-grain rule for a
  bolt axis parallel to fibers. This simple wrapper rejects axis-parallel
  grain in either member so that neither a main/side role swap nor the usual
  angle interpolation silently bypasses that issue. Analyze any such joint
  separately.

The focused [tests](../../tests/test_bolted_wood_wood_yield.py) compare all
six modes to the existing solver with independent bearing inputs, exercise
different angles and lengths, and reject a gap, axis-parallel grain, wrong
reduction terms, and incomplete inputs. They verify code behavior, not a
particular store-bought bolt or connection.

The current 1/4-in PB-01 **N-grain four-bolt** cleat has upright bolts along
X and rail bolts along local T; both axes are transverse to cleat grain N.
The earlier separate X-grain one-bolt pose has an axis-parallel upright
bolt and remains outside this wrapper. For the four-bolt pose, the retail
source screen still has no exact product root or `F_yb`, no qualified group
or member checks, and no new-topology same-case force. The small-root branch
is component groundwork, not a PB-01 capacity result.

## Still required for an actual PB joint

For each proposed bolt, record the actual two-member geometry, bearing
lengths, grain vectors and force direction, bolt axis, delivered shank/thread
exposure, bore, selected hardware evidence, bending-yield moment, and all
2024 NDS adjustment terms. Establish the applicable edge/end/spacing and
splitting or net-section checks before treating the minimum of these six
modes as an NDS reference value. The output does not check group action or
load sharing, multiple shear planes, axial tension/prying, washer contact and
local crushing, bolt tension/shear interaction, or same-case demand. Those
remain separate PB-04/PB-05 gates. Do not multiply this one-bolt value by
bolt count or issue a load or drilling rating from it.

[nds12]: https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf
[errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
[tr12]: https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf
