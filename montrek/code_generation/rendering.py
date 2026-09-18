"""Shared template rendering and formatting for the code generators.

Both the table/registry generators (``CodeGenerationCommandBase``) and
``start_montrek_app`` render Jinja templates from ``CODE_TEMPLATE_DIR`` and hand
the result to ruff, so the setup lives here rather than on one command class.
"""

import shutil

# Only used to run the pinned ruff binary, see format_python_file below.
# Bandit reads everything after 'nosec' as test ids, so the reason goes here
# rather than onto the same line.
import subprocess  # noqa: S404  # nosec B404

from jinja2 import Environment, FileSystemLoader, select_autoescape

from code_generation import CODE_TEMPLATE_DIR

# The code templates render Python source (``*.py.j2``), so HTML escaping would
# corrupt what they produce, turning quotes in the generated code into entities.
# Escaping is therefore off for those, but kept on for any markup template that
# may join them later, so a new ``*.html.j2`` is safe by default rather than by
# whoever adds it remembering to be.
MARKUP_TEMPLATE_EXTENSIONS = ("html", "htm", "xml", "html.j2", "htm.j2", "xml.j2")


def build_template_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(CODE_TEMPLATE_DIR),
        autoescape=select_autoescape(
            enabled_extensions=MARKUP_TEMPLATE_EXTENSIONS,
            default_for_string=False,
            default=False,
        ),
        # Without this Jinja drops the final newline, so appending one template
        # after another runs the two together on one line.
        keep_trailing_newline=True,
    )


def render_template(template_name: str, **context) -> str:
    template = build_template_environment().get_template(template_name)
    return template.render(**context)


def format_python_file(path: str) -> str:
    """Format a generated file with ruff.

    Templates cannot know how long a prefix or a dotted path will be, so lines
    such as a class header overflow for some inputs and not others. Formatting
    the result sidesteps that for every template at once.

    Returns an empty string on success, otherwise a message explaining why the
    file was left unformatted.
    """
    ruff_path = shutil.which("ruff")
    if ruff_path is None:
        return "ruff not found; generated code is not formatted."
    # Fixed argv: the resolved ruff binary, a literal subcommand and the path
    # the caller just wrote. No shell, no caller-supplied arguments.
    result = subprocess.run(  # noqa: S603  # nosec B603
        [ruff_path, "format", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return f"Could not format '{path}': {result.stderr.strip()}"
    return ""
