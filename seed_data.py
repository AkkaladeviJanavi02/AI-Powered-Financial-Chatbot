"""
seed_data.py - Populate DB with realistic sample data for demos/testing.
Run once: python seed_data.py
"""

from database import initialize_db, add_transaction, set_budget

TRANSACTIONS = [
    # Month 1: December 2024
    ("expense", 4200, "Food & Dining",   "Monthly groceries",          "2024-12-02"),
    ("expense", 1800, "Transport",       "Uber rides December",        "2024-12-05"),
    ("expense", 1200, "Entertainment",  "Netflix + Spotify",          "2024-12-06"),
    ("expense", 8500, "Rent & Housing",  "December rent",              "2024-12-01"),
    ("expense", 2300, "Shopping",        "Winter clothes Amazon",      "2024-12-15"),
    ("expense",  950, "Health",          "Gym membership",             "2024-12-10"),
    ("expense",  600, "Utilities",       "Electricity bill",           "2024-12-20"),
    ("income",  55000, "Income",         "December salary",            "2024-12-01"),

    # Month 2: January 2025
    ("expense", 3900, "Food & Dining",   "Food & dining January",      "2025-01-03"),
    ("expense", 1500, "Transport",       "Metro + Uber",               "2025-01-08"),
    ("expense", 1200, "Entertainment",  "Streaming subscriptions",    "2025-01-06"),
    ("expense", 8500, "Rent & Housing",  "January rent",               "2025-01-01"),
    ("expense", 3200, "Education",       "Udemy courses",              "2025-01-12"),
    ("expense",  750, "Health",          "Doctor visit",               "2025-01-18"),
    ("expense",  550, "Utilities",       "Internet bill",              "2025-01-22"),
    ("income",  55000, "Income",         "January salary",             "2025-01-01"),
    ("income",   8000, "Income",         "Freelance project payment",  "2025-01-20"),

    # Month 3: February 2025
    ("expense", 4600, "Food & Dining",   "Restaurant + groceries",     "2025-02-04"),
    ("expense", 2100, "Transport",       "Long distance travel",       "2025-02-10"),
    ("expense", 1200, "Entertainment",  "Streaming + movie tickets",  "2025-02-06"),
    ("expense", 8500, "Rent & Housing",  "February rent",              "2025-02-01"),
    ("expense", 5400, "Shopping",        "Electronics purchase",       "2025-02-14"),
    ("expense",  900, "Health",          "Pharmacy & supplements",     "2025-02-20"),
    ("expense",  620, "Utilities",       "Electricity + gas",          "2025-02-25"),
    ("income",  58000, "Income",         "February salary + bonus",    "2025-02-01"),

    # Month 4: March 2025  (current month, partial)
    ("expense", 2800, "Food & Dining",   "Swiggy + groceries",         "2025-03-02"),
    ("expense", 1200, "Transport",       "Ola + petrol",               "2025-03-05"),
    ("expense", 1200, "Entertainment",  "Hotstar subscription",       "2025-03-06"),
    ("expense", 8500, "Rent & Housing",  "March rent",                 "2025-03-01"),
    ("expense", 1500, "Education",       "Coursera subscription",      "2025-03-08"),
    ("income",  55000, "Income",         "March salary",               "2025-03-01"),
]

BUDGETS = [
    ("Food & Dining",  5000),
    ("Transport",      2500),
    ("Entertainment",  1500),
    ("Shopping",       3000),
    ("Health",         1500),
    ("Utilities",      1000),
    ("Education",      2000),
]

if __name__ == "__main__":
    initialize_db()
    print("Seeding transactions...")
    for tx in TRANSACTIONS:
        add_transaction(*tx)
    print(f"  → {len(TRANSACTIONS)} transactions added.")

    print("Setting budgets...")
    for b in BUDGETS:
        set_budget(*b)
    print(f"  → {len(BUDGETS)} budgets configured.")

    print("\n✅ Seed complete! Run:  streamlit run app.py")
