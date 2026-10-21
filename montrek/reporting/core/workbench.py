"""Scratch space for the files a LaTeX run includes.

Report elements write plot images and downloaded pictures while the report is
rendered to LaTeX, and xelatex then reads them back. `activate` gives each run
its own temporary directory and removes it afterwards, so nothing builds up and
nothing is written into the code tree, which an app image keeps read-only.
Outside a run, as when an element is rendered to LaTeX on its own, files go to
WORKBENCH_PATH.
"""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from django.conf import settings

_active: ContextVar[Path | None] = ContextVar("reporting_workbench", default=None)


@contextmanager
def activate() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="montrek-latex-") as directory:
        token = _active.set(Path(directory))
        try:
            yield Path(directory)
        finally:
            _active.reset(token)


def current() -> Path:
    path = _active.get() or Path(settings.WORKBENCH_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path
