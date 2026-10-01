# Static regression result, attempt 01

The frozen byte-level regression failed. Both native execution and trace capture completed, but `coupon.cvg` and clock-normalized `coupon.frd` differ from the historical reference. The failure and original acceptance gates remain unchanged.

Five other compared files are byte-identical, and `ResultsForLastIterations.frd` matches after the frozen clock normalization. All 24 inherited diagnostic events match exactly. The 1,680 mapped rows and 1,680 corrected-trial rows cover all 16 native convergence states with exact active-point counts; energy was disabled and remains unavailable.

Parent review found that the historical reference used two solver threads while this capture used one. This confounds attribution to the patch. A separate same-thread comparison is required; no numerical tolerance is added to this attempt.

The following diagnostic quantifies the differences without granting acceptance:

```json
{
  "status": "POST_RUN_DIAGNOSTIC_ONLY_FROZEN_FAILURE_RETAINED",
  "changed_frd_components": {
    "FORC": 864
  },
  "max_absolute_frd_difference_by_field": {
    "FORC": 2.4609220000000003e-12
  },
  "max_absolute_changed_value_by_field": {
    "FORC": 1.62359e-12
  },
  "other_non_clock_line_differences": [],
  "run_configuration_confound": {
    "reference_threads": 2,
    "new_threads": 1,
    "reference_cpu_limit": 2,
    "new_cpu_limit": 1,
    "reference_memory": "4g",
    "new_memory": "1g"
  },
  "cause": "Not established. Different thread settings confound attribution of the numerical differences to instrumentation.",
  "next_check": "Separate frozen controlled comparison with identical one-thread settings and unchanged byte-level gates.",
  "joint_acceptance": false
}
```

No current-joint mechanics, force output or fabrication is qualified.
