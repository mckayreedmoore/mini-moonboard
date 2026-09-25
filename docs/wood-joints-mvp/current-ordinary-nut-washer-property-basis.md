# Ordinary 1/4-20 nut and washer property basis

**Checked:** 2026-09-25. **Status:** conditional MVP-E source boundary for the
ordinary Grade 5 bolt scenario. Published supplier technical tables provide
a conditional J995 Grade 5 nut proof reference; public washer sources provide
class/material descriptions and dimensions but no numeric yield minimum. No
delivered-part conformity, resistance, or complete-joint result is inferred.

## Nut candidate and proof-load boundary

K.L. Jack identifies [25CNFH5Z](https://www.kljack.com/products/25cnfh5z/)
(supplier part `AFH5Z0250C`) as a zinc-plated steel 1/4-20 Grade 5 finished
hex nut, specified to SAE J995 Grade 5, ASME B18.2.2, and ASME B1.1 UNC
Class 2B. Its page lists 7/16 in across flats and 7/32 in nominal thickness.
The B18.2.2 finished-hex envelope used by the current ordinary hardware
basis is 0.212–0.226 in thickness, 0.428–0.438 in across flats, and at most
0.505 in across corners; the current identified edition is
[ASME B18.2.2-2022](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts).
These are supplier-stated specifications and standard dimensions for a
conditional model. They do not establish that a delivered nut conforms.

The [SAE J995_201707 record](https://saemobilus.sae.org/standards/j995_201707-mechanical-material-requirements-steel-nuts)
identifies the July 2017 revision and scope, but its public record does not
show the mechanical-properties tables. A later targeted source check found
the applicable published table in [STS Industrial's J995 technical data](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j995-technical-data):
finished hex Grade 5 nuts from 1/4 through 1 in have a proof-load stress of
120,000 psi for UNC/8UN and 109,000 psi for UNF/finer. It gives the
calculation rule `proof-load stress × tensile stress area` and lists
`At = 0.0318 in²` for 1/4-20 UNC. The resulting **conditional project nut
proof-load reference is 3,816 lbf** (`120,000 × 0.0318`) per conforming nut.
The Grade 5 UNC value is independently reproduced in [Fastenal's inch-fastener
mechanical-properties reference](https://crafter.fastenal.com/static-assets/pdfs/Mechanical_Properties_of_Inch_Fasteners.pdf),
[GlobalSupply's 2023 finished-hex datasheet](https://globalsupplyinc.com/wp-content/uploads/2023/11/Finished_Hex_Nuts_11-7-23.pdf),
and [Value Fastener's Grade 5/8 catalog](https://www.valuefastener.com/documents/products/nutsfinishedgr5-8.pdf).
These are published supplier technical references to J995, not evidence
that a delivered `25CNFH5Z` lot conforms to a particular J995 edition. This
property may be used as a conditional MVP-E scenario input for a Grade 5,
finished-hex, 1/4-20 UNC nut; it is not assigned to an unverified physical
nut.

Do not transfer the bolt's Grade 5 strength to the nut. The separate
[conditional bolt scenario](hypotheses/evaluation-resume-2026-09-24/ordinary-bolt-steel-reference-attempt01/README.md)
uses bolt minima `Fy = 92 ksi`, `Fu = 120 ksi`, and `Fp = 85 ksi`, with
`At = 0.0318 in²`; its calculated 2,703 lbf proof reference is for the bolt
only. It is not the nut proof load. Even a sourced nut proof value would not
by itself establish stripping capacity for a shorter-than-full nut thread
engagement. Thread compatibility and actual engaged length, nut entry/exit
chamfers, thread form, and a supported internal-thread failure method remain
separate inputs, as recorded in the [thread engagement method](thread-engagement-method.md)
and [bolt resistance basis](bolt-resistance-basis.md).

## Washer candidate and yield boundary

K.L. Jack identifies [25NWUS](https://www.kljack.com/products/25nwus/) as a
plain/light-oil, low-carbon-steel USS washer to ASME B18.21.1 Type A Wide,
regular series. The listing gives 1/4 in bolt size, 0.312 in nominal ID,
47/64 in nominal OD, nominal 1/16 in thickness, and thickness limits
0.051–0.080 in. The dimensional standard edition identified for the
candidate is [ASME B18.21.1-2009 (R2016)](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers),
which ASME says remains in effect. The corresponding Type A Wide dimensional
envelope used in the ordinary stack is ID 0.307–0.327 in, OD 0.727–0.749 in,
and thickness 0.051–0.080 in. The product page's material callout is only
“low carbon steel”; it gives no steel grade, heat condition, hardness, yield
strength, or tensile strength.

ASTM's current [F844-19(2024) record](https://store.astm.org/standards/f844)
covers plain steel washers furnished unhardened and says their dimensions
default to ASME B18.21.1 Type A Table 11 unless otherwise specified. Its
public abstract notes possible chemical analysis and hardness testing, but
does not publish a washer yield minimum. K.L. Jack does not state that
25NWUS conforms to ASTM F844. Neither the Type A Wide dimensions nor the
unqualified low-carbon-steel description supplies a numeric yield property.

An alternate same-size harder washer class is documented in K.L. Jack's
[25NWUS8Z listing](https://www.kljack.com/products/25nwus8z/): 1/4 in Type A
Wide dimensions, quenched-and-tempered steel, ASTM F436, through-hardness
38–45 HRC. The active [ASTM F436/F436M-24 record](https://store.astm.org/f0436_f0436m-24.html)
describes chemical, mechanical, and dimensional requirements and identifies
hardness among the specified/tested properties. The publicly exposed record
does not state a numerical yield minimum; neither the K.L. Jack listing nor
F436 hardness alone supplies one. This harder washer is only an alternate
conditional material description, not a selected substitute for 25NWUS.
No hardness-to-yield conversion is made here.

The repository's [steel elastic scenario](steel-elastic-material-scenario.md)
uses `E = 200,000 MPa` and `ν = 0.30` for response diagnostics. Those generic
elastic constants do not assign a steel grade or yield stress. A washer
bending/spreading check therefore still lacks a sourced conditional yield
minimum and a supported plate/contact resistance method; the existing
[resistance basis](bolt-resistance-basis.md) correctly leaves washer steel
resistance unresolved. Wood bearing beneath a washer is a separate
compression-perpendicular reference, not washer-metal bending.

## MVP-E boundary

The conditional Grade 5 hex nut property case can now use 120,000 psi proof
stress and a 3,816 lbf proof-load reference for 1/4-20 UNC. That proof check
is distinct from stripping resistance: it does not establish thread failure
capacity for a given engaged length, chamfer, or fit. The ordinary 25NWUS
washer case still has no source-backed yield minimum. ASTM F844's public
scope confirms it is an unhardened general-use washer specification; F436's
published hardness and product descriptions improve the alternate hardened
washer material identification but do not provide yield stress. Washer
bending/spreading therefore remains without a numerical metal-yield input
or supported plate/contact resistance method. Keep these scenario data
separate from eventual certificates, lot identity, and delivered-part
conformance. No nut stripping or washer bending capacity is assigned by
this note. No contact or purchase was made.
