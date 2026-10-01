# RF-to-opening known-answer fixture, attempt 02

This is a two-branch method fixture for the zero-offset scalar spring map used
by `normal_contact`. Its exact CalculiX 2.23 input is frozen in `native/` and
remains unlaunched. An independent pre-run review must approve that exact
freeze before the parent records one serialized native ledger entry.

Each branch has a wood-side host fixed at `U3=0`, a panel-side host free in
`U3`, and one host-only support `SPRING2` with `K_host=1,000,000 N/mm` to a
fixed anchor. The isolated contact `SPRING2` has `K_contact=179183.109378
N/mm`; its two scalar DOF-1 endpoints use the same MPC projection as
`normal_contact`, mapping to the wood and panel host U3 values. Contact
endpoints have no direct load or support. Panel-host U1 and U2 are fixed.

For a prescribed positive opening `g`, the host-side load is derived from the
parallel stiffness:

```text
Pz = -(K_host + K_contact) g
U3_panel - U3_wood = -g
F_contact_on_first = K_contact (U3_panel - U3_wood) = -K_contact g
opening = -F_contact_on_first / K_contact
```

| Branch | Known opening | Panel-host CLOAD, DOF 3 | Expected contact force on first | Expected classification |
| --- | ---: | ---: | ---: | --- |
| below | `0.9e-7 mm` | `-0.10612647984402 N` | `-0.01612647984402 N` | Entire inferred interval below `1e-7 mm` |
| above | `1.1e-7 mm` | `-0.12971014203158002 N` | `-0.01971014203158 N` | Entire inferred interval above `1e-7 mm` |

`check_fixture.py` is a read-only post-run audit. It uses the frozen DAT
parser/recovery helper to check the exact MPC equation occurrences, endpoint
isolation, host displacement answers, contact RF action/reaction, contact RF
versus KΔU print intervals, and the `-F/k` interval against both the known
opening and threshold side. It checks the primary contact endpoint pairs for
the two known-answer claims. The host support spring is a separate loading
fixture component; this result validates output-to-opening recovery only. It
does not validate unilateral contact, a frame response, joint capacity, or
mechanical acceptance.

The freeze pins the current solver profile and the source hashes for
`normal_contact`, the deck/output parser, `wood_joint_reduced_force_output`,
and `current_response_run`. `preparation.json` retains those hashes and the
freeze/deck hashes. The only execution allowed by this packet is one parent
serialized native ledger entry after independent pre-run review; `ready_to_launch`
remains false until that review and parent readiness are recorded.
