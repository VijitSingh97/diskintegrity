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

For **macOS 14 or later** and **Ubuntu 22.04 or later**. Works on whole physical
disks: internal or external SSDs, HDDs, USB flash drives, and SD cards.

## Modes

| Command | What it does | Time | Data |
| --- | --- | --- | --- |
| `diskintegrity --fast disk4` | SMART plus 64 sampled 4 MiB reads spread across the disk | seconds | untouched |
| `diskintegrity disk4` | Full surface scan: reads every sector, counts bad sectors and slow reads, plus SMART | size ÷ read speed | untouched |
| `diskintegrity --write disk4` | Writes a unique pattern to every block, reads it all back and compares, plus SMART | size ÷ write speed + size ÷ read speed | **erased** |

Omit the disk to choose from a numbered list. macOS accepts `disk4`,
`/dev/disk4`, or `/dev/rdisk4`. Linux accepts a whole block device such as
`sda`, `/dev/sda`, or `/dev/nvme0n1`.

> **`--write` erases all data on the selected disk.** It accepts only external,
> writable disks that are not in use, and asks you to type the exact device
> path first. On macOS it excludes the startup disk. On Linux it excludes every
> disk with a mounted filesystem anywhere below it, including partitions and
> LVM logical volumes, then checks the device again immediately before writing.

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

## Install with apt

On Ubuntu 22.04 or newer and Debian 12 or newer, use the signed APT repository:

```sh
sudo apt update
sudo apt install ca-certificates curl
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://vijitsingh97.github.io/diskintegrity/diskintegrity.asc \
  | sudo tee /etc/apt/keyrings/diskintegrity.asc >/dev/null
sudo tee /etc/apt/sources.list.d/diskintegrity.sources >/dev/null <<'EOF'
Types: deb
URIs: https://vijitsingh97.github.io/diskintegrity/
Suites: ./
Signed-By: /etc/apt/keyrings/diskintegrity.asc
EOF
sudo apt update
sudo apt install diskintegrity
```

The signing key fingerprint is
`35C6 2BA9 B0F7 5F04 9EC1 C247 2AB8 B7C6 F47C E1B7`. `Signed-By` scopes
the key to this repository. The architecture-independent package installs
Python 3, `smartmontools`, `util-linux`, `sudo`, and Zsh completion.
Future releases arrive through `sudo apt upgrade`.

## Install from source on Ubuntu

Ubuntu needs Python 3, `util-linux` for `lsblk`, `coreutils` for `dd`, and
`sudo`. `smartmontools` is optional but recommended for SMART health data.

```sh
sudo apt update
sudo apt install make python3 util-linux coreutils sudo smartmontools
sudo make install
```

For a quick read-only production check, run as your normal user:

```sh
diskintegrity --fast /dev/nvme0n1
```

Replace the path with the whole disk shown by `lsblk --paths`. Fast mode reads
64 samples spread across the device and does not open a write path.

`smartctl` adds power-on hours, temperature, SSD wear, NVMe media errors, and
reallocated, pending, and uncorrectable sector counts to the report. Without
it, Linux reports that SMART is unavailable; macOS still reports its one-word
SMART status.

## Usage

Run as your normal user. diskintegrity asks for your administrator password
through `sudo` because raw disk access needs it. On macOS it keeps the computer
awake until the test finishes. Press Ctrl-C to stop.

The report ends with:

- **Read speed / Write speed** and the time each phase took
- **Bad sectors**: unreadable sectors. Each failed 4 MiB read is rescanned
  sector by sector for an exact count. The count reads "at least" when that
  rescan exceeds 2 minutes.
- **Slow blocks**: 4 MiB reads that took over 1 second, a sign of weak sectors
  being retried
- **Verify** (`--write` only): whether every byte written read back intact
- **SMART**: smartctl details when available, plus macOS status on macOS
- **RESULT: PASS** or **RESULT: FAIL**

### What counts as FAIL

- Any unreadable sector, any write error, or any byte that failed verification
- macOS SMART status `Failing`, or the smartctl overall health check failing
- SMART prefail thresholds or failed self-tests reported by smartctl
- NVMe critical warnings or media/data-integrity errors
- Pending or offline-uncorrectable sectors (SMART 197/198)
- The scan stopping early: 32 unreadable regions, or over 1 GB failing verification

Reallocated sectors (SMART 5), slow reads, and SSDs past their rated
endurance are listed as warnings and do not fail the disk by themselves.
Missing or incomplete SMART data and historical error logs also produce warnings.

Exit codes: `0` PASS, `3` FAIL, `1` error, `2` invalid arguments,
`130` cancelled.

## Limitations

- A read-only scan cannot detect fake capacity or failing writes. Use
  `--write` on a disk you can erase.
- SSDs return reads of trimmed (unused) space without touching flash, so a
  read scan reports high speed there and leaves unused cells untested.
- Many USB enclosures and flash drives do not pass SMART through. The report
  says when SMART is unsupported or unavailable.
- The `--write` pattern generator runs at about 1.2 GB/s, which caps
  `--write` speed on very fast external NVMe drives.
- Drives that cache recent writes can mask a fault in the last few megabytes.
  For a stricter check, unplug and replug the disk, then run the default scan.

## Development

```sh
make check test
```

The tests mock `diskutil`, `lsblk`, `sudo`, and `dd`. They never touch a real
disk.
