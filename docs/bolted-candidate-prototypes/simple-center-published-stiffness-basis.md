# PB02 published stiffness basis

## Scope

`scripts/simple_center_published_stiffness_basis.py` records published lateral-slip
sensitivities and identifies the inputs still needed to calculate axial-joint and timber
face-contact stiffness. It is a source-bounded developmental record for the active PB02
geometry. It does not select a stiffness, establish connection resistance, or release any
drilling or fabrication.

The script reads all ten active PB02 bolt grips from the shared geometry and stack pairing.
Its output is tied to the `ligament_priority` geometry fingerprint. The calculated quantities
below are stiffness sensitivities, not bolt capacities or complete-joint acceptance checks.

## Lateral bolt-slip bases

### 2024 NDS group-action modulus

The corrected 2024 NDS group-action expression for a wood-to-wood dowel connection is:

`gamma = 180,000 D^1.5 lb/in`

For the nominal 1/4-in bolt, this gives 22,500 lb/in, or approximately
3,940.354 N/mm. The source is the [2024 NDS errata and addenda][nds-errata], which
corrects Section 11.3.6.1.

The script applies this number as a single-bolt, single-shear-plane PB02 sensitivity. Its
normative NDS role is the group-action-factor calculation. It is not a general three-dimensional
spring law, a strength value, or a complete-joint stiffness. Fastener fit, bore clearance,
moisture, load level, and cyclic response remain separate effects.

### Eurocode 5 service-slip sensitivity

The service-slip expression reproduced by USDA/FPL for predrilled dowel-type fasteners is:

`Kser = rho_mean^1.5 d / 23`

For `d = 6.35 mm`, the script reports:

| Mean density (kg/m3) | Kser (N/mm) |
| ---: | ---: |
| 460 | 2,723.847 |
| 480 | 2,903.406 |
| 500 | 3,086.746 |
| 520 | 3,273.791 |

The resulting density range is approximately 2,723.847 to 3,273.791 N/mm, including
3,086.746 N/mm at 500 kg/m3. The source is the USDA/FPL paper
[Wood Mechanical Fasteners](https://www.fpl.fs.usda.gov/documnts/pdf2016/fpl_2016_rammer001P.pdf),
which reproduces the Eurocode 5 service slip-modulus equation and describes its service region
as approximately 40% of maximum load.

Each value is per bolt and per shear plane. It must not be multiplied by the number of face
contact samples. Mean density at approximately 12% moisture is not interchangeable with the NDS
assigned specific gravity, and these four densities are sensitivities rather than measurements
of the delivered lumber. Hole tolerance must be handled separately.

## Diagnostic clearance dead zone

The script compares the nominal 6.35 mm bolt with a 7.50 mm diagnostic bore. Their diametral
difference is 1.15 mm, corresponding to an ideal centered one-sided travel of 0.575 mm before
shaft-to-bore contact. This is an unselected clearance dead-zone sensitivity, not a specified
drill size or qualified design input. Actual directional slack depends on initial bolt position,
the purchased fastener, drilling tolerance, moisture, and assembly conditions.

## Steel-only axial sensitivities

For each of the ten active bolt grips, the script evaluates `K = EA/L` with a steel modulus of
205,000 N/mm2. It calculates both a nominal 6.35 mm full-shank-area value and a 4.8006 mm
typical-root-diameter sensitivity. The latter is not verified purchased-bolt geometry.

These ten results are steel-only bolt-length sensitivities. They are not joint axial stiffnesses.
The active wood grip is used only as a transparent length assumption. A complete model must also
account for the actual shank and threaded lengths, thread play and engagement, head and nut
regions, washer deformation, preload or snug condition, and clamped-member compliance.

The series-compliance basis follows the
[bolted-joint axial model](https://link.springer.com/article/10.1186/s10086-022-02038-1):

`1/K_joint = 1/K_bolt + 1/K_washer_1 + 1/K_washer_2 + other compliances`

## Uncomputed washer-seat stiffness

Washer-seat stiffness remains uncomputed because the following inputs are not frozen or
qualified:

- purchased-bolt shank, thread, engagement, and free-length geometry;
- threaded tensile-stress area and applicable steel properties;
- washer inside and outside diameters, thickness, material, and bending rigidity;
- radial or tangential grain orientation and wood properties beneath each washer;
- preload or snug-tight condition, gaps, seating, moisture, and load level; and
- member compliance in the selected axial load path.

The published
[washer-embedment study](https://link.springer.com/article/10.1186/s10086-021-01973-9)
supports treating washer deformation separately, but its tested configurations do not supply a
transferable PB02 value for the unfrozen hardware and wood conditions.

## Uncomputed timber face-contact stiffness

The script records the elastic sensitivity form:

`K_face,total = E_normal A_active / L_effective`

If four samples represent one physical face, each sample receives one quarter of the total face
stiffness. Increasing the sample count must not multiply the physical face stiffness.

A value remains uncomputed because PB02 still needs the applicable longitudinal modulus for the
actual lumber, the face normal relative to grain and annual-ring orientation, active contact
area, justified effective compression depth, surface seating and gaps, moisture, creep, and load
level. [USDA Wood Handbook Chapter 5][wood-handbook-5] provides Douglas-fir elastic ratios of
`E_R/E_L = 0.068` and `E_T/E_L = 0.050`, but those ratios do not determine the missing effective
depth or actual contact state.

## Status

The published lateral values can replace arbitrary numbers in bounded sensitivity studies, but
they are not selected PB02 properties. Axial-joint stiffness and face-contact stiffness remain
unqualified and uncomputed. This record provides no structural acceptance and no design,
drilling, procurement, or fabrication release.

[nds-errata]: https://awc.org/resources/2024-nds/
[wood-handbook-5]: https://research.fs.usda.gov/treesearch/62244
