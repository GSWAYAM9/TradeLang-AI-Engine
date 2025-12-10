
# backend/api/nl_to_json.py
# Minimal rule-based Natural Language -> structured JSON converter.
# Supports common patterns used in the assignment examples.

import re
from typing import Dict, Any

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "ten": 10, "hundred": 100, "thousand": 1000, "million": 1_000_000
}

def _parse_number(s: str):
    if s is None:
        return None
    s = str(s).replace(",", "").strip().lower()
    # short forms: 1M, 1k
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([km]?)$", s)
    if m:
        val = float(m.group(1))
        suf = m.group(2)
        if suf == "k":
            return val * 1_000
        if suf == "m":
            return val * 1_000_000
        return val
    # words like "one million"
    parts = s.split()
    total = 0
    for p in parts:
        if p in NUM_WORDS:
            total += NUM_WORDS[p]
        else:
            try:
                total += float(p)
            except:
                pass
    if total > 0:
        return total
    try:
        return float(s)
    except:
        return s

def nl_to_structured(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Simple normalization
    cleaned = re.sub(r"\s+", " ", text).strip()

    structured = {"entry": [], "exit": []}

    # Split by periods or semicolons to sentences
    sentences = re.split(r"[.\n;]", cleaned)
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        low = s.lower()
        if re.search(r"\b(buy|enter)\b", low):
            target_list = structured["entry"]
        elif re.search(r"\b(exit|sell|close position)\b", low):
            target_list = structured["exit"]
        else:
            # If unclear, put into entry by default
            target_list = structured["entry"]

        # split by ' and ' / ' or '
        clauses = re.split(r"\band\b|\bor\b", s, flags=re.I)
        for c in clauses:
            cond = _parse_clause(c.strip())
            if cond:
                target_list.append(cond)

    return structured

def _parse_clause(clause: str):
    clause = clause.strip()
    if not clause:
        return None

    # close is above the 20-day moving average
    m = re.search(r"close\s*(?:is\s*)?(above|below|greater than|less than)\s*(the\s*)?(?P<num>\d+)\-?day\s*moving average", clause, re.I)
    if m:
        dir = m.group(1)
        num = int(m.group("num"))
        op = ">" if re.search(r"above|greater", dir, re.I) else "<"
        return {"left": "close", "operator": op, "right": {"indicator": "sma", "params": ["close", num]}}

    # rsi(14) is below 30 or RSI 14 < 30
    m = re.search(r"rsi\s*\(?\s*(?P<n>\d+)\s*\)?\s*(?:is\s*)?(?P<cmp><|>|<=|>=|less than|greater than|below|above)\s*(?P<num>\d+)", clause, re.I)
    if m:
        n = int(m.group("n"))
        cmp = m.group("cmp")
        op = ">" if re.search(r"greater|above|>", cmp, re.I) else "<"
        num = float(m.group("num"))
        return {"left": {"indicator": "rsi", "params": ["close", n]}, "operator": op, "right": num}

    # volume is above 1 million
    m = re.search(r"volume\s*(?:is\s*)?(above|below|greater than|less than|>|<|>=|<=)\s*(?P<num>[0-9\.,kmKM\s]+)", clause, re.I)
    if m:
        dir = m.group(1)
        num = _parse_number(m.group("num"))
        op = ">" if re.search(r"above|greater|>", dir, re.I) else "<"
        return {"left": "volume", "operator": op, "right": num}

    # price crosses above yesterday's high
    m = re.search(r"price\s*cross(?:es)?\s*(above|below)\s*(yesterday(?:'s)?\s*high|yesterday(?:'s)?\s*low)", clause, re.I)
    if m:
        dir = m.group(1)
        target = m.group(2)
        return {"type": "cross", "direction": dir.lower(), "target": target}

    # generic: left op right (e.g. close > SMA(close,20) or close > 100)
    m = re.search(r"(?P<left>\w+)\s*(?P<op>>=|<=|>|<|==|=)\s*(?P<right>.+)", clause)
    if m:
        left = m.group("left")
        op = m.group("op")
        right = m.group("right").strip()
        # try parse indicator in right
        m2 = re.search(r"(sma|rsi|ema)\s*\(?\s*([a-zA-Z_]+)?\s*,?\s*([0-9]+)?\s*\)?", right, re.I)
        if m2:
            ind = m2.group(1).lower()
            p1 = m2.group(2) if m2.group(2) else left
            p2 = int(m2.group(3)) if m2.group(3) else None
            params = [p1]
            if p2:
                params.append(p2)
            return {"left": left, "operator": op, "right": {"indicator": ind, "params": params}}
        # try number
        num = _parse_number(right)
        return {"left": left, "operator": op, "right": num}

    return None
