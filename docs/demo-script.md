# One-to-two-minute walkthrough

1. **Problem — 15 seconds.** “Retail and event teams need occupancy and
   engagement signals, but they usually do not need to identify visitors.”
2. **Architecture — 20 seconds.** Show the README Mermaid diagram. Explain that
   frames stay in memory, detection emits boxes/confidence, geometry-only tracks
   expire, and SQLite receives aggregates only.
3. **Privacy evidence — 20 seconds.** Open `docs/privacy.md` and point to the
   requirement-to-evidence matrix. Run `face-analytics privacy-audit`.
4. **Synthetic demo — 30 seconds.** Generate 48 synthetic windows and start the
   dashboard. Highlight the synthetic-data banner, occupancy, time-of-day
   traffic, dwell distribution, zones, and coarse heatmap.
5. **Evaluation honesty — 20 seconds.** Open `docs/evaluation.md`. Explain that
   the harness tests precision/recall/F1 and condition failures, while real
   WIDER FACE results and demographic fairness remain unclaimed.
6. **Close — 10 seconds.** Summarize the three differentiators: credible
   business value, identity-persistence prevention, and measurable limitations.
