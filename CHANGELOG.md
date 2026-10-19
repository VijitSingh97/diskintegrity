# Changelog

## 0.0.1 — 2026-10-19

- Full read-only surface scan of any physical disk: internal or external SSD, HDD, USB, or SD.
- `--fast` mode: SMART plus 64 sampled reads spread across the disk.
- `--write` mode: destructive write-and-verify test of external disks that detects fake capacity and lost writes.
- Exact bad-sector counts for unreadable regions, slow-read detection, and SMART health via smartmontools.
- Final report with read/write speed, time taken, bad sectors, SMART details, and a PASS/FAIL verdict.
- Startup-disk protection, exact device-path confirmation, and disk recheck before any write.
