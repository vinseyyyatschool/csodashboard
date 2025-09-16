import streamlit as st
import pandas as pd
import io
import datetime
import plotly.express as px

st.set_page_config(page_title="CSO Recommendations Dashboard", layout="wide")

st.title("CSO Recommendations Tracker (Philippines Budget)")

st.markdown("""
Upload your recommendations CSV.  
You can download the [sample template here](sample_recommendations.csv).
""")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="fileUploader")
if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["Date Submitted"])
else:
    # Load sample data
    df = pd.read_csv("sample_recommendations.csv", parse_dates=["Date Submitted"])

# Standardize Status
status_options = [
    "Submitted", "Under Review", "Adopted (Fully)", "Adopted (Partially)", "Not Adopted"
]
df["Status"] = pd.Categorical(df["Status"], categories=status_options, ordered=True)

# Sidebar filters
st.sidebar.header("Filter Recommendations")
agency = st.sidebar.multiselect("Agency", sorted(df["Agency"].dropna().unique()))
cso = st.sidebar.multiselect("CSO", sorted(df["CSO Name"].dropna().unique()))
status = st.sidebar.multiselect("Status", status_options)
budget_area = st.sidebar.multiselect("Budget Area", sorted(df["Budget Area"].dropna().unique()))
date_min, date_max = df["Date Submitted"].min(), df["Date Submitted"].max()
date_range = st.sidebar.date_input("Date Range", [date_min, date_max])

filtered_df = df.copy()
if agency: filtered_df = filtered_df[filtered_df["Agency"].isin(agency)]
if cso: filtered_df = filtered_df[filtered_df["CSO Name"].isin(cso)]
if status: filtered_df = filtered_df[filtered_df["Status"].isin(status)]
if budget_area: filtered_df = filtered_df[filtered_df["Budget Area"].isin(budget_area)]
if date_range and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["Date Submitted"] >= pd.to_datetime(date_range[0])) &
        (filtered_df["Date Submitted"] <= pd.to_datetime(date_range[1]))
    ]

# Top KPIs
st.markdown("### Summary Statistics")
total = len(filtered_df)
adopted_full = (filtered_df["Status"] == "Adopted (Fully)").sum()
adopted_partial = (filtered_df["Status"] == "Adopted (Partially)").sum()
not_adopted = (filtered_df["Status"] == "Not Adopted").sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Recommendations", total)
col2.metric("% Fully Adopted", f"{(adopted_full/total*100) if total else 0:.1f}%")
col3.metric("% Partially Adopted", f"{(adopted_partial/total*100) if total else 0:.1f}%")
col4.metric("% Not Adopted", f"{(not_adopted/total*100) if total else 0:.1f}%")

# Pie chart: Status breakdown
if total > 0:
    status_counts = filtered_df["Status"].value_counts().reindex(status_options, fill_value=0)
    fig = px.pie(
        names=status_counts.index,
        values=status_counts.values,
        title="Adoption Status Breakdown"
    )
    st.plotly_chart(fig, use_container_width=True)

# Table
st.markdown("### Recommendations Table")
def color_status(val):
    color_map = {
        "Submitted": "#e2e3e5",
        "Under Review": "#ffe599",
        "Adopted (Fully)": "#b6d7a8",
        "Adopted (Partially)": "#f9cb9c",
        "Not Adopted": "#ea9999"
    }
    return f"background-color: {color_map.get(val, '#fff')};"

st.dataframe(
    filtered_df.style.applymap(color_status, subset=["Status"]),
    use_container_width=True
)

# Export button
buffer = io.StringIO()
filtered_df.to_csv(buffer, index=False)
st.download_button(
    label="Download filtered data (CSV)",
    data=buffer.getvalue(),
    file_name="filtered_recommendations.csv",
    mime="text/csv"
)

# Detail view (clickable rows not natively supported, but we can show more on selection)
st.markdown("---\n#### View Recommendation Details")

selected_idx = st.selectbox(
    "Select a recommendation by row number",
    options=filtered_df.index,
    format_func=lambda idx: f"{idx+1}: {filtered_df.loc[idx, 'Recommendation'][:40]}..."
)
rec = filtered_df.loc[selected_idx]
st.write(f"**CSO Name:** {rec['CSO Name']}")
st.write(f"**Agency:** {rec['Agency']}")
st.write(f"**Date Submitted:** {rec['Date Submitted'].date()}")
st.write(f"**Status:** {rec['Status']}")
st.write(f"**Reason/Explanation:** {rec['Reason'] if pd.notnull(rec['Reason']) and rec['Reason'] else '(none)'}")
st.write(f"**Budget Area:** {rec['Budget Area']}")
st.write(f"**Recommendation:**")
st.info(rec['Recommendation'])

st.caption("Want more features? Ask for analytics, login, or API code! 🚀")