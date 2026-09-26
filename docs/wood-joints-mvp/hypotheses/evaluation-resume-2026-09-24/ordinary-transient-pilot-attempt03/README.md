# Larger-initial-increment motion pilot

This frozen diagnostic retains the exact twelve physical/load/report/set input
artifacts from attempt02. Only the requested initial time increment changes
from 0.0005 s to 0.0025 s; the adaptive procedure, maximum 0.0025 s, minimum
0.000001 s, final 0.025 s, sampled cubic 0.1 s ramp, ALPHA=0, zero gauge,
frictionless contact and provisional stiff nut engagement remain the same.
The producer snapshot also changes to expose the bounded increment parameter.

The purpose is to test whether a larger first displacement makes the active
contact set more stable than attempt02's approximately 1.7e-8 mm first
increment. This is a hypothesis, not a validated remedy. No convergence
criterion, contact count tolerance, material, geometry or physical support is
relaxed. The parent will use four threads and a four-CPU quota on the same
pinned executable, with the same 10 GiB and 600 s resource bounds. Heavy runs
remain serialized; execution.json is the authoritative execution record.

Neither this pilot nor its input preparation establishes seated response,
quasistatic stiffness, thread engagement, strength or a full-frame case.
