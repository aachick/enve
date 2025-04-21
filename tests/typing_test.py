"""Test that typing works as expected."""

import re
import shlex
import subprocess as sp
import sys

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def get_mypy_revelations(code: str) -> list[str]:
    """Run mypy and return the revealed type."""
    with TemporaryDirectory() as tmpdir:
        code_file = Path(tmpdir) / "test.py"
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        cache_dir = Path(tmpdir) / ".mypy_cache"

        cmd = [
            sys.executable,
            "-m",
            "mypy",
            "--cache-dir",
            str(cache_dir),
            "--no-color-output",
            "--no-error-summary",
            "--no-incremental",
            str(code_file),
        ]
        cmd_str = shlex.join(cmd)

        pipe = sp.run(
            cmd_str if sys.platform == "win32" else cmd,
            capture_output=True,
            check=False,
            text=True,
        )

    pattern = re.compile(r"Revealed type is \"(.+)\"$")
    output = pipe.stdout
    lines = output.splitlines()

    matches = (pattern.search(line) for line in lines)
    revelations = [match.group(1).strip() for match in matches if match]

    return revelations


TYPING_TO_REVEAL = {
    # str
    "get('a')": "builtins.str",
    "get('a', default=None)": "Union[builtins.str, None]",
    "get('a', dtype=str)": "builtins.str",
    "get('a', default=None, dtype=str)": "Union[builtins.str, None]",
    # int
    "get('a', dtype=int)": "builtins.int",
    "get('a', default=None, dtype=int)": "Union[builtins.int, None]",
    # float
    "get('a', dtype=float)": "builtins.float",
    "get('a', default=None, dtype=float)": "Union[builtins.float, None]",
    # bool
    "get('a', dtype=bool)": "builtins.bool",
    "get('a', default=None, dtype=bool)": "Union[builtins.bool, None]",
    # bytes
    "get('a', dtype=bytes)": "builtins.bytes",
    "get('a', default=None, dtype=bytes)": "Union[builtins.bytes, None]",
    # list + None
    "get('a', dtype=list)": "builtins.list[builtins.str]",
    "get('a', default=None, dtype=list)": "Union[builtins.list[builtins.str], None]",
    # list + str
    "get('a', dtype=list, item_dtype=str)": "builtins.list[builtins.str]",
    "get('a', default=None, dtype=list, item_dtype=str)": "Union[builtins.list[builtins.str], None]",  # noqa: E501
    # list + int
    "get('a', dtype=list, item_dtype=int)": "builtins.list[builtins.int]",
    "get('a', default=None, dtype=list, item_dtype=int)": "Union[builtins.list[builtins.int], None]",  # noqa: E501
    # list + float
    "get('a', dtype=list, item_dtype=float)": "builtins.list[builtins.float]",
    "get('a', default=None, dtype=list, item_dtype=float)": "Union[builtins.list[builtins.float], None]",  # noqa: E501
    # list + bool
    "get('a', dtype=list, item_dtype=bool)": "builtins.list[builtins.bool]",
    "get('a', default=None, dtype=list, item_dtype=bool)": "Union[builtins.list[builtins.bool], None]",  # noqa: E501
    # list + bytes
    "get('a', dtype=list, item_dtype=bytes)": "builtins.list[builtins.bytes]",
    "get('a', default=None, dtype=list, item_dtype=bytes)": "Union[builtins.list[builtins.bytes], None]",  # noqa: E501
}


@pytest.fixture(scope="module")
def mypy_revelations() -> dict[str, str]:
    """Fixture to run mypy and return the revealed type alongside the code."""
    setup = "from enve import get"
    statements = [f"reveal_type({s})" for s in TYPING_TO_REVEAL]
    code = "\n".join([setup, *statements])

    revelations = get_mypy_revelations(code)
    if len(revelations) != len(TYPING_TO_REVEAL):
        err_msg = f"Expected {len(TYPING_TO_REVEAL)} revelations, but got {len(revelations)}"
        raise RuntimeError(err_msg)

    results = dict(zip(TYPING_TO_REVEAL, revelations, strict=True))
    return results


@pytest.mark.parametrize("code", list(TYPING_TO_REVEAL.keys()))
def test_mypy_revelations(code: str, mypy_revelations: dict[str, str]) -> None:
    """Test that the revealed type of get() is as expected."""
    expected_type = TYPING_TO_REVEAL[code]
    revealed_type = mypy_revelations[code]

    err_msg = f"Expected '{expected_type}', got '{revealed_type}': {code}"
    assert revealed_type == expected_type, err_msg
