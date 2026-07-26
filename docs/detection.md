# In-memory detection

The detector layer accepts a BGR frame already held in memory and returns only
validated bounding boxes, confidence scores, and frame-relative geometry. The
output model has no identity, embedding, crop, demographic, or appearance
fields. Detection is intentionally independent of tracking and aggregation.

## Implementations

- `MediaPipeDetector` is the preferred lightweight implementation on Python
  3.11 and 3.12. MediaPipe is imported lazily so the rest of the project remains
  usable on unsupported interpreters.
- `OpenCVHaarDetector` is a dependency-free fallback within OpenCV for this
  workstation's Python 3.14 environment. Its bundled cascade avoids downloaded
  weights, but it is a legacy detector and should not be treated as equivalent
  in robustness to MediaPipe.

No implementation saves frames or face crops. OpenCV model and MediaPipe cache
artifacts must remain outside Git; the repository ignore rules cover common
weight formats and cache folders.

## Safe commands

Benchmark a detector on generated blank frames:

```bash
face-analytics benchmark-detector --detector opencv-haar --frames 100
```

Inspect a consented webcam session without saving frames:

```bash
face-analytics inspect-source --detector mediapipe --webcam 0 --max-frames 300
```

Inspect an explicitly supplied local video, which must stay Git-ignored:

```bash
face-analytics inspect-source --detector mediapipe \
  --video /absolute/path/to/consented-video.mp4
```

These commands report throughput and detection counts only. They do not report
accuracy. Camera access and local-video use require an appropriate consent,
license, retention, and access-control basis.
