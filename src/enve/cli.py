"""CLI entrypoint for the enve library."""

import argparse
import json
import os
import sys

from collections.abc import Sequence

from enve.parser import UNSET, get


def _get_docker_secret_value(docker_secret: str | None) -> bool | str:
    """Parse the docker secret value from the CLI."""
    if docker_secret is None:
        return False
    if not docker_secret:
        return True

    return docker_secret


def main(sys_args: Sequence[str] | None = None) -> None:
    """CLI entrypoint for the enve library."""
    from enve import __version__

    prog = "enve"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Print environment variables values without worrying about substitutions.",
    )
    parser.add_argument(
        "env_var",
        help=(
            "The environment variable to print the value of."
            " If unset, print all environment variables."
        ),
        nargs="?",
    )

    parser_grp = parser.add_argument_group("Parser options")
    parser_grp.add_argument(
        "-d",
        "--default",
        action="store",
        const="",
        help=(
            "The default value to use if the environment variable is not set."
            " This can be used a boolean flag (i.e., this option can be set"
            " without a value). In this case, the default value will be"
            " an empty string if the environment variable is not set."
        ),
        nargs="?",
    )
    parser_grp.add_argument(
        "-s",
        "--docker-secret",
        action="store",
        const="",
        help=(
            "If set, specify that the environment variable can also be a Docker secret."
            " This can be used a boolean flag (i.e., this option can be set without a value)."
            " If set this way, a docker secret with the same name as the environment will"
            " be search for. If set with a value, the value will be used as the docker secret name."
        ),
        nargs="?",
    )

    global_env_grp = parser.add_argument_group("Global environment options")
    global_env_grp.add_argument(
        "-0",
        "--null",
        action="store_true",
        help=(
            "End each output line with a null character instead of a newline"
            " when printing all environment variables."
        ),
    )
    global_env_grp.add_argument(
        "-j",
        "--json",
        action="store_true",
        help=(
            "Output the environment variable as a JSON object."
            " This is only used when printing all environment variables."
        ),
    )

    parser.add_argument("--version", action="version", version=f"{prog} {__version__}")
    parser._positionals.title = "Positional arguments"
    parser._optionals.title = "Optional arguments"

    args = parser.parse_args(args=sys_args)
    if not args.env_var and not sys.stdin.isatty():
        args.env_var = sys.stdin.read().strip()

    if not args.env_var:
        eol = "\0" if args.null else "\n"

        if args.json:
            output_str = json.dumps(dict(os.environ))
        else:
            output_str = eol.join(f"{k}={v}" for k, v in os.environ.items())

        sys.stdout.write(f"{output_str}{eol}")
        parser.exit(status=0)

    env_var = str(args.env_var)
    default = UNSET if args.default is None else str(args.default)
    docker_secret = _get_docker_secret_value(str(args.docker_secret))

    try:
        try:
            env_value = get(env_var, default=default, docker_secret=docker_secret)
            sys.stdout.write(env_value)
            parser.exit(status=0)
        except ValueError as err:
            parser.exit(status=1, message=f"{err}\n")
    except BrokenPipeError:  # pragma: no cover
        # NOTE: This is tested but I can't figure out how to make it covered.
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)  #  Python exits with error code 1 on EPIPE


if __name__ == "__main__":
    main()
