# Conditional wood-to-steel single-shear yield route

`mini_moonboard/bolted_steel_wood_yield.py` computes the minimum of the six
unadjusted 2024 NDS Table 12.3.1A single-shear yield modes for one solid
Douglas Fir–Larch wood main member and one steel side plate. It uses the
existing DF-L dowel-bearing helper. Steel dowel-bearing strength, bolt bending
yield, full-body and thread-root diameters, thread exposure in each member,
wood bearing length, steel thickness, and grain angle are required inputs.
There is no A36 or A66 material default.

The solver in `fea/dowel_yield.py` uses bearing intensity `q = Fe D`, dowel
moment `M = Fyb D³/6`, zero gap, and the 2024 Table 12.3.1B reduction terms.
The focused test independently evaluates all six Table 12.3.1A equations,
including `k1`, `k2`, and `k3`, and compares them to the solver for several
unequal wood/steel property and length cases. All six agree numerically.

The [AWC 2024 NDS Chapter 12, printed pp. 91–103](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
is the equation source. The Table 12B DF-L `G = 0.50` cell for a 1.5-inch
wood main member, 1/4-inch ASTM A36 steel side plate, and 1/2-inch full-body
bolt states 580 lb parallel and 310 lb perpendicular. The test compares that
cell only with its stated 45,000 psi bolt bending yield, 87,000 psi steel
dowel bearing, and zero thread exposure in both bearing regions. The table
rounds to 10 lb. This is a regression fixture, not an A36 or A66 selection.

NDS 12.3.7 controls the effective bolt diameter. The function uses full-body
diameter only when thread bearing length is at most one-quarter of each
member's bearing length; otherwise it uses the supplied thread-root diameter.
It rejects effective diameters below 1/4 inch because Table 12.3.1B then
requires different reduction terms.

The result is a **single-fastener lateral yield reference**, conditional on
contacting member faces, one shear plane, and load perpendicular to the bolt
axis. It does not establish edge/end/spacing compliance, wood splitting,
steel hole/plate/bend resistance, bolt axial action, washer contact, group
action, adjustments, or a complete angle-connector resistance. The A66 steel
property and actual station geometry remain unresolved.

The candidate shared center-header bolt stack has **two steel flanges around
wood with potentially unequal actions**. It is not the two-member single-shear
condition modeled here. Do not apply this helper directly to the shared stack;
its member actions and applicable multi-member resistance need separate
resolution.
