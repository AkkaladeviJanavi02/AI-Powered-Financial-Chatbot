"""
chatbot.py - Chatbot Response Engine
Routes user messages to the right handler and generates natural responses.
Ties together: NLP parser, database, ML models.
"""

import re
from datetime import datetime

import pandas as pd

import database as db
from nlp_parser import parse_transaction, is_query
from ml_models import ExpensePredictor, CategoryClassifier, generate_insights


# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_predictor:  ExpensePredictor | None  = None
_classifier: CategoryClassifier | None = None


def _get_predictor() -> ExpensePredictor:
    global _predictor
    if _predictor is None:
        _predictor = ExpensePredictor.load()
    return _predictor


def _get_classifier() -> CategoryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = CategoryClassifier.load()
    return _classifier


def _retrain_models():
    """Retrains both models on current DB data."""
    global _predictor, _classifier
    monthly  = db.get_monthly_summary()
    all_txns = db.get_all_transactions()

    pred = ExpensePredictor()
    pred.train(monthly)
    _predictor = pred

    clf = CategoryClassifier()
    clf.retrain_from_db(all_txns)
    _classifier = clf


# ══════════════════════════════════════════════════════════════════════════════
# Query handlers
# ══════════════════════════════════════════════════════════════════════════════

def _handle_balance(text: str) -> str:
    df = db.get_all_transactions()
    if df.empty:
        return "No transactions yet. Add some expenses or income first!"
    total_income  = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    net = total_income - total_expense
    return (
        f"💼 **Financial Summary**\n\n"
        f"- Total Income:  ₹{total_income:,.0f}\n"
        f"- Total Expenses: ₹{total_expense:,.0f}\n"
        f"- **Net Balance:  ₹{net:,.0f}** "
        f"({'✅ Surplus' if net >= 0 else '⚠️ Deficit'})"
    )


def _handle_spending(text: str) -> str:
    df = db.get_category_spending()
    if df.empty:
        return "No expense data recorded yet."
    lines = ["📊 **Spending by Category**\n"]
    for _, row in df.iterrows():
        bar = "█" * min(20, int(row["total"] / max(df["total"]) * 20))
        lines.append(f"- **{row['category']}**: ₹{row['total']:,.0f}  {bar}")
    return "\n".join(lines)


def _handle_insights(text: str) -> str:
    df = db.get_all_transactions()
    insights = generate_insights(df)
    return "🔍 **Financial Insights**\n\n" + "\n\n".join(insights)


def _handle_prediction(text: str) -> str:
    monthly = db.get_monthly_summary()
    pred = _get_predictor()
    pred.train(monthly)

    result = pred.predict_next_month()
    if result["predicted"] is None:
        return (
            "📉 I need at least **2 months** of data to make a prediction. "
            "Keep tracking your expenses!"
        )
    trend_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(
        result["trend"], "📊"
    )
    return (
        f"{trend_emoji} **Expense Forecast**\n\n"
        f"{result['message']}\n\n"
        f"*Confidence: {result['confidence']*100:.0f}%*"
    )


def _handle_history(text: str) -> str:
    df = db.get_all_transactions()
    if df.empty:
        return "No transactions found."
    # Show last 10
    recent = df.head(10)
    lines  = ["📋 **Recent Transactions**\n"]
    for _, row in recent.iterrows():
        icon = "💸" if row["type"] == "expense" else "💰"
        lines.append(
            f"{icon} **{row['category']}** — ₹{row['amount']:,.0f}  "
            f"_{row['description'] or 'No description'}_ ({row['date']})"
        )
    return "\n".join(lines)


def _handle_budget_status(text: str) -> str:
    budgets = db.get_budgets()
    if budgets.empty:
        return (
            "No budgets set. You can set one like this:\n"
            "> *Set budget for Food to 5000*"
        )
    now   = datetime.now()
    month_df = db.get_transactions_by_month(now.year, now.month)
    lines = ["💳 **Budget Status (This Month)**\n"]
    for _, row in budgets.iterrows():
        spent = month_df[
            (month_df["type"] == "expense") &
            (month_df["category"] == row["category"])
        ]["amount"].sum()
        pct  = spent / row["monthly_limit"] * 100 if row["monthly_limit"] else 0
        status = "🔴 Over budget!" if pct > 100 else (
            "🟡 Near limit" if pct > 80 else "🟢 On track"
        )
        lines.append(
            f"- **{row['category']}**: ₹{spent:,.0f} / ₹{row['monthly_limit']:,.0f} "
            f"({pct:.0f}%) {status}"
        )
    return "\n".join(lines)


def _handle_set_budget(text: str) -> str:
    # Pattern: "set budget for <category> to <amount>"
    match = re.search(
        r"budget\s+for\s+(.+?)\s+(?:to|as|=)\s*([\d,]+)", text, re.IGNORECASE
    )
    if not match:
        return (
            "I didn't catch that. Try:\n"
            "> *Set budget for Food to 5000*"
        )
    category = match.group(1).strip().title()
    amount   = float(match.group(2).replace(",", ""))
    db.set_budget(category, amount)
    return f"✅ Budget set: **{category}** → ₹{amount:,.0f}/month"


def _handle_help(text: str) -> str:
    return """
👋 **Hi! I'm FinBot — your AI financial assistant.**

Here's what you can ask me:

**➕ Add Transactions**
- *I spent 500 on food*
- *Paid ₹1200 for Netflix*
- *Got salary of 50000*

**📊 View Reports**
- *Show my balance*
- *What's my spending by category?*
- *Show recent transactions*

**💡 Get Insights**
- *Give me financial insights*
- *Predict my next month's expenses*
- *Show budget status*

**💰 Set Budgets**
- *Set budget for Food to 5000*

**🆘 Help**
- *Help* or *What can you do?*
"""


# ══════════════════════════════════════════════════════════════════════════════
# Main router
# ══════════════════════════════════════════════════════════════════════════════

QUERY_ROUTES: list[tuple[list[str], callable]] = [
    (["balance", "summary", "net", "total"],            _handle_balance),
    (["spending", "categor", "breakdown"],              _handle_spending),
    (["insight", "analysis", "analyze", "overview"],   _handle_insights),
    (["predict", "forecast", "next month", "future"],  _handle_prediction),
    (["history", "recent", "transaction", "list"],     _handle_history),
    (["budget status", "budget left", "how much budget"],  _handle_budget_status),
    (["set budget", "budget for"],                     _handle_set_budget),
    (["help", "what can you", "how do i"],             _handle_help),
]


def process_message(user_input: str) -> dict:
    """
    Main entry point for the chatbot.

    Returns:
        {
            "response": str,           # markdown response text
            "transaction_added": bool, # whether a transaction was recorded
            "transaction": dict | None # the transaction if added
        }
    """
    text = user_input.strip()
    if not text:
        return {"response": "Please type a message!", "transaction_added": False}

    text_lower = text.lower()

    # 1. Check if it's a query first
    if is_query(text):
        for keywords, handler in QUERY_ROUTES:
            if any(kw in text_lower for kw in keywords):
                return {"response": handler(text), "transaction_added": False}

        # Generic NLP fallback for unknown queries
        return {
            "response": (
                "I'm not sure what you're looking for. Type **help** to see "
                "what I can do!"
            ),
            "transaction_added": False,
        }

    # 2. Try to parse as a transaction
    parsed = parse_transaction(text)
    if parsed:
        # Use ML classifier to improve category if model is trained
        clf = _get_classifier()
        if clf.trained:
            ml_category, confidence = clf.predict(text)
            if confidence > 0.6:
                parsed.category = ml_category

        tx_id = db.add_transaction(
            type_=parsed.type_,
            amount=parsed.amount,
            category=parsed.category,
            description=parsed.description,
        )

        # Retrain models in background after every 5th transaction
        all_txns = db.get_all_transactions()
        if len(all_txns) % 5 == 0:
            _retrain_models()

        icon = "💸" if parsed.type_ == "expense" else "💰"
        response = (
            f"{icon} **Transaction Recorded!**\n\n"
            f"- Type: {parsed.type_.title()}\n"
            f"- Amount: ₹{parsed.amount:,.0f}\n"
            f"- Category: {parsed.category}\n"
            f"- Description: {parsed.description}\n"
            f"- ID: #{tx_id}"
        )

        return {
            "response": response,
            "transaction_added": True,
            "transaction": {
                "id": tx_id,
                "type": parsed.type_,
                "amount": parsed.amount,
                "category": parsed.category,
                "description": parsed.description,
            },
        }

    # 3. Fallback: no transaction found, no query matched
    return {
        "response": (
            "I couldn't understand that. Try:\n"
            "- *I spent 500 on food*\n"
            "- *Show my balance*\n"
            "- Type **help** for all commands."
        ),
        "transaction_added": False,
    }
