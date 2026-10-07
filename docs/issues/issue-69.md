---
type: issue
state: closed
created: 2026-10-06T09:28:19Z
updated: 2026-10-06T09:39:46Z
author: vig-os-release-app[bot]
author_url: https://github.com/vig-os-release-app[bot]
url: https://github.com/exoma-ch/brother-printer/issues/69
comments: 1
labels: bug
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-10-07T07:58:50.424Z
---

# [Issue 69]: [Release 0.3.0 failed — automatic rollback](https://github.com/exoma-ch/brother-printer/issues/69)

Release 0.3.0 failed during the automated release workflow.

**Workflow Run:** [View logs](https://github.com/exoma-ch/brother-printer/actions/runs/37442822934)
**Release PR:** #67

**Automatic rollback attempted:**
- Release branch: this run's finalize commit(s) reverted, but only when the branch tip matched exactly what the run wrote — otherwise the branch is left untouched and the rollback step fails loudly instead (vig-os/devkit#1462)

**Tag status (forward-fix policy):**
- Release tags are not deleted by automation (workflow choice; GitHub immutable-release lock-in applies only after a release is **published** when that setting is enabled). If a tag was pushed before the failure, it remains on the remote.
- Use a new release candidate to validate fixes, then re-run the final release when ready.
- If a draft GitHub Release exists, manage it from the Releases UI; **publishing** locks the linked tag and assets when **immutable releases** are enabled.
---

# [Comment #1]() by [c-vigo]()

_Posted on October 6, 2026 at 09:39 AM_

Resolved — cause identified and fixed.

The run failed in `Finalize Release Core` at `Trigger sync-issues workflow`:

```
HTTP 422: Cannot trigger a 'workflow_dispatch' on a disabled workflow
ERROR: Command failed after 2 attempts:
  gh workflow run sync-issues.yml --ref release/0.3.0 -f target-branch=release/0.3.0
```

Not a workflow or input problem — both the `main` and `release/0.3.0` copies of `sync-issues.yml` declare `target-branch`. GitHub had **auto-disabled the repository's schedule-triggered workflows for inactivity**: `Sync Issues and PRs`, `CodeQL` and `Scorecard` were all in state `disabled_inactivity`, consistent with the repo being dormant between the 0.2.0 release (2026-06-17) and now. CodeQL and Scorecard had therefore also not run for months, independent of the release.

Fixed by re-enabling all three (`gh workflow enable`); they are `active` again, and CodeQL now reports on PR #67.

Rollback behaved correctly: the finalize commit was reverted, CHANGELOG returned to `## [0.3.0] - TBD`, and no tag or draft Release was left behind. The re-run ([37443685104](https://github.com/exoma-ch/brother-printer/actions/runs/37443685104)) completed end to end — tag `0.3.0` at `29b231e`, draft GitHub Release created, tests green against the finalized commit.

Pre-flight for next time, since this recurs on any repo idle ~60 days and surfaces as a mid-release failure:

```sh
gh api repos/exoma-ch/brother-printer/actions/workflows \
  --jq '.workflows[] | select(.state != "active") | "\(.state)  \(.name)"'
```

