# Current wood splitting method screen — attempt01

Status: source and applicability screen only. No splitting demand, resistance,
capacity, pass, or failure is calculated. The
`supplemental_EC5_splitting` criterion remains `pending`.

## Finding

The identifiable first-generation candidate is EN 1995-1-1:2004 §8.1.4,
“Connection forces at an angle to the grain,” equations (8.2)–(8.5). The
retrieved CEN 2004/AC:2006 corrigendum corrects the §8.1.4 equation (8.4) and
the definitions tied to equations (8.2)–(8.3); its clause pages are German.
An official 2008 JRC workshop deck reproduces the English clause excerpt and
figure reference. The deck is explanatory training material, not the normative
standard; it corroborates transcription only and does not establish adoption.

For an explicitly analytical supplemental scenario, the first-generation
candidate may be selected as EN 1995-1-1:2004 §8.1.4, corrected by
EN 1995-1-1:2004/AC:2006. This names the method source for a bounded scenario;
it does not assert that EC5 governs this project or that the analysis complies
with a national code. The CEN correction covers Eq. (8.4) and definitions tied
to Eqs. (8.2)–(8.3). The official 2008 JRC workshop deck reproduces the English
clause excerpt and figure reference as explanatory material, not normative
text.

The project record does not select a governing jurisdiction, EC5 edition, or
National Annex. BSI lists both BS EN 1995-1-1:2004+A2:2014 and
BS EN 1995-1-1:2025 as “Current, Under Review.” Its statement that first-
generation Eurocodes remain the applicable UK editions until 30 March 2028
unless an authority or project specification says otherwise describes the UK
transition only. The public 2025 JRC workshop deck summarizes second-generation
connection clauses §§11.5–11.6 for brittle failures parallel and perpendicular
to grain, respectively, but does not provide enough normative text to apply
them. Do not carry first-generation §8.1.4 equations into a 2025 scenario.

The repository does not contain a complete authenticated EC5 text or National
Annex. The accessible correction and JRC reproduction support naming the
first-generation analytical candidate and transcribing only the provisions
they show. A scenario still needs source-backed applicability to the selected
Figure 8.1 arrangement, all factor inputs, and any clause text it relies on
beyond those reproduced sources. A claim of regulatory EC5 compliance requires
the complete governing edition and its applicable National Annex; that is not
a prerequisite for naming a non-regulatory analytical scenario.

## First-generation candidate method and limits

The CEN correction is the primary normative evidence retrieved for this
candidate. The following surrounding text is also reproduced in the JRC
workshop deck, which is not normative evidence:

```text
Fv,Ed = max(Fv,Ed,1, Fv,Ed,2)                  (8.3)
Fv,Ed ≤ F90,Rd                                (8.2)
F90,Rd is derived from F90,Rk under §2.4.3
```

For softwood and only for the arrangement shown in EN 1995-1-1 Figure 8.1,
the characteristic splitting resistance is reproduced as:

```text
F90,Rk = 14 b w √(he / (1 − he/h))            (8.4), N
```

The associated factor is `w = max((wpl/100)^0.35, 1)` for punched metal plate
fasteners and `w = 1` for all other fasteners (8.5). In the reproduced text,
`he` is the loaded-edge distance to the most distant fastener center (or plate
edge), `h` is timber member height, `b` is member thickness, and `wpl` is the
punched-plate width parallel to grain. The rule checks the maximum design shear
on either side of the connection against design splitting resistance.

This is a candidate provision, not an adopted result. Its stated softwood and
Figure 8.1 limits matter: it is not a general formula for every bolt group,
cleat, edge, or cross-grain force. No extra numeric `he/h` bound is asserted
here because the full selected-edition clause and figure are not available for
verification. The design conversion under §2.4.3 and any applicable National
Annex values also remain unbound. The accessible material does not establish
that a current group and its signed action match Figure 8.1.

## Comparison with the current ordinary joint

The representative patch in current coverage uses `bottom_center_right_cleat`,
`base_rail_bottom_right`, and `base_principal_center_right`. It has separate
two-fastener rail and principal groups plus a direct rail-to-principal butt
seat. The seat is a separate contact path, not another bolt group.

- **Rail group:** `rail_1` and `rail_2` under
  `bottom_center/clip_horizontal_bottom_right_1`; centers
  `(134.500,36.444,452.885)` and
  `(134.500,11.165,474.097)` mm, 33.0 mm apart. Axis is about
  `[0,-0.643,-0.766]`; nominal shaft 6.35 mm and modeled bore 7.5 mm. Cleat
  grain is `+N`; the row follows `+N`. Rail grain is `+X`, so the row crosses
  rail grain.
- **Principal group:** `principal_1` and `principal_2` under
  `bottom_center/clip_horizontal_bottom_right_1`; centers
  `(103.782,32.333,473.655)` and `(103.782,53.545,498.934)` mm, 33.0 mm apart.
  Axis is about `[-1,0,0]`; nominal shaft 6.35 mm and modeled bore 7.5 mm.
  Principal grain is `+T`; the row follows `+T`. Cleat grain is `+N`, so the
  row crosses cleat grain.

The conditional global grain directions are cleat `+N ≈ [0,-0.766,0.643]`,
rail `+X = [1,0,0]`, and principal `+T ≈ [0,0.643,0.766]`. The modeled bolt
axes are perpendicular to these longitudinal axes. The current material/frame
maps explicitly label these as analytical orientation scenarios, not observed
boards. Shaft axes and row directions do not identify the lateral force
direction, loaded edge, or EC5 angle `α`.

The rail and principal host maps record source cross-sections of 38.1 ×
139.7 mm, which supply candidate dimensions for EC5 `h` and `b`. No signed
action or loaded edge is selected here to bind their clause-specific
orientation or identify `he`. The cleat's world-axis bounding box is not its
local finished section. The current geometry snapshot is a placement/bounds screen; the
nominal 6.35 mm axes and 7.5 mm bores are not selected hardware or received
bore dimensions. Do not read a loaded edge or Figure 8.1 arrangement from these
unsigned locations.

Both two-fastener groups act on the same cleat through different faces. Any
member-level check must preserve each actual joint and the cleat's other group,
bores, and finished cuts in its method applicability review. Do not add the two
group capacities or substitute parallel-row tear-out for a splitting check.

## Inputs required to make an analysis executable

1. For a supplemental analytical scenario, pin the method identity as
   EN 1995-1-1:2004 §8.1.4 corrected by EN 1995-1-1:2004/AC:2006, and cite the
   JRC 2008 deck only as an explanatory reproduction. Bind the exact figure,
   clause text, and factors used to support each applicability or resistance
   claim; do not infer text that these sources do not provide. If making a
   regulatory-compliance claim, additionally select the governing jurisdiction,
   current adopted edition, and National Annex, then pin their complete
   authenticated text. Do not use first-generation equations as a substitute
   for the 2025 §§11.5–11.6.
2. For each member side of each two-fastener group, map the exact finished
   member and conditional grain scenario to the selected clause's figure.
   Specify the force direction and the loaded edge, then measure that
   arrangement's `h`, `b`, and `he` from the finished member, all holes, and
   cuts. Geometry supplies candidate distances, but no signed action or loaded
   edge is selected here to identify the applicable `he`.
3. Bind a named softwood/product and final-piece grade/material scenario,
   service condition, and load-duration class. Before calculating design
   resistance, source and specify the §2.4.3 conversion factors (including
   `kmod` and `gammaM`) for that scenario. A National Annex is needed if those
   values are claimed as the governing jurisdiction's EC5 values; it is not
   needed merely to label explicit analytical scenario assumptions. No factor
   values are selected here. `w=1` is the candidate for non-punched ordinary
   fasteners, subject to the source text and final fastener category. Do not
   assign an NDS row as an EC5 class without a supported mapping.
4. Obtain fresh accepted current-frame actions for all six WJ-09 cases. For
   each joint, resolve the design shear on both sides, `Fv,Ed,1` and
   `Fv,Ed,2`, their signs and force/grain angle, and use the method's prescribed
   side/group result. The six current load records are applied wrenches only;
   they contain no reactions, joint demands, or fastener load sharing.
5. Verify the selected source-backed method covers each member and the actual
   group arrangement. If it does not, identify a source-supported equivalent
   method with its exact geometry and material scope before calculating
   resistance.
   Keep the second group and any interacting finished-section failure paths in
   view; a geometry ratio or `4D/7D` screen does not close this criterion.

MVP-E may use a named, specified analytical final-piece grade/material and
grain scenario before receiving observations exist. Such a scenario must meet
the chosen EC5 method's material/product scope and specified design-conversion
eligibility, and remains a scenario rather than a claim about the delivered
piece. Original source 4×6
design values do not transfer to ripped blocks. WJ-11 receiving/regrading
observations stay separate and may remain blank while conditional scenarios
are analyzed. The corrected first-generation clause is selectable as an
analytical scenario, but this note has not selected loaded edges or design
factors, confirmed a Figure 8.1 match, or computed a demand or capacity. The
criterion remains `pending`.

## Sources and access record

All online records below were checked 2026-09-27. BSI records establish edition,
status, purchase/access route, and UK transition notes; they do not provide the
normative splitting equations in the accessed page text.

- **BSI first generation:** BS EN 1995-1-1:2004+A2:2014 record. BSI lists it
  Current, Under Review, with paid digital and hardcopy options. The record
  also gives the UK transition note.
  <https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-common-rules-and-rules-for-buildings>
- **BSI second generation:** BS EN 1995-1-1:2025 record. Published 2025-11-30;
  Current, Under Review, with purchase options.
  <https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings>
- **BSI UK National Annex:** 2004+A2:2014 record is Current and was published
  2019-09-30. This establishes only the UK annex record; no UK jurisdiction is
  selected here.
  <https://knowledge.bsigroup.com/products/uk-national-annex-to-eurocode-5-design-of-timber-structures-general-common-rules-and-rules-for-buildings-1>
- **CEN corrigendum:** EN 1995-1-1:2004/AC:2006. This is a primary correction
  to §8.1.4's Eq. (8.4) and definitions for (8.2)–(8.3). The June 2006,
  7-page PDF is retrievable from the SIA site; it is not the complete standard.
  <https://cms.sia.ch/en/api/getMedia/559>
- **JRC/TUM 2008 workshop deck:** explanatory reproduction of first-generation
  §8.1.4, Eqs. (8.2)–(8.5), and variables. It is not normative text.
  <https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf>
- **JRC 2025 workshop deck:** explanatory chapter outline identifying clauses
  11.5 and 11.6. It is not normative text.
  <https://eurocodes.jrc.ec.europa.eu/sites/default/files/2025-08/250603-JRC_Eurocode_5_Dietsch_Frangi_Schenk_website.pdf>

Downloaded official PDF byte hashes, captured 2026-09-27:

- CEN 2004/AC:2006 corrigendum: `ff5bd62c586cc714eed9b8b7e557bbe030f36fe7e3ccd29dd10a24db755b03a5`.
- JRC/TUM 2008 presentation: `20b6cfc83a1b3a1afb124f9c7cc337ab3b23c141ebe3da8c74906a8eece8017d`.
- JRC 2025 presentation: `dc95c9524698aa4e99ac2bb228a2632916de7643218b3bc56d9f921879630352`.

## Repository snapshots consumed

These SHA-256 values identify the file versions read for this attempt; they do
not assert that evolving plan or source files remain current afterward.

- `AGENTS.md`
  SHA-256: `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536`
- `docs/wood-joints-mvp/criteria-method-map.md`
  SHA-256: `2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`
- `docs/wood-joints-mvp/criteria.json`
  SHA-256: `fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784`
- `docs/wood-joints-mvp/wood-limit-state-basis.md`
  SHA-256: `1110e664a88f704773a463e83a2aeac3954b978048d811e4bff1effa55aa7c2e`
- `docs/wood-joints-mvp/current-criteria-coverage.md`
  SHA-256: `ccda149cf7add227a7a038311625595764331c57a43af6b23de973a88d1b6e0a`

Evaluation-resume base:
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/`

- `current-wood-resistance-method-screen-attempt01/README.md`
  SHA-256: `238afb034bb90c7945af1a6ec2c01dfeb3d9fee13c20f47340f1f8e00834d3f1`
- `geometry-snapshot.json`
  SHA-256: `0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187`
- `current-block-material-frame-map-attempt02/material-frame-map.json`
  SHA-256: `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`
- `current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json`
  SHA-256: `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`
- `current-attachment-topology-attempt01/attachment-topology.json`
  SHA-256: `a3e3d3dccca037a96e1931678b3b722281743a683f8c77264fe3a25168dbd446`
- `current-full-frame-input-manifest-attempt03/README.md`
  SHA-256: `98455c87f1961517a4a6747b60ff1c27d6b2e05612dc53051f6f31bad5b4961b`
- `current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json`
  SHA-256: `2f5eed3e4fa01e62e776d8fc0e4fae12182f86e1d84c63c956dbe7b44fbb5896`
- `current-load-cases.json`
  SHA-256: `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`
