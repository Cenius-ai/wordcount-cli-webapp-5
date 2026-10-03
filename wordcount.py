#!/usr/bin/env python3
"""wordcount - count the words in a UTF-8 text file.

A single-file, dependency-free Python 3 command line tool. It reads one text
file as explicit UTF-8, splits the decoded text on runs of Unicode whitespace
and prints the number of tokens as the only line on stdout. Every failure is
reported as one plain line on stderr with a non-zero exit code and no traceback.

Design source of truth for this terminal product (see README "Design"):

  accent    oklch(0.58 0.12 208) = #008d9f - the single status accent, committed
            here as ACCENT in its hex form because no terminal parses oklch();
            it is rendered only on a colour TTY
  type      system monospace, aligned columns, box-drawing separators
  surface   terminal dark; the accent is never the only signal
  density   compact; no chrome and nothing on screen that does not inform

Usage:
    python3 wordcount.py <file>
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

__version__ = "1.0.0"

PROG = "wordcount.py"

# The one accent, in the form a terminal can actually use: the oklch() spelling
# lives in the module docstring and the README; ANSI truecolor needs components.
ACCENT = "#008d9f"

# --- exit codes (the contract scripts depend on) -----------------------------
EXIT_OK = 0
EXIT_FILE_ERROR = 1
EXIT_USAGE_ERROR = 2

_RULE = "─" * 62
_COLUMN = 12


@dataclass(frozen=True)
class WordCount:
    """A file path paired with the number of words found in that file."""

    file_path: str
    count: int


def count_words(file_path: str) -> WordCount:
    """Read *file_path* as explicit UTF-8 and count its words.

    The explicit encoding keeps the result identical on every machine, and
    ``str.split()`` without arguments splits on runs of Unicode whitespace, so
    tabs, newlines, U+00A0 and non-ASCII words such as ``café`` or ``日本語``
    are all handled without a locale or a tokenizer.

    Raises the underlying :class:`OSError`/:class:`UnicodeDecodeError`; the
    caller turns those into the CLI's one-line stderr contract.
    """
    with open(file_path, encoding="utf-8") as handle:
        text = handle.read()
    return WordCount(file_path=file_path, count=len(text.split()))


def _accent_escape() -> str:
    """ANSI truecolor escape for the committed accent, derived from ACCENT."""
    red, green, blue = (int(ACCENT[index : index + 2], 16) for index in (1, 3, 5))
    return f"\x1b[38;2;{red};{green};{blue}m"


def _accent(text: str, enabled: bool) -> str:
    """Wrap *text* in the accent colour, or return it untouched."""
    return f"{_accent_escape()}{text}\x1b[0m" if enabled else text


def supports_accent(stream: object | None = None) -> bool:
    """True when the stream is a colour TTY and NO_COLOR has not been set."""
    if os.environ.get("NO_COLOR"):
        return False
    target = sys.stdout if stream is None else stream
    return bool(getattr(target, "isatty", lambda: False)())


def _columns(rows: list[tuple[str, str]], width: int = _COLUMN) -> list[str]:
    """Render label/description rows as aligned two-column lines."""
    return [f"  {label.ljust(width)}{description}" for label, description in rows]


def format_help(*, use_accent: bool) -> str:
    """The full help text: what the tool does, its streams, codes and examples."""
    lines = [
        _accent(
            f"wordcount {__version__} · count the words in a UTF-8 text file",
            use_accent,
        ),
        _RULE,
        "",
        "usage",
        f"  {PROG} file",
        "",
        "arguments",
        *_columns([("file", "path to the UTF-8 text file to count (required)")]),
        "",
        "options",
        *_columns(
            [
                ("-h, --help", "show this help and exit"),
                ("--version", "show the version and exit"),
            ]
        ),
        "",
        "behaviour",
        "  stdout carries exactly one line: the number of whitespace-separated words.",
        "  On failure stdout stays empty and the reason is written to stderr.",
        "",
        "exit codes",
        *_columns(
            [
                ("0", "counted successfully"),
                ("1", "file error: the path is missing, a directory,"),
                ("", "or not readable UTF-8 text"),
                ("2", "usage error: no file argument was given"),
            ]
        ),
        "",
        "examples",
        f"  python3 {PROG} fixtures/words_utf8.txt",
        f"  python3 {PROG} notes/draft.md",
    ]
    return "\n".join(lines)


class _HelpAction(argparse.Action):
    """Print the product's help banner to stdout and exit 0.

    argparse's built-in help formatter cannot render the aligned-column layout
    this product commits to, so ``-h``/``--help`` is rendered by hand while
    argparse keeps ownership of usage errors (exit code 2, stderr).
    """

    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None,
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        # argparse's exit() would print the message to stderr; help belongs on stdout.
        print(format_help(use_accent=supports_accent()))
        parser.exit(EXIT_OK)


def build_parser() -> argparse.ArgumentParser:
    """The CLI surface: one positional file, help and version."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        usage="%(prog)s file",
        description="Count the words in a UTF-8 text file.",
        add_help=False,
    )
    parser.add_argument(
        "file", metavar="file", help="path to the UTF-8 text file to count"
    )
    parser.add_argument(
        "-h", "--help", action=_HelpAction, help="show this help and exit"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROG} {__version__}",
        help="show the version and exit",
    )
    return parser


def _report_file_error(file_path: str, reason: str) -> int:
    """Write one plain line naming the offending path to stderr; never stdout."""
    print(f"{PROG}: error: cannot count '{file_path}': {reason}", file=sys.stderr)
    return EXIT_FILE_ERROR


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return its exit code."""
    args = build_parser().parse_args(argv)
    try:
        result = count_words(args.file)
    except FileNotFoundError:
        return _report_file_error(args.file, "no such file")
    except IsADirectoryError:
        return _report_file_error(args.file, "is a directory")
    except PermissionError:
        return _report_file_error(args.file, "permission denied")
    except UnicodeDecodeError as error:
        return _report_file_error(
            args.file, f"not valid UTF-8 text (byte offset {error.start})"
        )
    except OSError as error:
        return _report_file_error(args.file, error.strerror or error.__class__.__name__)

    print(result.count)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
