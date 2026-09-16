# Selected flush-top commercial-angle options

Date: September 15, 2026. Candidate:
`compact-spliced-flush-top-development`.

## Decision

The current public Simpson and evaluation-report material does not provide a
catalog-only larger-angle or larger-screw substitution that closes the retained
ML24Z gate. This search is complete. The design remains held at the commercial
angle gate; it is not held by the purchased panel screws.

The missing item is an applicable connection-system resistance, not screw
length or a small numerical overload. The six-case demand ledger records a
maximum listed-force interaction of 0.615121, but the eight bearing-like
stations all see positive F2 separation in at least one case and all 24 angles
carry an unresolved force-parallel couple in at least one case. The envelope is
240.815 N (54.14 lbf) separation and 16.340 N·m (144.62 in-lbf) couple.

## Public product search

| Route | Published information | Disposition |
| --- | --- | --- |
| ML26Z, ML28Z or ML210Z | Same 12-gauge, 2-inch-leg ML family and specified SDS25112 screws; added length and screw count. The current supplemental table still shows no bearing-installation F2 value and gives no moment/couple rating. | Does not close the missing action. |
| Longer/larger screw in an ML angle | The published ML assemblies specify SDS25112. | Unlisted substitution; cannot inherit the connector values. |
| A34 or GA angle | Published uplift and translational F1/F2 values exist for defined installations, but no independent moment/couple rating. Configuration, member-thickness and installation limits are not the current 24-station detail. | Possible redesign component, not a drop-in qualification. |
| HSLQ angle | Uses larger 1/4 × 2 1/2-inch SDS screws, but is for a larger member and a defined in-plane application. | Wrong geometry and load applicability. |
| RCKW knee-wall connector | The catalog gives an explicit moment value, but only for its prescribed post/sill and concrete-anchor assembly. | Not an applicable wood-to-wood replacement. |

The catalog's simultaneous-load equation combines rated translational actions.
It has no term that turns an unrated connection couple into a rated action. A
larger published force value therefore cannot be used as a moment value.

Sources:

- [Simpson 2026 Wood Construction Connectors catalog](https://ssttoolbox.widen.net/view/pdf/orplhjaqw1/C-C-2026.pdf?t.download=true)
- [Simpson ML angle supplemental load tables, L-C-MLZ25](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
- [IAPMO UES ER-280](https://forms.iapmo.org/ues_reports/reports/er_0280.pdf)

## Smallest completion routes

1. Keep the exact ML24Z/SDS25112 assembly and obtain written Simpson or
   connection-designer applicability for the full ledger actions, including
   bearing F2, force application lines and residual couple. This preserves the
   current geometry, stiffness and six authenticated global cases.
2. Perform a complete mechanics qualification of the unchanged assembly. This
   is not a screw-capacity lookup: it requires validated flexible-angle,
   screw-head/plate seating, prying, nonlinear wood embedment, combined
   shear/withdrawal, splitting and contact redistribution. The present rigid
   angle and linear spring response is not that resistance model.
3. Redesign each affected connection so its moment is resolved into separately
   rated translational load paths at a known spacing. That requires exact CAD,
   receiver and spacing checks, an updated stiffness representation, six fresh
   affected assembled cases, regenerated evidence and independent review.

Route 1 is the rush-to-MVP route because it is the only route that can close the
gate without changing the assembly or rerunning the structure. If no written
applicability is available, route 3 is the defensible no-call route; merely
buying a larger ML angle or screw is not.

## Ready-to-send technical question

For the exact ML24Z with six SDS25112 screws at each station, please confirm
whether the published connection values apply with concurrent listed-force
interaction up to 0.615121, positive bearing-installation F2 separation up to
240.815 N (54.14 lbf), and an independent force-parallel loaded-flange couple
up to 16.340 N·m (144.62 in-lbf). Please identify the rated force application
lines and any required interaction equation, installation restriction or
separate engineered check. The per-case/per-station forces and moments are in
[`compact-spliced-flush-top-angle-ledger.json`](compact-spliced-flush-top-angle-ledger.json).
