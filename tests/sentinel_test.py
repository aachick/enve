"""Test the Sentinel class."""

from enve.parser import UNSET, Sentinel


def test_sentinel_repr() -> None:
    """Test the __repr__ method of the Sentinel class."""
    assert repr(UNSET) == "Sentinel(UNSET)"


def test_sentinel_reduce() -> None:
    """Test the __reduce__ method of the Sentinel class."""
    assert UNSET.__reduce__() == (Sentinel, ("UNSET", "enve.parser"))


def test_sentinel_registry() -> None:
    """Test the registry of the Sentinel class."""
    unset = Sentinel("UNSET")
    assert unset is UNSET

    new_sentinel = Sentinel("NEW_SENTINEL")
    assert new_sentinel is not UNSET
