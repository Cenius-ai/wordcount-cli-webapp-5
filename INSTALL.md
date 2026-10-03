# Installing wordcount

`wordcount` is a plain-Python command line tool. There is no server, no
database, no migration and no seed step — it is a one-shot command that prints a
number and exits.

## Prerequisites (installed by you, never by this project)

| Requirement | Why | Check |
| --- | --- | --- |
| Python 3.8 or newer | The interpreter the tool runs on | `python3 --version` |

Nothing else is needed: no compiler, no `libsqlite3-dev`, no Node, no Docker, no
network access at runtime. `install.sh` never calls `sudo`, `apt-get`, `apk`,
`yum` or `brew`.

## Step 1 — install (optional)

```bash
bash install.sh
```

What it does, in order:

1. Upgrades `pip`, `setuptools` and `wheel` (old pip silently breaks modern installs).
2. Installs `requirements.txt` — the pinned test runner (`pytest`). The tool
   itself imports only `argparse`, `sys` and `dataclasses` from the standard library.
3. Self-checks with `python3 -c 'import wordcount'` so an incomplete environment
   fails loudly here instead of at first use.
4. Prints the next commands and **exits**.

It is idempotent (re-run it any time) and it never starts anything in the
foreground. If you only want to use the tool and not run its tests, skip this
step entirely — `python3 wordcount.py <file>` already works.

## Step 2 — verify

```bash
python3 -m pytest -q
```

Expected result: `30 passed, 1 skipped` as `root` (the skipped case is the
mode-000 file, which root can still read; the same failure path is covered by
the `PermissionError` mapping test), or `31 passed` as a normal user.

## Step 3 — run

```bash
python3 wordcount.py fixtures/words_utf8.txt
```

Expected: `65` on stdout and exit code `0`.

```bash
sh demo.sh
```

Expected: every shipped flow, non-interactively, ending with a summary table.

## Configuration

There is none to provide. `wordcount` reads no configuration file and no
database, and needs no secrets. `.env.example` lists the only two environment
variables the helper scripts look at — `NO_COLOR` (disables the optional help
accent) and `PYTHON` (chooses the interpreter for `install.sh`/`demo.sh`). Both
have working defaults, so copying `.env.example` to `.env` and leaving it empty
is a valid setup.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `python3: command not found` | Install Python 3.8+ (see Prerequisites); on some systems the interpreter is `python`. |
| `install.sh` warns it could not reach the package index | The machine is offline. The tool still works; only the test suite needs `pytest`, which is usually already present. |
| `ModuleNotFoundError: No module named 'pytest'` | Run `bash install.sh`, or `python3 -m pip install -r requirements.txt`. |
| A file reports `not valid UTF-8 text` | The file is not UTF-8 (for example Latin-1 or UTF-16). Convert it first: `iconv -f latin1 -t utf-8 file.txt > file.utf8.txt`. |
| A path reports `is a directory` | Point the command at a file, not a folder. |
| The count looks high or low | Every run of non-whitespace characters counts, punctuation included — see "What is counted" in `README.md`. |
