# Eight-step roadmap

Only one step is implemented at a time. A later step begins only after explicit
approval and after the current step is verified, committed, and pushed.

1. **Specification — complete.** Define the business problem, metrics, privacy
   boundaries, non-goals, success criteria, risks, and initial architecture.
2. **Detection pipeline — complete.** Benchmark candidate libraries and
   implement a replaceable OpenCV-compatible detector returning bounding boxes
   and confidence values.
3. **Ephemeral tracking — complete.** Add a justified tracker with
   process/session-local IDs and tested expiration behavior.
4. **Aggregation — not started.** Produce time-windowed occupancy, dwell, zone,
   and heatmap metrics with aggregate-only persistence.
5. **Fairness and robustness evaluation — not started.** Use licensed data and
   valid labels to measure performance by conditions and defensible subgroups.
6. **Dashboard — not started.** Present occupancy, dwell, zone, and heatmap
   aggregates without raw faces or stable identifiers.
7. **Privacy architecture write-up — not started.** Complete threat boundaries,
   retention rules, lifecycle evidence, and explicit non-goals.
8. **Portfolio polish — not started.** Refine the narrative, tests, architecture
   visual, reproducibility notes, and consented demo material.

## Gate for Step 2

Before Step 2, explicitly approve beginning detector work. Detector selection
must be based on a small benchmark rather than assumed, and no demo input may be
downloaded until its license, consent basis, privacy implications, and
repository suitability are reviewed.
