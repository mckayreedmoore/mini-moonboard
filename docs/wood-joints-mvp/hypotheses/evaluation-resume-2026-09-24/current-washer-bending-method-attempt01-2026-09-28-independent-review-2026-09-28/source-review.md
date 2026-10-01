# Source and method review notes

Review date: 2026-09-28. These checks compare the producer’s claims with
current public records or accessible abstracts. They do not substitute for
reviewing licensed standards in full.

| Source / claim checked | Independent check | Review result and boundary |
| --- | --- | --- |
| ASTM F844-19(2024) | ASTM’s public record identifies the active F844-19(2024) specification, covering unhardened plain steel washers for general-use bolt, nut, and stud applications; default dimensions point to ASME B18.21.1 Type A, Table 11. | Matches the packet’s product-specification description. The public abstract describes scope and possible chemical/hardness testing, not a washer-on-timber plate resistance or load-deflection rating. The landing page timed out on direct open, but the indexed ASTM record was available. |
| ASTM F436/F436M-24 | ASTM’s public record labels F436/F436M-24 active and describes chemical, mechanical, and dimensional requirements, including hardness, for hardened washers. | Matches the packet. These product requirements do not establish a load-deflection rating of a selected washer in the stated assembly. |
| ASME B18.21.1-2009 (R2016) | ASME’s official page names the 2009 (R2016) edition, says it remains in effect, and describes dimensional requirements, physical properties, and related tests for plain washers among other washer types. | Edition and scope match. The public description does not itself identify an assembly-specific annular plate-bending method. This is a statement about the exposed description, not an exhaustive interpretation of licensed text. |
| AISC 360-22 / Steel Construction Manual, 16th edition | AISC’s official Manual record identifies the 16th edition and its contents, including flexural members, connecting elements, beam bearing plates/base plates, and Part 16.1 containing ANSI/AISC 360-22. The official errata record lists January 2025 errata for the first printing of AISC 360-22. | Edition/topic claims match the records checked. The packet’s “no washer-specific method was found” statement is supportable only as its explicitly bounded source scan; public landing-page contents and errata do not prove that no potentially relevant method exists elsewhere or in full-text material not inspected. AISC direct page opens returned 403, but its official search records were available. |
| Strozzi, Dragoni, and Ciavatti (1995) | The University of Modena and Reggio Emilia institutional repository record and abstract identify a thin annular plate, simply supported at its inner boundary, free at the outer perimeter, and loaded by a concentrated transverse force at an arbitrary position; it reports a flexural series solution and comparison with tests for a specific plate geometry. | Matches the packet’s characterization. It is a benchmark for that stated idealization, not the finite head/nut footprint and possibly partial, compliant timber-seat support. The full article was not available in this review. |
| Heap, ANL-6905 (1964) | The OSTI report record/PDF abstract and UNT archival record identify the report and describe thin circular plates under uniform load on a concentric circle with several stated edge-condition cases. | Matches the packet’s benchmark description. It is not the washer/head-or-nut/timber-seat assembly. No result was computed or transferred. |
| K.L. Jack 25NWUS / 25NWUS8Z conditional descriptions | K.L. Jack’s current public entries identify 25NWUS as a low-carbon-steel, plain USS Type A Wide washer with dimensional data; 25NWUS8Z is described as heat-treated/quench-and-temper steel meeting F436 material requirements with Rockwell C 38–45 hardness and dimensional data. | Matches the local property-basis descriptions. The exposed entries contain no washer load-deflection curve, bending rating, or numeric yield minimum. Neither product is selected or assigned to all washer roles. Hardness is not converted to yield strength. |
| Local inventory and status claims | The 16 pinned local inputs verify without drift. The pinned current hardware coverage records 92 candidate plus 12 retained structural axes, 184 plus 24 washer roles, 208 total roles, and identifies conditional washer facts only for 16 side and four outer-post axes; method/coverage records retain `washer_bending` as pending. | Matches the packet’s counts and scope. The conditional facts do not establish selected hardware, conformance, support, demand, response, or capacity. |

## Method-route and application boundary

The packet presents classical thin-plate flexure as a candidate mechanics
family, with `D = E t^3 / [12 (1 - nu^2)]` and a biharmonic plate-response
equation. That is a coherent general elastic route for a suitably thin,
isotropic plate under small deflection. The cited annular and circular plate
sources show relevant solution/benchmark families, but their load footprints
and supports do not match the actual assembly. The packet expressly requires
the actual bolt-head/nut footprint, timber-support polygon and contact, fresh
actions, material properties, applicability checks, and a matching benchmark
before a candidate calculation. It separately calls for shear-deformable or
three-dimensional contact mechanics when the thin-plate/small-deflection
assumptions fail.

That distinction is technically important and is preserved: an elastic
response/stiffness solution does not itself provide a strength or design
resistance; first yield would additionally need a traceable material yield
basis and stress interaction, while contact, timber-seat crushing, transverse
shear, and inelastic effects may require separate treatment. The equation
statement is a general mechanics formulation; the packet does not claim that
the cited benchmark papers validate a specific implementation or WJ24 result.

## Source trail rechecked

- ASTM [F844-19(2024)](https://store.astm.org/standards/f844) and
  [F436/F436M-24](https://store.astm.org/f0436_f0436m-24.html).
- ASME [B18.21.1-2009 (R2016)](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers).
- AISC [Steel Construction Manual, 16th edition](https://www.aisc.org/aisc/publications/steel-construction-manual/),
  [revisions and errata](https://www.aisc.org/aisc/publications/revisions-and-errata/),
  and official [2022-specification announcement](https://www.aisc.org/news/aisc-releases-new-version-of-specification-for-structural-steel-buildings-ansiaisc-360-22/).
- Strozzi et al., 1995, DOI
  [10.1243/03093247V303211](https://doi.org/10.1243/03093247V303211), with
  the abstract indexed in the University of Modena and Reggio Emilia
  [institutional repository](https://iris.unimore.it/handle/11380/619344).
- Heap, ANL-6905, 1964, official OSTI
  [report PDF](https://www.osti.gov/servlets/purl/4005214) and UNT
  [archival record](https://digital.library.unt.edu/ark:/67531/metadc868796/).
- K.L. Jack [25NWUS](https://www.kljack.com/products/25nwus/) and
  [25NWUS8Z](https://www.kljack.com/products/25nwus8z/) product entries.
