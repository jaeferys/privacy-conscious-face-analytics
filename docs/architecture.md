# Implemented architecture and data flow

## Required lifecycle

```mermaid
flowchart LR
    subgraph volatile["Volatile processing boundary"]
        F[OpenCV frame source<br/>memory only]
        D[Replaceable detector<br/>boxes + confidence]
        T[Centroid/IoU tracker<br/>session-local ID]
        A[AggregateAnalytics<br/>time, zone, heatmap windows]
        F --> D --> T --> A
    end

    A --> P[(AggregateStore / SQLite<br/>aggregate rows only)]
    P --> UI[Streamlit dashboard<br/>aggregate views]
    F --> XF[Discard frame after operation]
    T --> XT[Expire or reset track]
    XT --> XI[Destroy temporary ID]

    classDef prohibited fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d;
    X[No crops, embeddings,<br/>identity labels, or face database]:::prohibited
    volatile -. prohibited boundary .-> X
```

`frame -> detection -> ephemeral tracking -> aggregation -> frame and track discarded`

## Component responsibilities

| Component | Receives | Emits | May persist |
|---|---|---|---|
| Frame source | Consented live/demo input | In-memory frame | Nothing |
| Detector | In-memory frame | Bounding boxes and confidence | Nothing |
| Ephemeral tracker | Current detections and volatile state | Session-local track events | Nothing |
| Aggregator | Track events and configured zones | Windowed aggregate metrics | Aggregate metrics only |
| Dashboard | Aggregate queries | Charts and summaries | Nothing beyond aggregate settings |

## Implemented modules

- `frame_sources.py`: consented webcam, explicit video, and generated in-memory
  frames; no write method.
- `detection/`: typed detector protocol, lazy MediaPipe adapter, and OpenCV
  fallback.
- `tracking/`: geometry-only ephemeral association with missed-frame and
  monotonic-time expiration.
- `analytics/`: transient per-track calculations converted into aggregate
  windows, zones, dwell bins, and coarse heatmaps.
- `storage/`: parameterized, versioned SQLite aggregate schema.
- `evaluation/`: annotation-driven condition metrics with frames discarded after
  inference.
- `dashboard/` and `demo/`: aggregate views and image-free synthetic rows.
- `privacy_checks.py`: repository and schema regression audit.

## Trust and retention boundaries

- The frame source, detector, and tracker are inside a volatile processing
  boundary. Logging and exception handling must not serialize their inputs.
- Tracking IDs exist only in process memory, are not globally unique, and are
  removed with expired track state.
- The persistence boundary accepts aggregate records only. It must reject image
  bytes, crops, embeddings, identity fields, and per-track histories.
- A later dashboard must query aggregates without exposing live or stored face
  imagery.
- Demo footage remains an unresolved dependency. Its license, consent basis,
  privacy implications, and repository suitability must be approved before use.

## Residual risks

This design minimizes persistence; it does not by itself guarantee anonymity or
legal compliance. Runtime compromise, overly granular aggregates, camera
placement, dataset provenance, operational access, and external data linkage
remain relevant. Each implementation step must test its own lifecycle boundary
and document limitations.
