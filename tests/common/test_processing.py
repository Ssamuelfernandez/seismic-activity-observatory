"""Pruebas de `common/processing.py` (T028)."""
import pytest

from common.processing import decide_version_outcome, is_inconsistent_state, is_newer_version
from common.records import VersionOutcome


@pytest.mark.parametrize(
    "stored,incoming,inserted,differs,expected",
    [
        (None, 100, True, False, VersionOutcome.NEW_EVENT),
        (100, 200, True, False, VersionOutcome.NEWER_VERSION),
        (200, 100, True, False, VersionOutcome.LATE_OLD_VERSION),
        (200, 100, False, False, VersionOutcome.REDELIVERY),
        (100, 100, False, False, VersionOutcome.REDELIVERY),
        (100, 100, False, True, VersionOutcome.SAME_UPDATED_CONFLICT),
        (200, 100, False, True, VersionOutcome.SAME_UPDATED_CONFLICT),
    ],
)
def test_decide_version_outcome_table(stored, incoming, inserted, differs, expected) -> None:
    assert decide_version_outcome(stored, incoming, inserted, differs) is expected


def test_inconsistent_state_returns_late_old_version_and_does_not_raise() -> None:
    assert decide_version_outcome(100, 100, True, False) is VersionOutcome.LATE_OLD_VERSION


def test_is_newer_version() -> None:
    assert is_newer_version(100, None) is True
    assert is_newer_version(101, 100) is True
    assert is_newer_version(100, 100) is False
    assert is_newer_version(99, 100) is False


@pytest.mark.parametrize(
    "stored,incoming,inserted,expected",
    [
        (100, 100, True, True),
        (100, 100, False, False),
        (None, 100, True, False),
        (200, 100, True, False),
        (100, 200, True, False),
    ],
)
def test_is_inconsistent_state(stored, incoming, inserted, expected) -> None:
    assert is_inconsistent_state(stored, incoming, inserted) is expected
