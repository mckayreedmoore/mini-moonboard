# Independent result review

The Luna/max reviewer `/root/section_output_review` performed a read-only
post-run audit on September 27, 2026. No material correction to `RESULTS.md`
was identified.

All 14 frozen inputs and all 13 recorded native output hashes match. The root
freeze hash matches the file, and the root run entry exactly equals the case
execution record. The executed deck is unchanged.

STA contains one rejected `1U` row at zero total and step time; CVG contains
iterations 1–201. Native output ends with `too many iterations needed`.
Both exit codes are 201, `OOMKilled=false`, and `stop_reason=null`; recorded
runtime and output remain below the bounds. The multiplier-removal warning
names nodes 1, 4 and 24 in both surface orderings. The reviewer also verified
the archive/member hashes and cited `remlagrangemult.f` source behavior.

The separate unchanged penalty controls are an appropriate bounded next
comparison with existing gates and stop-on-first-failure behavior. This audit
confirms a failed method fixture, not an accepted equilibrium or physical
joint failure. It changes no structural criterion or release status.
