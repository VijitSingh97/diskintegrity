# diskintegrity

**Is this disk worth keeping? Scan it and get a PASS/FAIL answer.**

[![CI](https://github.com/VijitSingh97/diskintegrity/actions/workflows/ci.yml/badge.svg)](https://github.com/VijitSingh97/diskintegrity/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

```console
$ diskintegrity disk6
Selected: DataTraveler 3.0 | 15.47 GB | /dev/disk6 | USB external | unknown media
Password:
Reading 100.0%  15.47 GB / 15.47 GB  78.4 MB/s  ETA 0m 00s

diskintegrity report
  Disk          DataTraveler 3.0 (/dev/disk6)
  Capacity      15.47 GB, 512-byte sectors
  Type          USB external, unknown media
  Test          full read-only surface scan
  Read speed    78.4 MB/s (3m 17s)
  Bad sectors   0
  Slow blocks   0 (4 MiB reads over 1 s)
  SMART         macOS: Not Supported; SMART not available over this connection
  Total time    3m 17s

RESULT: PASS
```

For **macOS 14 or later**. Works on any whole physical disk: internal or
external SSD, HDD, USB flash drive, or SD card.

## Modes

| Command | What it does | Time | Data |
| --- | --- | --- | --- |
| `diskintegrity --fast disk4` | SMART plus 64 sampled 4 MiB reads spread across the disk | seconds | untouched |
| `diskintegrity disk4` | Full surface scan: reads every sector, counts bad sectors and slow reads, plus SMART | size ÷ read speed | untouched |
| `diskintegrity --write disk4` | Writes a unique pattern to every block, reads it all back and compares, plus SMART | size ÷ write speed + size ÷ read speed | **erased** |

Omit the disk to choose from a numbered list. `disk4`, `/dev/disk4`, and
`/dev/rdisk4` are all accepted.

> **`--write` erases all data on the selected disk.** It accepts only external,
> writable disks that are not the startup disk, and asks you to type the exact
> device path first. Afterwards, reformat with
> `diskutil eraseDisk ExFAT NAME /dev/diskN`.

Only `--write` can catch **fake-capacity** drives and flash that silently drops
writes. Each block gets a unique pseudo-random pattern, so a drive that wraps
writes around past its real capacity fails verification, and the report gives
the approximate real size.

## Install with Homebrew

```sh
brew tap vijitsingh97/diskintegrity https://github.com/VijitSingh97/diskintegrity.git
brew install vijitsingh97/diskintegrity/diskintegrity
```

Homebrew installs Python 3.13, `smartmontools`, the command, and zsh
completion. macOS supplies `diskutil`, `sudo`, `dd`, and `caffeinate`.

`smartctl` adds power-on hours, temperature, SSD wear, NVMe media errors, and
reallocated, pending, and uncorrectable sector counts to the report. Without
it (for example, after `make install` from a clone), the report shows only
macOS's one-word SMART status.

## Usage

Run as your normal user. diskintegrity asks for your administrator password
through `sudo` because raw disk access needs it, and it keeps the Mac awake
until the test finishes. Press Ctrl-C to stop.

The report ends with:

- **Read speed / Write speed** and the time each phase took
- **Bad sectors**: unreadable sectors. Each failed 4 MiB read is rescanned
  sector by sector for an exact count. The count reads "at least" when that
  rescan exceeds 2 minutes.
- **Slow blocks**: 4 MiB reads that took over 1 second, a sign of weak sectors
  being retried
- **Verify** (`--write` only): whether every byte written read back intact
- **SMART**: macOS status plus smartctl details when available
- **RESULT: PASS** or **RESULT: FAIL**

### What counts as FAIL

- Any unreadable sector, any write error, or any byte that failed verification
- macOS SMART status `Failing`, or the smartctl overall health check failing
- NVMe critical warnings or media/data-integrity errors
- Pending or offline-uncorrectable sectors (SMART 197/198)
- The scan stopping early: 32 unreadable regions, or over 1 GB failing verification

Reallocated sectors (SMART 5), slow reads, and SSDs past their rated
endurance are listed as warnings and do not fail the disk by themselves.

Exit codes: `0` PASS, `3` FAIL, `1` error, `2` invalid arguments,
`130` cancelled.

## Limitations

- A read-only scan cannot detect fake capacity or failing writes. Use
  `--write` on a disk you can erase.
- SSDs return reads of trimmed (unused) space without touching flash, so a
  read scan reports high speed there and leaves unused cells untested.
- Most USB enclosures and flash drives do not pass SMART through on macOS.
  The report says so.
- The `--write` pattern generator runs at about 1.2 GB/s, which caps
  `--write` speed on very fast external NVMe drives.
- Drives that cache recent writes can mask a fault in the last few megabytes.
  For a stricter check, unplug and replug the disk, then run the default scan.

## Development

```sh
make check test
```

The tests mock `diskutil`, `sudo`, and `dd`. They never touch a real disk.
