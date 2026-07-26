# Aggregate analytics and storage

The aggregation layer receives temporary track snapshots in memory and emits
coarse `AggregateWindow` records. Temporary IDs are dictionary keys only while a
process is calculating metrics; they are not fields in the output model or
SQLite schema.

Each aggregate window can contain:

- occupancy sample count, sum, average, and peak;
- aggregate scene entries and exits;
- dwell count, total, average, and histogram;
- zone entry, exit, and total dwell;
- normalized counts in coarse spatial heatmap bins.

The default window is five minutes and cannot be configured below one minute.
Heatmap resolution and reporting suppression should be chosen for the physical
space and expected traffic. Coarser bins reduce linkage risk but do not
eliminate inference from time and location.

## SQLite boundary

`AggregateStore` uses parameterized SQL and a versioned aggregate-only schema.
There is no table or column for a temporary track ID, bounding box, trajectory,
image, crop, embedding, identity, or source path. Generated databases live
under `artifacts/` and are ignored by Git.

```bash
face-analytics init-db --db artifacts/analytics.sqlite3
face-analytics clear-aggregates --db artifacts/analytics.sqlite3
```

The clear command deletes generated aggregate windows. Operational backups and
retention schedules remain deployment responsibilities and must be documented
for a real installation.
