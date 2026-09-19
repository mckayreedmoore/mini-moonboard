# Center shared-header bolt: method gate

The nominal center-header trial puts one angle above and one below the 38.1 mm
wood header, with two coincident through-header bolt axes. This is an ordered
steel–wood–steel stack, not two independent steel-to-wood single-shear joints.
The trial has no specified fastener/washer stack, joint action, or capacity.

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
and formed-bend resistance. No new-candidate actions or ABB steel guarantees
are available for that calculation yet.

The present [two-member six-mode helper](../../mini_moonboard/bolted_steel_wood_yield.py)
must not be applied directly to the shared stack. This method gate does not
select AB205, establish a load rating, or release drilling.
