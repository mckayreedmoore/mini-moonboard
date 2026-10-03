# Handoff checkpoint — 2026-10-01

This packet is source-only. No CAD import, Boolean, STEP export, mesh, solver
input freeze, native run, Docker command, or output artifact was produced by
this worker. Runtime, geometry, mesh, and native readiness are all **false**.

Files written in this owned directory:

- `README.md` — R75/H1 source-bound mesh plan, exact catalog washer OD and
  original envelope distinction, two separate nut/washer stacks, resource
  bounds, mesh oracles, scope limits, and the source-normal output-frame note.
- `source-pins.json` — source hashes and historical Gmsh runtime receipt. The
  current `fea/floor_contact.py` pin was corrected to the observed
  `f72c9de2f046f6f207974779de555bfa37f5964484ffae2293fc450c35025825`.
- `prepare.py` — pure source/hash/frame/demand and analytic-shape preparation
  record producer. It verifies the conditional profile, both K12 seat actions,
  the external numerical receipt, and its source inputs. Its latest changes
  have not been executed or tested.
- `mesh_oracles.py` — pure TRI6 area/resultant integration, independent
  C3D10-to-TRI6 exterior ownership and connected-component checks, and a
  fail-closed mesh-only report/deck validator. No CAD or solver imports.
- `test_source_oracles.py` — synthetic arithmetic, frame, TRI6, topology,
  report-scope, and deck-keyword tests.
- `produce_mesh.py` — **UNREADY / UNVERIFIED** parent-gated five-solid geometry
  and mesh producer draft. It has not been syntax-checked or tested after its
  latest edits and has never been executed. Do not launch it.

The six source-only unit tests passed on an earlier snapshot. The preparation
and producer modules changed after that run, so this checkpoint does not claim
that the current packet passes tests. An earlier `py_compile` passed before the
producer was wired; it does not cover the current file contents. No current
end-to-end preparation record has been emitted.

The source-only review found the parent nut profile internally consistent and
matched an independently integrated H1/H2/washer oracle. The source crosscheck
binds K12 actions 64.40226 N and 20.52895 N to the two separate receiver seats.
The source member round-trip summary reports 34 valid natural faces, with
`PLANE` and `CYLINDER` areas; the producer allowlist also includes `Cone` and
rejects every other face type. The R75 crop and both stacks remain hypotheses;
no washer/nut capacity, material behavior, or acceptance claim follows.

The main unresolved implementation risk is Gmsh 4.12.1 OCC Boolean face-map
and analytic-signature behavior. The draft requires parent-known-answer
qualification for face ancestry, analytic plane/cylinder/cone signatures,
TRI6 extraction, and Gauss5 Jacobians before a future run. It has not received
that qualification. The parent reported its read-only Docker image inspection
failed with permission denied; no workaround or escalation is allowed. Continue
only with documentation/source work until a fresh authorized runtime
preflight, exact parent freeze, and one-run reservation exist.

The included-usage checker last returned 98% used at `2026-10-01T21:54:11Z`.
Stop if the next fresh check is stale, unknown, or at least 100%. No Git action
was taken.

## Primary continuation: source-only check and correction

This later observation supersedes the untested/syntax-unknown status above;
the original worker checkpoint remains preserved as history. Primary parsed
all four Python modules and passed the six existing synthetic tests. Running
the pure preparation then exposed a real contract-guard mismatch: the code
required absent wording `R75 mm`, while the immutable pinned contract says
`radius 75 mm`. Primary reproduced it with a full-preparation regression,
changed that one guard phrase, and passed all seven tests. No source pin,
contract, candidate geometry or mesh-producer byte changed.

The pure CLI now emits `source-preparation-parent-check-2026-10-01.json`.
All pinned source hashes, code bindings and its self-hash were checked, and
an independent CLI replay is byte-identical. Details and exact current code
hashes are in [the parent receipt](../mvp-integration-2026-10-01/washer-source-preparation-parent-validation.json).

The real Gmsh producer remains unexecuted and unqualified. Syntax and these
source/synthetic tests do not establish runtime, geometry, mesh or native
readiness. Independent review and the small OCC/signature/TRI6/Gauss5
known-answer qualification remain pending before any freeze/reservation.
No CAD, Gmsh, mesh or native job was started. The parent restored read-only
Docker/tmux access after the earlier permission failure, but that alone does
not make this packet ready. All 47 criteria remain pending.
