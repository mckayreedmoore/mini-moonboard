# Center shared-header bolt: method gate

The nominal center-header trial puts one angle above and one below the 38.1 mm
wood header, with two coincident through-header bolt axes. This is an ordered
steel–wood–steel stack, not two independent steel-to-wood single-shear joints.
The trial has no selected fastener/washer stack, qualified six-case joint
action, or capacity.

The [2024 NDS Chapter 12, Table 12.3.1A](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
provides symmetric double-shear lateral-yield Modes Im, Is, IIIs, and IV
(Equations 12.3-7 through 12.3-10). Its wood middle-member Mode Im bearing
uses the one full header bearing length; the two side-member contributions
are considered together. [AWC TR12 §§1.2–1.4](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
likewise model one fastener and its ordered bearing and bending response.
Neither source permits two separate full-header single-shear capacities to be
added for the same bolt. NDS 12.3.5.4's lesser side-member length provision
addresses unequal side *lengths*, not unequal side *actions*; 12.3.8's
adjacent-member procedure concerns four or more members.

Before choosing a method, resolve a simultaneous local force and moment at
each principal and post angle for every new-candidate case. Distribute each
angle's eccentric action to the two actual shared bolts, equilibrate both
flanges and the header, and determine whether their lateral actions meet the
symmetric double-shear assumptions. If they do not, use a documented
whole-fastener bearing/bending analysis for unequal side actions. Then check
bolt-axis tension and prying separately, as well as wood end/edge/spacing,
splitting, net/row/group sections, washers, and the angle's hole, flange,
and formed-bend resistance. No qualified six-case new-candidate actions or
ABB steel guarantees are available for that calculation yet.

The [left-center diagnostic](../bolted-candidate-center-design-convergence.md) now
recovers simultaneous actions for `a1-rear` under three provisional joint
stiffnesses. Its shared-bolt side actions are unequal and stiffness-sensitive;
it is not a qualified six-case design envelope. The bounded `a12-forward`
attempt did not converge its unilateral contact set, so its intermediate
forces are excluded. The
[10,000 N/mm accepted diagnostic](../bolted-candidate-center-design-convergence.md)
illustrates the method exclusion: for shared bolt 0, the upper/lower steel
flanges apply lateral XY vectors `(-49.37, -128.85)` and `(-34.46, +28.19) N`
to the same bolt; their magnitudes are 137.98 and 44.52 N. For shared bolt 1,
the lateral magnitudes are 74.13 and 38.09 N. These are simultaneous
provisional actions, not equal same-direction side loads and not a rated demand.
The existing
[two-member six-mode helper](../../mini_moonboard/bolted_steel_wood_yield.py)
must not be applied directly to the shared stack. This method gate does not
select AB205, establish a load rating, or release drilling.

The separate [2024 NDS symmetric double-shear reference helper](../../mini_moonboard/bolted_steel_wood_double_shear.py)
calculates the four one-bolt yield modes only with explicitly supplied steel
bearing and bolt-bending strengths, actual bearing lengths and thread exposure,
and an affirmative symmetric-action method gate. It has no AB205 default and
cannot be applied to the unequal actions above. Even in an admissible symmetric
case, its unadjusted minimum is not the installed wood/steel/bolt joint verdict.
The reviewed [NDS Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
and [AWC TR12](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
do not publish a direct three-member yield equation for these *unequal* outer
actions. NDS 12.3.8's adjacent-member procedure is for four or more members;
the shorter-side-length rule in 12.3.5.4 does not resolve unequal forces. Any
whole-fastener alternative must explicitly equilibrate both steel actions and
the distributed wood bearing, track bolt shear/flexure and any axial/prying
action, and be documented as a developed method rather than an NDS table value.

The steel-side limit is independent of that timber calculation. ABB calls
AB205 a [1/4-in steel fitting](https://empower.abb.com/ecatalog/ec/EN_NA/p/AB205EG)
and its [fittings catalog](https://www.tnb.ca/en/pdf-catalogues/metal-framing-fastening-and-identification/metal-framing/fittings-and-brackets.pdf)
calls the family hot-rolled carbon steel, but neither supplies a guaranteed
AB205 yield/tensile strength, bend resistance, or wood-joint rating. ABB's
[2,000-lb AB205 entry](https://library.e.abb.com/public/8d1baaf1d93a4d24b6ecc43da7850a39/TDS000752_A_1.pdf)
is for the illustrated both-ends-supported A1200/A1400 strut-channel
configuration; it cannot be transferred to this timber assembly. A future
component route needs traceable fitting material and formed geometry, actual
joint actions/contact, and applicable hole bearing/tear-out, net-section,
bend/prying, bolt interaction, and washer-seat checks. Common carbon-steel
properties or a Grade 5 bolt rating cannot fill the fitting-property gap.
