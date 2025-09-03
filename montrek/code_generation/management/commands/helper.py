import re
from typing import Tuple


def ensure_method_with_code(
    filename: str,
    class_name: str,
    method_name: str,
    code_to_insert: str,
    method_args: str = "self",
    import_statements: tuple[str, ...] = (),
):
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.splitlines(keepends=True)

    def leading_spaces(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def find_class_block(lines) -> Tuple[int, int, int]:
        """
        Returns (class_start_idx, class_end_idx_exclusive, class_indent)
        Raises ValueError if class not found.
        """
        class_header_re = re.compile(
            rf"^(\s*)class\s+{re.escape(class_name)}\s*(\([^)]*\))?\s*:\s*(#.*)?\n?$"
        )
        for i, line in enumerate(lines):
            m = class_header_re.match(line)
            if m:
                class_indent = leading_spaces(line)
                # Find end of class by indentation
                j = i + 1
                while j < len(lines):
                    lj = lines[j]
                    # Stop when we hit a line that's less-indented or equal to class indent
                    # and not blank/comment
                    if lj.strip() != "" and not lj.lstrip().startswith("#"):
                        if leading_spaces(lj) <= class_indent:
                            break
                    j += 1
                return i, j, class_indent
        raise ValueError(f"Class {class_name} not found.")

    def find_method_in_block(lines, start, end) -> Tuple[int, int, int] | None:
        """
        Search for method def in [start, end).
        Returns (def_line_idx, body_start_idx, def_indent) or None.
        """
        method_re = re.compile(
            rf"^(\s*)def\s+{re.escape(method_name)}\b.*:\s*(#.*)?\n?$"
        )
        for i in range(start + 1, end):
            m = method_re.match(lines[i])
            if m:
                def_indent = leading_spaces(lines[i])
                # Body starts at next line that is more indented
                j = i + 1
                while j < end:
                    if lines[j].strip() == "" or lines[j].lstrip().startswith("#"):
                        j += 1
                        continue
                    if leading_spaces(lines[j]) > def_indent:
                        return i, j, def_indent
                    else:
                        # empty body (we'll still treat j as body start right after def)
                        return i, i + 1, def_indent
                return i, i + 1, def_indent
        return None

    try:
        cls_start, cls_end, cls_indent = find_class_block(lines)
    except ValueError as e:
        raise

    method_info = find_method_in_block(lines, cls_start, cls_end)

    # Normalize code_to_insert with correct indentation
    body_indent = " " * (cls_indent + 4)
    method_indent = " " * (cls_indent + 4)
    def_indent_str = " " * (cls_indent + 4)

    # Indent each line of code_to_insert to body indent
    def indent_block(block: str, indent: str) -> str:
        block_lines = block.splitlines()
        if not block_lines:
            return ""
        return "".join(indent + ln + "\n" for ln in block_lines)

    if method_info is None:
        # Method doesn't exist: append it at the end of the class body
        insertion_index = cls_end
        # Ensure class has at least one blank line before insertion if needed
        to_insert = []
        if insertion_index > cls_start + 1 and (
            lines[insertion_index - 1].strip() != ""
        ):
            to_insert.append("\n")
        to_insert.append(f"{method_indent}def {method_name}({method_args}):\n")
        to_insert.append(indent_block(code_to_insert, body_indent))
        lines[insertion_index:insertion_index] = to_insert
    else:
        def_idx, body_start_idx, def_indent = method_info
        first_body_real_line_idx = None

        # Find first non-blank/non-comment line in method body
        for j in range(body_start_idx, cls_end):
            if lines[j].strip() == "" or lines[j].lstrip().startswith("#"):
                continue
            if leading_spaces(lines[j]) <= def_indent:
                break  # body ended (empty body)
            first_body_real_line_idx = j
            break

        # If first statement is 'pass', replace it with our code
        if first_body_real_line_idx is not None and lines[
            first_body_real_line_idx
        ].lstrip().startswith("pass"):
            # Replace this 'pass' line with code block
            lines[first_body_real_line_idx : first_body_real_line_idx + 1] = [
                indent_block(code_to_insert, " " * (def_indent + 4))
            ]
        else:
            # Insert code right after the def line (before existing body)
            insertion_at = def_idx + 1
            # Keep one newline if immediately there is another line of code
            to_insert = [indent_block(code_to_insert, " " * (def_indent + 4))]
            lines[insertion_at:insertion_at] = to_insert

    new_text = "".join(lines)

    def add_import_statements(in_text: str) -> str:
        import_statements_str = "\n".join(import_statements)
        return import_statements_str + in_text

    new_text = add_import_statements(new_text)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_text)
