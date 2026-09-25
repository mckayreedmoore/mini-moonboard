# Independent review: nominal 1/4-20 engagement tangent scenario

**Reviewed:** 2026-09-25. **Result:** source description, numerical adaptation,
and claim limits are sound for the stated conditional post-seating scenario.
No material correction is needed. This review does not establish a physical
thread law, zero-preload engagement, or joint acceptance.

## Pinned inputs

| Input | SHA-256 |
|---|---|
| [Current engagement proposal](../../current-engagement-analytical-proposal.md) | `ed71af102b1e8987d71597f72c9a8f7f756e45335e21a9e23d2ee234253b0d9b` |
| [Attempt 01 README](README.md) | `75ba388f3e9a1b6814bf024fea7cf835b5b3759dba118c672f1eee60cab4e2c1` |
| [Calculation JSON](calculation.json) | `80f73199d77e7d6147d6e4d8a74018c151a45a89070882c6c888a5440d0b44eb` |

## Primary-paper scope check

The primary [Matsubara and Teranishi paper](https://link.springer.com/article/10.1186/s10086-022-02038-1)
has the cited component equation in Eq. (5), `K_th = A_s E_b/L_th`, and the
equivalent-length relation `L_th = 0.85d` in Eq. (9). Its Eq. (4) places
`K_th` in series with thread-play, cylindrical-bolt, and bolt-head springs.
The paper defines `A_s` as the effective area from JIS B1082 and uses
`E_b = 205,000 N/mm²`. The proposal identifies that source basis and makes
the separate Unified-size tensile-stress-area substitution explicit instead
of implying that the paper used its `A_s` for 1/4-20.

Applicability is represented accurately. The paper tests M12 SWCH bolts with
1.75 mm pitch and 30 mm thread length in four timber species, 12 specimens
per species. It compares the *combined timber-joint tightening stiffness*
from the series model (including washer embedment) with tightening-test
measurements. It does not independently measure `K_th`, quantify thread-fit
backlash, or validate the equivalent-length component for Unified 1/4-20.
The article reports little axial-force growth during initial rotation/slip,
then a nearly linear force-rotation region before nonlinear behavior; this
supports the proposal's distinction between a seated tangent and the
unresolved initial seating branch. The paper's validation claims are not
transferred to WJ24.

ASME's [B1.1-2024 record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
confirms that B1.1 specifies Unified form, series, class, allowance, and
tolerance. That standard establishes nominal geometry and fit limits; it
does not provide an engagement-compliance law. The [NIST Handbook 28
Supplement](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28supp1963.pdf)
is the cited government source for the Unified tensile-stress-area equation.
Calling that stress area a model input—not a measured elastic contact area,
physical stiffness bound, or capacity—is appropriate.

## Independent numerical check

I recomputed the stated equation and all three elastic-modulus points from
the declared inputs. The relation `A_s = 0.7854(D − 0.9743/n)²` gives
`0.031820992472115 in²` for `D = 0.25 in` and `n = 20/in`, or
`20.529631503310 mm²`. With `d = 6.35 mm`, `L_th = 0.85d = 5.3975 mm`.

| `E_b` scenario | `K_th` (kN/mm) | `C_th = 1/K_th` (mm/kN) |
|---:|---:|---:|
| 180,000 MPa | 684.638012153 | 0.001460625881 |
| 200,000 MPa | 760.708902392 | 0.001314563293 |
| 220,000 MPa | 836.779792631 | 0.001195057539 |

These values reproduce the JSON within rounding. The unit conversion is
consistent: `mm² × N/mm² / mm = N/mm`, followed by division by 1,000 for
kN/mm. The 1/4-20 pitch is 0.05 in = 1.27 mm. The 180/220 GPa points are the
existing generic steel scenario's ±10% analyst sensitivities; they are not
physical bounds on WJ24 steel or on a thread pair.

## Compliance partition and zero-preload limits

The proposal correctly treats `K_th` as one **post-seating, local axial
tangent** on a particular active flank branch. It keeps the thread-play
length term `L_s` in the bolt's series extension model distinct from
flank-to-flank backlash and does not derive an initial free-travel value from
the article's slip observations. With no selected WJ24 thread classes,
matched profiles, or installed fit, its `g = 0` case is explicitly an
idealized zero-slack comparator rather than the real unpreloaded initial
state. It appropriately leaves seating travel unresolved and gives no
preload, stripping, pullout, bolt-proof, or nut-proof result.

The compliance-use warning is also adequate: the spring is included only if
engaged-thread deformation is omitted elsewhere; it must not be placed in
parallel with explicit thread/contact compliance or duplicate deformation
already carried by a bolt/nut model. Where deformable nut bodies remain
explicit, the connector's replaced deformation must be defined. These
conditions prevent an unspecified overlap in the compliance partition.

The proposal can proceed as the labeled sensitivity-only scenario it
describes. Any later physical use still needs an explicit coordinate and
compliance partition, actual active-flank/fit evidence for a physical
seating path, and separate strength checks; none is implied by this review.
