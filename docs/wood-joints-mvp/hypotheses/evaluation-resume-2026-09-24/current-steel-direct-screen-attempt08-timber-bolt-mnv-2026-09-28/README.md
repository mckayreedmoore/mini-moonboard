# T06 timber-bolt M–N–V primary-source screen — attempt08

**Disposition:** a potentially relevant published M–N–V interaction model was
located, but this source screen does **not** establish a complete, validated
method for the reviewed wood-to-wood through-bolts. Keep `steel_direct`
unresolved. The result is neither “no method exists” nor a method adoption.
No capacity, criterion disposition, hardware choice, method-map change,
candidate/geometry edit, solver input, or release claim is made.

This append-only packet follows T06 attempts03/05/06/07 and AWC NDS-2024
References 39–41 attempts01/02. Their relevant source/review bytes are pinned
in [`source-pins.json`](source-pins.json). They remain unchanged.

## What the new primary sources say

### Blaß 2018, KIT Scientific Publishing

Hans Joachim Blaß, “Moment-Normalkraft-Querkraft Interaktion in stiftförmigen
Verbindungsmitteln von Stahlblech-Holz-Verbindungen,” in *Karlsruher Tage 2018
– Holzbau: Forschung für die Praxis*, printed pp. 17–26, published by KIT
Scientific Publishing, 2018; KIT record DOI
[10.5445/IR/1000086376](https://doi.org/10.5445/IR/1000086376). The full chapter
was readable through the official KIT repository PDF at
<https://publikationen.bibliothek.kit.edu/1000086376/18283247>.

The source derives a connection model for laterally loaded pin fasteners in
steel-sheet–wood joints. In §2, printed pp. 18–20, a circular fastener section
is partitioned into areas carrying bending, axial tension, and shear under a
linear-elastic/perfectly-plastic steel idealization. For a thick-plate,
single-shear Johansen mechanism, it places sections A and B at the steel/wood
shear plane and in the timber, respectively; derives the local moments and
forces from the stated embedment mechanism; and maximizes the lower-bound
connection resistance over the area partition. Equation (8), printed p. 20,
gives the approximate section interaction:

`M/My + (N/ftens + V/fshear)^2 = 1`.

The paper says to satisfy Eq. (8) at every location along the fastener axis.
Its detailed connection resistance is characteristic-format `Fv,Rk`, built
on Eurocode 5 connection equations, and it invokes EN 1993-1-8 for bolt/dowel
shear resistance. The parametric study expressly includes 5.8 bolts of 12,
16, and 20 mm diameter with 90 mm timber thickness. For bolts and dowels, it
says nominal yield strength and tensile strength come from a manufacturer’s
declaration or tensile tests. The paper does not state a bolt-specific
thread-root bending or tensile section rule. The tests described in its
validation section are profiled-nail steel-sheet–beech-LVL specimens and
comparisons to earlier dowel tests; bolt cases are analytical parameter
cases, not bolt validation tests.

This is a serious candidate method lead: the article explicitly includes
bolts and simultaneous M/N/V on circular fastener sections. But its model
scope is steel-plate–wood lateral-shear joints, its detailed load/span model
depends on Johansen embedment and steel-plate restraint, and it does not
demonstrate the through-bolt section and support mechanics in this
wood-to-wood candidate. It is a 2018 conference-proceedings chapter; the
publisher record and chapter do not establish peer-review status. Do not
label it peer-reviewed on this evidence.

### Kuck, Sandhaas, and Blaß 2025, WCTE proceedings

Elisabet Kuck, Carmen Sandhaas, and Hans Joachim Blaß, “How Interaction of
Internal Forces and Moments Influence the Load-Bearing Capacity of Dowels,”
*Proceedings from the 14th World Conference on Timber Engineering 2025*, pp.
2834–2840, DOI
[10.52202/080513-0346](https://doi.org/10.52202/080513-0346). The article is
available from the proceedings publisher at
<https://www.proceedings.com/content/080/080513-0346open.pdf> and from the KIT
repository at <https://publikationen.bibliothek.kit.edu/1000183153>.

On printed p. 2835, Eq. (1) repeats a “possible” circular-fastener interaction
criterion attributed to Blaß 2018:

`M/My + (V/Fshear + N/Ftens)^2 ≤ 1`.

The paper’s experiments are double-shear steel-to-timber connections with
10 mm thick outer steel plates, a 0.5 mm gap at the shear planes, 6 mm
copper/aluminum/C15/silver-steel dowels, and beech LVL or densified veneer
wood (DVW); its specimen timber thicknesses span 15–60 mm. The tested M–N–V
case obtains normal force from inclined fastener segments under lateral
loading. It is not a direct axial-load test of a headed, threaded structural
through-bolt in a timber-only grip. The paper reports uncertain magnitudes of
the normal forces, says friction could not be ruled out, and calls for further
investigation. For the straight-axis M–V case, its Eq. (2) estimates shear
plane moment using a fastener clamped at the outer steel plates and a uniform
embedment assumption; the authors question both restraint and embedment
assumptions when comparing with results. This supports the interaction
phenomenon but does not validate a complete bolt method for the target
connection. The publisher/KIT records identify a conference-proceedings
paper; peer-review status for this exact paper was not authenticated here.

## Required method facts versus source evidence

| Required fact | New source evidence | Remaining boundary for the reviewed joint |
|---|---|---|
| Edition and exact source | Blaß 2018, KIT Scientific Publishing, chapter pp. 17–26; Kuck et al. 2025, WCTE proceedings, pp. 2834–2840; stable DOIs and publisher records are recorded in `source-observations.json`. | The two records are primary proceedings publications, not a currently adopted U.S. design standard. Exact peer-review status for either contribution is not confirmed in the source records reviewed. |
| Complete simultaneous interaction | Both state `M/My + (N/ftens + V/fshear)^2 ≤ 1` for a circular fastener section; Blaß says check it along the fastener axis. | It is an approximate interaction and its applicability to direct externally imposed bolt tension in a timber-only grip is not demonstrated. No separate source states that this is a qualified design interaction for the candidate. |
| Bolt section, thread/root basis | Blaß identifies manufacturer-declared or tested nominal yield and tensile properties for bolts/dowels; EN 1993-1-8 is cited for bolt/dowel shear. It also distinguishes bolt shear ratios for shank and threaded planes using EN 1993-1-8 Table 3.4. | No explicit thread-root/tensile-stress-area rule for `ftens`, no thread-root or shank section rule for `My`, and no instruction for where the threaded transition lies in the loaded grip are supplied. EN 1993-1-8’s shear reference does not by itself resolve bending/tension at the actual bolt section. |
| Bending span, restraint, and local N/V/M | Blaß requires the interaction at each section and derives A/B demands for its stated plate/timber Johansen mechanism. Kuck et al. use an assumed outer-plate clamp and derive a shear-plane moment for one specific embedment shape. | There is no generic clear-span or support/bearing model for the reviewed bolt’s wood-to-wood geometry. The candidate’s actual section-by-section force distribution, support locations, washer/nut bearing, contact restraint, and thread transitions must be mapped and justified independently. |
| Resistance format | Blaß uses characteristic fastener inputs and reports characteristic joint resistance `Fv,Rk`; wood resistance is coupled through the Eurocode 5 Johansen/rope-effect model. | No conversion to the project’s required U.S. design-strength basis, factors, load combinations, or acceptance criteria is established. No NDS transfer rule is shown. |
| Validation and applicability | Blaß compares the model to profiled-nail tests and prior dowel tests; it parameterizes bolt sizes but does not test bolts in the reported validation. Kuck et al. test six-mm solid dowels in steel-plate joints. | Neither source tests the candidate’s actual bolt type/thread profile, external axial tension, timber-only joint topology, or current block bearing/support conditions. They do not validate six current-frame cases or criteria. |

## Bounded finding

The 2018 chapter supplies a real analytical M–N–V interaction proposal that
includes round bolts as a fastener category; therefore the evidence supports
“a potentially relevant method exists for a defined steel-plate–wood dowel
joint,” not “no method exists.” The 2025 primary study separately supports
the observed M–N–V phenomenon for inclined dowels in high-density
steel-to-timber joints, while reporting unresolved force and friction
uncertainties.

Neither source authenticates direct applicability of its full method to a
single through-bolt in the reviewed timber-only grip. The missing source facts
are: (1) an explicit scope/transfer basis for wood-to-wood through-bolts with
the candidate’s support topology; (2) the actual bolt’s tension, bending, and
shear resistance at every shank/thread section, including root/stress-area
basis and transitions; (3) a force/span/restraint model for section-level
simultaneous demands in this connection; (4) the applicable U.S. design
strength format and factors; and (5) validation for bolt specimens and
geometry at issue. These gaps are not filled by a solver’s extraction of
demands or by a generic steel section interaction.

Therefore: keep `steel_direct` open; do not calculate or adopt a candidate
capacity from this packet. This finding does not transfer any historical
fastener capacity, load, criterion pass, or connection qualification.

## Next source route

Obtain and review the full 2017 Karena Goossens KIT master’s thesis,
*M-N-V Interaktion in stiftförmigen Verbindungsmitteln für Stahlblech-
Holzverbindungen*. It is identified by the official KIT wood-structures
completed-master-theses page and cited as the direct antecedent in Blaß 2018,
but no download URL or thesis bytes were returned through the source routes
tested here. The thesis is the most direct next primary source for checking
the proposed model’s bolt inputs, section rules, test basis, and restraint
assumptions. Obtain it from the KIT archive/author-facing repository route;
do not treat failure of the current web route as evidence that it is
unavailable.

## Reproduction and scope

Run from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-direct-screen-attempt08-timber-bolt-mnv-2026-09-28/verify_source_packet.py
cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-direct-screen-attempt08-timber-bolt-mnv-2026-09-28
sha256sum -c SHA256SUMS
```

The verifier checks packet checksums and the pinned local predecessor/context
sources. It does not fetch or hash publisher-hosted PDFs. Direct `curl` to the
KIT repository was attempted only to obtain PDF bytes and failed at DNS
resolution in this shell (`curl: (6) Could not resolve host`); the web PDF
reader returned the full extracted chapter and article text. No solver or
native run, capacity calculation, hardware choice, criteria or method-map
edit, candidate change, geometry edit, or external message was made.
