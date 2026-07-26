# Ephemeral tracking is not identification

`EphemeralTracker` associates nearby detections between adjacent frames using
bounding-box overlap and centroid distance only. It does not inspect appearance,
generate embeddings, match faces, infer identity, or compare people across
sessions.

Temporary IDs are monotonically generated inside one tracker instance. They are
never written to SQLite or operational logs. A track expires after the
configured missed-frame limit or monotonic timeout, and `reset()` destroys all
remaining state. Starting a process or tracker creates an empty session and
does not restore prior IDs.

The in-memory aggregator may receive only:

- temporary ID;
- first-seen monotonic time;
- current centroid;
- last-seen monotonic time;
- active or expired state.

The temporary ID exists only so one running process can calculate dwell and
transitions before converting them to aggregates.

## Residual risks

Geometry-only tracking still links observations within a session. Long
timeouts, broad camera coverage, high-resolution inputs, exposed debug state,
or combining outputs with external data can increase privacy risk. Ephemeral
IDs reduce persistence; they do not make the capture or deployment completely
anonymous.
