# a12-forward selected-floor normal-law screen, attempt 01

This read-only packet screens all 100 unchanged SPRINGA floor-normal laws at every recorded increment of the terminal, case-bound a12-forward selected-floor run. It reuses the exact pinned `audit_springa` and `_strict_normal_branch_check` methods with their conservative printed-token interval treatment. The producer does not run CalculiX.

The original 35/65 proposal is rejected by the observed branch: across 7 recorded increments the stable normal-law mask is 31 strictly positive, 69 strictly separated with zero endpoint RF, and 0 interval ambiguous or noncomplementary. The source selected set has 6 cells that no longer screen strictly positive; 2 originally inactive cells screen strictly positive, including `floor_base_floor_left_1` / `SPR1026`. Every cell’s displacement, geometric elongation, spring force, endpoint internal force, and endpoint RF intervals are recorded per increment in `screen.json`.

This identifies the case-specific support incompatibility only. No replacement mask, new input, accepted force, corner demand, or solver run is included. The branch remains diagnostic and cannot support demand adoption.
