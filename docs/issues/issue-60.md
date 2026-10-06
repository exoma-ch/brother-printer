---
type: issue
state: closed
created: 2026-10-05T13:35:40Z
updated: 2026-10-06T08:01:55Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/60
comments: 2
labels: chore, area:ci, area:workspace, effort:large, semver:patch
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-10-06T09:36:14.739Z
---

# [Issue 60]: [[CHORE] Upgrade to vigOS devkit 1.18.0 and move to direnv mode](https://github.com/exoma-ch/brother-printer/issues/60)

### Chore Type

CI / Build change

### Description

This repo was scaffolded from vigOS devkit `0.3.4` (commit 6921562, 2026-05-28)
and has never been upgraded. devkit `1.18.0` was released 2026-10-05, roughly 26
releases later — the gap spans the `1.0.0` Debian→Nix re-platform of the
devcontainer image.

`.vig-os` still carries only the legacy single-key manifest
(`DEVCONTAINER_VERSION=0.3.4`); the modern manifest resolves ~25 declarative
knobs. (`.devcontainer/.env=0.4.0-rc4` is gitignored local-only state left from
the ephemeral #57 release-candidate validation, not an upgrade.)

The upgrade also moves this repo off the devcontainer and onto the Nix
dev-shell, because the hardware test path needs it — see below.

### Acceptance Criteria

- [ ] `.vig-os` carries `DEVKIT_VERSION=1.18.0` and the resolved knob set
- [ ] `DEVKIT_MODE=direnv`; `.devcontainer/` removed, `flake.nix` + `.envrc` added
- [ ] `libusb` available to `pyusb` from the dev-shell, not from `apt`
- [ ] `just test-hardware` passes against a physically attached PT-E920BT
- [ ] Release-train `just` recipes still available (see Implementation Notes)
- [ ] `ci.yml` green, including the `scaffold-drift` and declared-language gates
- [ ] Container-era USB apparatus retired (udev rules, compose bind-mount, docs)
- [ ] `pre-commit run --all-files` green locally

### Implementation Notes

**Why `direnv` mode and not `devcontainer`.** `.devcontainer/scripts/post-create.sh`
was hand-edited to `apt-get install -y libusb-1.0-0`, because `pyusb` resolves
`libusb-1.0` through `ctypes.util.find_library`. The `1.18.0` image is
Nix-built: no `apt`, no `nix` CLI inside the image, and `libusb1` is not in
devkit's toolchain SSoT (`nix/devtools.nix`). There is no supported way to add
it to the container. A project `flake.nix` is the supported seam, and
devcontainer mode does not scaffold one.

`direnv` mode is also the better fit on its own terms for a USB device driver:
native host device access, no `/dev/bus/usb` bind-mount, no rootless-Podman
uid remapping, no udev workaround.

In `flake.nix` (preserved across upgrades once written):

```nix
extraPackages = pkgs: [ pkgs.libusb1 ];
```

plus a `shellHook` exporting `LD_LIBRARY_PATH` so `ctypes` can resolve it
(`mkProjectShell` accepts `shellHook`).

**Release recipes.** The release-train, `gh-*` and `worktree-*` `just` recipes
are defined only in `.devcontainer/justfile.gh` and
`.devcontainer/justfile.worktree`, which `direnv` mode does not ship. The
*workflows* are unaffected — all 17 are scaffolded in every mode and `1.18.0`
made the release set mode-aware — but the local dispatchers disappear. The
release recipes are thin `gh workflow run` wrappers (~107 lines), so vendor them
into `justfile.project` (preserved on upgrade). `justfile.worktree` is 418 lines
of real logic: drop it and declare the loss with
`DEVKIT_FEATURES_DISABLED=worktree`.

**Hand-edits to managed files.** Two are now fixed upstream and must be dropped
rather than re-applied: the `BASH_SOURCE[0]:-$0` guard in the lifecycle scripts,
and `entry: typos --force-exclude` in `.pre-commit-config.yaml`. One must be
re-applied by hand: the `.typos.toml` `[files] extend-exclude = ["*.bin"]`
exclusion for the binary protocol fixtures (precedent: 075a88b).

**Knobs.** `--org exoma-ch` and `--repo exoma-ch/brother-printer` must be passed
explicitly (the installer's org default is `vigOS`). `DEVKIT_TAG_PREFIX` must
stay empty — the existing `0.1.0`/`0.2.0` tags are bare and a `v` prefix would
fork the series. `DEVKIT_FLAKE_PIN_ADVANCE=true` with the `vigos` flake input
pinned to `1.18.0`. `DEVKIT_UPGRADE_EXCLUDE=docs/issues,docs/pull-requests`
keeps sync-issues churn out of future upgrade diffs. `DEVKIT_DRIFT_CHECK` and
`DEVKIT_AUTO_UPGRADE` stay at their enabled defaults.

**Python.** `mkProjectShell` now defaults to `python314`; this workspace
declares `requires-python = ">=3.12"`. Dependencies are `click`, `pillow`,
`pyusb` — expected to be fine, but verify rather than assume.

**Upgrade is report-first.** Run the installer with `--preview` before the real
pass; it prints the authoritative add/overwrite/preserve/delete report and exits
without touching the tree.

### Related Issues

- Blocked by #59 (the unsubstituted `OWNER/REPO` Renovate preset is fixed by the
  same `--repo` value this upgrade needs)
- Follows up #57 (ephemeral `0.4.0-rc4` validation, never merged)
- Upstream: devkit's `/devkit:release-*` plugin skills depend on `just` recipes
  that `direnv`/`bare` mode never ships

### Priority

Medium

### Changelog Category

Changed

---

# [Comment #1]() by [c-vigo]()

_Posted on October 6, 2026 at 07:09 AM_

## Hardware verification complete — 10/10

The two tape-consuming print tests have now been run against the physical
printer, closing the last gap in this issue's acceptance criteria.

```
test_print_chained_strip   PASSED
test_print_half_cut_strip  PASSED
2 passed in 19.34s
```

Device: `04f9:224b`, serial `000M5G726777`, bus 3 addr 18. Tape: 6 mm white
laminated, Ready. Four labels consumed across two jobs (each test prints a
two-label strip — one auto-cut chained, one half-cut).

Combined with the earlier run, the full `-m hardware` set passes:

| Area | Tests | Result |
|---|---|---|
| Connectivity | discover, open/close round trip | 2/2 |
| Status | request round trip, library API, CLI command, `discover --status` | 4/4 |
| Print guards | wrong width -> `TapeMismatchError`, wrong height -> `ImageScalingError` | 2/2 |
| Print | chained auto-cut strip, half-cut strip | 2/2 |

Run in two batches rather than one `just test-hardware` invocation, so the
non-destructive 8 could be confirmed before committing tape. The 19.34s runtime
is the printer actually feeding and cutting.

### Acceptance criteria

All met: `DEVKIT_VERSION=1.18.0`, `DEVKIT_MODE=direnv` with `.devcontainer/`
removed and `flake.nix`/`.envrc` in place, libusb reaching pyusb from the dev
shell, hardware suite green on real hardware, release-train recipes still
available (vendored into `justfile.project`), CI green including `Scaffold Drift`
and the declared-language gate, and `prek run --all-files` clean locally.

One criterion was met only in part, deliberately: "container-era USB apparatus
retired" covers the documentation and the compose bind-mount, but
`setup-usb.sh --devcontainer` and `99-brother-ptouch_devcontainer.rules` were
**kept**. On reading them they are generic rootless-container guidance for
*users* of the driver, not this repo's dev-environment plumbing, so removing
them would have deleted published capability. The container-specific parts that
referenced now-deleted paths are gone.

Note this issue will not auto-close on the `dev` merge — `Refs:` does not close,
and GitHub only auto-closes on a merge into the default branch. Close manually
or let the next release carry it.

Follow-up filed separately: `setup-usb.sh` cannot grant USB access on a NixOS
host, which also affects NixOS end users of the published driver.


---

# [Comment #2]() by [c-vigo]()

_Posted on October 6, 2026 at 08:01 AM_

Done — delivered in #61 (`90e3d40`), merged to `dev`.

All ten acceptance criteria are met, with the `-m hardware` suite verified
against the physical PT-E920BT; the detail is in the comment above. The one
partial item was deliberate: `setup-usb.sh --devcontainer` and
`99-brother-ptouch_devcontainer.rules` were **kept**, because they are generic
rootless-container guidance for *users* of the driver rather than this repo's
dev-environment plumbing — retiring them would have deleted published
capability.

Follow-ups this upgrade produced, all resolved or tracked where they belong:

- **#63** — `setup-usb.sh` could not grant USB access on a NixOS host, and the
  dev-shell documentation added here recommended a `TAG+="uaccess"` rule that is
  inert on NixOS. Fixed in #64; #63 closes with it.
- **Golden-image comparison** moved from byte-exact to structural (`c709500`),
  because the Nix dev shell and a hosted CI runner no longer share one
  interpreter and font stack by design.
- **Release-train and `gh` recipes** vendored into `justfile.project`, since
  devkit defines them only under `.devcontainer/`, which this mode does not
  ship. Reported upstream as vig-os/devkit#1823 and open there, not here.

Closing manually, as flagged above: `Refs:` does not close, and GitHub
auto-closes only on a merge into the default branch.

