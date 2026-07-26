# Project specification

## Purpose

Build a portfolio-quality retail and event foot-traffic analytics system that
produces useful aggregate engagement signals while deliberately avoiding
identity recognition and persistent biometric data.

## Goals

1. Measure occupancy, entries and exits, dwell-time distributions, zone traffic,
   heatmaps, and time-of-day patterns.
2. Process raw frames in memory and discard them after the current operation.
3. Use temporary tracking identifiers only within one running session and
   destroy them when tracks expire.
4. Persist only aggregate analytics needed for reporting.
5. Measure detector robustness and fairness with licensed evaluation data and
   valid labels, reporting uncertainty and failure modes.
6. Present a credible business use case, inspectable architecture, reproducible
   tests, and appropriately limited claims.

## Intended users

- Retail operations teams comparing traffic and dwell patterns by area or time.
- Event operators monitoring congestion and engagement zones.
- Analysts producing aggregate operational reports.
- Engineers and privacy reviewers assessing data lifecycle controls.

## Business value

- Inform staffing and operating-hour decisions from peak occupancy.
- Compare zone engagement without maintaining visitor profiles.
- Identify layout bottlenecks and underused areas.
- Evaluate campaigns or event programming using aggregate trends.
- Demonstrate a lower-retention alternative to identity-based analytics.

The project will not claim that aggregate metrics alone establish causation or
that ephemeral tracking makes a deployment anonymous.

## Metrics

### Product metrics

- Current, average, and peak occupancy per time window.
- Entry and exit counts at configured boundaries.
- Dwell-time distribution, reported in privacy-preserving aggregate bins.
- Zone entries, exits, and aggregate dwell time.
- Spatial heatmap counts with configurable resolution and suppression rules.
- Processing throughput and latency.

### Quality metrics

- Detection precision and recall on a documented evaluation set.
- Recall by lighting, scale, occlusion, and pose where labels permit.
- Subgroup performance only when subgroup labels have a defensible consent,
  licensing, and ethical basis.
- Tracking continuity and expiration behavior without cross-session matching.
- Aggregation correctness and resistance to double-counting.

## Non-goals

- Identifying, naming, authenticating, or recognizing a person.
- Face matching, persisted embeddings, face databases, or watchlists.
- Cross-camera or cross-session re-identification.
- Inferring demographic, emotional, health, or sensitive personal traits.
- Persisting production frames, face crops, raw footage, or stable identifiers.
- Claiming universal accuracy, fairness, anonymity, or legal compliance.
- Making high-stakes decisions about individuals.

## Privacy and retention boundaries

- Hold each frame in memory only for its immediate processing operation.
- Emit detections as bounding boxes and confidence values, not crops.
- Scope tracking IDs to the current process/session; expire and destroy them.
- Never reuse a tracking ID as evidence that a person has returned.
- Convert track events to aggregate windows before persistence.
- Persist no raw frames, face crops, embeddings, identities, or track histories.
- Apply minimum-count or suppression rules before exposing small-group slices.
- Document the demo input's license, consent basis, and local retention before
  it is downloaded or used.
- Restrict fairness evaluation to licensed datasets and defensible labels.

Residual risks include unauthorized camera capture, insecure runtime memory,
misconfigured logs, overly granular aggregates, dataset bias, inference from
location and time, and operators combining outputs with external information.

## Success criteria

- The implemented data path can be traced from an in-memory frame to aggregate
  output with no persistence path for frames, crops, embeddings, or stable IDs.
- Automated tests cover detector interfaces, track expiration, aggregation, and
  privacy-sensitive persistence boundaries as those components are introduced.
- A reproducible evaluation reports quality by documented conditions and valid
  subgroups without overstating conclusions.
- The dashboard exposes aggregate metrics and no raw faces or stable identities.
- Documentation states business assumptions, data provenance, limitations,
  retention rules, and residual privacy risks.
- The public repository contains no secrets, restricted data, biometric
  artifacts, raw footage, face crops, generated databases, or oversized model
  files.

## Principal risks and mitigations

| Risk | Initial mitigation |
|---|---|
| Raw frames or crops are written accidentally | In-memory interfaces, deny-listed artifact paths, lifecycle tests, and staged-file review |
| Temporary IDs become persistent identifiers | Session-local ID ownership, explicit expiration, and no track-level persistence schema |
| Aggregates reveal small groups | Time/space coarsening and minimum-count suppression before reporting |
| Dataset use is unlawful or misleading | License, consent, provenance, and repository-suitability review before adoption |
| Uneven detector performance | Condition- and subgroup-aware evaluation where labels are valid |
| Accuracy or privacy claims are overstated | Publish measured results, uncertainty, residual risks, and known failure modes |
| Scope drifts into recognition | Explicit non-goals, architecture review, and prohibited-artifact checks |

## Step 1 decisions

- Use Python 3.11+ with a `src` package layout.
- Keep the detector replaceable and OpenCV-compatible in the next step.
- Defer the detector library and demo-input decision until benchmarking and
  dataset due diligence are required.
- Prefer Streamlit for the later dashboard unless a future portfolio requirement
  justifies a custom frontend.
