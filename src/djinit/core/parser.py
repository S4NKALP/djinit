import re
from typing import Any, Dict, List


class InFileLogicParser:
    """
    A lightweight template parser that uses comment-style markers for logic
    and [[ variable ]] for substitutions.
    """

    def __init__(self, context: Dict[str, Any] = None):
        self.context = context or {}

    def _get_value(self, key: str) -> str:
        """
        Supports nested/dotted access like [[ user.name ]] or [[ settings["DEBUG"] ]].
        """
        key = key.strip()
        try:
            return str(eval(key, {"__builtins__": {}}, self.context))
        except (NameError, SyntaxError, KeyError, TypeError, AttributeError):
            return f"[[ {key} ]]"

    def _eval_expr(self, expr: str) -> bool:
        """Safely evaluate a boolean expression in the context. Defaults missing variables to False."""
        safe_context = dict(self.context)
        for key in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", expr):
            if key not in safe_context:
                safe_context[key] = False
        try:
            return bool(eval(expr, {"__builtins__": {}}, safe_context))
        except Exception:
            return False

    def render(self, template_text: str, context: Dict[str, Any] = None) -> str:
        if context is not None:
            self.context = context

        final_lines = []
        stack: List[List[bool]] = []

        lines = template_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("# @IF "):
                expr = stripped[6:].strip()
                result = self._eval_expr(expr)
                stack.append([result, result])
                i += 1
                continue

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
                    result = self._eval_expr(expr)
                    current_stack[0] = result
                    if result:
                        current_stack[1] = True
                i += 1
                continue

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

            elif stripped.startswith("# @ENDIF"):
                if stack:
                    stack.pop()
                else:
                    final_lines.append(line)
                i += 1
                continue

            elif stripped.startswith("# @LOOP "):
                if stack and not all(s[0] for s in stack):
                    loop_depth = 1
                    i += 1
                    while i < len(lines) and loop_depth > 0:
                        if lines[i].strip().startswith("# @LOOP "):
                            loop_depth += 1
                        elif lines[i].strip().startswith("# @ENDLOOP"):
                            loop_depth -= 1
                        i += 1
                    continue

                parts = stripped[7:].strip().split(" in ")
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    iterable_name = parts[1].strip()
                    try:
                        iterable = eval(iterable_name, {"__builtins__": {}}, self.context)
                    except Exception:
                        iterable = []

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

                    if i < len(lines):
                        i += 1

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

            elif stripped.startswith("# @ENDLOOP"):
                i += 1
                continue

            if stack and not all(s[0] for s in stack):
                i += 1
                continue

            rendered_line = line
            matches = re.findall(r"\[\[\s*(.*?)\s*\]\]", rendered_line)
            for match in matches:
                value = self._get_value(match)
                rendered_line = re.sub(r"\[\[\s*" + re.escape(match) + r"\s*\]\]", value, rendered_line)

            if "# @IF " in rendered_line:
                parts = rendered_line.split("# @IF ", 1)
                pre_content = parts[0].rstrip()
                rest = parts[1].strip()

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

                if self._eval_expr(expr):
                    if pre_content:
                        final_lines.append(pre_content + post_content)
                    else:
                        final_lines.append(post_content)
                i += 1
                continue

            final_lines.append(rendered_line)
            i += 1

        return "\n".join(final_lines)
