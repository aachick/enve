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
"""Parse environment variables into Python objects."""

import os
import warnings

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeAlias, TypeVar, cast, overload


UNSET = object()
EnvType: TypeAlias = bool | bytes | float | int | str | list
ItemType = TypeVar("ItemType", bound=bool | bytes | float | int | str)


def _parse_bool(envvar: str, value: str) -> bool:
    truthy_values = ("1", "on", "t", "true", "y", "yes")
    falsy_values = ("", "0", "off", "f", "false", "n", "no")
    if value.lower() in truthy_values:
        return True
    if value.lower() in falsy_values:
        return False

    err_msg = (
        f"Environment variable '{envvar}' is not a valid boolean value. "
        f"Expected one of {truthy_values + falsy_values}."
    )
    raise ValueError(err_msg)


def _parse_float(envvar: str, value: str) -> float:
    try:
        float_value = float(value)
    except (TypeError, ValueError):
        err_msg = f"Environment variable '{envvar}' is not a valid float: '{value}'"
        raise ValueError(err_msg) from None
    return float_value


def _parse_int(envvar: str, value: str) -> int:
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        err_msg = f"Environment variable '{envvar}' is not a valid integer: '{value}'"
        raise ValueError(err_msg) from None
    return int_value


def _parse_list(envvar: str, values: list[str], item_dtype: type[ItemType]) -> list:
    accepted_item_dtypes = (bool, bytes, float, int, str)
    if item_dtype not in accepted_item_dtypes:
        err_msg = (
            f"Invalid item type '{item_dtype}' for '{envvar}'."
            f" Expected one of {accepted_item_dtypes}."
        )
        raise TypeError(err_msg)

    if item_dtype is bool:
        return [_parse_bool(f"{envvar}[{i}]", v) for i, v in enumerate(values)]
    elif item_dtype is bytes:
        return [v.encode("utf-8") for v in values]
    elif item_dtype is float:
        return [_parse_float(f"{envvar}[{i}]", v) for i, v in enumerate(values)]
    elif item_dtype is int:
        return [_parse_int(f"{envvar}[{i}]", v) for i, v in enumerate(values)]
    else:  # item_dtype is str
        return values


def _get_envvar_value(envvar: str, *, docker_secret: bool | str = False) -> str | object:
    """Load an environment variable from a .env file."""
    value = os.environ.get(envvar, UNSET)
    if value is not UNSET:
        return value

    # `value` is UNSET, so we check if the envvar is a docker secret.
    if docker_secret is True:
        secrets_paths = (Path(f"/run/secrets/{envvar}"), Path(f"/run/secrets/{envvar.lower()}"))
        for path in secrets_paths:
            if path.exists():
                value = path.read_text()
                break
    elif isinstance(docker_secret, str):
        path = Path(f"/run/secrets/{docker_secret}")
        if path.exists():
            value = path.read_text()

    return value


@overload
def get(
    envvar: str,
    *,
    default: str = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: None = None,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> str: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: None = None,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> str | None: ...


@overload
def get(
    envvar: str,
    *,
    default: bool = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[bool] = bool,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> bool: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[bool] = bool,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> bool | None: ...


@overload
def get(
    envvar: str,
    *,
    default: int = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[int] = int,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> int: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[int] = int,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> int | None: ...


@overload
def get(
    envvar: str,
    *,
    default: float = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[float] = float,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> float: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[float] = float,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> float | None: ...


@overload
def get(
    envvar: str,
    *,
    default: str = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[str] = str,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> str: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[str],
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> str | None: ...


@overload
def get(
    envvar: str,
    *,
    default: bytes = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[bytes] = bytes,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> bytes: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[bytes],
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] | None = ...,
    item_sep: str = ...,
) -> bytes | None: ...


@overload
def get(
    envvar: str,
    *,
    default: list = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[list] = list,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: None = ...,
    item_sep: str = ...,
) -> list[str]: ...


@overload
def get(
    envvar: str,
    *,
    default: list = ...,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[list] = list,
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] = ...,
    item_sep: str = ...,
) -> list[ItemType]: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[list],
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: None = ...,
    item_sep: str = ...,
) -> list[str] | None: ...


@overload
def get(
    envvar: str,
    *,
    default: None = None,
    default_factory: Callable[[], EnvType] | None = ...,
    dtype: type[list],
    deprecated: bool = ...,
    deprecated_msg: str = ...,
    docker_secret: bool | str = ...,
    item_dtype: type[ItemType] = ...,
    item_sep: str = ...,
) -> list[ItemType] | None: ...


def get(
    envvar: str,
    *,
    default: Any | None = UNSET,
    default_factory: Callable[[], EnvType] | None = None,
    dtype: type[EnvType] | None = None,
    deprecated: bool = False,
    deprecated_msg: str = "",
    docker_secret: bool | str = False,
    item_sep: str = ",",
    item_dtype: type[ItemType] | None = None,
) -> EnvType | None:
    """
    Parse an environment variable into a bool, bytes, float, int, str, or a list.

    Rather than using `os.environ.get` or `os.getenv`, this function
    provides a convenient way to parse environment variables into a
    specific data type with type checking and conversion support.

    Valid boolean environment variable values are (case insensitive):
    - "1", "on", "t", "true", "y", "yes" for True
    - "", "0", "off", "f", "false", "n", "no" for False

    The function also supports parsing lists of values, where the values
    are separated by a specified separator (default is ","). The list items
    can be converted to a specific data type using the `item_dtype` parameter.

    Parameters
    ----------
    envvar : str
        The name of the environment variable to parse.
    default : Any | None, default UNSET
        The default value to return if the environment variable is not set.
        If UNSET, a ValueError will be raised if the environment variable is not set.
    default_factory : Callable[[], EnvType] | None, default None
        A callable that returns the default value if the environment variable is not set.
        If None, this will be ignored. This cannot be used alongside `default`. This should
        be used instead of `default` when the expected return type is a list.
    dtype : type[bool | bytes | float | int | str] | None, default None
        The data type to convert the environment variable to. If None, the value
        will be returned as a string. Supported types are bool, bytes, float, int, str, and list.
    deprecated : bool, default False
        If True, and the environment variable is set, a DeprecationWarning will be raised.
    deprecated_msg : str, default ""
        A custom message to include in the DeprecationWarning if deprecated is True.
    docker_secret : bool | str, default False
        If True, the function will attempt to read the environment variable value from
        a Docker secret file. Attempted file names are `/run/secrets/{envvar}` and
        `/run/secrets/{envvar.lower()}`. If a string is provided, it will be used as
        the file name instead of the environment variable name. If False, the function
        will not check for Docker secrets.
    item_dtype : type[bool | bytes | float | int | str] | None, default None
        The data type to convert the items in the list to. If None, the items will
        be returned as strings. Supported types are bool, bytes, float, int, and str.
    item_sep : str, default ","
        The separator used to split the list of values in the environment variable.
        Only used if dtype is list. The default is ",".

    Returns
    -------
    bool |  bytes | float | int | str | list | None
        The parsed value of the environment variable, converted to the specified type.
        If the environment variable is not set and no default is provided, a ValueError
        will be raised. If the environment variable is set but cannot be converted to
        the specified type, a ValueError will be raised.

    Raises
    ------
    TypeError
        If the dtype is not one of (bool, bytes, float, int, str, list).
        If the default value is not of the specified dtype.
        If the item_dtype is not one of (bool, bytes, float, int, str).
    ValueError
        If the environment variable is not set and no default is provided.
        If both default and default_factory are provided.
        If the environment variable cannot be converted to the specified dtype.

    Notes
    -----
    Only "simple" data types are supported by this library as environment
    variables shouldn't be used to store complex data types.

    Examples
    --------
    Environment variable parsing can be done by importing `enve`:
    >>> import os
    >>> import enve

    Parsing an environment variable as a string:

    >>> os.environ["ENV_VAR"] = "test"
    >>> enve.get("ENV_VAR")
    'test'
    >>> enve.get("ENV_VAR", dtype=str)
    'test'

    Parsing an environment variable as a boolean:

    >>> os.environ["ENV_VAR"] = "true"
    >>> enve.get("ENV_VAR", dtype=bool)
    True

    Parsing an environment variable as bytes:

    >>> os.environ["ENV_VAR"] = "random_bytes"
    >>> enve.get("ENV_VAR", dtype=bytes)
    b'random_bytes'

    Parsing an environment variable as a float:

    >>> os.environ["ENV_VAR"] = "3.14"
    >>> enve.get("ENV_VAR", dtype=float)
    3.14

    Parsing an environment variable as an integer:

    >>> os.environ["ENV_VAR"] = "42"
    >>> enve.get("ENV_VAR", dtype=int)
    42

    Parsing an environment variable with a default value:

    >>> _ = os.environ.pop("ENV_VAR", None)
    >>> enve.get("ENV_VAR", default="default_value")
    'default_value'

    Parsing an environment variable as a list:

    >>> os.environ["ENV_VAR"] = "1,2,3"
    >>> enve.get("ENV_VAR", dtype=list)
    ['1', '2', '3']

    Parsing an environment variable as a list of integers:

    >>> os.environ["ENV_VAR"] = "1,2,3"
    >>> enve.get("ENV_VAR", dtype=list, item_dtype=int)
    [1, 2, 3]
    """
    dtype = str if dtype is None else dtype
    accepted_dtypes = (bool, bytes, float, int, str, list)
    if dtype not in accepted_dtypes:
        err_msg = f"Invalid type '{dtype}' for '{envvar}'. Expected one of {accepted_dtypes}."
        raise TypeError(err_msg)

    if default is not UNSET and default_factory is not None:
        err_msg = (
            f"Cannot use both 'default' and 'default_factory' for '{envvar}'. Use one or the other."
        )
        raise ValueError(err_msg)

    if default not in (UNSET, None):
        if not isinstance(default, dtype):
            err_msg = (
                f"Default value '{default}' (type={type(default).__name__}) for '{envvar}'"
                f" is not of type '{dtype.__name__}'."
            )
            raise TypeError(err_msg)

        if dtype in (list,):
            warn_msg = (
                f"Using a default value for '{envvar}' of type '{dtype.__name__}'"
                " is not recommended as it may be mutated."
            )
            warnings.warn(warn_msg, UserWarning, stacklevel=2)

    if default_factory is not None and not callable(default_factory):
        err_msg = f"Default factory '{default_factory}' for '{envvar}' is not callable."
        raise TypeError(err_msg)

    value = _get_envvar_value(envvar, docker_secret=docker_secret)
    if value is UNSET:
        if default is not UNSET:
            return default
        if default_factory is not None:
            return default_factory()

        err_msg = (
            f"Environment variable '{envvar}' is not set and no default"
            " or default_factory is provided."
        )
        raise ValueError(err_msg)

    value = cast(str, value)

    if deprecated:
        if not deprecated_msg:
            deprecated_msg = f"The '{envvar}' environment variable is deprecated."
        warnings.warn(deprecated_msg, DeprecationWarning, stacklevel=2)

    if dtype is bool:
        return _parse_bool(envvar, value)
    elif dtype is bytes:
        return value.encode("utf-8")
    elif dtype is float:
        return _parse_float(envvar, value)
    elif dtype is int:
        return _parse_int(envvar, value)
    elif dtype is list:
        values = value.split(item_sep)
        if item_dtype is None:
            return values
        values = _parse_list(envvar, values, item_dtype)
        return cast(list[ItemType], values)
    else:  # dtype is str
        return value
