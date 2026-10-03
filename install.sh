#!/usr/bin/env bash
# wordcount installer - installs this project's dependencies, then EXITS.
#
# It never uses sudo, never touches a system package manager, never starts the
# tool and is safe to re-run. Prerequisites (Python 3.8+) are listed in
# INSTALL.md and are not installed here.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  printf 'install: %s not found. Install Python 3.8 or newer (see INSTALL.md).\n' "$PYTHON" >&2
  exit 1
fi

printf 'install: using %s (%s)\n' "$PYTHON" "$("$PYTHON" -c 'import platform; print(platform.python_version())')"

# wordcount itself is standard-library only; requirements.txt pins the test
# runner. Upgrade the toolchain first (old pip breaks modern installs), then
# install the pinned requirements.
if ! "$PYTHON" -m pip install --upgrade pip setuptools wheel; then
  printf 'install: warning: could not upgrade pip/setuptools/wheel (offline?)\n' >&2
fi

if ! "$PYTHON" -m pip install -r requirements.txt; then
  if "$PYTHON" -c 'import pytest' >/dev/null 2>&1; then
    printf 'install: warning: could not install requirements; using the existing pytest\n' >&2
  else
    printf 'install: error: could not install the test runner pytest (see INSTALL.md)\n' >&2
    exit 1
  fi
fi

# Cheap self-check: an import that fails here fails loudly at install time.
"$PYTHON" -c 'import wordcount; print("install: wordcount", wordcount.__version__, "imports cleanly from the project root")'

printf '\nSetup complete. Nothing was started - the tool is a one-shot command.\n'
printf '  count a file : %s wordcount.py fixtures/words_utf8.txt\n' "$PYTHON"
printf '  run the tests: %s -m pytest -q\n' "$PYTHON"
printf '  run the demo : sh demo.sh\n'
