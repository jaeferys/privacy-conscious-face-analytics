# Release-readiness checklist

## Quality

- [x] Tests pass.
- [x] Ruff lint and formatting checks pass.
- [x] Strict mypy check passes.
- [x] Editable install and source distribution/wheel build are verified.
- [x] CLI help, detector benchmark, synthetic generation, deletion, and privacy
      audit are verified.
- [x] Streamlit starts headlessly and returns a healthy status.

## Privacy and data

- [x] No raw footage, frames, crops, embeddings, datasets, weights, databases,
      secrets, or oversized artifacts are tracked.
- [x] SQLite schema contains aggregate fields only.
- [x] Temporary IDs expire/reset and are never stored.
- [x] Synthetic data is explicitly labeled.
- [x] Dataset/license review remains a gate before real evaluation.
- [x] Demographic inference is absent and demographic fairness is unclaimed.

## Documentation

- [x] README covers setup, demo, architecture, commands, evaluation, privacy,
      limitations, structure, tradeoffs, and licenses.
- [x] Privacy requirements map to implementation and test evidence.
- [x] Demo and recording instructions avoid identifiable people.
- [x] Portfolio summary and honest limitations are present.

## GitHub

- [x] Repository is public.
- [x] CI badge points to the real workflow.
- [x] Eight milestone commits are pushed to `origin/main`.
- [ ] Optional release tag intentionally deferred until the owner reviews the
      repository presentation.
