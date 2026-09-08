# Repository working agreements

## Agent workflow

- Automated agents may work and commit locally at any time. Publish outside
  Monday–Thursday 07:30–18:00 America/Denver, accounting for daylight saving.
- Configure the local workflow guard with `git config --local core.hooksPath
  .githooks` after preserving any existing hooks. The guard applies to pushes
  from this configured clone; it is not agent identity detection or a scheduler.
- Preserve other contributors' work and verify remote state before publishing.
  History changes require explicit user direction, a local recovery reference
  and verification that only the requested metadata or content changed.

## Current hardware decision

Develop threaded inserts with machine screws for removable face and kicker
panels where receiver geometry and connection resistance support them. Retain
existing through-bolts/nuts. Retain manufacturer-specified structural screws in
commercial brackets; insert substitution does not retain their published ratings.
Do not claim the insert concept is installed, qualified or build-ready before
model, hardware schedule and checks have actually been updated.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal prose.
Preserve changes belonging to other agents, including untracked files.
