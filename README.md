
# TradeLang AI Engine (NL → DSL → AST → Python → Backtest)

## What this repo contains
A full-stack demo that:
- Accepts natural-language trading rules
- Converts to a small DSL
- Parses DSL to an AST
- Generates Python/pandas code from the AST
- Runs a simple backtest on sample OHLCV data
- Optionally uses Groq LLM (via HTTP) to assist NL→structured conversion

## Project structure
TradeLang-AI-Engine/
├─ backend/
│ └─ api/ (serverless files)
├─ frontend/
│ ├─ index.html
│ ├─ style.css
│ └─ script.js
├─ vercel.json
└─ README.md


## Setup (local)
1. Clone the repo.
2. (Optional) Create a virtualenv and activate it:
3. Install backend deps:
4. Run the backend locally:
This starts a Flask dev server on `http://localhost:8080/api/groq`.

5. Open `frontend/index.html` in a static server or use a simple local HTTP server:
Then open `http://localhost:5500/frontend/index.html` and use the UI.

## Deploy to Vercel
1. Push the repo to GitHub.
2. Create a new project in Vercel and import the repo.
3. In Vercel project Settings → Environment Variables, add:
- `GROQ_API_KEY` = your Groq API key (optional; if absent, rule-based NL parsing used)
- `GROQ_API_URL` = optional URL if different from default
4. Deploy. Vercel will route `/api/groq` to `backend/api/groq.py`.

## Security
- **Do NOT** commit `.env` or any secrets.
- Backend expects `GROQ_API_KEY` via environment variables.

## Notes & Limitations
- This is a demo/prototype; generated Python code is simplistic and intended for demonstration.
- The backtester is purposely minimal and not for live/trading use.
- Groq API integration uses a generic HTTP call — adapt to Groq SDK if required.

## License
GSWAYAM9
