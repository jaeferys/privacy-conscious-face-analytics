# Portfolio summary

## One-sentence pitch

Privacy-Conscious Face Analytics turns consented retail or event video into
aggregate occupancy, flow, dwell, zone, and heatmap insights while preventing
identity persistence by design.

## Problem and audience

Retail and event operators often want traffic and engagement evidence, but
identity-oriented computer vision collects more sensitive data than the
operational question requires. This project demonstrates a narrower system for
store managers, event operators, analysts, privacy reviewers, and engineers.

## Engineering story

The pipeline separates frame ingestion, replaceable detection, geometry-only
ephemeral tracking, in-memory aggregation, aggregate-only SQLite persistence,
condition-aware evaluation, and an aggregate Streamlit dashboard. MediaPipe is
the preferred detector on supported Python versions, with OpenCV's bundled Haar
cascade as a dependency-light local fallback. The tracker uses centroid distance
and IoU instead of appearance features.

Privacy constraints are executable: the detection and tracking schemas contain
no identity or embedding fields, IDs expire and reset, the database schema is
inspected in tests, and a repository audit rejects sensitive artifacts and
frame-write APIs.

## Evidence

- Deterministic tests span detection, expiration, analytics, storage,
  evaluation, dashboard preparation, the integrated pipeline, and privacy
  regressions.
- Ruff lint/format and strict mypy checks.
- CI package build and CLI/privacy smoke checks.
- Live Streamlit health verification with synthetic aggregate data.
- Eight focused milestone commits pushed to the public repository.

## Honest limitations

- No real-world WIDER FACE evaluation has been run because dataset terms and
  image provenance require review.
- Demographic fairness is not measured and demographic traits are not inferred.
- The OpenCV Haar fallback is less robust than the intended MediaPipe path.
- Entry/exit counts currently represent track lifecycle within one camera view,
  not calibrated directional doorway crossings.
- Operational camera governance, host security, backups, access controls, and
  legal assessment remain deployment responsibilities.

## Resume-ready talking points

1. Designed a privacy-minimizing computer-vision lifecycle with volatile frames,
   expiring geometry-only tracks, and aggregate-only persistence.
2. Built a modular Python pipeline and recruiter-safe Streamlit demo using
   deterministic synthetic aggregate data.
3. Treated fairness and robustness honestly by shipping a tested evaluation
   harness, condition-level metrics, and explicit evidence gaps rather than
   invented benchmark claims.
