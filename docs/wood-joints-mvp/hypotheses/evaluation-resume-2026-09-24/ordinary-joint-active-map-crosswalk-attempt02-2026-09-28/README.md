# Ordinary-joint active-map crosswalk, attempt02

## Status and scope

This append-only successor addresses the non-blocking attempt01 review note
that its recorded offline replay had no saved script or captured command and
output. The standard-library-only replay is [`replay.py`](replay.py), and its
deterministic successful output is preserved in
[`replay-output.txt`](replay-output.txt). The source pins bind the four
attempt01 packet artifacts; the attempt01 packet and source manifests are
also checked by the replay.

The replay rechecks the attempt01 SHA256SUMS entries, its 35 source pins and
`crosswalk.json` source-hash parity; the 14-artifact base freeze and its
case-deck, case-lock, bundle-lock and base-freeze digest chain; all seven
direct deck includes and their source/freeze pins; and the ordered A00–A03
nut-map, inventory and crosswalk joins. It also parses the nut equation cards
and the four `*RIGID BODY` cards, recomputes the 3D and 6D coordinate-basis
inverse and determinant, checks the N+ port controls, deck boundary scalars
and bolt-axis transforms, checks the A00 fixture hashes, scope and transformed
angular drive, and confirms the recorded A09 no-accepted-increment output
sizes and unfrozen follow-on status. Acceptance, criteria and release flags
are required to remain false.

No attempt01 bytes, source inputs, geometry, queue, ledger, plan or criteria
were changed. This packet ran no solver and no geometry operation. The replay
confirms source binding and arithmetic for the inspected records only. It
closes **no mechanics or acceptance gate** and grants no release.

## Invocation

From the repository root, run this exact command to regenerate the preserved
output:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28/replay.py > docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28/replay-output.txt
```

The script locates the repository by walking from its own path to `.git`, so
the Python command can also be run from another working directory if given the
script's repository path. It uses only the Python standard library and reads
the frozen sources; the shell redirection above writes only this packet's
`replay-output.txt`.

Check the packet payload manifest from this directory with
`sha256sum -c SHA256SUMS`. Check the four attempt01 pins from the repository
root with
`sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28/SOURCE-SHA256SUMS`.
The attempt02 SHA256SUMS follows the usual non-self-referential convention:
it covers README.md, replay.py, replay-output.txt and SOURCE-SHA256SUMS, and
does not list itself.

## Hash-bound limits

The saved output establishes that the replay passed against the bytes pinned
by the attempt01 source manifest and the current base freeze at replay time.
It does not make those sources authoritative beyond their recorded scope or
prove that their inputs are physically adequate. The A00 fixture remains a
small rotational known-answer check of A00 and its optional carrier. The A09
static N+ attempt still accepted no increment, its recorded `.dat` and `.sta`
files are empty and its `.frd` file is 80 bytes. The proposed physical-mass
transient remains unselected and unfrozen.

The crosswalk remains input-composition, source-identity and coordinate
arithmetic evidence. It establishes no accepted ordinary-joint response,
equilibrium, contact transfer, engagement, sensitivity, demand/capacity result,
criteria disposition, mechanical acceptance, joint acceptance or release.
