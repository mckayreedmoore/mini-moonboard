# Historical prose pin and numeric geometry dependencies

The existing face atlas remains byte-preserved. Its recorded 217-source
closure contains one changed live file:

- Path: `docs/wood-joints-mvp/criteria-method-map.md`.
- Recorded hash: `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`.
- Current and HEAD hash: `bd356fc8751e17c860fd6df8150c3076b9cfbd742fff9b0de518b970868f324a`.

The three Git revisions of this file available in the current checkout do
not reproduce the recorded hash. This audit therefore makes no assertion
about the exact former prose and does not claim the historical full closure
or its public verifier passes. The mismatch is `STALE_PROSE_INPUT` and the
historical exact-closure status is `REFUSED`. No upstream pin is rewritten.
The primary's October 1 bolt-source wording reconciliation is a separate
additive note; it did not cause this change.

The current packet authenticates the existing atlas artifact itself and
all unchanged numerical source bytes. The dependency distinction follows
the pinned source code:

1. `scripts/wood_joint_wj08_overlap_contact_geometry.py` includes
   `METHOD_MAP_REL` in `PINNED_INPUTS`. Its
   `_load_and_check_pinned_inputs` loop reads file bytes only to check their
   hashes. Subsequent semantic inputs are criterion, coverage and candidate
   JSON. It does not parse the method-map Markdown for geometry or numbers.
2. The later overlap-attempt producers inherit this pin and source
   metadata. The atlas's `_current_source_hashes` carries the inherited
   hash through the overlap evidence. This inherited guard would refuse a
   fresh historical full replay under the changed prose; this audit does
   not call or bypass that historical verifier.
3. The atlas's `_build_current` reads the frozen graph, overlap evidence,
   finished-solid descriptor and attempt04 manifest, then imports the
   pinned STEP solids. `source_face_records`, `_intersection_regions` and
   `collect_opposed_face_pairs` compute face signatures and overlaps from
   those shapes. The method-map Markdown supplies no numeric geometry.
4. This new audit reads only the authenticated saved signatures. It
   validates face hashes, STEP bindings, graph joins, outline edges,
   circular holes and reconstructed areas before analytic projection.
   It performs no CAD import, geometry rebuild or native solve.

All of these producer files, the atlas and its recorded pin manifest, STEP
files and numerical JSON inputs are bound in the new live source closure.
Each original upstream binding remains associated with its expected hash.
Only the exact known prose expected/current pair is permitted as a recorded
stale input. Any other changed file, or another change to this prose, stops
the audit. Current criterion authority and the current edge-obligation
document are pinned separately. Their pending status and the absence of a
blanket continuous-direct-backing requirement remain explicit.

This is reuse of authenticated numerical evidence with a disclosed
historical provenance limitation. It is neither a historical full-closure
pass nor an adopted criterion, load-path or mechanical acceptance.
