![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge)

![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)

![Mypy](https://img.shields.io/badge/mypy-checked-blue?style=for-the-badge)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=for-the-badge)](https://github.com/astral-sh/uv)

<div style="text-align: center;">
    <img src="https://raw.githubusercontent.com/aachick/enve/main/docs/assets/enve.png" />
</div>

# enve

An environment variable parser library with type hint and conversion support.

The complete documentation is available [here](https://aachick.github.io/enve/).

## Usage

`enve.get` is the main package function. It's essentially `os.getenv` on
(arguably unnecessarily strong) steroids. It's advantage is that it will
automatically validate the environment variable's data type based on what
you desire and provide typing support for the used variable. For complete
details, see the `enve.get` function docstring.

The example below illustrates how you can obtain environment variables and
convert them to a desired data type.

```python
import enve


ENVVAR = enve.get("ENVVAR")  # will be parsed and typed as `str`
ENVVAR_STR = enve.get("ENVVAR", dtype=str)  # will be parsed and typed as `str`
MY_SWITCH = enve.get("MY_SWITCH", dtype=bool)  # will be parsed and typed as `bool`
HASH_SALT = enve.get("HASH_SALT", dtype=bytes)  # will be parsed and typed as `bytes`
RANDOM_SEED = enve.get("RANDOM_SEED", dtype=int)  # will be parsed and typed as `int`
MY_PI = enve.get("MY_PI", dtype=float)  # will be parsed and typed as `float`
CUDA_VISIBLE_DEVICES = enve.get("CUDA_VISIBLE_DEVICES", dtype=list)  # will be parsed and typed as `list`
```

Supported data types are `bool`, `bytes`, `float`, `int`, `str` (the default), and `list`.

In all these examples, a `ValueError` will be raised if the environment variable is not
defined. To use a default value, set the `default` parameter accordingly. Note that the
default value's type must be `None` or the same as the expected return type.

```python
import enve


ENVVAR_WITH_DEFAULT = enve.get("MISSING_ENVVAR", default="foobar")
```

`enve.get` also supports [Docker secrets](https://docs.docker.com/engine/swarm/secrets/).
By setting the `docker_secret` parameter to `True` or to the name of a Docker secret,
`enve.get` will attempt to retrieve its value (even if unset in the current environment).

```python
import enve


# The following snippet will:
# 1. Check whether the `MY_SECRET` envvar exists. If true, this will be returned.
# 2. Check whether `/run/secrets/MY_SECRET` exists. If true, the file will be read
#    and the value will be returned.
# 3. Check whether `/run/secrets/my_secret` exists. If true, the file will be read
#    and the value will be returned.
# 4. Raise a `ValueError` as no default is provided.
MY_SECRET = enve.get("MY_SECRET", docker_secret=True)
```
