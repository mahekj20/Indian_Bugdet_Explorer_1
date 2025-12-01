# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ------------------- Page Config -------------------
st.set_page_config(
    page_title="India's Budget Shift (2014-2025)",
    page_icon="India",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- Load & Clean Data -------------------
@st.cache_data
def load_data():
    df = pd.read_csv("budget.csv")
    
    # Clean and standardize ministry names
    df["Ministry Name"] = df["Ministry Name"].replace({
        "MINISTRY OF AGRICULTURE AND FARMERS WELFARE": "MINISTRY OF AGRICULTURE AND FARMERS' WELFARE",
        "MINISTRY OF AGRICULTURE": "MINISTRY OF AGRICULTURE AND FARMERS' WELFARE"
    })
    
    # Fill missing total with sum where possible
    numeric_cols = ['Revenue (Plan)', 'Capital (Plan)', 'Total (Plan)',
                    'Revenue (Non-Plan)', 'Capital (Non-Plan)', 'Total (Non-Plan)', 'Total Plan & Non-Plan']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].replace({',': '', '-': np.nan}), errors='coerce')
    
    # Use Total Plan & Non-Plan first, then Total (Plan), then sum
    df["Total Allocation"] = df["Total Plan & Non-Plan"].fillna(df["Total (Plan)"])
    
    # For years after 2017, only Plan exists → already filled
    df["Year"] = df["Year"].str[:9]  # Clean year format
    return df

df = load_data()

# Top ministries to focus on
focus_ministries = [
    "MINISTRY OF DEFENCE",
    "MINISTRY OF FINANCE",
    "MINISTRY OF HOME AFFAIRS",
    "MINISTRY OF AGRICULTURE AND FARMERS' WELFARE",
    "MINISTRY OF HEALTH AND FAMILY WELFARE"
]

df_focus = df[df["Ministry Name"].isin(focus_ministries)].copy()

# Calculate yearly total budget
yearly_total = df_focus.groupby("Year")["Total Allocation"].sum().reset_index()
yearly_total = yearly_total.sort_values("Year")

# Merge to get % share
df_focus = df_focus.merge(yearly_total, on="Year", suffixes=('', '_total'))
df_focus["% of Total Budget"] = (df_focus["Total Allocation"] / df_focus["Total Allocation_total"]) * 100

# Indian Rupee formatting
def inr(x):
    if x >= 100000:
        return f"₹{x/100000:.1f} Lakh Cr"
    elif x >= 1000:
        return f"₹{x/1000:.0f} Thousand Cr"
    else:
        return f"₹{x:.0f} Cr"

# ------------------- Sidebar -------------------
st.sidebar.title("India Budget Explorer")
st.sidebar.markdown("### 2014 → 2025")
year_selected = st.sidebar.selectbox("Select Year", sorted(df_focus["Year"].unique()))

ministry_selected = st.sidebar.selectbox(
    "Deep Dive into Ministry",
    options=focus_ministries,
    format_func=lambda x: x.replace("MINISTRY OF ", "").title()
)

# ------------------- Header -------------------
st.title("India's Great Budget Shift (2014–2025)")
st.markdown("""
**Defence & Interest Payments are exploding. Agriculture & Health are shrinking as % of budget.**  
Explore the dramatic reordering of national priorities.
""")

# ------------------- Key Insight Cards -------------------
col1, col2, col3, col4 = st.columns(4)

defence_2014 = df_focus[(df_focus["Ministry Name"] == "MINISTRY OF DEFENCE") & (df_focus["Year"] == "2014-2015")]["Total Allocation"].iloc[0]
defence_2024 = df_focus[(df_focus["Ministry Name"] == "MINISTRY OF DEFENCE") & (df_focus["Year"] == "2024-2025")]["Total Allocation"].iloc[0]
defence_growth = (defence_2024 / defence_2014)

agri_share_2014 = df_focus[(df_focus["Ministry Name"] == "MINISTRY OF AGRICULTURE AND FARMERS' WELFARE") & (df_focus["Year"] == "2014-2015")]["% of Total Budget"].iloc[0]
agri_share_2024 = df_focus[(df_focus["Ministry Name"] == "MINISTRY OF AGRICULTURE AND FARMERS' WELFARE") & (df_focus["Year"] == "2024-2025")]["% of Total Budget"].iloc[0]

with col1:
    st.metric("Defence Budget Growth", f"{defence_growth:.1f}x", "2014 → 2025")
with col2:
    st.metric("Defence 2024–25", inr(defence_2024))
with col3:
    st.metric("Agri Share 2014", f"{agri_share_2014:.1f}%")
with col4:
    st.metric("Agri Share 2024", f"{agri_share_2024:.2f}%", f"-{agri_share_2014 - agri_share_2024:.1f} pp")

# ------------------- Sankey Diagram (2014 vs 2024) -------------------
st.markdown("## The Great Reallocation: 2014 vs 2024")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 2014–2015")
    df_2014 = df_focus[df_focus["Year"] == "2014-2015"]
    fig1 = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
            label = ["Total Budget"] + df_2014["Ministry Name"].str.replace("MINISTRY OF ", "").str.title().tolist(),
            color = ["#636EFA"] + px.colors.qualitative.Plotly[:len(df_2014)]
        ),
        link = dict(
            source = [0] * len(df_2014),
            target = list(range(1, len(df_2014)+1)),
            value = df_2014["Total Allocation"].tolist()
        ))])
    fig1.update_layout(height=600, font_size=12)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("### 2024–2025")
    df_2024 = df_focus[df_focus["Year"] == "2024-2025"]
    fig2 = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
            label = ["Total Budget"] + df_2024["Ministry Name"].str.replace("MINISTRY OF ", "").str.title().tolist(),
            color = ["#636EFA"] + px.colors.qualitative.Plotly[:len(df_2024)]
        ),
        link = dict(
            source = [0] * len(df_2024),
            target = list(range(1, len(df_2024)+1)),
            value = df_2024["Total Allocation"].tolist()
        ))])
    fig2.update_layout(height=600, font_size=12)
    st.plotly_chart(fig2, use_container_width=True)

# ------------------- Trend Lines -------------------
st.markdown("## Budget Allocation Over Time")

fig = make_subplots(specs=[[{"secondary_y": True}]])

# Absolute
for ministry in focus_ministries:
    data = df_focus[df_focus["Ministry Name"] == ministry]
    fig.add_trace(go.Scatter(
        x=data["Year"], y=data["Total Allocation"],
        name=ministry.replace("MINISTRY OF ", "").title(),
        mode='lines+markers'
    ), secondary_y=False)

fig.update_layout(
    title="Absolute Allocation (in Crore ₹)",
    xaxis_title="Year",
    yaxis_title="Amount (₹ Crore)",
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig.update_yaxes(title_text="Amount (₹ Crore)", secondary_y=False)
st.plotly_chart(fig, use_container_width=True)

# Percentage share
st.markdown("### Real Story: % Share of Total Budget")
fig2 = px.area(df_focus, x="Year", y="% of Total Budget", color="Ministry Name",
               title="Share of Total Union Budget Over Time",
               color_discrete_sequence=px.colors.qualitative.Bold)
fig2.update_layout(height=600, legend_title="Ministry")
st.plotly_chart(fig2, use_container_width=True)

# ------------------- Ministry Deep Dive -------------------
st.markdown(f"## Deep Dive: {ministry_selected.replace('MINISTRY OF ', '').title()}")

data = df_focus[df_focus["Ministry Name"] == ministry_selected]

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(data, x="Year", y="Total Allocation", title="Total Allocation Over Time")
    fig.update_yaxes(title="₹ Crore")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.line(data, x="Year", y="% of Total Budget", title="% Share of Total Budget", markers=True)
    fig.update_yaxes(title="% of Total Budget")
    st.plotly_chart(fig, use_container_width=True)

# ------------------- Fun Comparisons -------------------
st.markdown("## What Could This Money Buy?")
defence_2024_cap = 182240.85 * 1000000000  # in rupees
health_2024_total = 90958.63 * 1000000000

st.markdown(f"""
- One **Defence Capital Budget (2024–25)** = **₹1.82 lakh crore**  
  → Could fund the **entire Health Ministry budget twice over**  
  → Could give **₹15,000** to every farmer in India (~12 crore farmers)
- Interest payments on debt (under Finance) now > ₹10 lakh crore → bigger than Defence!
""")

# ------------------- Footer -------------------
st.markdown("---")
st.markdown("""
Made with ❤️ by a Data Science Student | Data: Union Budget of India (2014–2025)  
Deployed on [share.streamlit.io](https://share.streamlit.io) | Source code: [GitHub](https://github.com/yourusername/india-budget-explorer)
""")
