# Privacy-safe Streamlit dashboard

The dashboard reads `AggregateStore` records through a pure preparation layer.
It displays current and peak occupancy, entries, exits, dwell distribution,
time-of-day traffic, zone aggregates, data freshness, and a coarse normalized
heatmap. It has no input or view for frames, face crops, temporary IDs, or
individual trajectories.

Generate deterministic aggregate-only demonstration data:

```bash
face-analytics generate-synthetic \
  --db artifacts/analytics.sqlite3 \
  --windows 48 \
  --seed 7
```

Start the dashboard:

```bash
face-analytics dashboard --db artifacts/analytics.sqlite3
```

Clear generated records:

```bash
face-analytics clear-aggregates --db artifacts/analytics.sqlite3
```

Synthetic rows are labeled in SQLite and visibly identified in the interface.
They contain no images or identity-like records. The dashboard caches aggregate
queries for 15 seconds only and handles an empty database with a safe setup
message.
