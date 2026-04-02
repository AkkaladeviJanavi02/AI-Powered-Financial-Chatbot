# 💹 FinBot — AI-Powered Financial Chatbot

A production-ready, ML-powered personal finance chatbot built with Python + Streamlit.

---

## 🚀 Features

| Feature | Details |
|---|---|
| 💬 Natural Language Input | "I spent ₹500 on food" → auto-parsed |
| 🏷️ ML Auto-categorization | Naïve Bayes classifier trained on your data |
| 📊 Interactive Dashboard | Plotly charts: pie, bar, trend, gauge |
| 🔮 Expense Prediction | Linear Regression forecasting next month |
| 💰 Budget Tracking | Set per-category limits with gauge charts |
| 📋 Transaction History | Filter, search, export as CSV |
| 🔍 AI Insights | Savings rate, trends, category analysis |
| 🗄️ Persistent Storage | SQLite — no cloud required |

---

## 📁 Project Structure

```
finbot/
├── app.py              ← Streamlit UI (main entry point)
├── chatbot.py          ← NLP query router & response engine
├── nlp_parser.py       ← Transaction parser (regex + keywords)
├── ml_models.py        ← Linear Regression + Naïve Bayes + Insights
├── database.py         ← SQLite data layer (all CRUD)
├── charts.py           ← Plotly chart builders
├── seed_data.py        ← Demo data seeder
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── data/               ← SQLite DB (auto-created)
└── models/             ← Trained model pkl files (auto-created)
```

---

## ⚙️ Setup & Run

### 1. Clone / download the project
```bash
git clone <your-repo-url>
cd finbot
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Seed with demo data
```bash
python seed_data.py
```

### 5. Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 💬 Chat Commands

**Adding transactions:**
```
I spent 500 on food
Paid ₹1200 for Netflix
Got salary of 50000
Uber ride cost 350 rupees
Bought shoes for 2.5k
```

**Queries:**
```
Show my balance
What's my spending by category?
Give me financial insights
Predict my next month expenses
Show recent transactions
Show budget status
Set budget for Food to 5000
Help
```

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push to GitHub:
```bash
git init && git add . && git commit -m "init"
git remote add origin https://github.com/<you>/finbot.git
git push -u origin main
```

2. Go to https://share.streamlit.io
3. Click **New app** → select your repo → set **Main file: app.py**
4. Click **Deploy** — live in ~2 minutes!

> **Note:** On Streamlit Cloud, the SQLite DB resets on restart. For persistent storage in production, replace `database.py` with Firebase Firestore or Supabase (PostgreSQL).

---

## 🚀 Deploy to Render (Persistent)

1. Create a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. Push to GitHub.
3. Go to https://render.com → New Web Service → connect repo.
4. Set build command: `pip install -r requirements.txt`
5. Set start command from Procfile above.

---

## 🧠 ML Architecture

### Transaction Categorization
- **Algorithm:** Multinomial Naïve Bayes (pure Python, no sklearn)
- **Training data:** Your own transactions (auto-retrains every 5 txns)
- **Fallback:** Keyword-based category matching

### Expense Prediction
- **Algorithm:** OLS Linear Regression (pure numpy)
- **Input:** Monthly expense totals
- **Output:** Next month prediction + trend + confidence score

### NLP Parsing
- **Approach:** Regex + keyword pattern matching
- **Handles:** ₹, Rs, INR, $, "1.5k", comma-formatted numbers
- **Detects:** Income signals vs expense signals

---

## 📈 Improvements for Industry Level

1. **Auth:** Add Streamlit-Authenticator for multi-user support
2. **Firebase:** Replace SQLite with Firestore for cloud persistence
3. **OpenAI API:** Plug in GPT-4 for more powerful NLP
4. **Time-series:** Upgrade to ARIMA/Prophet for better forecasting
5. **Alerts:** Email/SMS alerts when budget threshold crossed
6. **Mobile:** Convert to FastAPI + React Native for a mobile app
7. **CI/CD:** Add GitHub Actions for auto-deploy on push

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python 3.11+
- **Database:** SQLite (via Python `sqlite3`)
- **ML:** Pure NumPy (Linear Regression) + Pure Python (Naïve Bayes)
- **Charts:** Plotly Express + Graph Objects
- **NLP:** Regex + Keyword Matching

---

Built for placement portfolio projects. MIT License.
