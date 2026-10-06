"""Tests of the versions and of the steps a delivery proposes."""

import pytest

from island.deliver import Bump, Version, suggest_bump


@pytest.mark.parametrize(
    ("text", "bump", "released"),
    [
        ("", "patch", "0.0.1"),
        ("", "minor", "0.1.0"),
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
        # a version being developed is released as itself at least
        ("1.2.4-dev", "patch", "1.2.4"),
        ("1.2.4-dev", "minor", "1.3.0"),
        ("1.3.0-dev", "minor", "1.3.0"),
        ("1.3.0-dev", "major", "2.0.0"),
        ("2.0.0-dev", "major", "2.0.0"),
        ("1.2.4-dev\n", "patch", "1.2.4"),
        ("1.2", "patch", "1.2.1"),
    ],
)
def test_the_version_released(text: str, bump: Bump, released: str) -> None:
    assert str(Version.parse(text).release(bump)) == released


def test_the_version_developed_after_a_release() -> None:
    assert str(Version.parse("1.3.0").next_dev()) == "1.3.1-dev"
    # the next patch release is the version being developed: no number is skipped
    assert str(Version.parse("1.3.0").next_dev().release("patch")) == "1.3.1"


def test_the_step_proposed_from_the_commits() -> None:
    assert suggest_bump(["[FIX] a fix", "[DOC] a doc"]) == "patch"
    assert suggest_bump(["[FIX] a fix", "[FEAT] a feature"]) == "minor"
    assert suggest_bump(["[FEAT] a feature", "[API] change the interface"]) == "major"
    assert suggest_bump(["[DEV] BREAKING: the old option is gone"]) == "major"
