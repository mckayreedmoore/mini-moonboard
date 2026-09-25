# Third full-layout preparation failure

The parent run stopped after 4.360027 seconds after machining hosts but before
returning a composed layout or running the full-scene diagnostic. The legacy
hardware removal loop read `target_duty_ids` from top-center and bottom-center
objects; those frozen producers expose the already validated `duties` map.
Bottom-outer has `target_duty_ids`. The parent audited all direct local-object
attribute reads against the three actual dataclasses and found only these two
missing attributes. Exact failed sources and unchanged hashes are preserved.
No geometry pass, acceptance or native response is established.
