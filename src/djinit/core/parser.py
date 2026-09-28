"""
Safe template expression evaluation for djinit.

Templates use a tiny, comment-style logic language:

    # @IF <expression>      ...  # @ELSEIF <expression>  ...  # @ELSE  ...  # @ENDIF
    # @LOOP <var> in <expression>  ...  # @ENDLOOP
    [[ variable ]]           variable / attribute / index substitution

Expressions are evaluated by walking the parsed syntax tree with an explicit
allow-list. ``eval()`` is never used: restricting ``__builtins__`` is *not* a
sandbox, because object graphs reachable from ordinary literals (for example
``().__class__.__base__.__subclasses__()``) still hand out ``os.system`` and
friends. An explicit interpreter has no such escape hatch.
"""

import ast
import operator
import re
from collections.abc import Mapping
from typing import Any, Dict, List, Optional

__all__ = ["InFileLogicParser", "SafeExpressionError"]


class SafeExpressionError(ValueError):
    """Raised when a template expression is malformed or uses a disallowed feature."""


# The only names an expression may reference besides the render context. These are
# side-effect free helpers; nothing that can import, open, execute or mutate.
_SAFE_BUILTINS: Mapping[str, Any] = {
    "True": True,
    "False": False,
    "None": None,
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "reversed": reversed,
    "sorted": sorted,
    "str": str,
    "zip": zip,
}

# Attribute names that must never be reachable, even on an otherwise harmless
# object. Together with rejecting every ``_``-prefixed name this closes the usual
# attribute-hop escape routes (``__class__``, ``__globals__``, ``__subclasses__``…).
# ``format``/``format_map`` are included because the *format string* they receive is
# resolved with ``getattr`` inside CPython, which would sidestep the checks below.
_FORBIDDEN_ATTRIBUTES = frozenset(
    {
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "eval",
        "exec",
        "exit",
        "format",
        "format_map",
        "fork",
        "getattr",
        "globals",
        "input",
        "locals",
        "open",
        "popen",
        "quit",
        "setattr",
        "spawn",
        "system",
        "vars",
    }
)

# Calling a method is only allowed on plain data values. Without this, a context
# value that happens to be a module, class or function would expose its whole
# (dangerous) surface through dotted access.
_PLAIN_DATA_TYPES = (str, bytes, bytearray, bool, int, float, complex, list, tuple, dict, set, frozenset, Mapping)

# Guards against cheap resource exhaustion such as ``2 ** 99999999``.
_MAX_EXPONENT = 1000


class _SafeExpressionEvaluator(ast.NodeVisitor):
    """Interprets a validated expression tree against the render context."""

    _BINARY_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    _UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }

    _COMPARISON_OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda a, b: operator.contains(b, a),
        ast.NotIn: lambda a, b: not operator.contains(b, a),
    }

    def __init__(self, context: Mapping[str, Any]) -> None:
        # Outermost scope is the render context; comprehension bodies push their own
        # dicts so loop variables never leak into the surrounding scope.
        self._scopes: List[Any] = [context]

    # -- entry point ---------------------------------------------------------

    def evaluate(self, tree: ast.Expression) -> Any:
        return self.visit(tree.body)

    def generic_visit(self, node: ast.AST) -> Any:
        raise SafeExpressionError(f"{type(node).__name__} is not allowed in template expressions")

    # -- literals ------------------------------------------------------------

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_List(self, node: ast.List) -> list:
        return [self.visit(element) for element in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> tuple:
        return tuple(self.visit(element) for element in node.elts)

    def visit_Set(self, node: ast.Set) -> set:
        return {self.visit(element) for element in node.elts}

    def visit_Dict(self, node: ast.Dict) -> dict:
        result: dict = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                raise SafeExpressionError("Dictionary unpacking is not allowed")
            result[self.visit(key_node)] = self.visit(value_node)
        return result

    def visit_JoinedStr(self, node: ast.JoinedStr) -> str:
        return "".join(str(self.visit(value)) for value in node.values)

    def visit_FormattedValue(self, node: ast.FormattedValue) -> str:
        value = self.visit(node.value)
        if node.conversion == 115:  # !s
            return f"{value:s}"
        if node.conversion == 114:  # !r
            return repr(value)
        if node.conversion == 97:  # !a
            return ascii(value)
        if node.format_spec is not None:
            return format(value, self.visit(node.format_spec))
        return str(value)

    # -- names and attributes ------------------------------------------------

    def visit_Name(self, node: ast.Name) -> Any:
        return self._lookup(node.id)

    def _lookup(self, name: str) -> Any:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        if name in _SAFE_BUILTINS:
            return _SAFE_BUILTINS[name]
        raise SafeExpressionError(f"Unknown name: {name!r}")

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        return self._resolve_attribute(self.visit(node.value), node.attr)

    @staticmethod
    def _resolve_attribute(value: Any, name: str) -> Any:
        if name.startswith("_") or name in _FORBIDDEN_ATTRIBUTES:
            raise SafeExpressionError(f"Access to attribute {name!r} is not allowed")
        if isinstance(value, Mapping):
            # Templates routinely index plain dicts with dotted syntax.
            try:
                return value[name]
            except KeyError:
                raise AttributeError(name) from None
        resolved = getattr(value, name)
        if callable(resolved) and not isinstance(value, _PLAIN_DATA_TYPES):
            raise SafeExpressionError(f"Access to method {name!r} is not allowed here")
        return resolved

    # -- operators -----------------------------------------------------------

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = self.visit(value)
                if not result:
                    return result
            return result
        result = False
        for value in node.values:
            result = self.visit(value)
            if result:
                return result
        return result

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        handler = self._UNARY_OPERATORS.get(type(node.op))
        if handler is None:
            raise SafeExpressionError(f"Unary operator {type(node.op).__name__} is not allowed")
        return handler(self.visit(node.operand))

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        handler = self._BINARY_OPERATORS.get(type(node.op))
        if handler is None:
            raise SafeExpressionError(f"Binary operator {type(node.op).__name__} is not allowed")
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Pow) and isinstance(left, int) and isinstance(right, int):
            if abs(right) > _MAX_EXPONENT:
                raise SafeExpressionError("Exponent is too large")
        return handler(left, right)

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for operator_node, comparator_node in zip(node.ops, node.comparators):
            handler = self._COMPARISON_OPERATORS.get(type(operator_node))
            if handler is None:
                raise SafeExpressionError(f"Comparison {type(operator_node).__name__} is not allowed")
            right = self.visit(comparator_node)
            if not handler(left, right):
                return False
            left = right
        return True

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    # -- subscripts ----------------------------------------------------------

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        value = self.visit(node.value)
        key = self._resolve_subscript_key(node.slice, value)
        try:
            return value[key]
        except TypeError as exc:
            raise SafeExpressionError(f"Cannot subscript {type(value).__name__}") from exc

    def _resolve_subscript_key(self, node: ast.AST, value: Any) -> Any:
        if isinstance(node, ast.Slice):
            return slice(
                self._resolve_subscript_bound(node.lower),
                self._resolve_subscript_bound(node.upper),
                self._resolve_subscript_bound(node.step),
            )
        if isinstance(node, ast.Tuple):
            return tuple(self.visit(element) for element in node.elts)
        return self.visit(node)

    def _resolve_subscript_bound(self, node: Optional[ast.AST]) -> Optional[Any]:
        return None if node is None else self.visit(node)

    # -- calls ---------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> Any:
        if any(keyword.arg is None for keyword in node.keywords):
            raise SafeExpressionError("** unpacking is not allowed in calls")
        args = [self.visit(argument) for argument in node.args]
        kwargs = {keyword.arg: self.visit(keyword.value) for keyword in node.keywords}
        callee = self.visit(node.func)
        if not callable(callee):
            raise SafeExpressionError(f"{callee!r} is not callable")
        return callee(*args, **kwargs)

    # -- comprehensions ------------------------------------------------------

    def visit_ListComp(self, node: ast.ListComp) -> list:
        result: list = []
        self._run_comprehension(node.generators, 0, lambda: result.append(self.visit(node.elt)))
        return result

    def visit_SetComp(self, node: ast.SetComp) -> set:
        result: set = set()
        self._run_comprehension(node.generators, 0, lambda: result.add(self.visit(node.elt)))
        return result

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> tuple:
        result: list = []
        self._run_comprehension(node.generators, 0, lambda: result.append(self.visit(node.elt)))
        return tuple(result)

    def visit_DictComp(self, node: ast.DictComp) -> dict:
        result: dict = {}
        self._run_comprehension(
            node.generators,
            0,
            lambda: result.__setitem__(self.visit(node.key), self.visit(node.value)),
        )
        return result

    def _run_comprehension(self, generators: List[ast.comprehension], index: int, emit) -> None:
        if index >= len(generators):
            emit()
            return

        generator = generators[index]
        for value in self._as_iterable(self.visit(generator.iter)):
            self._scopes.append({})
            try:
                self._assign(generator.target, value)
                if all(self.visit(condition) for condition in generator.ifs):
                    self._run_comprehension(generators, index + 1, emit)
            finally:
                self._scopes.pop()

    @staticmethod
    def _as_iterable(value: Any) -> Any:
        if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
            raise SafeExpressionError(f"{type(value).__name__} is not iterable")
        return value

    def _assign(self, target: ast.AST, value: Any) -> None:
        if isinstance(target, ast.Name):
            self._scopes[-1][target.id] = value
            return
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (tuple, list)):
            if len(target.elts) != len(value):
                raise SafeExpressionError("Cannot unpack mismatched number of loop variables")
            for element, item in zip(target.elts, value):
                self._assign(element, item)
            return
        raise SafeExpressionError("Unsupported loop target")


def safe_eval(expression: str, context: Optional[Mapping[str, Any]] = None) -> Any:
    """Evaluate a template expression without ``eval()``.

    Args:
        expression: The expression source, e.g. ``"use_tailwind and len(app_names) > 0"``.
        context: Names available to the expression.

    Raises:
        SafeExpressionError: If the expression is empty, malformed or disallowed.
    """
    source = expression.strip()
    if not source:
        raise SafeExpressionError("Empty expression")

    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise SafeExpressionError(f"Invalid expression syntax: {source!r}") from exc

    return _SafeExpressionEvaluator(context or {}).evaluate(tree)


class InFileLogicParser:
    """
    A lightweight template parser that uses comment-style markers for logic
    and [[ variable ]] for substitutions.
    """

    def __init__(self, context: Dict[str, Any] = None):
        self.context = context or {}

    def _evaluate(self, expression: str) -> Any:
        """Evaluate ``expression`` against the current context, safely."""
        return safe_eval(expression, self.context)

    def _get_value(self, key: str) -> str:
        """
        Supports nested/dotted access like [[ user.name ]] or [[ settings["DEBUG"] ]].
        Dotted names are resolved against the context, and arbitrary expressions are
        evaluated by the safe interpreter. Anything that cannot be resolved is
        returned verbatim so a missing context key stays visible in the output.
        """
        key = key.strip()
        try:
            return str(self._evaluate(key))
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return f"[[ {key} ]]"

    def render(self, template_text: str, context: Dict[str, Any] = None) -> str:
        if context is not None:
            self.context = context

        final_lines = []
        # Stack stores boolean results of nested IF blocks
        # Each element is (current_block_result, has_any_true_branch_executed)
        stack: List[List[bool]] = []

        lines = template_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Handle @IF
            if stripped.startswith("# @IF "):
                expr = stripped[6:].strip()
                try:
                    result = bool(self._evaluate(expr))
                except (AttributeError, IndexError, KeyError, TypeError, ValueError):
                    result = False
                stack.append([result, result])
                i += 1
                continue

            # Handle @ELSEIF
            elif stripped.startswith("# @ELSEIF "):
                if not stack:
                    final_lines.append(line)
                    i += 1
                    continue

                expr = stripped[9:].strip()
                current_stack = stack[-1]

                if current_stack[1]:
                    current_stack[0] = False
                else:
                    try:
                        result = bool(self._evaluate(expr))
                    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
                        result = False
                    current_stack[0] = result
                    if result:
                        current_stack[1] = True
                i += 1
                continue

            # Handle @ELSE
            elif stripped.startswith("# @ELSE"):
                if not stack:
                    final_lines.append(line)
                    i += 1
                    continue

                current_stack = stack[-1]
                if current_stack[1]:
                    current_stack[0] = False
                else:
                    current_stack[0] = True
                    current_stack[1] = True
                i += 1
                continue

            # Handle @ENDIF
            elif stripped.startswith("# @ENDIF"):
                if stack:
                    stack.pop()
                else:
                    final_lines.append(line)
                i += 1
                continue

            # Handle @LOOP
            elif stripped.startswith("# @LOOP "):
                if stack and not all(s[0] for s in stack):
                    # Skip the entire loop block if inside a false conditional
                    loop_depth = 1
                    i += 1
                    while i < len(lines) and loop_depth > 0:
                        if lines[i].strip().startswith("# @LOOP "):
                            loop_depth += 1
                        elif lines[i].strip().startswith("# @ENDLOOP"):
                            loop_depth -= 1
                        i += 1
                    continue

                parts = stripped[7:].strip().split(" in ", 1)
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                    var_name = parts[0].strip()
                    iterable_name = parts[1].strip()
                    try:
                        iterable = self._evaluate(iterable_name)
                        if not hasattr(iterable, "__iter__"):
                            raise TypeError(f"{iterable_name!r} is not iterable")
                    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
                        iterable = []

                    # Capture loop body
                    loop_body = []
                    i += 1
                    loop_depth = 1
                    while i < len(lines) and loop_depth > 0:
                        if lines[i].strip().startswith("# @LOOP "):
                            loop_depth += 1
                        elif lines[i].strip().startswith("# @ENDLOOP"):
                            loop_depth -= 1

                        if loop_depth > 0:
                            loop_body.append(lines[i])
                            i += 1

                    if i < len(lines):  # Skip the @ENDLOOP line itself
                        i += 1

                    # Execute loop
                    if hasattr(iterable, "__iter__"):
                        old_val = self.context.get(var_name)
                        for val in iterable:
                            self.context[var_name] = val
                            rendered_body = self.render("\n".join(loop_body), self.context)
                            final_lines.extend(rendered_body.splitlines())
                        if old_val is not None:
                            self.context[var_name] = old_val
                        else:
                            self.context.pop(var_name, None)
                    continue
                else:
                    final_lines.append(line)
                    i += 1
                    continue

            # Handle @ENDLOOP (should only be hit if out of sync or error)
            elif stripped.startswith("# @ENDLOOP"):
                i += 1
                continue

            # Check if we should skip this line based on conditional stack
            if stack and not all(s[0] for s in stack):
                i += 1
                continue

            # Variable substitution
            rendered_line = line
            matches = re.findall(r"\[\[\s*(.*?)\s*\]\]", rendered_line)
            for match in matches:
                value = self._get_value(match)
                # Replace all variations of the variable syntax
                rendered_line = re.sub(r"\[\[\s*" + re.escape(match) + r"\s*\]\]", value, rendered_line)

            # In-line @IF support
            # Case 1: content # @IF cond
            # Case 2: # @IF cond content
            if "# @IF " in rendered_line:
                parts = rendered_line.split("# @IF ", 1)
                pre_content = parts[0].rstrip()
                rest = parts[1].strip()

                # Split rest into expression and post-content (if any)
                # This is tricky because the expression might have spaces.
                # If there's an # @ENDIF on the same line, use it.
                post_content = ""
                expr = rest
                if " # @ENDIF" in rest:
                    expr_parts = rest.split(" # @ENDIF", 1)
                    expr = expr_parts[0].strip()
                    post_content = expr_parts[1].lstrip()
                elif "# @ENDIF" in rest:
                    expr_parts = rest.split("# @ENDIF", 1)
                    expr = expr_parts[0].strip()
                    post_content = expr_parts[1].lstrip()

                try:
                    if bool(self._evaluate(expr)):
                        # If Case 1, we want pre_content. If Case 2, we want post_content.
                        # Usually, if pre_content is empty (or just whitespace), it's Case 2.
                        if pre_content:
                            final_lines.append(pre_content + post_content)
                        else:
                            final_lines.append(post_content)
                except (AttributeError, IndexError, KeyError, TypeError, ValueError):
                    pass
                i += 1
                continue

            final_lines.append(rendered_line)
            i += 1

        return "\n".join(final_lines)
