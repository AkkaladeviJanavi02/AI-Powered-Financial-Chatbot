"""
nlp_parser.py - Natural Language Transaction Parser
Extracts amount, type, category, and description from user messages
using regex patterns + keyword matching (no external NLP dependencies needed).
"""

import re
from dataclasses import dataclass
from typing import Optional


# ── Category keyword map ───────────────────────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Food & Dining":    ["food", "lunch", "dinner", "breakfast", "restaurant",
                         "cafe", "coffee", "pizza", "snack", "groceries", "grocery",
                         "swiggy", "zomato", "eat", "meal", "biryani", "dosa"],
    "Transport":        ["uber", "ola", "cab", "taxi", "bus", "auto", "metro",
                         "fuel", "petrol", "diesel", "train", "flight", "travel",
                         "commute", "toll", "parking"],
    "Shopping":         ["amazon", "flipkart", "shopping", "clothes", "shirt",
                         "shoes", "dress", "mall", "purchase", "bought", "buy"],
    "Entertainment":    ["movie", "netflix", "spotify", "prime", "hotstar",
                         "game", "concert", "ticket", "show", "fun", "outing"],
    "Health":           ["medicine", "doctor", "hospital", "pharmacy", "gym",
                         "fitness", "health", "medical", "checkup", "clinic"],
    "Utilities":        ["electricity", "water", "internet", "wifi", "mobile",
                         "phone", "bill", "recharge", "broadband", "gas"],
    "Education":        ["course", "book", "tuition", "college", "school",
                         "udemy", "coursera", "fee", "study", "exam"],
    "Rent & Housing":   ["rent", "house", "apartment", "maintenance", "society"],
    "Income":           ["salary", "freelance", "payment received", "got paid",
                         "income", "earned", "stipend", "bonus", "refund", "cashback"],
    "Miscellaneous":    [],   # fallback
}

# Patterns that signal an INCOME transaction
INCOME_SIGNALS = [
    "received", "earned", "got paid", "salary", "income",
    "credited", "added", "deposited", "stipend", "bonus", "refund"
]


@dataclass
class ParsedTransaction:
    type_: str          # 'expense' | 'income'
    amount: float
    category: str
    description: str
    raw: str            # original user message
    confidence: float   # 0–1


def _extract_amount(text: str) -> Optional[float]:
    """
    Finds the first currency amount in the text.
    Handles: ₹500, Rs 500, 500 rupees, $20, 1,500, 1.5k
    """
    # Handle shorthand like "1.5k", "2K"
    k_match = re.search(r"(\d+\.?\d*)\s*k\b", text, re.IGNORECASE)
    if k_match:
        return float(k_match.group(1)) * 1000

    # Standard currency patterns
    patterns = [
        r"(?:₹|rs\.?|inr|usd|\$)\s*([\d,]+\.?\d*)",   # ₹500, Rs 500
        r"([\d,]+\.?\d*)\s*(?:rupees?|rs\.?|inr|\$)",   # 500 rupees
        r"\b([\d,]+\.?\d*)\b",                           # bare number fallback
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_num = match.group(1).replace(",", "")
            try:
                return float(raw_num)
            except ValueError:
                continue
    return None


def _detect_type(text: str) -> str:
    """Returns 'income' if text contains income signals, else 'expense'."""
    text_lower = text.lower()
    for signal in INCOME_SIGNALS:
        if signal in text_lower:
            return "income"
    return "expense"


def _detect_category(text: str, tx_type: str) -> str:
    """Finds best matching category by scanning keywords."""
    text_lower = text.lower()

    if tx_type == "income":
        return "Income"

    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "Income":
            continue
        score = sum(1 for kw in keywords if kw in text_lower)
        if score:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return "Miscellaneous"


def parse_transaction(user_input: str) -> Optional[ParsedTransaction]:
    """
    Main entry point. Returns a ParsedTransaction or None if no amount found.

    Examples:
        "I spent 500 on food" → expense, 500, Food & Dining
        "Got salary of 50000" → income, 50000, Income
        "Paid ₹1200 for Netflix" → expense, 1200, Entertainment
    """
    text = user_input.strip()
    amount = _extract_amount(text)
    if amount is None or amount <= 0:
        return None

    tx_type = _detect_type(text)
    category = _detect_category(text, tx_type)

    # Build a clean description from the message (strip numbers / currency words)
    description = re.sub(
        r"(?:₹|rs\.?|inr|\$)?\s*[\d,]+\.?\d*\s*(?:rupees?|rs\.?|k)?",
        "", text, flags=re.IGNORECASE
    ).strip(" ,.;:-")
    description = re.sub(r"\s{2,}", " ", description).strip() or text

    # Simple confidence: higher if explicit currency symbol or known keyword matched
    confidence = 0.6
    if re.search(r"₹|rs\.?|inr|\$", text, re.IGNORECASE):
        confidence += 0.2
    if category != "Miscellaneous":
        confidence += 0.2

    return ParsedTransaction(
        type_=tx_type,
        amount=amount,
        category=category,
        description=description,
        raw=text,
        confidence=min(confidence, 1.0),
    )


def is_query(text: str) -> bool:
    """
    Returns True if the message looks like a question / query
    rather than a transaction entry.
    """
    query_patterns = [
        r"\?$",
        r"^(how|what|when|where|why|show|tell|give|list|display|summarize|predict|analyze)",
        r"(spending|expenses?|income|balance|budget|trend|insight|forecast|report|history)",
    ]
    text_lower = text.lower().strip()
    return any(re.search(p, text_lower) for p in query_patterns)


# ── Quick self-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    samples = [
        "I spent 500 on food today",
        "Paid ₹1200 for Netflix subscription",
        "Got salary of 50000",
        "Uber ride cost me 350 rupees",
        "Bought shoes for 2.5k",
        "What is my total spending this month?",
    ]
    for s in samples:
        result = parse_transaction(s)
        print(f"Input : {s}")
        print(f"Parsed: {result}\n")
