
import json
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from rich.console import Console

from audit.logger import AUDIT_LOG_FILE

console = Console()


def load_data():
    """
    Load and preprocess the audit log data.
    """
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            data = [json.loads(line) for line in f]
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame()


def main():
    """
    Main function for the Streamlit dashboard.
    """
    st.set_page_config(page_title="CloudCraver Dashboard", layout="wide")
    st.title("Enterprise Reporting & Analytics Dashboard")

    df = load_data()

    if df.empty:
        st.warning("No audit data found. Please run some commands to generate audit logs.")
        return

    # --- Filters ---
    st.sidebar.header("Filters")
    days_to_filter = st.sidebar.slider("Days to Display", 1, 365, 7)
    start_date = datetime.now() - timedelta(days=days_to_filter)
    df_filtered = df[df["timestamp"] >= start_date]

    event_types = st.sidebar.multiselect(
        "Event Types",
        options=df_filtered["event"].unique(),
        default=df_filtered["event"].unique(),
    )
    df_filtered = df_filtered[df_filtered["event"].isin(event_types)]

    # --- Key Metrics ---
    st.header("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", len(df_filtered))
    col2.metric("Successful Logins", len(df_filtered[df_filtered["event"] == "user.login.success"]))
    col3.metric("Permission Denials", len(df_filtered[df_filtered["event"] == "rbac.permission.denied"]))
    col4.metric("Infra Changes", len(df_filtered[df_filtered["event"].str.startswith("infra.")]))

    # --- Visualizations ---
    st.header("Event Timeline")
    fig_timeline = px.histogram(
        df_filtered,
        x="timestamp",
        title="Events Over Time",
        color="event",
        nbins=50,
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    st.header("Event Distribution")
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(
            df_filtered,
            names="event",
            title="Event Types",
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        fig_bar = px.bar(
            df_filtered["actor_id"].value_counts().reset_index(),
            x="index",
            y="actor_id",
            title="Top Users",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Raw Data ---
    st.header("Raw Audit Data")
    st.dataframe(df_filtered)


if __name__ == "__main__":
    main()
