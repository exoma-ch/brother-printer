---
type: issue
state: closed
created: 2026-10-06T09:16:31Z
updated: 2026-10-06T09:29:36Z
author: vig-os-release-app[bot]
author_url: https://github.com/vig-os-release-app[bot]
url: https://github.com/exoma-ch/brother-printer/issues/68
comments: 1
labels: bug
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-10-06T09:36:13.243Z
---

# [Issue 68]: [Release 0.3.0 failed — automatic rollback](https://github.com/exoma-ch/brother-printer/issues/68)

Release 0.3.0 failed during the automated release workflow.

**Workflow Run:** [View logs](https://github.com/exoma-ch/brother-printer/actions/runs/37441620628)
**Release PR:** #67

**Automatic rollback attempted:**
- Release branch: this run's finalize commit(s) reverted, but only when the branch tip matched exactly what the run wrote — otherwise the branch is left untouched and the rollback step fails loudly instead (vig-os/devkit#1462)

**Tag status (forward-fix policy):**
- Release tags are not deleted by automation (workflow choice; GitHub immutable-release lock-in applies only after a release is **published** when that setting is enabled). If a tag was pushed before the failure, it remains on the remote.
- Use a new release candidate to validate fixes, then re-run the final release when ready.
- If a draft GitHub Release exists, manage it from the Releases UI; **publishing** locks the linked tag and assets when **immutable releases** are enabled.
---

# [Comment #1]() by [c-vigo]()

_Posted on October 6, 2026 at 09:29 AM_

Resolved — cause identified and fixed.

The run failed in `Validate Release Core` with `ERROR: PR #67 is still in draft`. `prepare-release` deliberately opens the release PR as a draft, and the **final** release gates on it being ready for review (the candidate kind defers that gate, vig-os/devkit#902). The missing step between the two was simply `gh pr ready 67`.

Rollback was a no-op here: the failure happened before any finalize commit, so no tag was pushed, no draft Release was created, and `release/0.3.0` stayed at the freeze commit `239f283`.

The PR is now out of draft and the draft gate passes. The re-run hit a *different*, unrelated problem — `sync-issues.yml` being `disabled_inactivity` — tracked in #69.

