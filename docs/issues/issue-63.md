---
type: issue
state: closed
created: 2026-10-06T07:09:53Z
updated: 2026-10-06T08:02:14Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/63
comments: 2
labels: feature, area:docs, area:transport, effort:small, semver:minor
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-10-06T09:36:14.172Z
---

# [Issue 63]: [[FEATURE] setup-usb.sh: support NixOS hosts (read-only /etc/udev/rules.d, no plugdev, no distro package manager)](https://github.com/exoma-ch/brother-printer/issues/63)

### Description

`packaging/scripts/setup-usb.sh` cannot grant non-root USB access on a NixOS
host. It is the repo's answer to "how do I make the printer reachable", exposed
as `just setup-usb` and documented as the quick-setup path in
`docs/install/linux-usb.md`, but on NixOS every step it performs is
inapplicable.

### Problem Statement

Two hard blockers:

1. **libusb installation.** The script dispatches on `apt-get`, `dnf`, `pacman`
   and `zypper`. NixOS has none of them, so it falls through to a warning and
   installs nothing. (For this repo's contributors that part is moot — the dev
   shell supplies `libusb`, see #60 — but an end user following the published
   docs gets no guidance.)
2. **udev rule installation.** The script copies into
   `UDEV_DIR=/etc/udev/rules.d`, which on NixOS is a read-only symlink into
   `/nix/store`. The copy cannot succeed, and it should not: durable udev rules
   on NixOS live in the system configuration, which a driver's install script
   has no business editing.

It also creates and joins a `plugdev` group, which does not exist on a stock
NixOS system and cannot be persistently created from outside the system
configuration.

Observed while verifying #60 on a NixOS host. The device enumerates but cannot
be opened:

```
usb.core.find(...)  -> device found
d.set_configuration() -> USBError [Errno 13] Access denied (insufficient permissions)
```

because the node comes up `root:lp 0664` from NixOS's own `70-printers.rules`
and the invoking user is not in `lp`. The failure mode is exactly the one
`docs/install/linux-usb.md` describes, but the script offered to fix it cannot.

### Proposed Solution

Detect NixOS (`/etc/NIXOS`, or `ID=nixos` in `/etc/os-release`) and take a
different path rather than warning and proceeding:

1. **Skip the package-manager step** with an explanatory note — on NixOS
   `libusb` comes from the dev shell or the user's own profile, not from the
   script.
2. **Offer a one-off grant.** Locate the connected `04f9:224b` device via sysfs
   (`/sys/bus/usb/devices/*/{idVendor,idProduct,busnum,devnum}`), derive
   `/dev/bus/usb/<bus>/<dev>`, and `chmod` it after confirming. This is the one
   thing the script genuinely can do, it needs no rebuild, and it saves the user
   hand-deriving a path that changes on every replug. It is still privileged, so
   it still prompts — that is unavoidable and fine.
3. **Print the declarative rule** for persistence, rather than pretending to
   install it:

   ```nix
   services.udev.extraRules = ''
     SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="224b", TAG+="uaccess"
   '';
   ```

   `TAG+="uaccess"` grants the locally logged-in user access through
   systemd-logind, so no `plugdev` group is needed at all — which also sidesteps
   blocker 3.

A `--one-off` / `--no-rules` style flag would make the chmod path scriptable and
testable without a NixOS host, and the existing `--no-libusb` flag already
covers part of step 1.

### Alternatives Considered

- **Leave it and document only.** The dev-shell section of
  `docs/install/linux-usb.md` already documents the manual NixOS path (added in
  #60), so contributors are unblocked. Rejected as the whole answer because the
  **end-user** Quick setup and Prerequisites sections still point at the script,
  and a NixOS user of the published driver gets a warning and no working path.
- **Have the script edit the system configuration.** Rejected outright: a driver
  install script must not write to a host's NixOS configuration.
- **Ship a NixOS module / flake output** exposing the udev rules package, so a
  user adds the repo as a flake input and gets the rule declaratively. Cleaner
  long-term and composes with `services.udev.packages`, but a much larger
  surface than this issue needs. Worth its own discussion if demand appears.

### Additional Context

`99-brother-ptouch.rules` already exists and is exactly the right content; the
problem is purely how it gets installed. The script's own
`--devcontainer` mode writes `99-brother-ptouch_devcontainer.rules` with
`MODE="0666"` for rootless containers and is unaffected.

### Impact

Contributors on NixOS and end users on NixOS. No impact on the supported
distributions, which keep the current path unchanged.

### Changelog Category

Added

---

# [Comment #1]() by [c-vigo]()

_Posted on October 6, 2026 at 07:22 AM_

## Correction: `TAG+="uaccess"` does not work on NixOS

This issue's proposed solution (step 3) says to print a `TAG+="uaccess"` rule as
the declarative path for NixOS. **That advice is wrong**, and the same wrong
advice is already merged into `docs/install/linux-usb.md` via #61. Found by
implementing it on a real NixOS host and watching it fail.

`uaccess` is the modern mechanism — systemd-logind puts an ACL for the active
local session's user on the device node, so no group membership is needed — and
it is what this repo's own `packaging/udev/99-brother-ptouch.rules` already
carries. On NixOS the tag is applied but **nothing consumes it**:

```
$ udevadm info --query=all --name=/dev/bus/usb/003/019 | grep TAGS
E: TAGS=:systemd:seat:uaccess:
E: CURRENT_TAGS=:systemd:seat:uaccess:

$ getfacl /dev/bus/usb/003/019
user::rw-
group::rw-
other::r--          # no user:<name>:rw- — the ACL was never applied
```

The `RUN{builtin}+="uaccess"` that actually applies the ACL lives in systemd's
`71-seat.rules` and `73-seat-late.rules`. Both ship in the systemd store output
but neither is part of the rule set NixOS assembles into `/etc/udev/rules.d` —
confirmed absent from all 57 files there, and `/etc/udev/rules.d` is the only
rules directory present on the system. So the tag is inert, and no amount of
file-ordering fixes it.

### What works instead

Set `GROUP`/`MODE` directly and add the user to that group:

```nix
services.udev.extraRules = ''
  SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="224b", GROUP="lp", MODE="0660"
'';
users.users.<name>.extraGroups = [ "lp" ];
```

`GROUP` is worth setting explicitly rather than leaning on the `root:lp` the
node already arrives with: nothing in the assembled rule set grants that, so it
comes from udev's built-in printer-class default and is not a contract to depend
on. Group membership takes effect at login, so this needs a fresh session, not
just a `nixos-rebuild switch`.

`MODE="0666"` is the zero-friction alternative (no group, no re-login) and is
what this repo's `--devcontainer` rule already does, but it exposes the device
to every local process.

### Scope added to this issue

Two things now, same root cause:

1. The original ask — teach `setup-usb.sh` about NixOS. Its "print the
   declarative rule" step must emit the `GROUP`/`MODE` form, not `uaccess`.
2. Correct `docs/install/linux-usb.md`, whose dev-shell section currently
   recommends the `uaccess` rule and would leave a NixOS reader with a live rule
   and no access — the same dead end hit here.

Worth checking whether `uaccess` is similarly inert on other distributions
before recommending it anywhere, since `99-brother-ptouch.rules` relies on it
alongside `GROUP="plugdev"`. On a distro that ships the seat rules it is fine;
the `plugdev` fallback is probably what has been carrying it.


---

# [Comment #2]() by [c-vigo]()

_Posted on October 6, 2026 at 08:02 AM_

Fixed in #64 (`bfddb35`), merged to `dev`.

`setup-usb.sh` now detects NixOS (`/etc/NIXOS`, or `ID=nixos` in
`/etc/os-release`) and takes all three steps proposed here: it skips the
package-manager step with a pointer to the dev shell or the user's own profile,
locates the connected `04f9:224b` through sysfs to derive
`/dev/bus/usb/<bus>/<dev>` and offers to `chmod` it after confirming, and prints
the rule to declare in the system configuration rather than pretending to
install it. The new `--one-off` flag (plus `-y`/`--yes` for unattended use)
makes that grant the whole run, on any distribution — not just NixOS.

**One deviation from the proposal, following the finding in the comment above:**
the printed rule grants through `GROUP="lp"` + `MODE="0660"` with a matching
`users.users.<you>.extraGroups`, **not** `TAG+="uaccess"`. A test asserts on the
rule line itself, so a `uaccess` regression fails rather than shipping. The
`docs/install/linux-usb.md` text flagged in scope item 2 is corrected the same
way, and the new `## NixOS hosts` section additionally records that the
`services.udev.packages` route needs `users.groups.plugdev` plus membership,
since the shipped rule grants `GROUP="plugdev"` and stock NixOS has no such
group.

Verified on a real NixOS 26.05 host with the printer attached: the default run
and `--one-off` both resolve `/dev/bus/usb/003/019` (matching sysfs `3-2`,
`busnum=3`, `devnum=19`) and change nothing without confirmation. The `sudo
chmod` itself is exercised only by the tests, since it needs an interactive
password. Those tests drive the real script through overridable `SETUP_USB_*`
path hooks with stub executables ahead on `PATH`, so both the NixOS and the
conventional path run end to end on a non-NixOS CI runner — `Tests` is green on
#64, and the conventional path has regression coverage it did not have before.

Not done, by design: the NixOS module / flake output exposing the rules package,
which this issue parks as a larger surface worth its own discussion. Also left
open deliberately — whether `99-brother-ptouch.rules` should carry
`TAG+="uaccess"` at all on conventional distributions, given `GROUP="plugdev"`
is what has been carrying it regardless. The rule file now documents that
distinction instead of settling it; worth its own issue if it ever bites.

