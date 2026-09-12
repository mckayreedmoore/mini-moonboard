# Reinforcement development and modeled T-nuts

The separate `round-reinforcement-development` candidate contains actual CAD
changes to address the preceding base-connection and kicker-equilibrium
findings. It also adds the owner's requested T-nuts. **It is not build-ready.**
The selected `round-structural-development` and its drawings remain preserved.

## What changed

| Component | Development change |
| --- | --- |
| Outer base connections | Two provisional fabricated steel shoes replace two ML24Z angles and twelve SDS25112 screws. Sixteen new through-bolt stacks and sixteen separate bearing plates provide explicit groups for subsequent calculations. |
| Outer rim bearing cuts | Each cut rises 9.525 mm to accommodate the shoe's steel foot on the unchanged header. Other lumber remains the existing single-member stock. |
| Kicker attachment | Five additional SPAX #8 × 2-inch screws enter the existing header on each side at Z = 205.95 mm. Each independent kicker now has nine screws; total panel/kicker count is 66. |
| Hold T-nuts | All 142 locations receive individually selectable Escape three-hole T-nut envelopes, using recorded user dimensions and explicitly provisional barrel/thread details. |
| Hold bolts | Published wood/plastic kit lengths and installation guidance are recorded. Installed bolts remain absent because hold-seat positions and the plastic hold-to-length mapping are unavailable. |

The candidate retains eight original complete leg bolt stacks and 22 ML24Z
angles with their 132 specified SDS screws. It introduces no doubled vertical
stock, panel-seam connection, insert pilot or substituted plywood. New base
bolts have independently selectable heads, nuts and washers.

The [base-shoe detail](steel-base-reinforcement.md) describes the new steel,
rim cut, bolt positions and unresolved fabrication/resistance work. The
[kicker detail](kicker-header-development.md) describes the additional axes and
their existing header receiver. The [hold-hardware reference](moonboard-hold-hardware.md)
records the selected T-nut measurements, CAD assumptions, US bolt-kit lengths
and full-thread-engagement guidance.

## Review artifacts

The combined source is
[`round_reinforcement_frame.py`](../mini_moonboard/round_reinforcement_frame.py).
Its [review report](round-reinforcement-review/review.json) records actual
drilled-body mass at assumed densities, preserved leg connections, added and
removed hardware, nominal interference checks and all 48 retained global
overturning sensitivities. The [open-frame image](round-reinforcement-review/open-frame.png)
and [lower-frame image](round-reinforcement-review/lower-frame.png) show actual
CAD. The lower image crops geometry only for presentation.

The viewer offers this development candidate separately from the selected
design. T-nuts have their own visibility control and individual inspection
names. Its weight includes their modeled steel envelopes, while excluding
holds, hold bolts, unknown retention screws and electrical mass. T-nut internal
threads and barrel dimensions are approximate, so this is not a measured weight.

Current combined results are:

| Check | Result and boundary |
| --- | --- |
| Added hardware against machined bodies and other hardware | No occupied-volume intersections; nominal geometry only |
| Base-specific fit | 16 complete stacks, 32 assumed socket envelopes and 58 retained screw receiver intervals pass the bounded v3 checks |
| Revised mass | 181.206 kg, including 1.530 kg of modeled T-nut envelopes; all material densities are assumptions |
| Global overturning comparisons | 48 of 48 meet the retained 1.5 comparison; minimum factor 1.64459, with no floor or structural qualification |
| Revised kicker equilibrium | 450 of 450 restricted six-component witnesses; largest individual tension 272.8798 N versus the unqualified 304.1245 N head reference |
| Viewer | All 787 parts load; 142 unique T-nuts have working visibility controls and actual click selection |

The [rear-view browser capture](round-reinforcement-browser/assembly-rear.png)
and [selected T-nut capture](round-reinforcement-browser/selected-t-nut.png)
come from the actual application. The scale mannequin is a separate display
object and is excluded from CAD mass and structural analysis.

## What the checks establish

The independent [kicker calculation](round-structural-kicker-revision.md)
assigns each screw force separately and balances three force and three moment
components across the sampled single-hold loads. A feasible distribution
within conditional references is not a prediction of elastic load sharing or
an approved plywood/head resistance. Reactions entering the header and posts
remain loads to carry through the frame, not qualified connection capacities.

The steel-shoe checks establish nominal geometric fit, complete bolt-stack
placement and assumed tool envelopes. The combined check additionally covers
new kicker hardware and T-nuts against machined bodies and other hardware.
These checks do not establish manufacturing tolerance, installation access for
every operation, or actual structural resistance.

Remaining release work includes current frame/member/connection force demand,
steel plate and weld resistance, timber groups and bearing, applicable screw
head resistance, panel/contact behavior, routing tolerances and installation
assumptions. Physical floor tests are not required by the owner's scope;
analytical assumptions do not become measured friction or floor qualification.
Keep [issue #8](https://github.com/mckayreedmoore/mini-moonboard/issues/8) open.
