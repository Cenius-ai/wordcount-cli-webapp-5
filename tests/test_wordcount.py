"""End-to-end tests for the wordcount CLI.

Every test drives shipped artefacts: the module's public functions, the bundled
fixtures, and the real command line through a subprocess. Stdout, stderr and the
exit code are asserted separately, because that separation is the contract a
shell script depends on.
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
FIXTURES = ROOT / "fixtures"
WORDS_UTF8 = FIXTURES / "words_utf8.txt"
EMPTY = FIXTURES / "empty.txt"
WHITESPACE_ONLY = FIXTURES / "whitespace_only.txt"

# The documented count for fixtures/words_utf8.txt (see README).
WORDS_UTF8_COUNT = 65


def run_cli(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the CLI the way a user or a script would, capturing both streams."""
    environment = None
    if env is not None:
        environment = {**os.environ, **env}
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


def _raiser(error: BaseException):
    """A stand-in for count_words that always raises *error*."""

    def _fail(_file_path: str) -> wordcount.WordCount:
        raise error

    return _fail


# --- counting core -----------------------------------------------------------


def test_count_words_returns_the_path_and_the_token_count() -> None:
    result = wordcount.count_words(str(WORDS_UTF8))

    assert isinstance(result, wordcount.WordCount)
    assert result.file_path == str(WORDS_UTF8)
    assert result.count == WORDS_UTF8_COUNT


def test_non_ascii_words_are_counted_once_each() -> None:
    result = wordcount.count_words(str(WORDS_UTF8))
    text = WORDS_UTF8.read_text(encoding="utf-8")

    assert "café" in text and "日本語" in text and "naïve" in text
    assert result.count == len(text.split())


def test_non_ascii_whitespace_separates_words(tmp_path: Path) -> None:
    nb = tmp_path / "nbsp.txt"
    # U+00A0 NO-BREAK SPACE is whitespace for str.split(), so this is 3 words.
    nb.write_text("café\u00a0naïve\u00a0日本語\n", encoding="utf-8")

    assert wordcount.count_words(str(nb)).count == 3
    assert "\u00a0" in WORDS_UTF8.read_text(encoding="utf-8")


def test_tabs_newlines_and_space_runs_collapse_to_one_separator(tmp_path: Path) -> None:
    messy = tmp_path / "messy.txt"
    messy.write_text("one \t two\n\nthree   four\t\n", encoding="utf-8")

    assert wordcount.count_words(str(messy)).count == 4


@pytest.mark.parametrize(
    "fixture", [EMPTY, WHITESPACE_ONLY], ids=["empty", "whitespace-only"]
)
def test_empty_and_whitespace_only_files_count_zero(fixture: Path) -> None:
    assert wordcount.count_words(str(fixture)).count == 0


def test_utf8_words_survive_an_ascii_only_locale() -> None:
    ascii_locale = run_cli(str(WORDS_UTF8), env={"LC_ALL": "C", "LANG": "C"})
    utf8_locale = run_cli(str(WORDS_UTF8), env={"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})

    assert ascii_locale.stdout == utf8_locale.stdout == f"{WORDS_UTF8_COUNT}\n"
    assert ascii_locale.returncode == utf8_locale.returncode == 0


# --- success path ------------------------------------------------------------


def test_success_prints_only_the_count_on_stdout() -> None:
    result = run_cli(str(WORDS_UTF8))

    assert result.returncode == 0
    assert result.stdout == f"{WORDS_UTF8_COUNT}\n"
    assert result.stderr == ""


def test_stdout_is_exactly_one_line() -> None:
    result = run_cli(str(WORDS_UTF8))

    assert result.stdout.count("\n") == 1


def test_main_prints_the_count_and_returns_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert wordcount.main([str(WORDS_UTF8)]) == 0

    captured = capsys.readouterr()
    assert captured.out == f"{WORDS_UTF8_COUNT}\n"
    assert captured.err == ""


def test_results_are_deterministic() -> None:
    first, second = run_cli(str(WORDS_UTF8)), run_cli(str(WORDS_UTF8))

    assert (first.stdout, first.returncode) == (second.stdout, second.returncode)


# --- usage errors ------------------------------------------------------------


def test_no_argument_is_a_usage_error() -> None:
    result = run_cli()

    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage" in result.stderr
    assert "file" in result.stderr
    assert "Traceback" not in result.stderr


def test_second_argument_is_rejected() -> None:
    result = run_cli(str(WORDS_UTF8), str(EMPTY))

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Traceback" not in result.stderr


# --- file errors -------------------------------------------------------------

MISSING_PATH = "notes/does-not-exist.txt"


def test_missing_path_is_named_on_stderr() -> None:
    result = run_cli(MISSING_PATH)

    assert result.returncode == 1
    assert result.stdout == ""
    assert MISSING_PATH in result.stderr
    assert result.stderr.count("\n") == 1
    assert "Traceback" not in result.stderr


def test_broken_symlink_is_reported_as_missing(tmp_path: Path) -> None:
    link = tmp_path / "dangling.txt"
    link.symlink_to(tmp_path / "gone.txt")

    result = run_cli(str(link))

    assert result.returncode == 1
    assert result.stdout == ""
    assert str(link) in result.stderr


def test_directory_path_is_reported() -> None:
    result = run_cli(str(FIXTURES))

    assert result.returncode == 1
    assert result.stdout == ""
    assert str(FIXTURES) in result.stderr
    assert "directory" in result.stderr
    assert "Traceback" not in result.stderr


def test_non_utf8_input_is_reported_without_a_traceback(tmp_path: Path) -> None:
    latin1 = tmp_path / "latin1.txt"
    latin1.write_bytes(b"caf\xe9 na\xefve\n")

    result = run_cli(str(latin1))

    assert result.returncode == 1
    assert result.stdout == ""
    assert str(latin1) in result.stderr
    assert "UTF-8" in result.stderr
    assert "Traceback" not in result.stderr


def test_unreadable_file_is_reported(tmp_path: Path) -> None:
    locked = tmp_path / "locked.txt"
    locked.write_text("a locked file\n", encoding="utf-8")
    locked.chmod(0o000)
    try:
        if os.access(locked, os.R_OK, effective_ids=True):
            pytest.skip("running with privileges that ignore the file mode")

        result = run_cli(str(locked))

        assert result.returncode == 1
        assert result.stdout == ""
        assert str(locked) in result.stderr
        assert "Traceback" not in result.stderr
    finally:
        locked.chmod(0o600)


def test_permission_error_maps_to_exit_code_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    denied = PermissionError(13, "Permission denied")
    monkeypatch.setattr(wordcount, "count_words", _raiser(denied))

    assert wordcount.main(["/protected/notes.txt"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "/protected/notes.txt" in captured.err
    assert "permission denied" in captured.err


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError(2, "No such file or directory"),
        IsADirectoryError(21, "Is a directory"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
        OSError(5, "Input/output error"),
    ],
)
def test_every_expected_failure_keeps_stdout_empty(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: BaseException,
) -> None:
    monkeypatch.setattr(wordcount, "count_words", _raiser(error))

    assert wordcount.main(["some/file.txt"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "some/file.txt" in captured.err
    assert "Traceback" not in captured.err


# --- help and version --------------------------------------------------------


def test_help_is_written_to_stdout() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert result.stderr == ""
    assert "usage" in result.stdout
    assert "wordcount.py file" in result.stdout
    assert "exit codes" in result.stdout


def test_short_help_flag_matches_long_flag() -> None:
    assert run_cli("-h").stdout == run_cli("--help").stdout


def test_version_is_written_to_stdout() -> None:
    result = run_cli("--version")

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.strip() == f"wordcount.py {wordcount.__version__}"
