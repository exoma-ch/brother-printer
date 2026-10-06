---
type: issue
state: closed
created: 2026-09-21T06:24:23Z
updated: 2026-10-06T08:01:40Z
author: renovate[bot]
author_url: https://github.com/renovate[bot]
url: https://github.com/exoma-ch/brother-printer/issues/59
comments: 1
labels: none
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-10-06T09:36:15.700Z
---

# [Issue 59]: [Action Required: Fix Renovate Configuration](https://github.com/exoma-ch/brother-printer/issues/59)

There is an error with this repository's Renovate configuration that needs to be fixed. As a precaution, Renovate will stop PRs until it is resolved.

Error type: Cannot find preset's package (github>OWNER/REPO//.github/renovate-default)

---

# [Comment #1]() by [c-vigo]()

_Posted on October 6, 2026 at 08:01 AM_

Fixed in #62 (`08f6fc0`), merged to `dev`: `renovate.json` extends
`github>exoma-ch/brother-printer//.github/renovate-default` instead of the
literal `OWNER/REPO` scaffold placeholder. The preset itself was always present
at `.github/renovate-default.json` — only the reference to it was wrong.

**Caveat worth recording before this closes.** Renovate reads `renovate.json`
from the repository's *default* branch, and `main` still carries the
placeholder:

```console
$ git show origin/main:renovate.json
    "github>OWNER/REPO//.github/renovate-default"
```

So from Renovate's point of view the error condition is still live, and it may
re-raise this issue on its own until the fix reaches `main` with the next
release. Closing as bookkeeping: the fix is done and queued on `dev`, not
pending further work here.

