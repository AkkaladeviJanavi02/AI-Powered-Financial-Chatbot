"""
ml_models.py - Machine Learning Models
1. ExpensePredictor  - Linear Regression to forecast next month's spend
2. CategoryClassifier - Naive Bayes text classifier for auto-categorization
Both models persist to disk so they survive app restarts.
"""

import re
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from math import log

warnings.filterwarnings("ignore")

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

PREDICTOR_PATH  = MODEL_DIR / "expense_predictor.pkl"
CLASSIFIER_PATH = MODEL_DIR / "category_classifier.pkl"


# ══════════════════════════════════════════════════════════════════════════════
# 1.  EXPENSE PREDICTOR  (Linear Regression — pure numpy, no sklearn needed)
# ══════════════════════════════════════════════════════════════════════════════

class ExpensePredictor:
    """
    Predicts next month's total expenses using a simple OLS linear regression
    over historical monthly expense totals.
    Requires at least 3 months of data for a meaningful prediction.
    """

    def __init__(self):
        self.slope: float = 0.0
        self.intercept: float = 0.0
        self.trained: bool = False
        self.months_seen: int = 0

    def train(self, monthly_df: pd.DataFrame):
        """
        Args:
            monthly_df: DataFrame with columns ['month', 'type', 'total']
                        (output of database.get_monthly_summary())
        """
        expenses = (
            monthly_df[monthly_df["type"] == "expense"]
            .sort_values("month")
            .reset_index(drop=True)
        )
        if len(expenses) < 2:
            self.trained = False
            return

        self.months_seen = len(expenses)
        x = np.arange(len(expenses), dtype=float)
        y = expenses["total"].values.astype(float)

        # OLS: beta = (X'X)^-1 X'y  with X = [1, x]
        X = np.column_stack([np.ones_like(x), x])
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            self.intercept, self.slope = float(beta[0]), float(beta[1])
            self.trained = True
        except Exception:
            self.trained = False

        self._save()

    def predict_next_month(self) -> dict:
        """
        Returns a dict with predicted amount, trend direction, and confidence.
        """
        if not self.trained:
            return {"predicted": None, "trend": "unknown",
                    "confidence": 0.0, "message": "Not enough data yet."}

        next_x = float(self.months_seen)
        predicted = self.intercept + self.slope * next_x
        predicted = max(0.0, predicted)

        trend = "increasing" if self.slope > 50 else (
            "decreasing" if self.slope < -50 else "stable"
        )
        confidence = min(0.95, 0.5 + 0.05 * self.months_seen)

        return {
            "predicted": round(predicted, 2),
            "trend": trend,
            "confidence": round(confidence, 2),
            "message": (
                f"Based on {self.months_seen} months of data, your expenses are "
                f"{trend}. Predicted next month: ₹{predicted:,.0f}."
            )
        }

    def _save(self):
        with open(PREDICTOR_PATH, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls) -> "ExpensePredictor":
        if PREDICTOR_PATH.exists():
            with open(PREDICTOR_PATH, "rb") as f:
                return pickle.load(f)
        return cls()


# ══════════════════════════════════════════════════════════════════════════════
# 2.  CATEGORY CLASSIFIER  (Multinomial Naïve Bayes — no sklearn needed)
# ══════════════════════════════════════════════════════════════════════════════

class CategoryClassifier:
    """
    Text-based category classifier trained on transaction descriptions.
    Uses Multinomial Naïve Bayes with Laplace smoothing.
    Falls back gracefully if not trained.
    """

    def __init__(self):
        self.class_log_prior: dict[str, float] = {}
        self.feature_log_prob: dict[str, dict[str, float]] = {}
        self.vocab: set[str] = set()
        self.classes: list[str] = []
        self.trained: bool = False

    # ── Tokenizer ─────────────────────────────────────────────────────────────
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        tokens = re.findall(r"[a-z]+", text)
        stopwords = {"i", "a", "the", "on", "for", "to", "my", "me",
                     "at", "in", "of", "and", "or", "is", "was", "it"}
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def train(self, texts: list[str], labels: list[str]):
        """Train on (description, category) pairs."""
        if len(texts) < 5:
            return  # too little data

        class_counts: dict[str, int] = Counter(labels)
        self.classes = list(class_counts.keys())
        n_total = len(labels)

        # Class log-priors
        self.class_log_prior = {
            c: log(count / n_total)
            for c, count in class_counts.items()
        }

        # Word frequencies per class
        word_freq: dict[str, Counter] = defaultdict(Counter)
        for text, label in zip(texts, labels):
            tokens = self._tokenize(text)
            word_freq[label].update(tokens)
            self.vocab.update(tokens)

        vocab_size = len(self.vocab)

        # Feature log-probabilities with Laplace smoothing
        self.feature_log_prob = {}
        for cls in self.classes:
            total = sum(word_freq[cls].values()) + vocab_size
            self.feature_log_prob[cls] = {
                word: log((word_freq[cls].get(word, 0) + 1) / total)
                for word in self.vocab
            }

        self.trained = True
        self._save()

    def predict(self, text: str) -> tuple[str, float]:
        """Returns (predicted_category, confidence_score)."""
        if not self.trained or not self.classes:
            return "Miscellaneous", 0.0

        tokens = self._tokenize(text)
        scores: dict[str, float] = {}

        for cls in self.classes:
            score = self.class_log_prior[cls]
            for token in tokens:
                if token in self.feature_log_prob[cls]:
                    score += self.feature_log_prob[cls][token]
            scores[cls] = score

        best_class = max(scores, key=scores.get)

        # Softmax-like confidence from log scores
        max_score = scores[best_class]
        exp_scores = {c: np.exp(s - max_score) for c, s in scores.items()}
        total_exp = sum(exp_scores.values())
        confidence = exp_scores[best_class] / total_exp if total_exp else 0.0

        return best_class, round(float(confidence), 2)

    def retrain_from_db(self, transactions_df: pd.DataFrame):
        """Convenience method: retrain directly from the transactions table."""
        if transactions_df.empty or "description" not in transactions_df.columns:
            return
        df = transactions_df[transactions_df["type"] == "expense"].dropna(
            subset=["description", "category"]
        )
        if len(df) < 5:
            return
        self.train(df["description"].tolist(), df["category"].tolist())

    def _save(self):
        with open(CLASSIFIER_PATH, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls) -> "CategoryClassifier":
        if CLASSIFIER_PATH.exists():
            with open(CLASSIFIER_PATH, "rb") as f:
                return pickle.load(f)
        return cls()


# ══════════════════════════════════════════════════════════════════════════════
# 3.  INSIGHTS ENGINE  (rule-based financial analysis)
# ══════════════════════════════════════════════════════════════════════════════

def generate_insights(transactions_df: pd.DataFrame) -> list[str]:
    """
    Produces a list of human-readable insight strings from transaction data.
    """
    insights: list[str] = []
    if transactions_df.empty:
        return ["No transactions recorded yet. Start by adding your expenses!"]

    df = transactions_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    expenses = df[df["type"] == "expense"]
    income   = df[df["type"] == "income"]

    # Total stats
    total_expense = expenses["amount"].sum()
    total_income  = income["amount"].sum()
    net = total_income - total_expense

    insights.append(
        f"💰 **Net Balance:** ₹{net:,.0f} "
        f"({'surplus' if net >= 0 else 'deficit'})"
    )

    # Top spending category
    if not expenses.empty:
        top_cat = expenses.groupby("category")["amount"].sum().idxmax()
        top_amt = expenses.groupby("category")["amount"].sum().max()
        insights.append(
            f"🏷️ **Biggest spend category:** {top_cat} (₹{top_amt:,.0f})"
        )

    # Month-over-month change
    monthly_exp = (
        expenses.groupby("month")["amount"]
        .sum()
        .sort_index()
    )
    if len(monthly_exp) >= 2:
        prev, curr = float(monthly_exp.iloc[-2]), float(monthly_exp.iloc[-1])
        change_pct = ((curr - prev) / prev * 100) if prev else 0
        direction  = "📈 increased" if change_pct > 0 else "📉 decreased"
        insights.append(
            f"📅 **Monthly trend:** Spending {direction} by "
            f"{abs(change_pct):.1f}% vs last month."
        )

    # Savings rate
    if total_income > 0:
        savings_rate = max(0, (total_income - total_expense) / total_income * 100)
        emoji = "✅" if savings_rate >= 20 else "⚠️"
        insights.append(
            f"{emoji} **Savings rate:** {savings_rate:.1f}% "
            f"({'healthy' if savings_rate >= 20 else 'below recommended 20%'})"
        )

    # Daily average
    if not expenses.empty:
        n_days = max(1, (df["date"].max() - df["date"].min()).days + 1)
        daily_avg = total_expense / n_days
        insights.append(f"📊 **Daily avg spend:** ₹{daily_avg:,.0f}")

    return insights
