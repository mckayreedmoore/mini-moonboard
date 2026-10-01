# NDS-2024 group-action applicability for four-plus members — audit attempt01

Status: **source-bound normative audit; four-plus-member application remains
unresolved and must fail closed**. This is a method-scope finding only. It
adds no current group factor, resistance, demand/capacity ratio, or criterion
disposition. No geometry or candidate evidence was edited, and no native
mechanics run was made.

## Exact maintained method examined

The maintained evaluator is
[`mini_moonboard/nds_2024_group_action.py`](../../../../../mini_moonboard/nds_2024_group_action.py),
SHA-256 `2fb1a905a2e65a7ad9d2e6f8199b682e9b50a423474654301c825f13802d200e`.
Its pinned focused tests are
[`tests/test_nds_2024_group_action.py`](../../../../../tests/test_nds_2024_group_action.py),
SHA-256 `29f5f5cbf52be2df3eaca26505c282a597262bd405c232bdea32a369f90c1085`.
These are the same byte pins recorded in `current-group-action-method-attempt01`.

The evaluator accepts one main member and any positive number of side members,
requires all side-member moduli to match, forms one `E_s A_s` using the sum of
all side gross areas, and returns one `Cg`. Its member binding defines one
side-member ID per shear plane. The current tests cover one side member and
two side members (three total members); none covers four or more total
members.

## Authoritative 2024 text and limits

The official AWC [NDS-2024 Chapter 11 PDF][ch11] is pinned at SHA-256
`774d13c8a92cb8bfa876c45044fc40e8c3a90b1e3513075ed64626d5988f027d`.
Printed page 72, §§11.3.6.1–11.3.6.3, gives Eq. 11.3-1, defines `A_s` as the
sum of the gross cross-sectional areas of side members, and defines a row to
include same-diameter dowels loaded in single or multiple shear and aligned
with load. Section 11.3.6.3 requires gross, not net, areas. This normative
text is consistent with an aggregate-side-area calculation for multiple
shear; by itself it does not state how the factor is to be evaluated for a
connection with four or more members.

The current AWC [consolidated 2024 NDS errata][errata] is pinned at SHA-256
`b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0`. Its PDF
page 7 corrects the §11.3.6.1 `gamma` exponent to `D^1.5`. The nine-page
consolidated errata contains no four-plus-member or per-shear-plane
clarification for §11.3.6.

The official AWC [2024 Chapter 12 PDF][ch12] is pinned at SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
Printed pages 95–96, §12.3.8, give a new four-or-more-member lateral
resistance procedure, subject to the stated opposing-force condition:

- For an even number `n` of members, analyze every adjacent pair as a single-
  shear connection under §12.3.1, take the minimum `Z`, and use
  `Z = Z_min n/2`.
- For an odd number `n` of members, analyze every adjacent set of three as a
  double-shear connection under §12.3.1, take the minimum `Z`, and use
  `Z = Z_min (n-1)/2`.

Section 12.3.8 also permits a more detailed analysis accounting for wood
bearing resistance and dowel moment resistance along the dowel length. This
is a connection reference-lateral-resistance procedure, not the group-action
factor equation. It does not establish how multiple plane-specific `Cg`
values combine with those `Z` procedures. That downstream integration must
remain separate and unresolved.

The AWC [2024 NDS resource page][nds-page] identifies the 2024 Commentary as
part of an AWC store package and shows a view-only option. The AWC [store
package page][nds-package] says the package contains the NDS and Commentary.
I did not obtain an official Chapter 11 Commentary file for this audit; the
scope of the view-only option was not established from the public page text.
Accordingly, no current official Commentary wording for C11.3.6 is claimed
as bound evidence here. The official 2018 Commentary is not used to prove a
2024 rule.

A third-party [full-text copy](https://studylib.net/doc/28419537/awc-nds2024-withcommentary-20250328-abdi-electronic)
that identifies itself as the 2024 NDS with Commentary appears to repeat the
older explanatory rule that four-plus connections are assessed plane by
plane, with a Cg per plane based on the thinnest member adjacent to that
plane. I excluded that copy from the authoritative source set: its bytes are
not obtained from or authenticated against AWC. This is a lead for locating
the 2024 C11.3.6 Commentary, not a design basis or sufficient proof.

## Answers and safe-use decision

**(a) Aggregate `E_s A_s` for four or more members:** the normative equation
and variable definition alone do not reject the evaluator's sum, but they do
not establish that one whole-stack factor is the applicable 2024 treatment
for four-plus members. The exact maintained branch is therefore **not
validated for four-plus use**. This is an applicability hold, not a finding
that a candidate connection fails.

**(b) Plane rule:** an authoritative, source-bound 2024 C11.3.6 Commentary
was not available in this audit, so no per-plane rule is established to the
required source standard. The equation to apply if the current Commentary is
obtained and confirms that treatment is Eq. 11.3-1 separately for each shear
plane, with the plane's own `N`, `s`, `D`, `E_m A_m`, and `E_s A_s`; the
Commentary clue above says `A_s` is based on the thinnest member adjacent to
that plane. Do not substitute the aggregate of all non-main plies. For any
such implementation, each plane needs an explicit ordered adjacent-member
pair and source-bound gross/equivalent areas and moduli. The per-plane factor
must not be collapsed into a capacity or a single connection factor until
its combination with 2024 §12.3.8 has also been explicitly resolved.

**(c) Follow-up:** the immutable method attempt02 should reject four or more
total members (`1 + len(side_members) >= 4`) with `status=pending`, `cg=null`,
and `capacity=null`, while retaining the already tested one-, two-, and
three-member scope. It should not implement a per-plane algorithm from the
2018 Commentary alone. Attempt02 includes an isolated candidate patch and
regression; it is not applied to the maintained evaluator or to attempt01.

## Synthetic branch reproduction

Using the existing synthetic test fixture shape (not candidate data), I
supplied three side members of 5 in² each, each at 1,400,000 psi, with one
10 in² main member at the same modulus; the row had `N=3`, `D=1 in`, and
`s=4 in`. The exact maintained evaluator returned:

```json
{
  "status": "calculated_method_only",
  "main_ea_lbf": 14000000.0,
  "side_ea_lbf": 21000000.0,
  "cg": 0.9637875158517683,
  "capacity": null
}
```

This demonstrates that an accurately bound four-member payload currently
receives one aggregate factor. It does not identify a candidate result or a
standard known-answer value. Under the unverified plane interpretation, a
stack ordered `[10, 5, 5, 5] in²` would instead have plane-pair factors
`0.9163482163`, `0.9689119171`, and `0.9689119171` for those synthetic
equation inputs. These values are a diagnostic contrast only, not an adopted
four-plus-member answer.

## Proposed regression scope

The attempt02 test should construct valid, digest-bound synthetic four- and
five-member payloads and assert that both return pending with a dedicated
four-plus-member reason, `cg is None`, `capacity is None`, and
`criterion_disposition == "pending"`. The five-member case guards the odd-
member branch as well as the even four-member case. Existing one-member-side
and two-member-side cases must still calculate as before. If a future source-
bound plane implementation is authorized, its separate tests should include
unequal adjacent-member sections with the same aggregate side area but
different plane Cg values, a reversed stack yielding the reversed plane
sequence, plane-ID/order mismatch rejection, and an independent published
Table 11.3.6A plane known-answer. Integration tests for §12.3.8's even/odd
`Z` procedure belong to the resistance method, not this method-only factor
gate.

No current-candidate Cg, capacity, bolt action, or disposition is created by
this audit or attempt02.

[ch11]: https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf
[errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
[ch12]: https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf
[nds-page]: https://awc.org/resources/2024-nds/
[nds-package]: https://shop.awc.org/product/2024-nds/
