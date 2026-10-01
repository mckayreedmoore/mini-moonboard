# Independent review — timber-bolt M–N–V attempt08

**Verdict: supported within its stated source boundary.** The two papers give
a serious M–N–V method lead for defined steel-plate–wood dowel connections, but
do not establish a complete or validated method for the reviewed timber-only
through-bolts. The review found no substantive source or applicability error.

## Scope and checks

I reviewed the frozen attempt08 packet and reran its verifier and checksum
list. The verifier now passes for four terminal files, 35 immutable source
pins, and five `SHA256SUMS` entries. The first check in this review caught a
stale README digest in `terminal-hashes.json`; after the producer-reported
regeneration, both the terminal manifest and `SHA256SUMS` match current bytes.
That integrity mismatch was transient and is not a remaining source or scope
finding. This review did not edit attempt08 or any pinned file.

I read the full KIT 2018 chapter and WCTE 2025 paper through the publisher or
institutional PDF viewers and checked their repository metadata. No publisher
PDF bytes were downloaded locally or hashed. Input packet hashes and the
current verifier results are in [`review-record.json`](review-record.json).

The key source statements are accurately bounded:

- **Blaß 2018, Eq. (8), printed p. 20:** the approximate circular-section
  interaction is `M/My + (N/ftens + V/fshear)^2 = 1`. The chapter says to check
  it at every location along the fastener axis. Its derivation partitions the
  circular section for a specified thick-plate, single-shear Johansen mechanism
  in a steel-sheet–wood connection. It couples section limits to a lower-bound
  connection model and Eurocode 5 characteristic resistance `Fv,Rk`.
- **Bolts are included in analysis, not in the reported validation tests.**
  Blaß’s parameter study includes class 5.8 bolts at 12, 16, and 20 mm with
  90 mm timber thickness. Those are analytical cases. The chapter’s own
  connection tests concern profiled nails in beech LVL; its other comparison
  uses earlier steel-sheet–wood dowel tests. It does not report validation
  tests for the modeled bolts.
- **The thread/root question remains open.** Blaß obtains bolt/dowel nominal
  yield and tensile strengths from declarations or tensile tests and cites
  EN 1993-1-8 for bolt/dowel shear, including distinct shear ratios for shank
  and threaded planes. The text does not give a thread-root or tensile-stress
  area rule for the interaction’s tensile term, a root/shank rule for `My`, or
  a threaded-transition check. The shear reference alone does not supply
  those missing section rules.
- **Kuck et al. 2025, Eq. (1), printed p. 2835:** repeats the criterion as a
  *possible* criterion attributed to Blaß, using
  `M/My + (V/Fshear + N/Ftens)^2 ≤ 1.0`. Its connection tests are double-shear
  steel-to-timber joints with 10 mm outer steel plates, a nominal 0.5 mm gap,
  6 mm solid copper, aluminium, C15 steel, or silversteel dowels, and beech LVL
  or DVW. The studied M–N–V action comes from fastener inclination under
  lateral loading. It is not a direct axial-load test of a headed, threaded
  bolt in a timber-only grip, and it does not validate Eq. (1) for that target.
- **Restraint and embedment assumptions are specific and questioned.** For
  straight-axis M–V, Eq. (2) estimates shear-plane moment assuming the dowel is
  clamped in outer steel plates. The discussion says this may overestimate
  moment and questions both full clamp restraint and uniform embedment stress.
  The tests initially used gaps to avoid plate friction, but the authors say
  embedment deformation could close the gap; friction could not be ruled out.
  The normal-force magnitudes also remain uncertain.
- **No U.S. design-format transfer is supplied.** The KIT model uses Eurocode 5
  connection equations and EN 1993-1-8 for bolt/dowel shear. The WCTE study
  uses Eurocode comparisons and tested dowel properties. Neither provides a
  conversion to U.S. design strengths, factors, load combinations, NDS transfer
  rule, or this project’s acceptance basis.

The packet therefore correctly says that a potentially relevant model exists
for a defined steel-plate–wood dowel joint, while applicability to the reviewed
wood-to-wood through-bolts is not established. The papers do not prove that no
other method exists. No capacity was calculated and no method, criterion,
hardware, candidate, geometry, or solver state was changed.

## Primary source records

- [Blaß 2018 KIT record](https://publikationen.bibliothek.kit.edu/1000086376) and
  [full chapter PDF](https://publikationen.bibliothek.kit.edu/1000086376/18283247).
  KIT identifies a 2018 proceedings contribution, pp. 17–26, DOI
  `10.5445/IR/1000086376`, published by KIT Scientific Publishing.
- [Kuck, Sandhaas, and Blaß 2025 KIT record](https://publikationen.bibliothek.kit.edu/1000183153)
  and [full proceedings PDF](https://www.proceedings.com/content/080/080513-0346open.pdf).
  KIT identifies a 2025 WCTE proceedings contribution, pp. 2834–2840, DOI
  `10.52202/080513-0346`.

Exact peer-review status for either contribution was not independently
authenticated; attempt08 correctly avoids describing either as peer-reviewed.
