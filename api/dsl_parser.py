
# backend/api/dsl_parser.py
# Lark grammar parser to convert DSL text into an AST (dictionary).

from lark import Lark, Transformer
from typing import Any, Dict

DSL_GRAMMAR = r"""
?start: rules
rules: entry_block exit_block?
entry_block: "ENTRY:" expr_line
exit_block: "EXIT:" expr_line
?expr_line: or_expr
?or_expr: and_expr ("OR" and_expr)*
?and_expr: atom ("AND" atom)*
?atom: comparison | indicator | cross | NAME | NUMBER
comparison: NAME COMP_OP value
indicator: NAME "(" NAME? ","? NUMBER? ")"
cross: "CROSS" "(" NAME "," NAME ")"
value: indicator | NUMBER

%import common.CNAME -> NAME
%import common.SIGNED_NUMBER -> NUMBER
%import common.WS
%ignore WS
COMP_OP: ">="|"<="|">"|"<"|"=="|"="
"""

parser = Lark(DSL_GRAMMAR, parser="lalr", propagate_positions=True)

class ASTNode(dict):
    def to_dict(self):
        return dict(self)

class TreeToAST(Transformer):
    def NAME(self, token):
        return str(token)
    def NUMBER(self, token):
        try:
            return int(token)
        except:
            return float(token)
    def comparison(self, items):
        left = items[0]
        op = str(items[1])
        right = items[2]
        return ASTNode({"type": "comparison", "left": left, "op": op, "right": right})
    def indicator(self, items):
        name = items[0]
        params = []
        for it in items[1:]:
            params.append(it)
        return ASTNode({"type": "indicator", "name": name.lower(), "params": params})
    def cross(self, items):
        return ASTNode({"type": "cross", "direction": items[0].lower(), "target": items[1].lower()})
    def and_expr(self, items):
        if len(items) == 1:
            return items[0]
        return ASTNode({"type": "and", "items": items})
    def or_expr(self, items):
        if len(items) == 1:
            return items[0]
        return ASTNode({"type": "or", "items": items})
    def entry_block(self, items):
        return ASTNode({"type": "entry", "expr": items[0]})
    def exit_block(self, items):
        return ASTNode({"type": "exit", "expr": items[0]})
    def rules(self, items):
        out = {}
        for it in items:
            if isinstance(it, dict) and it.get("type") == "entry":
                out["entry"] = it["expr"]
            elif isinstance(it, dict) and it.get("type") == "exit":
                out["exit"] = it["expr"]
        return out

def _astnode_to_py(obj):
    # Convert ASTNode / dict recursively to plain dicts
    if isinstance(obj, ASTNode):
        return {k: _astnode_to_py(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: _astnode_to_py(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_astnode_to_py(v) for v in obj]
    return obj

def parse_dsl(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        return {"entry": None, "exit": None}
    # Lark grammar expects uppercase tokens in our grammar; convert to uppercase for keywords, but keep names intact
    # Simple approach: uppercase DSL keywords only
    # This parser tolerates both uppercase and lowercase names because NAME token matches CNAME
    tree = parser.parse(text)
    ast = TreeToAST().transform(tree)
    return _astnode_to_py(ast)
