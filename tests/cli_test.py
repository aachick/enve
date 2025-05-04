"""Test the CLI entrypoint for the enve library."""

import json
import os
import subprocess as sp
import sys

import pytest

from enve.cli import _get_docker_secret_value


CDIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CDIR)
BASE_CMD = [
    sys.executable,
    "-m",
    "coverage",
    "run",
    os.path.join(PROJ_DIR, "src", "enve", "cli.py"),
]


def test_main_with_envvar() -> None:
    """Test the main function using subprocess."""
    env_var = "TEST_ENV_VAR"
    env_value = "test_value"
    env = {env_var: env_value, "COVERAGE_PROCESS_START": "1"}

    pipe = sp.run(
        [*BASE_CMD, env_var],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert pipe.returncode == 0, f"Return code: {pipe.returncode} (!= 0): {pipe.stderr}"
    assert env_value == pipe.stdout


def test_main_with_missing_envvar() -> None:
    """Test the main function with a missing environment variable."""
    env_var = "TEST_ENV_VAR"
    env = {"COVERAGE_PROCESS_START": "1"}

    pipe = sp.run(
        [*BASE_CMD, env_var],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert pipe.returncode == 1, f"Return code: {pipe.returncode} (!= 0): {pipe.stderr}"
    expected_msg = f"Environment variable '{env_var}' is not set and no default or default_factory is provided."  # noqa: E501
    assert expected_msg in pipe.stderr


def test_main_with_piped_in_input() -> None:
    """Test the main function with piped input."""
    env_var = "TEST_ENV_VAR"
    env_value = "test_value"
    env = {env_var: env_value, "COVERAGE_PROCESS_START": "1"}

    pipe = sp.run(
        [*BASE_CMD],
        input=env_var,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert pipe.returncode == 0, f"Return code: {pipe.returncode} (!= 0): {pipe.stderr}"
    assert env_value == pipe.stdout


def test_main_with_piped_output() -> None:
    """Test the main function with piped output."""
    env_var = "TEST_ENV_VAR"
    env_value = "test_value"
    env = {env_var: env_value, "COVERAGE_PROCESS_START": "1"}

    cmd = "type" if sys.platform == "win32" else "cat"

    output = sp.check_output(
        " ".join([*BASE_CMD, env_var, "|", cmd]),
        env=env,
        shell=True,
        text=True,
    )
    assert env_value == output


@pytest.mark.parametrize("args", [[], ["--null"]])
def test_main_print_all_envvars(args: list[str]) -> None:
    """Test the main function printing of all envvars."""
    env = {"COVERAGE_PROCESS_START": "1", "FOOBAR": "1"}

    pipe = sp.run(
        [*BASE_CMD, *args],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    pipe_stdout = pipe.stdout.strip()
    assert pipe.returncode == 0
    for env_var, env_val in env.items():
        assert f"{env_var}={env_val}" in pipe_stdout


def test_main_print_all_envvars_to_json() -> None:
    """Test the main function's print of all envvars in JSON format."""
    env = {"COVERAGE_PROCESS_START": "1", "FOOBAR": "1"}

    pipe = sp.run(
        [*BASE_CMD, "--json"],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    pipe_stdout = pipe.stdout.strip()
    assert pipe.returncode == 0
    returned_json = json.loads(pipe_stdout)
    assert isinstance(returned_json, dict)
    for env_var, env_val in env.items():
        assert env_var in returned_json
        assert returned_json[env_var] == env_val


@pytest.mark.parametrize(("value", "expected"), [(None, False), ("", True), ("FOOBAR", "FOOBAR")])
def test_get_docker_secret_value(value: str, expected: bool | str) -> None:
    """Test the _get_docker_secret_value function."""
    result = _get_docker_secret_value(value)
    assert result == expected, f"Expected {expected}, got {result}"
