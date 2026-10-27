# Changelog

## 0.0.2 — 2026-10-27

- Add Ubuntu 22.04 and 24.04 and Debian 12 support.
- Add signed APT packages and release automation for Linux installation.
- Preserve SMART failure flags when device data is incomplete, and warn about unavailable health data.
- Honor passwordless sudo rules when starting and renewing disk access.

## 0.0.1 — 2026-10-19

- Full read-only surface scan of any physical disk: internal or external SSD, HDD, USB, or SD.
- `--fast` mode: SMART plus 64 sampled reads spread across the disk.
- `--write` mode: destructive write-and-verify test of external disks that detects fake capacity and lost writes.
- Exact bad-sector counts for unreadable regions, slow-read detection, and SMART health via smartmontools.
- Final report with read/write speed, time taken, bad sectors, SMART details, and a PASS/FAIL verdict.
- Startup-disk protection, exact device-path confirmation, and disk recheck before any write.
