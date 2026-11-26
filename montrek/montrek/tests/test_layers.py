import ast
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

# The core apps in layers: a module may import modules of its own layer and of
# the layers below, never of a layer above. An install can then take over the
# core layer by layer, each layer running and passing its tests on its own.
# Keys are module paths; the longest key that prefixes a module decides its
# layer. Apps that are not listed here are extensions and sit above the core.
CORE_LAYERS: dict[str, int] = {
    "montrek": 0,
    "storage": 0,
    "tasks": 0,
    "baseclasses": 1,
    "user": 1,
    "middleware": 1,
    "rest_api": 1,
    "testing": 1,
    "reporting": 2,
    "mailing": 2,
    "info": 2,
    "process_pipeline": 3,
    "file_upload": 3,
    # The project modules that combine everything installed.
    "montrek.settings": 4,
    "montrek.urls": 4,
    "montrek.media": 4,
    "montrek.wsgi": 4,
    "montrek.asgi": 4,
    "montrek.tests.test_local_host": 4,
    "montrek.tests.test_media": 4,
}
EXTENSION_LAYER = 5


class TestCoreLayers(SimpleTestCase):
    def test_no_core_module_imports_a_higher_layer(self):
        violations = [
            f"{path}:{line} ({source_layer}) imports {target} ({target_layer})"
            for path, source_layer, line, target, target_layer in self._imports()
            if target_layer > source_layer
        ]
        self.assertEqual(violations, [], "\n".join(violations))

    def test_layer_of_modules(self):
        self.assertEqual(self._layer("baseclasses.views"), 1)
        self.assertEqual(self._layer("montrek.utils"), 0)
        self.assertEqual(self._layer("montrek.settings"), 4)
        self.assertEqual(self._layer("rest_framework.views"), -1)
        with mock.patch.object(Path, "is_dir", return_value=True):
            self.assertEqual(self._layer("some_extension.views"), EXTENSION_LAYER)

    def _imports(self):
        base_dir = Path(settings.BASE_DIR)
        top_level = {key.split(".")[0] for key in CORE_LAYERS}
        for package in sorted(top_level):
            for path in sorted((base_dir / package).rglob("*.py")):
                if "migrations" in path.parts:
                    continue
                module = ".".join(path.relative_to(base_dir).with_suffix("").parts)
                source_layer = self._layer(module)
                tree = ast.parse(path.read_text(), filename=str(path))
                for node in ast.walk(tree):
                    for target in self._imported_modules(node):
                        yield (
                            path.relative_to(base_dir),
                            source_layer,
                            node.lineno,
                            target,
                            self._layer(target),
                        )

    @staticmethod
    def _imported_modules(node: ast.AST) -> list[str]:
        # Imports under ``if TYPE_CHECKING:`` count as well: an install without
        # the higher layer could not type check them.
        if isinstance(node, ast.Import):
            return [alias.name for alias in node.names]
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            return [node.module]
        return []

    @staticmethod
    def _layer(module: str) -> int:
        matches = [
            key for key in CORE_LAYERS if module == key or module.startswith(f"{key}.")
        ]
        if matches:
            return CORE_LAYERS[max(matches, key=len)]
        # Third-party packages sit below the core.
        is_local = (Path(settings.BASE_DIR) / module.split(".")[0]).is_dir()
        return EXTENSION_LAYER if is_local else -1
