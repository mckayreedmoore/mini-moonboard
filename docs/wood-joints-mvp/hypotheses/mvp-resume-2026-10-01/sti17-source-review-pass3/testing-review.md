# STI17 source testing review — pass 3

Target: `source-review-target.json`

Target SHA-256: `008ba73850288a620561a26558001f913079a7e904b85d029d16e07b1dd0fcf7`.

Pin verification: all 15 target inputs matched their declared byte sizes and SHA-256 digests before source inspection.

## Finding

**P2 — cleanup can forcibly remove a container this launch did not create.**

`launch_sti17_coupon.py:137, 235–264` derives a predictable Docker name from `run_id`. If another container already owns that name, `docker run --name ...` fails; the following name-filtered `docker ps` finds the existing container, and exception cleanup unconditionally runs `docker rm -f <name>`. This can terminate and remove unrelated work during the one-shot coupon attempt. The launcher then records cleanup as terminal even though it did not own the removed container.

Capture the container ID created by this invocation and clean up only that ID. If Docker reports a name collision before creation, fail closed without removing the existing container. Add mocked coverage for pre-existing-name collision and verify cleanup leaves that container intact.

## Review limits

Reviewed only packet-scoped sources and provenance inputs. Parent reports 27 tests / 48 subtests and Ruff passing; tests were not rerun. Hard-stop known-answer qualifies GNU `timeout` in immutable base image only. STI17 image build, final-image timeout qualification, and free-C3D20 native coupon remain unperformed. Source readiness does not establish runtime behavior or mechanical acceptance.
