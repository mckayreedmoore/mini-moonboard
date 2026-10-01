# T06 AISC 360-22 bolt-method boundary — attempt07

**Status: `steel_direct` remains unresolved.** The current issued AISC
Specification gives separate bolt tension/shear provisions and an interaction
for combined tension and shear in bearing-type connections. The reviewed text
does not give a bolt bending term or a combined bolt-section tension, shear,
and bending rule. Its stated scope is structural-steel systems defined through
ANSI/AISC 303-22; that scope does not establish application of its connection
provisions to a through-bolt whose grip and connected members are timber.

This screen preserves the distinction between a possible steel-only bolt
section check and a complete timber-grip connection method. ANSI/AISC 360-22
§J3.7 may be a reference for separate bolt tension/shear component strengths
if an independent applicability basis and actual bolt identity are supplied.
§J3.8 covers only the tension–shear combination for bearing-type connections.
Neither clause is a bolt-bending resistance method. §J4.5 concerns flexural
strength of affected/connecting elements; Chapter H concerns members. They do
not fill the bolt-section bending term or provide an N+V+M interaction for this
timber joint.

## Edition and source boundary

As of the review date, 2026-09-28, AISC identifies ANSI/AISC 360-22 as the
issued standard and lists January 2025 errata for its first printing. AISC's
next-edition 360 public-review draft opened September 11, 2026 and closes
October 26, 2026; it is a draft and is not treated here as the current issued
standard. AISC 360-22 is dated August 1, 2022. The current scope cross-reference
is ANSI/AISC 303-22 §2.1. The January 2025 303-22 errata corrects §1.12 on
printed p. 16.3-7 and does not list a change to §§2.1–2.2.

The exact clause locations, source URLs, and retrieval limits are recorded in
[`source-observations.json`](source-observations.json). AISC's current-standard
and errata pages plus its standards PDFs were not directly downloadable in this
review: direct page/PDF opens returned HTTP 403, and the exact
`vpn2.modernsteel.com` 360-22 PDF timed out. Clause content was checked using
search-indexed extracts tied to AISC-published PDFs and an AISC-authorized
publication preview for pagination. No external PDF bytes or PDF SHA-256 are
claimed. This is weaker than a byte-pinned full-standard review and is retained
as an explicit limitation.

## Clause observations

- **360-22 §A1, printed p. 16.1-1:** applies to structural-steel systems and
  refers to structural-steel elements as defined in 303-22 §2.1. The AISC
  language allowing tests or analysis for conditions not covered is subject to
  AHJ approval; it is not a transfer rule for timber-grip bolts.
- **360-22 §J3.7, printed p. 16.1-496:** “Tension and Shear Strength of Bolts
  and Threaded Parts.” The section uses the nominal unthreaded body area `Ab`
  and Table J3.2 bolt stress values for its stated tension/shear limit states.
  That can inform separate steel-bolt component references only after the
  actual product, section, and applicability are established.
- **360-22 §J3.8, printed p. 16.1-499:** “Combined Tension and Shear in
  Bearing-Type Connections.” Its interaction is tension plus shear. The
  interaction modifies nominal tensile stress as a function of required shear
  stress; it has no bolt bending moment term. The AISC v16.0 Design Examples,
  Example J.3, likewise demonstrates a steel bearing-type bolt tension/shear
  check, not a timber-grip or N+V+M design.
- **360-22 §J4.5, printed p. 16.1-508:** “Strength of Elements in Flexure.”
  This is an affected/connecting-element flexural-strength provision, not an
  identified bolt-shank bending provision. Chapter H's combined-force clauses
  address structural members, not individual bolts.
- **303-22 §§2.1–2.2, printed pp. 16.3-8–9:** §2.1 defines structural steel
  through elements of a structural frame shown and sized in design documents
  and essential to support design loads; its connection materials and
  fasteners are for structural-steel items. §2.2 excludes other steel, iron,
  or metal items not described in §2.1, even if shown or attached to the frame.
  A wood-to-wood timber through-bolt is not made an AISC structural-steel
  connection by its metal material alone.

## Finding and next source route

The available AISC material does **not** establish a complete, applicable
steel bolt-section N+V+M method for this timber-grip through-bolt. The exact
scope boundary is “not established by these sources,” not “no engineering
method exists.” Do not compose §J3.7/§J3.8 with §J4.5 or Chapter H and treat
that combination as an approved method without an explicit applicability and
mechanics basis.

Next, obtain the official ANSI/AWC NDS-2024 References pages through AWC's
2024 NDS viewer and authenticate whether references 39–41 match the provisional
transcription in attempt03/05. Then review official NDS-2024 §11.2.3 together
with the complete cited source texts for an explicit transfer rule that covers
a non-steel timber grip and bolt bending. Attempt06's official AWC TR-12-2026
screen remains a separate lateral-yield source question: its indexed excerpts
did not resolve axial bolt tension or N+V+M. If those AWC sources do not state
the required scope and interaction, the remaining route is a source-backed
timber through-bolt mechanics/design method with a specified bolt section,
thread/shank basis, bending span/restraint, simultaneous actions, strength
format, and independent benchmark. Keep timber bearing, splitting, group
effects, and complete-joint load transfer as distinct checks.

This packet calculates no capacity, selects no bolt, adopts no method, changes
no criterion disposition, and modifies no prior attempt, criterion, method
map, geometry, hardware, candidate, or solver state. No native or solver run
was made. The mutable task queue is deliberately not frozen as a source.

## Integrity and reproduction

`terminal-hashes.json` binds this README, the source observations, and the
verifier. `SHA256SUMS` provides the same terminal file checksums in standard
format. Reproduce the local integrity and context-pin checks with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-direct-screen-attempt07-aisc-2022-boundary-2026-09-28/verify_source_packet.py
```

The verifier does not claim to fetch or authenticate external AISC PDFs; their
retrieval limitation is part of the source record.
