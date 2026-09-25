# Current thread-engagement evidence routes

Status: scope clarification, 2026-09-25. This note distinguishes adopted
candidate obligations from proposed mechanics routes. It does not revise the
criteria register, change a gate, or accept any current connector law.

## Authority and current boundary

The source authority for the 36 adopted legacy checks is
[`criteria.json`](criteria.json):
[`floor-runner-mvp-criteria.md`](../floor-runner-mvp-criteria.md),
authenticated by `scripts.floor_flush_checks.FROZEN_ADOPTED_CRITERIA`. The
separate 11 candidate obligations in that file are also pending. In
particular, `steel_direct` requires actual selected bolt and thread/shank
resistance under axial and lateral actions; `complete_joint_actions` requires
fresh signed simultaneous joint actions; and `joint_stiffness` requires
justified slip/rotation and their effect on complete-frame response. Neither
the adopted register nor the owner authorization in [`AGENTS.md`](../../AGENTS.md)
requires a matched stiffness coupon, a helical thread mesh, or a measured
force-displacement curve as a universal prerequisite.

The [criteria method map](criteria-method-map.md) and
[current coverage report](current-criteria-coverage.md) are planning records,
not additional authorities or passes. The current [execution plan](next-mvp-plan.md)
requires declared engagement assumptions for a bounded joint diagnostic and
states that provisional method diagnostics need not wait for hardware sourcing.
Unknown physical axial transfer remains unresolved; it cannot be called zero
bolt force or credited as an accepted restraint. The later owner authorization
permits analysis of the reviewed candidate and does not authorize physical
inspection, receiving, fabrication, or release.

## What the current four-stack evidence establishes

The local evidence path
`hypotheses/evaluation-resume-2026-09-24/ordinary-native-preflight-attempt04/README.md`
describes a zero-load matrix preflight with an assumed six-degree-of-freedom
stiff nut fit. Its rigid seat carriers have zero density and it does not model
nut-bore contact or a physical thread traction law. This is a named stiff-limit
sensitivity, not engagement acceptance.

The local evidence path
`hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt04/README.md`
describes eight accepted diagnostic increments. Its local terminal record at
`hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt04/terminal-outcome.md`
states that it stopped at 0.003129826 s before the requested endpoint and that
the first increment has a known force-ramp integration error. It did not take
up the bolt-hole clearances or establish joint stiffness/capacity. Like the
preflight, it uses an assumed stiff engagement relation and does not establish
physical thread fit or transfer.

The [WJ24 sensitivity method](thread-engagement-sensitivity-options.md)
explicitly labels an equality-row branch `STIFF_LIMIT_SENSITIVITY_ONLY` and
its analyst-set spring ratios `PARAMETRIC_SPRING_SENSITIVITY_ONLY`. Those
ratios are exploration points, not confidence limits or evidence that they
bracket a delivered thread. With changing unilateral contacts, the source
method also warns that response and demand need not vary monotonically with
engagement stiffness. Neither the equality row nor the sweep is a physical
finite law or a conservative whole-joint bound.

## Evidence routes for a conditional finite law

The [WJ04 engagement proposal](thread-engagement-method.md) and WJ24
sensitivity method are author-proposed methods, not adopted criteria. A
finite axial engagement law may be supported by one of these routes:

1. A matched engagement test or coupon.
2. Published test data with a demonstrated scope applicable to the declared
   thread specification and its material, geometry, engagement, fit, and load
   range.
3. A validated analytical or numerical model with documented applicability to
   that same declared specification and range.

The evidence need not be brand-specific where a standard-defined thread,
bounded dimensions/tolerances, and material-property range are sufficient for
the validated model. Do not assume a generic model automatically applies to a
Unified inch thread, or that nominal size alone bounds delivered fit. If the
model depends on an unbounded product-specific attribute, retain it as an
explicit receiving condition or leave the affected response unresolved.

For a conditional engineering scenario, the minimum defensible record is:

- a declared bolt/nut specification and property range, including thread
  family/form, nominal size/pitch/class, nut geometry, partial-thread
  transition, assumed full-form engagement, fit/slack, and applicable material
  properties; source-bound these inputs or mark them as assumptions and state
  the later receiving condition;
- a finite compliance/slack envelope over the signed loading range, with the
  evidence route, model-validation scope, uncertainty, and the engagement-only
  contribution separated from bolt-shank, washer-seat, and timber compliance
  already represented elsewhere;
- a one-time implementation check for the chosen law and solver mapping,
  including force direction/sign, equal-and-opposite action, work/energy, and
  equilibrium at the engagement datum; and
- whole-joint and complete-frame comparisons across the evidence-derived
  envelope. Audit contact/opening states, free modes, signed interface and
  per-bolt actions, all governing resistance checks, and frame response. A
  stable scalar displacement alone does not show demand or contact invariance.

If these comparisons show material sensitivity or a mechanism within the
supported envelope, keep the affected result sensitive/unresolved and do not
replace it with the stiff limit. If the model is validated and the full
response remains acceptable across its applicable envelope, the analysis may
support a conditional engineering scenario without a new per-product measured
curve. It still does not establish actual delivered fit or thread/shank
resistance: the adopted `steel_direct` check and separate WJ-10 source-backed
hardware basis remain necessary. Receiving conditions remain conditions, not
claims that hardware was inspected.

## Source applicability

- [ASME B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
  defines Unified thread form, series, class, allowance, tolerance, and
  designation. It does not select a delivered part or provide its engagement
  stiffness law.
- Matsubara and Teranishi's [2022 timber-joint study](https://link.springer.com/article/10.1186/s10086-022-02038-1)
  separates thread engagement, thread play, bolt cylinder, bolt head, and
  washer embedment compliance in a series model, and checks overall tightening
  stiffness against specified timber/washer test cases. It supports that
  component decomposition; its reported validation does not furnish a law for
  the current four stacks.
- Zhang, Gao, and Xu's [2016 thread-stiffness method](https://journals.sagepub.com/doi/10.1177/1687814016682653)
  compares its analytical model with FE and tensile-test results, but its
  equations are stated for ISO metric triangular threads. That publication
  alone does not validate transfer to a Unified inch thread. Any such transfer
  needs a separately documented applicability argument or validation.

The [official CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.pdf)
documents available element and constraint formulations. The locally pinned
copy supplies the exact edition used here; neither version validates this
application-specific thread law or its physical applicability.
