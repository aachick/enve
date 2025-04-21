# MIT License

# Copyright (c) 2025 Aurélien Chick

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Environment variable parser tests."""

import re

from pathlib import Path
from typing import Any

import pytest

from pyfakefs.fake_filesystem import FakeFilesystem

import enve


ENVVARS = {
    "ENVVAR": ("foo", None),
    "ENVVAR_BYTES": (b"foo", bytes),
    "ENVVAR_INT": (42, int),
    "ENVVAR_FLOAT": (3.14, float),
    "ENVVAR_STR": ("bar", str),
}
OS_ENVIRON_DICT = {key: str(value) for key, (value, _) in ENVVARS.items()}
OS_ENVIRON_MODULE = "enve.parser.os.environ"


@pytest.mark.parametrize("envvar", list(ENVVARS.keys()))
def test_get_envvar(monkeypatch: pytest.MonkeyPatch, envvar: str) -> None:
    """Test parsing environment variables."""
    expected_value, dtype = ENVVARS[envvar]
    expected_type = str if dtype is None else dtype

    str_val = expected_value.decode() if isinstance(expected_value, bytes) else str(expected_value)
    monkeypatch.setenv(envvar, str_val)

    result = enve.get(envvar, dtype=dtype)
    assert isinstance(result, expected_type)
    assert result == expected_value


@pytest.mark.parametrize("value", ["1", "on", "T", "True", "t", "true", "y", "yes"])
def test_get_envvar_bool_truthy(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """Test parsing truthy boolean values."""
    monkeypatch.setenv("ENVVAR_BOOL", value)

    result = enve.get("ENVVAR_BOOL", dtype=bool)
    assert isinstance(result, bool)
    assert result is True


@pytest.mark.parametrize("value", ["", "0", "off", "F", "False", "f", "false", "n", "no"])
def test_get_envvar_bool_falsy(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """Test parsing falsy boolean values."""
    monkeypatch.setenv("ENVVAR_BOOL", value)

    result = enve.get("ENVVAR_BOOL", dtype=bool)
    assert isinstance(result, bool)
    assert result is False


@pytest.mark.parametrize("default", [True, False])
def test_get_envvar_bool_missing_with_default(
    monkeypatch: pytest.MonkeyPatch, *, default: bool
) -> None:
    """Test parsing missing boolean values with default."""
    monkeypatch.delenv("ENVVAR_BOOL", raising=False)

    result = enve.get("ENVVAR_BOOL", default=default, dtype=bool)
    assert isinstance(result, bool)
    assert result is default


@pytest.mark.parametrize(
    ("dtype", "factory", "expected_value"),
    [(str, lambda: "foo", "foo"), (list, lambda: ["foo"], ["foo"])],
)
def test_get_envvar_with_default_factory(
    monkeypatch: pytest.MonkeyPatch, dtype: Any, factory: Any, expected_value: Any
) -> None:
    """Test parsing environment variables with a default factory."""
    monkeypatch.delenv("ENVVAR", raising=False)

    result = enve.get("ENVVAR", dtype=dtype, default_factory=factory)
    assert result == expected_value


@pytest.mark.parametrize(
    ("str_value", "item_dtype", "expected_value"),
    [
        ("1,2,3", None, ["1", "2", "3"]),
        ("1,2,3", str, ["1", "2", "3"]),
        ("1,2,3", int, [1, 2, 3]),
        ("1.0,2.0,3.0", float, [1.0, 2.0, 3.0]),
        ("true,false", bool, [True, False]),
        ("foo", bytes, [b"foo"]),
    ],
)
def test_get_envvar_list(
    monkeypatch: pytest.MonkeyPatch, str_value: str, item_dtype: Any, expected_value: Any
) -> None:
    """Test parsing list environment variables."""
    monkeypatch.setenv("ENVVAR_LIST", str_value)

    result = enve.get("ENVVAR_LIST", dtype=list, item_dtype=item_dtype)
    assert isinstance(result, list)
    assert result == expected_value


def test_get_envvar_list_with_custom_item_sep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test parsing list environment variables with a custom item separator."""
    monkeypatch.setenv("ENVVAR_LIST", "1;2;3")

    result = enve.get("ENVVAR_LIST", dtype=list, item_dtype=int, item_sep=";")
    assert isinstance(result, list)
    assert result == [1, 2, 3]


def test_get_envvar_list_with_invalid_item_dtype(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an invalid item dtype raises a TypeError."""
    invalid_item_dtype = frozenset
    expected_msg = (
        f"Invalid item type '{invalid_item_dtype}' for 'ENVVAR_LIST'."
        f" Expected one of ({bool}, {bytes}, {float}, {int}, {str})."
    )

    monkeypatch.setenv("ENVVAR_LIST", "1,2,3")
    with pytest.raises(TypeError, match=re.escape(expected_msg)):
        enve.get("ENVVAR_LIST", dtype=list, item_dtype=invalid_item_dtype)


@pytest.mark.parametrize("secret", ["ENVVAR", "envvar"])
def test_get_envvar_from_docker_secrets(
    monkeypatch: pytest.MonkeyPatch, fs: FakeFilesystem, secret: str
) -> None:
    """Test that getting an envvar from Docker secrets works."""
    monkeypatch.delenv("ENVVAR", raising=False)
    fs.create_file(f"/run/secrets/{secret}", contents="foo")

    result = enve.get("ENVVAR", docker_secret=True)
    assert isinstance(result, str)
    assert result == "foo"


def test_get_envvar_from_non_existing_docker_secrets_with_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that getting an envvar from Docker secrets works."""
    monkeypatch.delenv("ENVVAR", raising=False)
    monkeypatch.setattr(Path, "exists", lambda _: False)

    result = enve.get("ENVVAR", default="foo", docker_secret=True)
    assert isinstance(result, str)
    assert result == "foo"


def test_get_envvar_from_named_docker_secrets(
    monkeypatch: pytest.MonkeyPatch, fs: FakeFilesystem
) -> None:
    """Test that getting an envvar from Docker secrets works."""
    monkeypatch.delenv("ENVVAR", raising=False)
    fs.create_file(f"/run/secrets/foobar", contents="foo")

    result = enve.get("ENVVAR", docker_secret="foobar")
    assert isinstance(result, str)
    assert result == "foo"


def test_get_envvar_from_non_existing_named_docker_secrets_with_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that getting an envvar from Docker secrets works."""
    monkeypatch.delenv("ENVVAR", raising=False)
    monkeypatch.setattr(Path, "exists", lambda _: False)

    result = enve.get("ENVVAR", default="foo", docker_secret="barino")
    assert isinstance(result, str)
    assert result == "foo"


def test_get_envvar_with_invalid_dtype(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an invalid dtype raises a TypeError."""
    invalid_dtype = frozenset
    expected_msg = (
        f"Invalid type '{invalid_dtype}' for 'ENVVAR'."
        f" Expected one of ({bool}, {bytes}, {float}, {int}, {str}, {list})."
    )

    monkeypatch.setenv("ENVVAR", "foo")
    with pytest.raises(TypeError, match=re.escape(expected_msg)):
        enve.get("ENVVAR", dtype=invalid_dtype)


@pytest.mark.parametrize("dtype", [None, str, int, float, bool])
def test_get_non_existing_envvar_with_none_default(
    monkeypatch: pytest.MonkeyPatch,
    dtype: type[str | int | float | bool] | None,
) -> None:
    """Test that a None default returns None."""
    monkeypatch.setenv("ENVVAR", "foo")

    result = enve.get("ENVVAR_non_existing", default=None, dtype=dtype)
    assert result is None


def test_get_non_existing_envvar_with_no_default_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a non-existing envvar with no default raises a ValueError."""
    expected_msg = (
        "Environment variable 'ENVVAR' is not set and no default or default_factory is provided."
    )

    monkeypatch.delenv("ENVVAR", raising=False)
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        enve.get("ENVVAR")


def test_get_envvar_with_invalid_default_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that getting an envvar with an invalid default type raises a TypeError."""
    invalid_default = 42
    expected_msg = "Default value '42' (type=int) for 'ENVVAR' is not of type 'str'."

    monkeypatch.setenv("ENVVAR", "foo")
    with pytest.raises(TypeError, match=re.escape(expected_msg)):
        enve.get("ENVVAR", default=invalid_default, dtype=str)


def test_get_envvar_with_default_and_default_factory_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that getting an envvar with both default and default_factory raises a ValueError."""
    expected_msg = (
        "Cannot use both 'default' and 'default_factory' for 'ENVVAR'. Use one or the other."
    )

    monkeypatch.setenv("ENVVAR", "foo")
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        enve.get("ENVVAR", default="bar", default_factory=lambda: "baz")


def test_get_envvar_with_list_default_raises_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that getting an envvar with a list default raises a warning."""
    expected_msg = (
        "Using a default value for 'ENVVAR' of type 'list' is not recommended as it may be mutated."
    )

    monkeypatch.delenv("ENVVAR", raising=False)
    with pytest.warns(UserWarning, match=re.escape(expected_msg)):
        value = enve.get("ENVVAR", default=["bar"], dtype=list)

    assert value == ["bar"]


def test_get_envvar_with_invalid_default_factory_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that getting an envvar with an invalid default factory raises a TypeError."""
    invalid_default_factory = 42
    expected_msg = "Default factory '42' for 'ENVVAR' is not callable."

    monkeypatch.setenv("ENVVAR", "1,2,3")
    with pytest.raises(TypeError, match=re.escape(expected_msg)):
        enve.get("ENVVAR", default_factory=invalid_default_factory, dtype=list)


def test_get_deprecated_envvar_with_custom_msg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a deprecated envvar raises a DeprecationWarning."""
    msg = "This envvar is deprecated!"

    monkeypatch.setenv("ENVVAR", "foo")
    with pytest.deprecated_call(match=re.escape(msg)):
        value = enve.get("ENVVAR", deprecated=True, deprecated_msg=msg)

    assert value == ENVVARS["ENVVAR"][0]


def test_get_deprecated_envvar_with_default_msg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a deprecated envvar raises a DeprecationWarning."""
    expected_msg = "The 'ENVVAR' environment variable is deprecated."

    monkeypatch.setenv("ENVVAR", "foo")
    with pytest.deprecated_call(match=re.escape(expected_msg)):
        value = enve.get("ENVVAR", deprecated=True)

    assert value == ENVVARS["ENVVAR"][0]


def test_get_invalid_int_envvar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an invalid int envvar raises a ValueError."""
    expected_msg = "Environment variable 'ENVVAR_INT' is not a valid integer: 'foo'"

    monkeypatch.setenv("ENVVAR_INT", "foo")
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        enve.get("ENVVAR_INT", dtype=int)


def test_get_invalid_float_envvar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an invalid float envvar raises a ValueError."""
    expected_msg = "Environment variable 'ENVVAR_FLOAT' is not a valid float: 'foo'"

    monkeypatch.setenv("ENVVAR_FLOAT", "foo")
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        enve.get("ENVVAR_FLOAT", dtype=float)


def test_get_invalid_bool_envvar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an invalid bool envvar raises a ValueError."""
    expected_msg = (
        "Environment variable 'ENVVAR_BOOL' is not a valid boolean value. "
        "Expected one of ('1', 'on', 't', 'true', 'y', 'yes',"
        " '', '0', 'off', 'f', 'false', 'n', 'no')."
    )

    monkeypatch.setenv("ENVVAR_BOOL", "foo")
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        enve.get("ENVVAR_BOOL", dtype=bool)
