# Privacy-safe screenshot and recording instructions

Use only the synthetic aggregate demo:

```bash
face-analytics clear-aggregates --db artifacts/analytics.sqlite3
face-analytics generate-synthetic --db artifacts/analytics.sqlite3 --windows 48
face-analytics dashboard --db artifacts/analytics.sqlite3
```

Before capturing:

- Confirm the yellow “Synthetic demonstration data” banner is visible.
- Close tabs, notifications, terminal panes, and browser UI containing personal
  names, tokens, local paths, or unrelated projects.
- Do not enable a webcam or open a real video.
- Do not include dataset images, face crops, or evaluation manifests.
- Use a clean browser profile and crop the capture to the dashboard.

Capture a 10–20 second scroll showing the summary metrics, traffic chart, dwell
distribution, zones, and heatmap. Export a reasonably sized GIF or MP4. Review
every frame for personal information before sharing. Generated media should be
committed only when it contains no people, has clear ownership, and remains
small; this repository currently commits instructions rather than media.
