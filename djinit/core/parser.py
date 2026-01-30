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
        For simplicity, it uses eval in the provided context for complex expressions,
        but falls back to safe dictionary lookup for simple keys.
        """
        key = key.strip()
        try:
            # Try evaluating the expression in the context
            return str(eval(key, {"__builtins__": {}}, self.context))
        except (NameError, SyntaxError, KeyError, TypeError, AttributeError):
            # Fallback for common patterns or just return the key as is if it fails
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
                    result = bool(eval(expr, {"__builtins__": {}}, self.context))
                except Exception:
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
                        result = bool(eval(expr, {"__builtins__": {}}, self.context))
                    except Exception:
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

                parts = stripped[7:].strip().split(" in ")
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    iterable_name = parts[1].strip()
                    try:
                        iterable = eval(iterable_name, {"__builtins__": {}}, self.context)
                    except Exception:
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
                rendered_line = rendered_line.replace(f"[[ {match} ]]", value)
                rendered_line = rendered_line.replace(f"[[{match}]]", value)

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
                    if bool(eval(expr, {"__builtins__": {}}, self.context)):
                        # If Case 1, we want pre_content. If Case 2, we want post_content.
                        # Usually, if pre_content is empty (or just whitespace), it's Case 2.
                        if pre_content:
                            final_lines.append(pre_content + post_content)
                        else:
                            final_lines.append(post_content)
                except Exception:
                    pass
                i += 1
                continue

            final_lines.append(rendered_line)
            i += 1

        return "\n".join(final_lines)
