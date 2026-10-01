# Step 6 tool and operation feasibility, attempt 01

Status: **no complete reversible route demonstrated** for the six candidate
nut/nut-washer slide intersections or the four retained lumber-leg bolt/wire
withdrawals. This screen uses the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry and leaves its geometry,
axes, and existing operation register unchanged.

The generated [JSON screen](tool-route-feasibility.json) joins the current
operation register with the exact-component access report, the prior captured-
nut motion probe, the retained wire report, the current hardware schedule, the
thread-boundary note, and the wire service note. Each input digest is recorded
in JSON. It records source-backed tool profiles as candidate dimensions only;
no tool is selected or fit-qualified.

## Findings

- The direct axial nut and nut-washer slides have six source-solid hits on four
  candidate axes. Two bottom-center axes hit their center principal cleats;
  two bottom-outer axes hit their knee inner blocks.
- An existing CAD probe clears one local escape path per affected axis: remove
  the bolt headward, move the nut/washer pair sideways about 49–56 mm, then
  continue 25 mm nutward. This assumes thread disengagement and continuous part
  capture. The final segment is not a reachable staging location, and the
  reverse installation path was not screened.
- Four retained 1/2-in lumber-leg bolt withdrawals each have three modeled
  wire-sweep intersections against `wire_010_A10_A11` or
  `wire_130_K10_K11`. The fixed wire solids do not prove that flexible cable is
  physically blocked. The proposed service state depends on real connectors,
  anchors, slack, bend limits, the PWR1 branch, and a reversible string removal
  and refeed route that the available wiring records do not specify.
- The existing tool proxy is FACOM 34.7/16: FACOM's public product data list a
  short 7/16-in wrench with 15/75-degree inclined heads, 22-mm head width,
  3-mm thickness, and 100-mm length. The previous screen uses those three
  dimensions as a simplified envelope, not the exact wrench shape. It does not
  clear all approach/turn proxy checks on the affected candidate axes.
- A Wera 6000 7/16-in wrench is another real profile with a 30-degree open-end
  return angle, 80-tooth ring, and larger 25-by-6.3-mm open-end and
  22-by-7.5-mm ratchet-head envelopes. A Wera 3/4-in profile is relevant to
  Bolt Depot's unselected 1/2-13 lumber-leg bolt comparator, whose head is
  3/4 in across flats. The old 7/16-in proxy cannot establish fit for those
  retained bolts. Neither Wera record publishes a numeric tool torque capacity
  or a fit for these joints.
- The four candidate axes are in the schedule's 152.4-mm ordinary length
  group. The thread-boundary note's conditional 1/4-20 class check places the
  earliest nut bearing plane 4.7592 mm headward of `LG,max`; it does not give
  delivered thread coordinates or matched-nut engagement. Threading the nut
  fully off the shaft therefore remains unproven.

The possible operation routes are still worth screening if the missing inputs
become available: use a correctly sized tool pair with a captured, reachable
nut staging route; temporarily remove and reinstall the blocking wood members;
or stage the affected LED strings before frame-bolt service. None currently
has source-backed evidence for a complete operation from initial tool approach
through restored joint and wiring state.

## Minimum evidence to continue

1. Select matched bolts, nuts, and washers for the four candidate axes. Obtain
   delivered or guaranteed bounds for complete thread, runout, tip, and nut
   active-thread/chamfer regions so full engagement and disengagement can be
   checked.
2. Select the turning and counterhold tools, their exact profiles, tool access
   direction, usable stroke, torque/force method, and the paired workspace at
   each affected axis.
3. Establish how the free nut and washer stay captured through the local
   lateral/axial move, where they can be restrained, and how the reverse path
   installs them again. Include a supported structure state during removal.
4. If a blocker is removed instead, check that block's own tool/fastener access,
   member removal/insertion motion, and supported frame states.
5. For the retained bolts, identify the actual harness and connector parts,
   boundary and PWR1 routes, anchors, slack/bend limits, and a reversible
   disconnect, restraint, refeed, and restart procedure. Then screen the staged
   cable with bolt withdrawal and reverse insertion.

## Public manufacturer and product sources

- FACOM 34.7/16 product page and inch-series dimension table describe the
  wrench and its profile. Their URLs are in the JSON source list.
- Wera 6000 Joker imperial wrench product page lists the 7/16-in and 3/4-in
  dimensions and ratchet details. Its URL is in the JSON source list.
- Bolt Depot items 2569 and 407 are the unselected 1/4-20 and 1/2-13 schedule
  comparators. Their URLs are in the JSON source list.
- MoonBoard V5 LED installation guide describes string installation,
  connectors, and damaged-LED repair, but no reversible whole-string service
  operation. Its URL is in the JSON source list.

## Reproduce and verify

```sh
python3 produce.py --write
python3 produce.py --verify
```

Run those commands from this attempt directory.

The producer validates four target axes, six direct slide intersections, one
clear local captured-nut diagnostic per affected axis, and three modeled wire
component hits for each retained bolt axis. Machine JSON SHA-256:
`f7848741b4e3edbc15b36084bc5a89f884cea38e1f39c8edfe26527e4eb1b292`.
