from functools import wraps
from PIL import Image
from unittest import mock
from pathlib import Path

from plotly.graph_objs import Figure


def mock_plotly_image_write_disabled(exists=False):
    """
    Mock plotly image generation and filesystem side effects.
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            with (
                mock.patch.object(Path, "mkdir"),
                mock.patch.object(Path, "exists", return_value=exists),
                mock.patch.object(
                    Figure,
                    "write_image",
                ) as mock_write_image,
            ):
                return test_func(*args, mock_write_image=mock_write_image, **kwargs)

        return wrapper

    return decorator


def write_dummy_png(path: str, *args, **kwargs):
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    img.save(path, format="PNG")


def mock_plotly_write_dummy_png():
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            with mock.patch.object(
                Figure,
                "write_image",
                side_effect=write_dummy_png,
            ) as mock_write_image:
                return test_func(
                    *args,
                    mock_write_image=mock_write_image,
                    **kwargs,
                )

        return wrapper

    return decorator
