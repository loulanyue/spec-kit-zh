"""Expression evaluation and template interpolation for Spec Kit Workflows."""

from __future__ import annotations

import ast
import json
import re
from typing import Any


class ExpressionError(ValueError):
    """Raised when an expression cannot be parsed or evaluated."""


class AttrDict(dict):
    """Dictionary supporting attribute-style access and safe missing key resolution."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            val = self[name]
            if isinstance(val, dict) and not isinstance(val, AttrDict):
                val = AttrDict(val)
                self[name] = val
            return val
        return None

    def __getitem__(self, key: Any) -> Any:
        if key in self:
            val = super().__getitem__(key)
            if isinstance(val, dict) and not isinstance(val, AttrDict):
                val = AttrDict(val)
                self[key] = val
            return val
        return None


def _wrap_namespace(val: Any) -> Any:
    if isinstance(val, dict):
        return AttrDict({k: _wrap_namespace(v) for k, v in val.items()})
    if isinstance(val, list):
        return [_wrap_namespace(x) for x in val]
    return val


def filter_default(value: Any, fallback: Any = "") -> Any:
    """Return fallback if value is None, empty string, or empty container."""
    if value is None or value == "":
        return fallback
    return value


def filter_join(value: Any, sep: str = ", ") -> str:
    """Join iterable into string with separator."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return sep.join(str(item) for item in value)
    return str(value)


def filter_contains(value: Any, item: Any) -> bool:
    """Check if value contains item."""
    if value is None:
        return False
    try:
        return item in value
    except TypeError:
        return False


def filter_map(value: Any, attr: str) -> list[Any]:
    """Extract attribute or key from each item in collection."""
    if not isinstance(value, (list, tuple)):
        return []
    results = []
    for elem in value:
        if isinstance(elem, dict):
            results.append(elem.get(attr))
        elif hasattr(elem, attr):
            results.append(getattr(elem, attr))
        else:
            results.append(None)
    return results


def filter_from_json(value: Any) -> Any:
    """Parse JSON string into typed Python data."""
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if not isinstance(value, str):
        raise ExpressionError(f"from_json requires string, got {type(value).__name__}")
    try:
        return json.loads(value)
    except Exception as e:
        raise ExpressionError(f"Invalid JSON string in from_json filter: {e}") from e


BUILTIN_FILTERS = {
    "default": filter_default,
    "join": filter_join,
    "contains": filter_contains,
    "map": filter_map,
    "from_json": filter_from_json,
}


def _split_filter_chain(expr_str: str) -> list[str]:
    """Split an expression by pipe `|` ignoring pipes within strings."""
    tokens: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0
    while i < len(expr_str):
        char = expr_str[i]
        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
        elif char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
        elif char == "|" and not in_single and not in_double:
            tokens.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    if current:
        tokens.append("".join(current).strip())
    return [t for t in tokens if t]


class SafeEvaluator(ast.NodeVisitor):
    """Safely evaluates an AST expression against a namespace."""

    def __init__(self, namespace: dict[str, Any]):
        self.ns = namespace

    def eval(self, node: ast.AST) -> Any:
        return self.visit(node)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        name = node.id
        if name == "true":
            return True
        if name == "false":
            return False
        if name == "null" or name == "none" or name == "None":
            return None
        if name in self.ns:
            return self.ns[name]
        return None

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        value = self.visit(node.value)
        attr = node.attr
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get(attr)
        if hasattr(value, attr):
            return getattr(value, attr)
        return None

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        value = self.visit(node.value)
        slice_val = self.visit(node.slice)
        if value is None:
            return None
        try:
            return value[slice_val]
        except (KeyError, IndexError, TypeError):
            return None

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        val = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not val
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.UAdd):
            return +val
        raise ExpressionError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.FloorDiv):
            return left // right
        if isinstance(op, ast.Mod):
            return left % right
        raise ExpressionError(f"Unsupported binary operator: {type(op).__name__}")

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            for val_node in node.values:
                val = self.visit(val_node)
                if not val:
                    return val
            return val
        if isinstance(node.op, ast.Or):
            for val_node in node.values:
                val = self.visit(val_node)
                if val:
                    return val
            return val
        raise ExpressionError(f"Unsupported boolean operator: {type(node.op).__name__}")

    def visit_Compare(self, node: ast.Compare) -> Any:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Eq):
                res = left == right
            elif isinstance(op, ast.NotEq):
                res = left != right
            elif isinstance(op, ast.Lt):
                res = left < right
            elif isinstance(op, ast.LtE):
                res = left <= right
            elif isinstance(op, ast.Gt):
                res = left > right
            elif isinstance(op, ast.GtE):
                res = left >= right
            elif isinstance(op, ast.In):
                res = (left in right) if right is not None else False
            elif isinstance(op, ast.NotIn):
                res = (left not in right) if right is not None else True
            else:
                raise ExpressionError(f"Unsupported comparison: {type(op).__name__}")
            if not res:
                return False
            left = right
        return True

    def visit_List(self, node: ast.List) -> Any:
        return [self.visit(elt) for elt in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> Any:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_Dict(self, node: ast.Dict) -> Any:
        return {
            self.visit(k): self.visit(v)
            for k, v in zip(node.keys, node.values)
            if k is not None
        }

    def visit_Call(self, node: ast.Call) -> Any:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        args = [self.visit(arg) for arg in node.args]
        kwargs = {kw.arg: self.visit(kw.value) for kw in node.keywords if kw.arg}

        if func_name in BUILTIN_FILTERS:
            return BUILTIN_FILTERS[func_name](*args, **kwargs)

        # Allow basic functions
        if func_name == "len" and args:
            return len(args[0])
        if func_name == "str" and args:
            return str(args[0])
        if func_name == "int" and args:
            return int(args[0])
        if func_name == "float" and args:
            return float(args[0])
        if func_name == "bool" and args:
            return bool(args[0])

        raise ExpressionError(
            f"Function call '{func_name}' is not allowed or supported"
        )

    def generic_visit(self, node: ast.AST) -> Any:
        raise ExpressionError(f"Unsupported expression syntax: {type(node).__name__}")


def _preprocess_expression(expr: str) -> str:
    """Preprocess dot-notated steps/inputs with hyphens e.g. steps.foo-bar -> steps['foo-bar']."""
    # Replace steps.some-name or inputs.some-name where name has hyphens
    pattern = r"\b(inputs|steps|context)\.([a-zA-Z0-9_\-]+)"

    def repl(m: re.Match) -> str:
        base, attr = m.group(1), m.group(2)
        return f'{base}["{attr}"]'

    processed = re.sub(pattern, repl, expr)
    return processed


def evaluate_single_expression(expr_str: str, namespace: dict[str, Any]) -> Any:
    """Evaluate a single expression string without enclosing braces."""
    expr_str = expr_str.strip()
    if not expr_str:
        return ""

    filter_tokens = _split_filter_chain(expr_str)
    base_expr = filter_tokens[0]
    filters = filter_tokens[1:]

    # Evaluate base expression
    prep = _preprocess_expression(base_expr)
    try:
        parsed = ast.parse(prep, mode="eval")
        evaluator = SafeEvaluator(_wrap_namespace(namespace))
        result = evaluator.eval(parsed)
    except Exception as e:
        # Fallback: if single word and not found in namespace, check literal or return None
        if (
            re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", base_expr)
            and base_expr not in namespace
        ):
            result = None
        else:
            raise ExpressionError(
                f"Failed to evaluate expression '{expr_str}': {e}"
            ) from e

    # Apply filters sequentially
    for flt in filters:
        flt = flt.strip()
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)(?:\((.*)\))?$", flt)
        if not m:
            raise ExpressionError(f"Invalid filter syntax: {flt}")
        fname = m.group(1)
        fargs_raw = m.group(2)

        if fname not in BUILTIN_FILTERS:
            raise ExpressionError(f"Unknown filter: {fname}")

        filter_fn = BUILTIN_FILTERS[fname]
        extra_args: list[Any] = []
        if fargs_raw:
            # Parse arguments
            call_code = f"__dummy__({fargs_raw})"
            parsed_call = ast.parse(call_code, mode="eval")
            if isinstance(parsed_call.body, ast.Call):
                evaluator = SafeEvaluator(_wrap_namespace(namespace))
                extra_args = [evaluator.eval(arg) for arg in parsed_call.body.args]

        result = filter_fn(result, *extra_args)

    return result


EXPR_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")


def evaluate_expression(template: Any, context: Any) -> Any:
    """Evaluate expressions in template (string, dict, list, or primitive).

    If the template is a string exactly equal to '{{ expr }}', the evaluated typed
    result is returned. Otherwise, if template is a string with embedded '{{ expr }}',
    string interpolation is performed.
    """
    if isinstance(context, dict):
        namespace = context
    elif hasattr(context, "to_namespace"):
        namespace = context.to_namespace()
    else:
        namespace = getattr(context, "__dict__", {})

    if isinstance(template, str):
        stripped = template.strip()
        single_match = re.fullmatch(r"\{\{\s*(.*?)\s*\}\}", stripped)
        if single_match:
            # Single expression, preserve typed return value
            expr_body = single_match.group(1)
            return evaluate_single_expression(expr_body, namespace)

        # Mixed string template
        def replace_match(m: re.Match) -> str:
            expr_body = m.group(1)
            res = evaluate_single_expression(expr_body, namespace)
            if res is None:
                return ""
            if isinstance(res, bool):
                return "true" if res else "false"
            return str(res)

        return EXPR_PATTERN.sub(replace_match, template)

    if isinstance(template, dict):
        return {k: evaluate_expression(v, namespace) for k, v in template.items()}

    if isinstance(template, list):
        return [evaluate_expression(elem, namespace) for elem in template]

    return template


def evaluate_condition(condition: str, context: Any) -> bool:
    """Evaluate a condition expression to a boolean."""
    if not condition or not str(condition).strip():
        return True

    res = evaluate_expression(str(condition).strip(), context)
    return bool(res)


__all__ = [
    "AttrDict",
    "BUILTIN_FILTERS",
    "ExpressionError",
    "evaluate_condition",
    "evaluate_expression",
    "evaluate_single_expression",
    "filter_contains",
    "filter_default",
    "filter_from_json",
    "filter_join",
    "filter_map",
]
