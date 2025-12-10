
# backend/api/groq.py
# Vercel-compatible Python serverless endpoint.
# Expects POST JSON: { "text": "<natural language rule>" }
# Returns JSON with: nl_input, structured, dsl, ast, python, backtest

import os
import json
import traceback
from typing import Any, Dict

# Local modules (same folder)
from nl_to_json import nl_to_structured
from dsl_printer import structured_to_dsl
from dsl_parser import parse_dsl
from ast_to_python import generate_python_code
from backtester import run_backtest_with_code

# Optional: use requests to call Groq HTTP endpoint if GROQ_API_KEY is provided
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Default Groq endpoint placeholder. Update if Groq docs specify another.
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.ai/v1/outputs")

def _call_groq_prompt(prompt: str, timeout: int = 20) -> str:
    if not GROQ_API_KEY:
        return ""
    try:
        payload = {"model": "llama3-70b-8192", "input": prompt}
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        # Attempt to extract a textual result from common fields
        # (This is defensive because Groq responses may vary)
        if isinstance(data, dict):
            for k in ("output", "result", "text", "choices"):
                if k in data:
                    v = data[k]
                    if isinstance(v, str):
                        return v
                    try:
                        return json.dumps(v)
                    except:
                        return str(v)
        return json.dumps(data)
    except Exception as e:
        # Log error server-side; fallback to rule-based mapping
        print("Groq call failed:", e)
        print(traceback.format_exc())
        return ""

def handler(request):
    """
    Vercel-style handler: request has .json() when invoked by Flask dev server we'll adapt.
    Return a dict with statusCode and body (JSON string).
    """
    try:
        try:
            body = request.json()
        except Exception:
            # If request is a raw dict, accept it
            if isinstance(request, dict):
                body = request
            else:
                # fallback: try to read raw body string
                try:
                    body = json.loads(request)
                except Exception:
                    return {"statusCode": 400, "body": json.dumps({"error": "Invalid request format"})}
    except Exception:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid request"})}

    text = body.get("text") if isinstance(body, dict) else None
    if not text:
        return {"statusCode": 400, "body": json.dumps({"error": "No 'text' field provided"})}

    try:
        # Step 1: NL -> structured JSON (rule-based)
        structured = nl_to_structured(text)

        # Step 1b: optionally call Groq model to get a structured JSON override
        if GROQ_API_KEY:
            prompt = (
                "Convert the following natural-language trading rule into a JSON object with keys 'entry' and 'exit'.\n"
                "Each condition should be an object with 'left', 'operator', 'right' fields. Indicators as {\"indicator\": name, \"params\": [...]}.\n"
                "Return only valid JSON and nothing else.\n\n"
                f"Text: {text}"
            )
            model_out = _call_groq_prompt(prompt)
            if model_out:
                try:
                    parsed = json.loads(model_out)
                    if isinstance(parsed, dict):
                        structured = parsed
                except Exception:
                    # ignore non-JSON model output
                    pass

        # Step 2: structured -> DSL
        dsl_text = structured_to_dsl(structured)

        # Step 3: parse DSL -> AST
        ast = parse_dsl(dsl_text)

        # Step 4: AST -> Python code (string)
        py_code = generate_python_code(ast)

        # Step 5: execute backtest using the generated code (safe sandbox)
        backtest_report = run_backtest_with_code(py_code)

        response = {
            "nl_input": text,
            "structured": structured,
            "dsl": dsl_text,
            "ast": ast,
            "python": py_code,
            "backtest": backtest_report,
        }
        return {"statusCode": 200, "body": json.dumps(response, default=str)}
    except Exception as e:
        print("Handler error:", e)
        print(traceback.format_exc())
        return {"statusCode": 500, "body": json.dumps({"error": "Internal server error", "detail": str(e)})}

# Local debugging run (Flask)
if __name__ == "__main__":
    from flask import Flask, request, Response
    app = Flask(__name__)

    @app.route("/api/groq", methods=["POST"])
    def api_groq():
        r = handler(request)
        return Response(r["body"], status=r.get("statusCode", 200), mimetype="application/json")

    app.run(host="0.0.0.0", port=8080)
