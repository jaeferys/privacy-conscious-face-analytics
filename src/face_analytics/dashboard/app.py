"""Streamlit dashboard showing aggregate analytics only."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from face_analytics.dashboard.data import prepare_dashboard_data
from face_analytics.storage import AggregateStore, StoredWindow


@st.cache_data(ttl=15)  # type: ignore[untyped-decorator]
def _load_windows(path: str) -> tuple[StoredWindow, ...]:
    store = AggregateStore(Path(path))
    store.initialize()
    return store.list_recent(limit=500)


def run() -> None:
    st.set_page_config(
        page_title="Privacy-Conscious Face Analytics",
        page_icon="📊",
        layout="wide",
    )
    st.title("Privacy-Conscious Foot-Traffic Analytics")
    st.caption("Retail and event engagement signals without identity persistence")
    st.info(
        "Privacy boundary: this dashboard reads aggregate windows only. It does "
        "not display faces, temporary tracking IDs, or individual trajectories."
    )
    default_path = os.environ.get(
        "FACE_ANALYTICS_DB_PATH", "artifacts/analytics.sqlite3"
    )
    database_path = st.sidebar.text_input("Aggregate database", value=default_path)
    st.sidebar.markdown(
        "Evaluation methodology: [`docs/evaluation.md`](docs/evaluation.md)"
    )
    data = prepare_dashboard_data(_load_windows(database_path))
    if not data.traffic:
        st.warning(
            "No aggregate windows are available. Generate the synthetic demo to "
            "explore the dashboard without a webcam or face dataset."
        )
        st.code(f"face-analytics generate-synthetic --db {database_path} --windows 48")
        return

    source_label = ", ".join(data.data_sources)
    if "synthetic" in data.data_sources:
        st.warning("Synthetic demonstration data — not measured from people or video.")
    st.caption(f"Data source: {source_label} · Latest window: {data.latest_timestamp}")

    metrics = st.columns(5)
    metrics[0].metric("Current occupancy", f"{data.current_occupancy:.1f}")
    metrics[1].metric("Entries", data.total_entries)
    metrics[2].metric("Exits", data.total_exits)
    metrics[3].metric("Peak occupancy", data.peak_occupancy)
    metrics[4].metric("Average dwell", f"{data.average_dwell_seconds:.0f}s")

    traffic = pd.DataFrame(
        {
            "time": [point.timestamp for point in data.traffic],
            "average occupancy": [point.average_occupancy for point in data.traffic],
            "entries": [point.entries for point in data.traffic],
            "exits": [point.exits for point in data.traffic],
        }
    ).set_index("time")
    st.subheader("Traffic by time")
    st.line_chart(traffic)

    left, right = st.columns(2)
    with left:
        st.subheader("Dwell-time distribution")
        labels = ["<5s", "5–15s", "15–30s", "30–60s", "1–2m", "2–5m", "5m+"]
        dwell = pd.DataFrame(
            {
                "bin": labels[: len(data.dwell_histogram)],
                "completed visits": data.dwell_histogram,
            }
        ).set_index("bin")
        st.bar_chart(dwell)
    with right:
        st.subheader("Zone aggregates")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "zone": zone.name,
                        "entries": zone.entries,
                        "exits": zone.exits,
                        "dwell minutes": round(zone.dwell_minutes, 1),
                    }
                    for zone in data.zones
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Latest aggregate heatmap")
    heatmap = pd.DataFrame(
        [
            data.heatmap[row * data.heatmap_columns : (row + 1) * data.heatmap_columns]
            for row in range(data.heatmap_rows)
        ]
    )
    st.dataframe(
        heatmap.style.background_gradient(cmap="YlOrRd", vmin=0, vmax=1),
        use_container_width=True,
    )
    st.caption(
        "Heatmap values are normalized coarse-bin counts. Granularity reduces but "
        "does not eliminate privacy risk."
    )


if __name__ == "__main__":
    run()
