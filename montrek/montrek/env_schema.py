"""The environment schema and the start-up checks against it.

`env.schema.toml` next to this module lists every runtime variable of a montrek
install. An extension app lists its own in an `env.schema.toml` next to its
`apps.py`.

Two checks use it, with different reach:

- `raise_for_invalid_settings` runs while `settings.py` is imported, so it stops
  every process -- gunicorn, celery, `manage.py` -- before it serves or runs
  anything. It covers the core schema's `scope = "app"` variables, the ones
  `settings.py` reads; the extension apps are not discovered yet at that point.
  It reports every missing required value and every value of the wrong type in
  one message, instead of failing on the first `config()` call that hits one.
- `check_environment` is a Django system check, run by `manage.py check`,
  `migrate`, `runserver` and `test`. It reports the extension apps' `scope = "app"`
  variables as errors, and as warnings the `scope = "compose"` variables of the
  wrong type, from core and extensions alike, the keys in `.env` or a secrets directory that no schema lists, since a
  misspelt key leaves its setting silently at the default, and the
  `scope = "build"` credentials found there, since `.env` is handed to every
  application container.

Compose-scope problems are only warnings because compose and the shell scripts
read those values themselves; whether they work is not decided here.
"""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from decouple import strtobool
from django.core.checks import CheckMessage, Error, Warning, register
from django.core.exceptions import ImproperlyConfigured

SCHEMA_FILENAME = "env.schema.toml"
CORE_SCHEMA_FILE = Path(__file__).with_name(SCHEMA_FILENAME)

TYPES = ("str", "int", "bool", "csv", "choice")
SCOPES = ("app", "compose", "build")
_FIELDS = {"type", "description", "required", "secret", "choices", "default", "scope"}

# A secrets directory can also hold files that are not a variable, such as the
# Cloud SQL key file. Only names that could be a variable are matched up.
_VARIABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_MISSING = object()


@dataclass(frozen=True)
class Variable:
    name: str
    type: str
    description: str
    required: bool = False
    secret: bool = False
    scope: str = "app"
    choices: tuple[str, ...] = ()

    def type_problem(self, value: str) -> str | None:
        """Why `value` is not a valid value of this variable, or None."""
        if self.type == "int":
            try:
                int(value)
            except ValueError:
                return f"{self.name} must be an integer, got {self._shown(value)}."
        elif self.type == "bool":
            try:
                strtobool(value)
            except ValueError:
                return (
                    f"{self.name} must be a boolean (1/0, true/false, yes/no, "
                    f"on/off), got {self._shown(value)}."
                )
        elif self.type == "choice" and value not in self.choices:
            return (
                f"{self.name} must be one of {', '.join(self.choices)}, "
                f"got {self._shown(value)}."
            )
        return None

    def _shown(self, value: str) -> str:
        return (
            "a value not shown because it is a secret" if self.secret else repr(value)
        )


def load_schema(path: Path) -> dict[str, Variable]:
    """The variables `path` declares, by name."""
    with path.open("rb") as file:
        entries = tomllib.load(file)
    return {name: _variable(path, name, fields) for name, fields in entries.items()}


def _variable(path: Path, name: str, fields: dict) -> Variable:
    def invalid(reason: str) -> ImproperlyConfigured:
        return ImproperlyConfigured(f"{path}: {name} {reason}")

    if unknown := set(fields) - _FIELDS:
        raise invalid(f"has unknown fields {', '.join(sorted(unknown))}.")
    if fields.get("type") not in TYPES:
        raise invalid(f"needs a type, one of {', '.join(TYPES)}.")
    if fields.get("scope", "app") not in SCOPES:
        raise invalid(f"has a scope other than {' or '.join(SCOPES)}.")
    if (fields["type"] == "choice") != bool(fields.get("choices")):
        raise invalid("must list choices exactly when its type is choice.")
    if not fields.get("description"):
        raise invalid("needs a description.")
    return Variable(
        name=name,
        type=fields["type"],
        description=fields["description"],
        required=fields.get("required", False),
        secret=fields.get("secret", False),
        scope=fields.get("scope", "app"),
        choices=tuple(fields.get("choices", ())),
    )


def with_scope(schema: dict[str, Variable], scope: str) -> dict[str, Variable]:
    return {
        name: variable for name, variable in schema.items() if variable.scope == scope
    }


def find_problems(schema: dict[str, Variable], config) -> list[str]:
    """Missing required values and values of the wrong type, one message each.

    An empty value counts as missing for a required variable, as an empty secret
    file already does in `configuration.py`: `SECRET_KEY=` is a blank left in a
    template, not a key.
    """
    problems = []
    for variable in schema.values():
        value = config(variable.name, default=_MISSING)
        if variable.required and value in (_MISSING, ""):
            problems.append(
                f"{variable.name} is required and must not be empty: "
                f"{variable.description}"
            )
        elif value is not _MISSING and (problem := variable.type_problem(value)):
            problems.append(problem)
    return problems


def find_configured_keys(config) -> list[tuple[str, str]]:
    """`(name, source)` for each key set in `.env` or a secrets directory.

    The environment itself is not searched: it holds PATH, HOME and whatever
    else the host or CI sets, so nothing in it can be told apart as a typo.
    """
    keys = [(name, ".env") for name in config.repository.data]
    for directory in config.secrets_dirs:
        if not directory.is_dir():
            continue
        keys += [
            (path.name.upper(), str(directory))
            for path in sorted(directory.iterdir())
            if path.is_file() and _VARIABLE_NAME.match(path.name)
        ]
    return keys


def raise_for_invalid_settings(config) -> None:
    """Stop the start-up if a variable `settings.py` reads is missing or invalid."""
    schema = with_scope(load_schema(CORE_SCHEMA_FILE), "app")
    if problems := find_problems(schema, config):
        raise ImproperlyConfigured(
            "Invalid configuration (see montrek/montrek/env.schema.toml):\n"
            + "\n".join(f"- {problem}" for problem in problems)
        )


def extension_schemas() -> dict[str, Variable]:
    """The variables the installed apps declare in their own schema files."""
    from django.apps import apps

    core = load_schema(CORE_SCHEMA_FILE)
    variables: dict[str, Variable] = {}
    for app_config in apps.get_app_configs():
        path = Path(app_config.path) / SCHEMA_FILENAME
        if not path.is_file():
            continue
        for name, variable in load_schema(path).items():
            if name in core or name in variables:
                raise ImproperlyConfigured(
                    f"{path}: {name} is already declared by another env.schema.toml."
                )
            variables[name] = variable
    return variables


@register("montrek_env")
def check_environment(app_configs=None, **kwargs) -> list[CheckMessage]:
    from montrek.configuration import config

    core = load_schema(CORE_SCHEMA_FILE)
    extensions = extension_schemas()
    known = core | extensions
    # The core app scope is already enforced while settings.py is imported, and
    # build-scope values are never read at runtime, so neither is checked here.
    messages: list[CheckMessage] = [
        Error(problem, id="montrek.E008")
        for problem in find_problems(with_scope(extensions, "app"), config)
    ]
    messages += [
        Warning(problem, id="montrek.W001")
        for problem in find_problems(with_scope(known, "compose"), config)
    ]
    for name, source in find_configured_keys(config):
        if name not in known:
            messages.append(
                Warning(
                    f"{name} is set in {source}, but no env.schema.toml lists it.",
                    hint="Check its spelling, or remove it if this version no "
                    "longer reads it.",
                    id="montrek.W002",
                )
            )
        elif known[name].scope == "build":
            messages.append(
                Warning(
                    f"{name} is a build-time credential, but it is set in {source}, "
                    "which every application container can read.",
                    hint="Move it to .env.build.",
                    id="montrek.W003",
                )
            )
    return messages
