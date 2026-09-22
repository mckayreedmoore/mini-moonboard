# Historical preliminary numerical screen: prior outward-post barrel joints

**Historical research screen only; no pass, load rating, drilling, fabrication,
or climbing release.** This does not analyze the now-published seam-side
center posts or their revised principal/header joint. Its rail and outer-header
figures are conditional constituent references, not a whole-frame assessment.
Run `.venv/bin/python -m scripts.owner_barrel_mvp_preliminary` for the live,
source-built numbers. The script reads the earlier outward-post
`export_owner_barrel_scene.build_viewer_assembly()` with its revised 6 in /
60 mm outer-rail pose and recessed outer-header pose. It does not read the
published scene JSON or change any producer. The 66 panel/kicker and 12 frame
bolt axes remain in the source assembly. The two added kicker backer duties
and the other 22 former-angle duties are outside this screen.

| Current station | Pitch | Barrel center to grain end | Historical scale per row |
| --- | ---: | ---: | ---: |
| `clip_horizontal_lower_right_2` | 32.25 mm | 60.0 mm | 490.1 N |
| `clip_timber_header_outer_right` | 50.0 mm | 70.0 mm | 488.8 N |

Both have two 6.35 mm shaft envelopes and 10.0076 mm barrel envelopes. At the
rail, 152.4 mm shafts reach assumed barrel centers by 1.849 mm and leave
5.155 mm to modeled bore caps. At the recessed header, 127 mm shafts extend
23.9 mm past assumed centers, **18.9 mm past barrel far walls**, and now have
**4 mm nominal clearance** to the revised modeled bore caps. This is not
verified delivered tip clearance. Header counterbores are 25.4 mm OD
and 6.651 mm deep; their nominal edge-to-edge gap is 24.6 mm.

The scale calculation is `|F|/2 + |M|/pitch`, using force and moment from the
**same** historical ML24Z beam-flange case. It supposes two point reactions
and assigns the full moment norm to that pair. The old angle topology, contact,
and stiffness differ. This is a scenario size for prioritizing investigation,
**not an actual or conservative bound on barrel-joint demand**. No new-topology
signed joint actions or load sharing are available; no utilization is computed.
The rail's `k12-rear` source has 99.59 N and 14.201 N·m; the header's
`k12-right` source has 589.42 N and 9.706 N·m.

## Conditional constituent numbers

The repository's [2024 material record](../bolted-candidate-material-basis.json)
specifies dry, unincised US DF-L No. 2 dimension lumber: `Ft = 575 psi`,
`Fc⊥ = 625 psi`, `E = 1.6 million psi`, and assigned `G = 0.50`, all
unadjusted. Actual stock, moisture, grade, dimensions, cuts, and contact remain
unverified. [AWC's 2024 Supplement][supplement] must be used with the matching
NDS edition; the [2024 NDS errata][errata] confirms the DF-L specific gravity
input. Existing 2024 helpers supply the calculations below.

- Ideal 25.4 mm OD washer annulus over a 7.5 mm modeled bore, at
  `Fc⊥ = 625 psi`: **1.993 kN per bolt**. This requires full, stiff, sound
  perpendicular-grain contact. Washer bending, prying, preload, adjustments,
  and other axial-chain failures are omitted. This is not barrel/bolt capacity.
- Isolated 38.1 × 139.7 mm receiving-member section with two hypothetical
  **full-through** 10.0076 mm barrel-width slots, at `Ft = 575 psi`:
  **18.08 kN section reference**. Parallel-grain tension only; neighboring
  holes, splitting, stress concentration, actual blind cuts, interaction and
  adjustments are omitted. This is not joint capacity or a lower bound for the
  actual cut member.
- DF-L dowel-bearing inputs for a nominal 6.35 mm dowel: **5,600 psi parallel;
  4,450 psi perpendicular**. Inputs only. The bolt aligns with grain in the
  receiving rail/post. The ordinary two-member lateral-yield helper rejects
  that configuration and cannot rate the barrel.

The modeled barrel-body ligaments to the grain end are **55.0 mm** at the rail
and **65.0 mm** at the post. Nearest modeled barrel-body edge ligaments are
**42.45 mm** and **35.70 mm**, respectively. These are CAD distances, not
minimum-placement or splitting approvals. The header counterbore also cuts
the *other* member; its local net section is not included in the 18.08 kN
post sensitivity.

## Stiffness sensitivity

For a hypothetical steel-only axial path, `K = E_steel πd²/(4L)` with
`E_steel = 205,000 N/mm²`, and the CAD head-side-to-assumed-barrel-center
lengths of 150.551 mm (rail) and 103.1 mm (header):

| Per bolt | 6.35 mm full-area sensitivity | 4.8006 mm typical-root sensitivity |
| --- | ---: | ---: |
| Rail | **43.12 kN/mm** | **24.65 kN/mm** |
| Header/post | **62.97 kN/mm** | **35.99 kN/mm** |

The typical root and steel modulus are **assumptions**, not verified product
properties. Under a bolt-only tensile path, seat, thread, wood and barrel
compliances add in series, so these steel-only figures are optimistic
conditional ceilings for their assumed areas and lengths. Compression face
contact could follow another path. No complete axial stiffness is supportable.

The [corrected 2024 NDS §11.3.6.1][errata] wood-to-wood group-action slip
parameter is 3.94 kN/mm per 1/4 in bolt (`180000 D^1.5 lb/in`). It is a
**comparison only**: neither barrel joint is an ordinary qualifying
wood-to-wood dowel group and it is not a service spring or measured stiffness.
The nominal 7.5 versus 6.35 mm bore has 0.575 mm centered radial clearance;
actual seating, initial bolt position, threads, and cyclic slip are unknown.

## Decisions still needed

- Solve signed forces and moments at these *new* joint stations for the
  adopted load cases, with contact and unequal sharing between the two rows.
- Obtain controlled delivered bolt/barrel/thread geometry and part properties.
  In particular, resolve the header's 18.9 mm barrel far-wall overrun and
  tolerance-sensitive tip clearance before treating its nominal stack as
  installable.
- Check the complete axial and lateral chain: steel and threads, barrel wall,
  barrel-to-wood bearing and breakout, head/washer seating, split and net
  sections of both members, group action, installation tolerance, and repeated
  assembly stiffness. Use complete-joint evidence where a defensible
  component model is unavailable.

No barrel or thread resistance is inferred from bolt grade, and no two-bolt
sum or apparent comparison with the historical scale is a pass. No one was
contacted.

[supplement]: https://awc.org/resources/2024-nds-supplement/
[errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
