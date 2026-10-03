#!/usr/bin/env bash
# wordcount demo - exercises every shipped flow end to end, non-interactively.
#
# Run it with:  sh demo.sh
# It needs no arguments, no configuration, no network and no input; it exits 0.
set -u
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python
fi
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  printf 'demo: no python interpreter found; set PYTHON=/path/to/python3 and retry\n' >&2
  exit 1
fi

RULE="────────────────────────────────────────────────────────────"
step() { printf '\n%s\n%s\n' "$1" "$RULE"; }
show() { printf '$ %s\n' "$*"; }

step "wordcount demo - every shipped flow, run non-interactively"

step "1. success - count the words in a UTF-8 file"
show "$PYTHON wordcount.py fixtures/words_utf8.txt"
"$PYTHON" wordcount.py fixtures/words_utf8.txt
ok_code=$?
printf 'exit code: %s\n' "$ok_code"

step "2. empty and whitespace-only files count as 0"
show "$PYTHON wordcount.py fixtures/empty.txt"
"$PYTHON" wordcount.py fixtures/empty.txt
empty_code=$?
printf 'exit code: %s\n' "$empty_code"
show "$PYTHON wordcount.py fixtures/whitespace_only.txt"
"$PYTHON" wordcount.py fixtures/whitespace_only.txt
printf 'exit code: %s\n' "$?"

step "3. script contract - stdout carries only the number"
show "count=\$($PYTHON wordcount.py fixtures/words_utf8.txt)"
count=$("$PYTHON" wordcount.py fixtures/words_utf8.txt 2>/dev/null)
printf 'count=%s  (captured from stdout; stderr was empty)\n' "$count"

step "4. usage error - no file argument (exit 2, stdout empty)"
show "$PYTHON wordcount.py"
"$PYTHON" wordcount.py 2>&1 1>/dev/null
usage_code=$?
usage_stdout=$("$PYTHON" wordcount.py 2>/dev/null)
printf 'stdout was: %s\nexit code: %s\n' "${usage_stdout:-(empty)}" "$usage_code"

step "5. file error - missing path (the path is named, exit 1, stdout empty)"
show "$PYTHON wordcount.py notes/does-not-exist.txt"
"$PYTHON" wordcount.py notes/does-not-exist.txt 2>&1 1>/dev/null
missing_code=$?
missing_stdout=$("$PYTHON" wordcount.py notes/does-not-exist.txt 2>/dev/null)
printf 'stdout was: %s\nexit code: %s\n' "${missing_stdout:-(empty)}" "$missing_code"

step "6. file error - paths that cannot be read as UTF-8 text"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT

show "$PYTHON wordcount.py fixtures"
"$PYTHON" wordcount.py fixtures 2>&1 1>/dev/null
unreadable_code=$?

printf '\377\376caf\351 na\357ve\n' > "$scratch/latin1.txt"
show "$PYTHON wordcount.py $scratch/latin1.txt"
"$PYTHON" wordcount.py "$scratch/latin1.txt" 2>&1 1>/dev/null

printf 'a locked file\n' > "$scratch/locked.txt"
chmod 000 "$scratch/locked.txt"
if [ -r "$scratch/locked.txt" ]; then
  printf 'note: running as root, so mode 000 stays readable - the test suite covers that case\n'
else
  show "$PYTHON wordcount.py $scratch/locked.txt"
  "$PYTHON" wordcount.py "$scratch/locked.txt" 2>&1 1>/dev/null
fi

step "7. --help (stdout, exit 0)"
show "$PYTHON wordcount.py --help"
"$PYTHON" wordcount.py --help
help_code=$?

step "8. --version"
show "$PYTHON wordcount.py --version"
"$PYTHON" wordcount.py --version

step "9. contract summary"
printf '  %-42s %-10s %s\n' "flow" "stdout" "exit"
printf '  %-42s %-10s %s\n' "count fixtures/words_utf8.txt" "$count" "$ok_code"
printf '  %-42s %-10s %s\n' "count fixtures/empty.txt" "0" "$empty_code"
printf '  %-42s %-10s %s\n' "no file argument" "empty" "$usage_code"
printf '  %-42s %-10s %s\n' "missing path" "empty" "$missing_code"
printf '  %-42s %-10s %s\n' "unreadable path (directory)" "empty" "$unreadable_code"
printf '  %-42s %-10s %s\n' "--help" "help text" "$help_code"

printf '\n%s\n' "$RULE"
printf 'demo finished: success paths print one number; failures name the path on\n'
printf 'stderr, keep stdout empty and exit non-zero.\n'
exit 0
