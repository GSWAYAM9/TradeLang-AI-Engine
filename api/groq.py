# backend/api/groq.py
# Vercel Python Serverless Function
# Endpoint: POST /api/groq

import os
import json
import traceback

from nl_to_json import nl_to_structured
from dsl_printer import structured_to_dsl
from dsl_parser import parse_dsl
from ast_to_python import generate_python_code
from backtester import run_backtest_with_code


def handler(request):
    # ✅ REQUIRED DEBUG LOGGING
    print("HANDLER HIT")
    print("ENV KEY PRESENT:", bool(os.getenv("GROQ_API_KEY")))

    try:
        # -----------------------------
        # Parse request body
        # -----------------------------
        try:
            body = request.json()
        except Exception:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid request"})
            }

        text = body.get("text")
        if not text:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'text' field"})
            }

        # -----------------------------
        # NL → Structured JSON
        # -----------------------------
        structured = nl_to_structured(text)

        # -----------------------------
        # Structured → DSL
        # -----------------------------
        dsl_text = structured_to_dsl(structured)

        # -----------------------------
        # DSL → AST
        # -----------------------------
        ast = parse_dsl(dsl_text)

        # -----------------------------
        # AST → Python
        # -----------------------------
        python_code = generate_python_code(ast)

        # -----------------------------
        # Run backtest
        # -----------------------------
        backtest_result = run_backtest_with_code(python_code)

        # -----------------------------
        # Final response
        # -----------------------------
        response = {
            "nl_input": text,
            "structured": structured,
            "dsl": dsl_text,
            "ast": ast,
            "python": python_code,
            "backtest": backtest_result
        }

        return {
            "statusCode": 200,
            "body": json.dumps(response, default=str)
        }

    except Exception as e:
        print("❌ SERVER ERROR")
        print(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal Server Error",
                "detail": str(e)
            })
        }
