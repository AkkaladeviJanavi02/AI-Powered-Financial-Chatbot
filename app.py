"""
app.py - FinBot: AI-Powered Financial Chatbot
Main Streamlit Application Entry Point

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Local modules
import database as db
import chatbot
import charts

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinBot — AI Financial Assistant",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- Global ---- */
html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, sans-serif;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #e0e0e0 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* ---- Chat bubbles ---- */
.chat-user {
    display: flex;
    justify-content: flex-end;
    margin: 8px 0;
}
.chat-user .bubble {
    background: linear-gradient(135deg, #6C63FF, #9B59B6);
    color: white;
    padding: 12px 18px;
    border-radius: 20px 20px 4px 20px;
    max-width: 75%;
    font-size: 15px;
    line-height: 1.5;
    box-shadow: 0 2px 8px rgba(108,99,255,0.3);
}
.chat-bot {
    display: flex;
    justify-content: flex-start;
    margin: 8px 0;
    align-items: flex-start;
    gap: 10px;
}
.chat-bot .avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #11998e, #38ef7d);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.chat-bot .bubble {
    background: #ffffff;
    color: #2d2d2d;
    padding: 12px 18px;
    border-radius: 4px 20px 20px 20px;
    max-width: 75%;
    font-size: 15px;
    line-height: 1.5;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border: 1px solid #f0f0f0;
}

/* ---- KPI cards ---- */
.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    border-left: 4px solid #6C63FF;
    transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
.kpi-label { font-size: 13px; color: #888; margin-top: 4px; }

/* ---- Input area ---- */
.stTextInput > div > input {
    border-radius: 25px !important;
    border: 2px solid #6C63FF !important;
    padding: 12px 20px !important;
    font-size: 15px !important;
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab"] {
    font-size: 15px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: #6C63FF !important;
    border-bottom-color: #6C63FF !important;
}

/* ---- Scrollable chat ---- */
.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 12px;
    scroll-behavior: smooth;
}
</style>
""", unsafe_allow_html=True)


# ── Initialization ────────────────────────────────────────────────────────────
db.initialize_db()

# Session state defaults
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I'm **FinBot**, your AI financial assistant.\n\n"
                "You can tell me things like:\n"
                "- *I spent ₹500 on food*\n"
                "- *Got salary of 50000*\n"
                "- *Show my balance*\n\n"
                "Type **help** to see all commands!"
            ),
        }
    ]

if "last_tx" not in st.session_state:
    st.session_state.last_tx = None


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ₹ FinBot")
    st.markdown("*AI-Powered Financial Assistant*")
    st.divider()

    # Quick stats
    all_txns = db.get_all_transactions()
    total_income  = all_txns[all_txns["type"] == "income"]["amount"].sum() if not all_txns.empty else 0
    total_expense = all_txns[all_txns["type"] == "expense"]["amount"].sum() if not all_txns.empty else 0
    net_balance   = total_income - total_expense

    st.markdown("### 📊 Quick Stats")
    st.metric("Income",   f"₹{total_income:,.0f}")
    st.metric("Expenses", f"₹{total_expense:,.0f}")
    st.metric("Balance",  f"₹{net_balance:,.0f}",
              delta=f"{'Surplus' if net_balance >= 0 else 'Deficit'}")

    st.divider()

    # Manual transaction form
    st.markdown("### ➕ Add Transaction")
    with st.form("manual_add", clear_on_submit=True):
        tx_type = st.selectbox("Type", ["expense", "income"])
        amount  = st.number_input("Amount (₹)", min_value=0.0, step=50.0)
        category_options = [
            "Food & Dining", "Transport", "Shopping", "Entertainment",
            "Health", "Utilities", "Education", "Rent & Housing",
            "Income", "Miscellaneous"
        ]
        category    = st.selectbox("Category", category_options)
        description = st.text_input("Description")
        date        = st.date_input("Date", value=datetime.today())
        submitted   = st.form_submit_button("Add ✓", use_container_width=True)

        if submitted and amount > 0:
            db.add_transaction(
                type_=tx_type, amount=amount,
                category=category, description=description,
                date=str(date)
            )
            st.success("Transaction added!")
            st.rerun()

    st.divider()

    # Budget setter
    st.markdown("### 💰 Set Budget")
    with st.form("budget_form", clear_on_submit=True):
        b_cat   = st.selectbox("Category", [
            "Food & Dining", "Transport", "Shopping", "Entertainment",
            "Health", "Utilities", "Education", "Rent & Housing"
        ], key="b_cat")
        b_limit = st.number_input("Monthly Limit (₹)", min_value=0.0, step=500.0)
        b_sub   = st.form_submit_button("Set Budget", use_container_width=True)
        if b_sub and b_limit > 0:
            db.set_budget(b_cat, b_limit)
            st.success(f"Budget set for {b_cat}!")

    st.divider()

    # Clear chat
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        db.clear_chat_history()
        st.rerun()

    st.markdown(
        "<div style='color:#888;font-size:12px;margin-top:20px;'>"
        "Built with Streamlit + SQLite + Pure ML</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("# ₹ FinBot — AI Financial Assistant")
st.markdown("*Track, analyze, and predict your finances with natural language.*")
st.divider()

tab_chat, tab_dashboard, tab_transactions = st.tabs(
    ["💬 Chat", "📊 Dashboard", "📋 Transactions"]
)


# ── TAB 1: CHAT ───────────────────────────────────────────────────────────────
with tab_chat:
    # Chat display
    chat_html_parts = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_html_parts.append(
                f'<div class="chat-user">'
                f'<div class="bubble">{msg["content"]}</div>'
                f'</div>'
            )
        else:
            # Convert markdown bold to HTML for the bubble
            content = msg["content"].replace("**", "<b>", 1)
            # Simple markdown bold: replace remaining **text** patterns
            import re
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", msg["content"])
            content = content.replace("\n", "<br>")
            chat_html_parts.append(
                f'<div class="chat-bot">'
                f'<div class="avatar">🤖</div>'
                f'<div class="bubble">{content}</div>'
                f'</div>'
            )

    st.markdown(
        f'<div class="chat-container">{"".join(chat_html_parts)}</div>',
        unsafe_allow_html=True
    )

    # Input
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "Message", placeholder="e.g. I spent ₹500 on food  or  Show my balance",
            label_visibility="collapsed", key="chat_input"
        )
    with col_send:
        send_btn = st.button("Send ➤", use_container_width=True, type="primary")

    # Quick action buttons
    st.markdown("**Quick actions:**")
    qcols = st.columns(5)
    quick_actions = [
        ("💰 Balance",   "Show my balance"),
        ("📊 Spending",  "Show my spending by category"),
        ("🔍 Insights",  "Give me financial insights"),
        ("🔮 Predict",   "Predict my next month expenses"),
        ("📋 History",   "Show recent transactions"),
    ]
    quick_trigger = None
    for i, (label, query) in enumerate(quick_actions):
        if qcols[i].button(label, use_container_width=True):
            quick_trigger = query

    # Process input
    trigger = quick_trigger or (user_input if send_btn and user_input else None)

    if trigger:
        st.session_state.messages.append({"role": "user", "content": trigger})
        db.save_message("user", trigger)

        with st.spinner("Thinking..."):
            result = chatbot.process_message(trigger)

        response = result["response"]
        st.session_state.messages.append({"role": "assistant", "content": response})
        db.save_message("assistant", response)
        st.session_state.last_tx = result.get("transaction")
        st.rerun()


# ── TAB 2: DASHBOARD ──────────────────────────────────────────────────────────
with tab_dashboard:
    all_txns   = db.get_all_transactions()
    monthly_df = db.get_monthly_summary()
    cat_df     = db.get_category_spending()

    if all_txns.empty:
        st.info(
            "📭 No data yet! Start by chatting with FinBot or adding transactions "
            "from the sidebar."
        )
    else:
        # KPI row
        now          = datetime.now()
        month_txns   = db.get_transactions_by_month(now.year, now.month)
        month_exp    = month_txns[month_txns["type"] == "expense"]["amount"].sum()
        month_inc    = month_txns[month_txns["type"] == "income"]["amount"].sum()
        total_txns   = len(all_txns)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("This Month Expenses", f"₹{month_exp:,.0f}")
        k2.metric("This Month Income",   f"₹{month_inc:,.0f}")
        k3.metric("Net Balance",         f"₹{net_balance:,.0f}")
        k4.metric("Total Transactions",  total_txns)

        st.divider()

        # Charts row 1
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(charts.spending_pie(cat_df),    use_container_width=True)
        with c2:
            st.plotly_chart(charts.monthly_bar(monthly_df), use_container_width=True)

        # Charts row 2
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(charts.spending_trend(all_txns),            use_container_width=True)
        with c4:
            st.plotly_chart(charts.category_comparison_bar(cat_df),     use_container_width=True)

        # Prediction
        st.divider()
        st.markdown("### 🔮 AI Expense Forecast")

        from ml_models import ExpensePredictor
        pred = ExpensePredictor.load()
        pred.train(monthly_df)
        pred_result = pred.predict_next_month()

        if pred_result["predicted"]:
            pc1, pc2 = st.columns([2, 1])
            with pc1:
                st.plotly_chart(
                    charts.prediction_chart(monthly_df, pred_result["predicted"]),
                    use_container_width=True
                )
            with pc2:
                st.markdown("#### Prediction Details")
                st.markdown(pred_result["message"])
                st.metric(
                    "Confidence", f"{pred_result['confidence']*100:.0f}%"
                )
                trend_map = {
                    "increasing": "📈 Spending going up",
                    "decreasing": "📉 Spending coming down",
                    "stable":     "➡️ Spending stable",
                }
                st.info(trend_map.get(pred_result["trend"], ""))
        else:
            st.info("Add at least 2 months of data to unlock expense predictions!")

        # Budgets
        budgets = db.get_budgets()
        if not budgets.empty:
            st.divider()
            st.markdown("### 💳 Budget Tracker")
            gauge_cols = st.columns(min(4, len(budgets)))
            for i, (_, row) in enumerate(budgets.iterrows()):
                spent = month_txns[
                    (month_txns["type"] == "expense") &
                    (month_txns["category"] == row["category"])
                ]["amount"].sum()
                with gauge_cols[i % len(gauge_cols)]:
                    st.plotly_chart(
                        charts.budget_gauge(row["category"], spent, row["monthly_limit"]),
                        use_container_width=True
                    )

        # Insights
        st.divider()
        st.markdown("### 🔍 AI Insights")
        from ml_models import generate_insights
        insights = generate_insights(all_txns)
        for insight in insights:
            st.markdown(f"> {insight}")


# ── TAB 3: TRANSACTIONS ───────────────────────────────────────────────────────
with tab_transactions:
    all_txns = db.get_all_transactions()

    if all_txns.empty:
        st.info("No transactions yet. Add some via chat or the sidebar form!")
    else:
        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            type_filter = st.selectbox("Type", ["All", "expense", "income"])
        with f2:
            cats = ["All"] + sorted(all_txns["category"].unique().tolist())
            cat_filter = st.selectbox("Category", cats)
        with f3:
            search = st.text_input("Search description", placeholder="e.g. food")

        filtered = all_txns.copy()
        if type_filter != "All":
            filtered = filtered[filtered["type"] == type_filter]
        if cat_filter != "All":
            filtered = filtered[filtered["category"] == cat_filter]
        if search:
            filtered = filtered[
                filtered["description"].str.contains(search, case=False, na=False)
            ]

        st.markdown(f"**{len(filtered)} transactions**")

        # Style the dataframe
        styled = filtered[["id", "date", "type", "category", "amount", "description"]].copy()
        styled.columns = ["ID", "Date", "Type", "Category", "Amount (₹)", "Description"]
        styled["Amount (₹)"] = styled["Amount (₹)"].map(lambda x: f"₹{x:,.0f}")

        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Export
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export as CSV", data=csv,
            file_name=f"finbot_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


