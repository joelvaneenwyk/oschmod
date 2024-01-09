"""Contains the fixtures used by the oschmod tests."""

import shutil
from pathlib import Path
from typing import Generator

import pytest

from oschmod import set_mode_recursive


@pytest.fixture(name="test_dir")
def fixture_test_output_directory(tmp_path: Path) -> Generator[str, None, None]:
    """Destination directory for package tests."""
    output_path = tmp_path.joinpath("oschmod")
    output_path.mkdir(exist_ok=False)
    yield str(output_path)
    set_mode_recursive(output_path, 0o777)
    shutil.rmtree(str(output_path), ignore_errors=True)
