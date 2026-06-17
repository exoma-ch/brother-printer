---
type: issue
state: closed
created: 2026-06-17T12:44:19Z
updated: 2026-06-17T13:03:37Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/42
comments: 0
labels: bug, priority:medium, area:workspace, effort:small, semver:patch
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-17T18:22:40.026Z
---

# [Issue 42]: [just label loses quoting: spaced label text split into multiple CLI args](https://github.com/exoma-ch/brother-printer/issues/42)

## Summary

The `just label` recipe (and other `*args` forwarding recipes) lose argument quoting, so any label text containing a space is split into multiple CLI arguments and the command fails.

## Reproduction

```console
$ just label "Flex ID"
uv run brother-ptouch-label Flex ID
Usage: brother-ptouch-label [OPTIONS] TEXT
Try 'brother-ptouch-label --help' for help.

Error: Got unexpected extra argument (ID)

$ just label "FlexID"
uv run brother-ptouch-label FlexID
Printed 9890 bytes.
```

## Root cause

The recipe forwards arguments via raw textual interpolation:

```just
label *args:
    uv run brother-ptouch-label {{ args }}
```

`{{ args }}` is a plain text substitution, so `just label "Flex ID"` expands to the literal line `uv run brother-ptouch-label Flex ID`. The shell then word-splits this into two arguments (`Flex`, `ID`). The quoting the user supplied is lost before the CLI ever sees it.

The `brother-ptouch-label` CLI is correct — it takes a single `TEXT` argument and rightly rejects the second one.

## Affected recipes

All `*args` recipes that forward to a command via `{{ args }}` in `justfile.project`:

- `discover`
- `printer-status`
- `tapes`
- `print`
- `label`
- `setup-usb`

## Proposed fix

Enable `set positional-arguments` and forward `"$@"` (real shell positional parameters, which preserve quoting) instead of `{{ args }}`:

```just
set positional-arguments

label *args:
    uv run brother-ptouch-label "$@"
```

## Workaround

Double-quote/escape so a quoted string survives interpolation:

```console
$ just label "'Flex ID'"
```

