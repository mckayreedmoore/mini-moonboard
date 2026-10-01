# Current group-action-factor method — attempt01

Status: **method implementation and published-example check only**. This
artifact computes no candidate Cg, bolt capacity, demand/capacity ratio, or
criterion disposition. `additional_group_reduction_sensitivity` remains
pending, and every method-only synthetic result is explicitly non-acceptance
evidence.

## NDS basis and applicability

The method is based on the official AWC [2024 National Design Specification
(NDS), Chapter 11][nds-ch11], printed p. 72, §§11.3.6.1–11.3.6.3, Eq. 11.3-1,
and printed p. 73, Table 11.3.6A. The current AWC consolidated [errata dated
March 23, 2026][nds-errata] includes the January 2025 correction for §11.3.6.1
and confirms the corrected wood-to-wood `γ = 180,000 D^1.5 lb/in` and
wood-to-metal `γ = 270,000 D^1.5 lb/in`. The 2024 chapter PDF prints the
exponent imperfectly; the current errata is the controlling correction. The
evaluator implements only the wood-to-wood branch. Any metal side member
returns pending; no wood-to-metal factor is inferred.

Eq. 11.3-1 is evaluated as:

```text
R_E = min(E_s A_s / (E_m A_m), E_m A_m / (E_s A_s))
u   = 1 + γ s/2 (1/(E_m A_m) + 1/(E_s A_s))
m   = u - sqrt(u² - 1)
C_g = [m(1 - m^(2N)) /
       {N[(1 + R_E m^N)(1 + m) - 1 + m^(2N)]}]
      [(1 + R_E)/(1 - m)]
```

The implementation uses the numerically equivalent `m = 1/(u + sqrt(u²-1))`.
For dowels with `D < 1/4 in`, §11.3.6.1 sets `C_g = 1`; at exactly
`D = 1/4 in`, the equation applies. `A_m` is the main-member gross section
area, and `A_s` is the sum of gross side-member areas. Net-section deductions
are excluded from these terms. When a member is loaded perpendicular to grain,
§11.3.6.3 instead specifies equivalent area equal to member thickness times
the overall width of the fastener group. For a single row, §11.3.6.3 defines
that width as the minimum spacing parallel to grain; in this method's uniform
single-row scope, the supplied width must equal the computed pitch within
numerical geometry tolerance. The API also requires member thickness and
checks that the equivalent area is exactly their product. The coordinator
must bind these dimensions to the actual member and group geometry.

§11.3.6.2 limits a dowel row to two or more same-diameter fasteners loaded in
single or multiple shear and aligned with the load direction. The evaluator
requires an independently source-bound fastener inventory and action case,
checks that every fastener lies in one straight line at uniform pitch, and
checks that the signed lateral resultant is parallel or antiparallel to that
row. It supports one main member plus one or more wood side members only when
all side members have the same modulus. The independent `member_sections`
binding must enumerate the main member ID, ordered side-member IDs, and shear
plane count; the payload must match them, with one side member per shear plane.
This source-bound roster is the applicability evidence for the supported
single/multiple-shear equations. It does not infer member roles, member grain,
a row, a load direction, or a side-member modulus.

Adjacent-row/stagger treatment is intentionally unsupported. NDS §11.3.6.2
combines adjacent rows when the row offset is less than one-quarter of the
parallel-to-row distance between closest fasteners; for an even row count it
applies the rule to each pair, and for an odd row count it requires the most
conservative interpretation. This attempt does not classify those cases or
choose an interpretation: all multi-row and staggered layouts return pending.
Nonuniform pitch, oblique action relative to a row, oblique load-to-grain
orientation, mixed fastener diameter, D above 1 in, different side-member
moduli, unbound inputs, or nonwood connections also return pending.

The method applies `C_g` to reference lateral design values only. It does not
calculate a lateral resistance, a complete wood-joint resistance, group force
sharing, individual fastener actions, axial/shear interaction, or a criterion
ratio. The current criterion's adopted demand/capacity comparison and its
required sensitivity scenario set remain unresolved. The sensitivity helper
reports a Cg-only ratio for two separately bound inputs only after receiving a
coordinator-reviewed scenario contract and a separate expected contract
binding from the upstream coordinator. The contract declares `sha256` as the
SHA-256 of its complete strict-JSON content with only the `sha256` field
excluded to avoid self-reference. Every other contract field is included,
including review status, classification, scenario identities, and exact
changed JSON input paths. The evaluator recomputes that digest and requires it
to match both the contract's declaration and the separately supplied
coordinator binding. It then checks the listed paths against the actual
scenario changes. Altering contract terms while retaining the digest tokens
returns pending. The evaluator does not establish review authority itself.
This Cg-only ratio is not the criterion's `≤ 1.0` acceptance ratio.

## Implementation and checks

Maintained implementation: [`mini_moonboard/nds_2024_group_action.py`](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py).
Focused tests: [`tests/test_nds_2024_group_action.py`](/home/mckay-linux/repos/mini-moonboard/tests/test_nds_2024_group_action.py).

The input API takes a group payload plus `expected_bindings` supplied
separately by an upstream independent source manifest. It matches the source
IDs and SHA-256 values for geometry, member sections, fastener product, and
load cases before returning a factor. It also requires a separately supplied
`expected_payload_sha256`. This digest is over the complete payload mapping,
not a producer-selected field list: all IDs, source bindings, fastener array
order and coordinates/diameters, action and grain vectors, member IDs,
sections, orientations, elastic moduli, shear planes, and any other supplied
payload fields are included. The reproducible v1 byte rule is UTF-8 JSON with
recursively lexicographically sorted string keys, compact `,`/`:` separators,
unescaped Unicode, and finite JSON numbers only; array order is retained.
Python-only values (including tuples and non-string mapping keys) are rejected.
`canonical_group_record_sha256()` implements that rule. The upstream
coordinator must compute the expected digest from its frozen independent
record, then pass it separately; the evaluator recomputes and requires an
exact match before evaluating. The method validates format and equality only:
it cannot prove that the caller's expected manifest or digest is authoritative.
The synthetic tests exercise mismatch mechanics and do not claim independent
source authority. Missing or mismatched bindings or digest cannot produce
`C_g`.

The canonicalizer's full payload rule deliberately binds incidental fields as
well as factor inputs, so schema extension changes require a new expected
digest. Its documented JSON serialization is a versioned local byte contract,
not a claim of standards-based JSON canonicalization. Establishing, reviewing,
and preserving the independent manifest/digest remains an upstream authority
responsibility outside this evaluator.
The legacy `fea.reinforced_timber_resistance.group_factor()` is not imported
or reused, and its example defaults do not enter this API.

The primary published known-answer check uses Table 11.3.6A at `D=1 in`,
`s=4 in`, `E=1,400,000 psi`, `A_s=5 in²`, and `A_s/A_m=0.5` (so
`A_m=10 in²`). The independent Eq. 11.3-1 evaluations for `N=2,3,4` are
0.9766839378, 0.9163482163, and 0.8371926374, rounding to table entries
0.98, 0.92, and 0.84. A separate synthetic exact check verifies the NDS
two-fastener, equal-EA case gives `C_g=1`. Negative checks cover row
alignment, geometry, group layout, grain orientation, source bindings,
member inventory, sensitivity-contract gates and content tampering, and
independent group-payload digest tampering of geometry, diameter, elastic
modulus, and action while retaining source references. The focused suite has
27 passing tests.

The sensitivity unit-test contract is a synthetic fixture only; its
`coordinator_reviewed` token does not represent a real review or authorize
current-candidate use. Tests pass a distinct expected binding and verify that
the content digest excludes only the contract's `sha256` field; a mutation of
`changed_input_paths` with both hash tokens preserved fails closed.

Run the focused suite:

```sh
.venv/bin/pytest -q tests/test_nds_2024_group_action.py
```

## Current-revision inventory

[`current-group-action-pending.json`](current-group-action-pending.json) is a
read-only status record for the current revision. The frozen coverage source
lists 92 candidate bolt axes and 460 installed hardware components, while
stating that it has no candidate group factors or bolt-group actions. Those
axes are not a complete grouped-row inventory. The record emits `cg: null`
because current row groups, member section/grain/modulus inputs, current
fastener mapping, signed lateral group actions, and an independently reviewed
sensitivity scenario and full-record digest are unavailable. The current
pending inventory requires a coordinator-frozen payload and its separately
calculated expected digest; no digest is inferred from producer input.

The coverage file retains its historical method-map digest. The separate
current source overlay and parent review reconcile that hash provenance only;
they do not resolve this method's missing inputs or accept a group factor.
The current method-map source digest, frozen coverage digest, current geometry
references, overlay, reviewer status, and AWC PDFs are captured in
[`source-pins.json`](source-pins.json). No frozen criterion, map, geometry,
action result or capacity record was edited.

## Exact next consumer

The next consumer is WJ-08/T06's current group-action evaluator after an
independent, coordinator-frozen input manifest provides every new and retained
group's exact centers, row classification, fastener products, member section
and grain properties, and fresh signed case actions. That consumer must also
bind the reviewed sensitivity-case contract and combine Cg with applicable
lateral resistance and demand results. Until those bindings and calculations
exist, `additional_group_reduction_sensitivity` remains pending.

[nds-ch11]: https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf
[nds-errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
