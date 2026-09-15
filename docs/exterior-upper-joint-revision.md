# Exterior knee: bounded upper-joint correction

The corrected, collocated floor-friction model produced a valid A12-left response for the original exterior knee. It identified two local hardware shortfalls: upper bolt lateral demand/reference 1.02862 and upper washer bending 1.59492. Member checks did not require larger legs or additional braces.

The next exterior-only revision retains two half-inch upper bolts per leg and all exterior knee stock. Upper bolt pitch increases from 56 to 64 mm along the existing grain-angle bisector. The leg top projects 24 mm normal to the inclined rim instead of 18 mm, providing wood above the wider pattern. This is a fresh-stock layout: the former 56 mm holes are not retained. Existing floor-rail and inboard-knee designs remain separate.

## Washer procurement condition

The four upper bolt stacks retain modeled round washers, nominal 1⅜-inch OD, 9/16-inch hole and ⅛-inch thickness. Require **3.0–3.3528 mm delivered thickness** for each of their eight washers. Ordinary USS washers meeting only the preceding 2.1844 mm minimum do not satisfy this revision.

The assessment retains its conservative 34.7472 mm outside diameter, 14.6558 mm hole, 33 ksi steel yield reference and 1.67 washer bending factor. It does not credit a higher material grade, stacked thin washers, bolt preload or composite washer action. The 3.0 mm minimum and retained 3.3528 mm maximum are explicit purchasing/acceptance conditions, not tolerances inferred from a nominal ⅛-inch catalog description. Supplier dimensions and material must satisfy this stated envelope.

The nominal CAD washer was already 3.175 mm thick, so this correction changes the required delivered minimum rather than enlarging the viewer's washer. The maximum retains the existing [bolt seating and thread/runout envelope](compact-half-inch-hardware.md). Require the specified plain shank at the shear plane; arbitrary fully threaded substitutions do not inherit the pass. The full-root sensitivity is 1.43044 and is not the adopted plain-shank detail.

## Validation

Fixed-wrench arithmetic predicts a lateral ratio near 0.966 at 64 mm pitch; it is only a trial-selection calculation. The changed bolt positions and leg top require fresh actual-CAD receiver checks and assembled-frame analysis under all six current load cases. No load reduction or increase in duration factor is adopted. Current results are recorded in the [contact verification](exterior-knee-contact-verification.md).

The fresh revised A12-left case now meets all 25 listed conditional criteria, including the added leg-foot normal-bearing check. Its actual lateral ratio is **0.985043**, washer bending **0.757756**, and minimum directional edge/end margin **1.563 mm**. The assembled-frame result differs from the fixed-wrench prediction; the fresh result governs. A12-rear and A12-forward also meet all 25 criteria, with bolt ratios 0.707702 and 0.942397. All six current load cases now meet all 25 listed criteria. K12-right, K12-rear and A1-rear have bolt ratios 0.969421, 0.698719 and 0.095861. The revised exterior is the selected conditional candidate; the explicit hardware, material, load and assumed-floor limits remain.

## Contact-grid sensitivity and foot bearing

A fresh 5×5 leg-foot grid retains the same total support stiffness, material basis, A12-left load and assumed μ = 0.4. All 25 listed criteria pass. The actual upper-bolt ratio decreases from 0.985043 (3×3) to 0.961255 (5×5), so the coarse-grid joint result remains the more demanding of these two checks. This is a stable pass decision across two grids, not a claim of converged local contact pressure.

The new foot check verifies the actual horizontal footprint and every contact cell. It evaluates normal pressure using NDS §3.10.3 with the existing dry DF-L No. 2, CD = 1 basis: Fc* = 1485 psi (without column-stability reduction), Fc⊥′ = 625 psi, and bearing-length factor 1. The leg grain is 13.8365° from vertical; the resulting normal-bearing reference is 1376.66 psi. [NDS Appendix J.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210113_AWCWebsite_Appendix.pdf) uses the component normal to the bearing surface for this comparison; horizontal friction is not added to that normal pressure.

Peak normal-bearing ratio increases from 0.203852 to 0.569322 with refinement; both pass. The 625 psi perpendicular-grain-only screen is retained as a conservative diagnostic, not substituted for the actual-grain calculation. Existing member shear/combined-stress checks remain. This additional check covers normal timber bearing, not measured floor pressure, local friction-traction stress fields or physical floor qualification.
