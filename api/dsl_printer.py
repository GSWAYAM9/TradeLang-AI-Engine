
# backend/api/dsl_printer.py
# Turn structured JSON into a readable DSL text block.

from typing import Any, Dict

def _format_expr(expr):
    if isinstance(expr, dict):
        if 'indicator' in expr:
            name = expr['indicator'].upper()
            params = ",".join(str(p) for p in expr.get('params', []))
            return f"{name}({params})"
        if expr.get('type') == 'cross':
            return f"CROSS({expr.get('direction').upper()}, {expr.get('target')})"
        return str(expr)
    return str(expr)

def structured_to_dsl(structured: Dict[str, Any]) -> str:
    lines = []
    if structured.get('entry'):
        lines.append("ENTRY:")
        parts = []
        for c in structured['entry']:
            if 'type' in c and c['type'] == 'cross':
                parts.append(_format_expr(c))
            else:
                left = c.get('left')
                op = c.get('operator')
                right = _format_expr(c.get('right'))
                parts.append(f"{left} {op} {right}")
        lines.append(" AND ".join(parts))
    if structured.get('exit'):
        lines.append("EXIT:")
        parts = []
        for c in structured['exit']:
            if 'type' in c and c['type'] == 'cross':
                parts.append(_format_expr(c))
            else:
                left = c.get('left')
                op = c.get('operator')
                right = _format_expr(c.get('right'))
                parts.append(f"{left} {op} {right}")
        lines.append(" AND ".join(parts))
    return "\n".join(lines)
