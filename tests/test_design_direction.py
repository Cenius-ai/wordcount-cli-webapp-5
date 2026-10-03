"""Tests for the committed design direction of this CLI.

The product commits to one accent colour and to a plain, non-decorated surface.
These tests pin that contract: the token value, the fact that piped/captured
output never carries escape codes, and the fact that the accent is opt-in and
honours NO_COLOR.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import wordcount

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "wordcount.py"

# The committed accent: oklch(0.58 0.12 208) in the hex form a terminal can use.
COMMITTED_ACCENT = "#008d9f"


def run_cli(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, **(env or {})} if env is not None else None
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


class _ColourTTY:
    """Stands in for a stdout that reports itself as a colour terminal."""

    @staticmethod
    def isatty() -> bool:
        return True


def test_the_committed_accent_is_shipped_verbatim() -> None:
    assert wordcount.ACCENT == COMMITTED_ACCENT


def test_help_banner_is_plain_when_stdout_is_not_a_tty() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "\x1b[" not in result.stdout


def test_help_banner_stays_plain_in_captured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)

    result = run_cli("--help", env={"NO_COLOR": "", "TERM": "xterm-256color"})

    assert "\x1b[" not in result.stdout


def test_accent_is_opt_in_and_uses_the_committed_colour(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)

    assert wordcount.supports_accent(_ColourTTY()) is True
    assert "\x1b[38;2;0;141;159m" in wordcount.format_help(use_accent=True)
    assert "\x1b[" not in wordcount.format_help(use_accent=False)


def test_no_color_disables_the_accent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")

    assert wordcount.supports_accent(_ColourTTY()) is False
