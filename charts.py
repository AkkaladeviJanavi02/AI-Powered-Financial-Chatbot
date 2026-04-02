"""
charts.py - Data Visualization Layer
All Plotly chart builders used by the Streamlit dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime


# Shared color palette
PALETTE = px.colors.qualitative.Pastel
ACCENT  = "#6C63FF"
BG      = "rgba(0,0,0,0)"


def _empty_chart(message: str = "No data available yet.") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=16, color="#888")
    )
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG,
                      xaxis_visible=False, yaxis_visible=False)
    return fig


def spending_pie(category_df: pd.DataFrame) -> go.Figure:
    """Donut chart: spending breakdown by category."""
    if category_df.empty:
        return _empty_chart("No expense data to display.")
    fig = px.pie(
        category_df, names="category", values="total",
        hole=0.45,
        color_discrete_sequence=PALETTE,
        title="Spending by Category",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        showlegend=True,
        paper_bgcolor=BG,
        title_font_size=18,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def monthly_bar(monthly_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: income vs expenses per month."""
    if monthly_df.empty:
        return _empty_chart("No monthly data yet.")

    pivot = monthly_df.pivot_table(
        index="month", columns="type", values="total", aggfunc="sum"
    ).fillna(0).reset_index()

    fig = go.Figure()

    if "income" in pivot.columns:
        fig.add_trace(go.Bar(
            x=pivot["month"], y=pivot["income"],
            name="Income", marker_color="#2ECC71", opacity=0.85
        ))
    if "expense" in pivot.columns:
        fig.add_trace(go.Bar(
            x=pivot["month"], y=pivot["expense"],
            name="Expense", marker_color="#E74C3C", opacity=0.85
        ))

    fig.update_layout(
        barmode="group",
        title="Monthly Income vs Expenses",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        title_font_size=18,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig


def spending_trend(transactions_df: pd.DataFrame) -> go.Figure:
    """Line chart: cumulative spending over time."""
    if transactions_df.empty:
        return _empty_chart()

    expenses = transactions_df[transactions_df["type"] == "expense"].copy()
    if expenses.empty:
        return _empty_chart("No expenses recorded.")

    expenses["date"] = pd.to_datetime(expenses["date"])
    daily = expenses.groupby("date")["amount"].sum().reset_index()
    daily = daily.sort_values("date")
    daily["cumulative"] = daily["amount"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["cumulative"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=2.5),
        marker=dict(size=6, color=ACCENT),
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.08)",
        name="Cumulative Spend",
    ))
    fig.update_layout(
        title="Cumulative Expense Trend",
        xaxis_title="Date",
        yaxis_title="Cumulative (₹)",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        title_font_size=18,
        margin=dict(t=60, b=40),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig


def budget_gauge(category: str, spent: float, limit: float) -> go.Figure:
    """Gauge chart for a single budget category."""
    pct = min(spent / limit * 100, 120) if limit else 0
    color = "#2ECC71" if pct < 80 else ("#F39C12" if pct < 100 else "#E74C3C")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=spent,
        delta={"reference": limit, "valueformat": ".0f",
               "prefix": "₹", "increasing": {"color": "#E74C3C"}},
        number={"prefix": "₹", "valueformat": ",.0f"},
        title={"text": f"{category}<br><sub>Budget: ₹{limit:,.0f}</sub>"},
        gauge={
            "axis": {"range": [0, limit * 1.2], "tickformat": ",.0f"},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,        limit * 0.8], "color": "#eafaf1"},
                {"range": [limit*0.8,limit],       "color": "#fef9e7"},
                {"range": [limit,    limit * 1.2], "color": "#fdedec"},
            ],
            "threshold": {
                "line": {"color": "#c0392b", "width": 3},
                "thickness": 0.75,
                "value": limit,
            },
        },
    ))
    fig.update_layout(paper_bgcolor=BG, height=250,
                      margin=dict(t=60, b=10, l=20, r=20))
    return fig


def prediction_chart(monthly_df: pd.DataFrame, predicted: float) -> go.Figure:
    """Bar chart showing historical monthly spend + predicted next month."""
    if monthly_df.empty:
        return _empty_chart()

    expenses = (
        monthly_df[monthly_df["type"] == "expense"]
        .sort_values("month")
        .copy()
    )
    if expenses.empty:
        return _empty_chart("No expense history.")

    # Next month label
    last_month_str  = expenses["month"].iloc[-1]
    last_month_date = pd.Period(last_month_str, freq="M")
    next_month_str  = str(last_month_date + 1)

    hist = go.Bar(
        x=expenses["month"], y=expenses["total"],
        name="Actual", marker_color=ACCENT, opacity=0.75
    )
    pred = go.Bar(
        x=[next_month_str], y=[predicted],
        name="Predicted", marker_color="#F39C12",
        marker_pattern_shape="/",
    )

    fig = go.Figure([hist, pred])
    fig.add_annotation(
        x=next_month_str, y=predicted,
        text=f"₹{predicted:,.0f}",
        showarrow=True, arrowhead=2, ay=-40,
        font=dict(color="#F39C12", size=13)
    )
    fig.update_layout(
        title="Expense Forecast",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        title_font_size=18,
        barmode="overlay",
        margin=dict(t=60, b=40),
    )
    return fig


def category_comparison_bar(category_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart for category-wise total spend."""
    if category_df.empty:
        return _empty_chart()

    df = category_df.sort_values("total")
    fig = go.Figure(go.Bar(
        x=df["total"], y=df["category"],
        orientation="h",
        marker=dict(
            color=df["total"],
            colorscale="Purples",
            showscale=False,
        ),
        text=[f"₹{v:,.0f}" for v in df["total"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Expense by Category",
        xaxis_title="Total (₹)",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        title_font_size=18,
        margin=dict(t=60, b=40, l=150, r=80),
        height=max(300, 50 * len(df)),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=False)
    return fig
