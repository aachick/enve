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
"""Test that getting the version works."""

from importlib.metadata import PackageNotFoundError

import pytest

from enve import _get_module_version


def test_get_version_without_installation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a version can be returned without installation."""
    monkeypatch.setattr(
        "enve._get_version", lambda _: (_ for _ in ()).throw(PackageNotFoundError())
    )
    assert _get_module_version() == "0.0.0"


def test_get_version_with_pinned_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that getting the version works."""
    monkeypatch.setattr("enve._get_version", lambda _: "X.Y.Z")
    assert _get_module_version() == "X.Y.Z"
