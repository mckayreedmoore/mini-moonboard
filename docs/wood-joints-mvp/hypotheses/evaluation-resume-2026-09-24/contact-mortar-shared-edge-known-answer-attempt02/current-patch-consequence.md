# Consequence for the proposed current-joint MORTAR route

The parent reread the existing [current-patch eligibility audit][eligibility]
and independently recounted contact-node-set memberships in attempt09's
`contact-fragment.inc`. Its SHA-256 matches the contact manifest:
`35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24`.
The fragment retains the original surface-to-surface penalty formulation;
it is not a new MORTAR deck.

Across its 35 slave and 35 master sets, seven node IDs are shared by slave
sets: `7, 12, 122, 123, 124, 125, 126`. There are also 752 unique cross-role
node IDs. Together these make 759 unique overlap IDs and 766 slave-list
occurrences flagged by the source's overlap rule. The recount agrees with
the preserved eligibility audit. That audit, rather than this membership
recount, supplies the face-topology and perpendicular-normal checks.

The [failed small fixture](RESULTS.md) therefore concerns a contact-node
pattern present in the proposed current-joint route. It does not prove that
the full patch fails in the same way, quantify its error, or establish a
physical joint failure. It does prevent using the single-interface fixture's
pass as justification for changing all current-joint pairs to MORTAR. The
representative sharing-pattern gate remains failed/unresolved; no full-joint
MORTAR launch is ready from this evidence.

Keep the current geometry, surfaces and roles intact. Removing boundary
contact, relabeling physically common nodes, or adding restraints would
require a separately justified representation and verification; it is not
an output correction. The unchanged penalty controls are a bounded method
comparison, not a current-joint acceptance result.

[eligibility]: ../ordinary-external-force-transient-attempt04-diagnostic/mortar-current-patch-eligibility.md
