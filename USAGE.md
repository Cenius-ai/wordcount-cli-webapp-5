# Using wordcount

Task-oriented walkthroughs of everything the tool actually does. Every command
below was run from a clean checkout of this project.

## Count a file

```bash
$ python3 wordcount.py fixtures/words_utf8.txt
65
```

The number goes to stdout, on its own line, and the exit code is `0`. Nothing
else is printed.

## Count inside a script

Because stdout carries only the integer, a shell script can capture it directly:

```bash
$ count=$(python3 wordcount.py fixtures/words_utf8.txt)
$ echo "captured: $count"
captured: 65
```

Trust the exit code instead of parsing the text:

```bash
if count=$(python3 wordcount.py "$draft"); then
    echo "$draft: ${count} words"
else
    echo "$draft: could not be counted (see the error above)" >&2
fi
```

The `else` branch runs for a missing file, a directory, an unreadable file or a
file that is not UTF-8 — in all those cases stdout stays empty, so `count` is
never a half-written number.

## Empty and whitespace-only files

```bash
$ python3 wordcount.py fixtures/empty.txt
0
$ python3 wordcount.py fixtures/whitespace_only.txt
0
```

A file with no words is a success: `0` on stdout, exit code `0`.

## Non-ASCII text and non-ASCII whitespace

The file is decoded as UTF-8 and split on runs of Unicode whitespace, so words
and separators outside ASCII behave the same as ASCII ones:

```bash
$ printf 'caf\303\251\302\240na\303\257ve\302\240\346\227\245\346\234\254\350\252\236\n' > /tmp/x.txt
$ python3 wordcount.py /tmp/x.txt
3
```

That file is `café`, `naïve` and `日本語` separated by U+00A0 NO-BREAK SPACE —
three words. The bundled `fixtures/words_utf8.txt` uses the same trick and
counts `65`.

Locale does not change the result:

```bash
$ LC_ALL=C python3 wordcount.py fixtures/words_utf8.txt
65
$ LC_ALL=C.UTF-8 python3 wordcount.py fixtures/words_utf8.txt
65
```

## Ask for help

```bash
$ python3 wordcount.py --help
wordcount 1.0.0 · count the words in a UTF-8 text file
──────────────────────────────────────────────────────────────

usage
  wordcount.py file
...
exit codes
  0           counted successfully
  1           file error: the path is missing, a directory,
              or not readable UTF-8 text
  2           usage error: no file argument was given

examples
  python3 wordcount.py fixtures/words_utf8.txt
  python3 wordcount.py notes/draft.md
```

Help goes to **stdout** and exits `0`, so `python3 wordcount.py --help | less`
works. `-h` prints exactly the same text. The help banner is accented only when
stdout is a colour terminal and `NO_COLOR` is unset; piped or captured output is
always plain.

```bash
$ python3 wordcount.py --version
wordcount.py 1.0.0
```

## When something is wrong

### No file argument

```bash
$ python3 wordcount.py
usage: wordcount.py file
wordcount.py: error: the following arguments are required: file
$ echo $?
2
```

The usage line and the error are on stderr; stdout is empty. Exit code `2` means
"you called it wrong".

### A path that does not exist

```bash
$ python3 wordcount.py notes/does-not-exist.txt
wordcount.py: error: cannot count 'notes/does-not-exist.txt': no such file
$ echo $?
1
```

The exact path you typed appears in the message, so a script log shows which
file failed. Nothing was written to stdout, and no Python traceback appeared.

### A directory, an unreadable file, or non-UTF-8 bytes

```bash
$ python3 wordcount.py fixtures
wordcount.py: error: cannot count 'fixtures': is a directory

$ chmod 000 locked.txt && python3 wordcount.py locked.txt   # as a normal user
wordcount.py: error: cannot count 'locked.txt': permission denied

$ printf 'caf\351 na\357ve\n' > latin1.txt && python3 wordcount.py latin1.txt
wordcount.py: error: cannot count 'latin1.txt': not valid UTF-8 text (byte offset 3)
```

Each of these exits `1`, keeps stdout empty and prints one plain line.

### Too many arguments

```bash
$ python3 wordcount.py a.txt b.txt
usage: wordcount.py file
wordcount.py: error: unrecognized arguments: b.txt
$ echo $?
2
```

One file per run. Counting several files is a `for` loop away:

```bash
for f in drafts/*.txt; do printf '%s\t%s\n' "$(python3 wordcount.py "$f")" "$f"; done
```

## See every flow at once

```bash
sh demo.sh
```

Runs the success paths, the script capture, and each failure path
non-interactively, printing the real output, the exit code, and a final summary
table. It takes no arguments and needs no network.

## What is *not* counted

Punctuation is kept, so `note.` and `"quoted"` are one word each. Case is not
folded. There is no stemming, no CJK segmentation, no line/character/unique-word
output, and no stdin or multi-file mode — none of those were part of this tool's
contract, and none of them is half-built in the code.
