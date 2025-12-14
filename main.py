from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from api.nl_to_json import nl_to_structured
from api.dsl_printer import structured_to_dsl
from api.dsl_parser import parse_dsl
from api.ast_to_python import generate_python_code
from api.backtester import run_backtest_with_code

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- API ----------
@app.post("/api/groq")
async def groq_endpoint(payload: dict):
    text = payload.get("text")
    if not text:
        return {"error": "Missing text"}

    structured = nl_to_structured(text)
    dsl = structured_to_dsl(structured)
    ast = parse_dsl(dsl)
    python_code = generate_python_code(ast)
    backtest = run_backtest_with_code(python_code)

    return {
        "nl_input": text,
        "structured": structured,
        "dsl": dsl,
        "ast": ast,
        "python": python_code,
        "backtest": backtest,
    }

# ---------- FRONTEND ----------
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")
