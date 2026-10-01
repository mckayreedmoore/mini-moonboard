# Stock Code_Aster bounded trial

The completed primitive trial and its limitations are recorded in
[RESULTS.md](RESULTS.md).

Owner authorized proceeding after the September 27 solver reuse assessment.
This trial concerns numerical methods for the reviewed wood-joint development
lane only. It does not alter or accept the selected baseline or the reviewed
frame geometry. The parent owns input freezes, serialized native execution,
and final interpretation. Luna agents at maximum reasoning effort prepare
independent fixtures; they do not run native jobs.

The initial scope is small known-answer checks for orthotropic elasticity,
linear load/displacement maps, constrained inertia with a zero-density carrier,
contact opening/compression/reopening, and free impact. Inputs, tolerances and
analytical expectations must precede each run. Changed inputs create a new
attempt. Successful process exit is not mechanical validation.

The installation target is the prebuilt `simvia/code_aster:17.4.0` image linked
by the [official download portal](https://open-simulation-center.org/downloads/code_aster/code_aster/17.4.0).
The portal identifies the version as stable and its linked container as a
community distribution, not an EDF nuclear-qualified binary. The
[publisher's instructions](https://hub.docker.com/r/simvia/code_aster) describe
the batch interface. We will pin the pulled digest and check the runtime
version rather than relying on moving `stable` tags. No solver source patch
or custom material implementation is part of this trial.

Passing primitive fixtures permits further applicability work; it does not
validate the actual A09 nut map, curved bore contact, complete joint response,
timber resistance, or frame load sharing. Those require their own evidence.
Any later representative-patch run depends on readiness of those methods and
preservation of the reviewed inputs.
