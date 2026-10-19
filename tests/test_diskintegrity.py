import contextlib
import io
from pathlib import Path
import runpy
import subprocess
import sys
import unittest
from unittest import mock


sys.dont_write_bytecode = True
LOADED = runpy.run_path(str(Path(__file__).parents[1] / "bin" / "diskintegrity"), run_name="diskintegrity_test")
DI = LOADED["main"].__globals__
Error = DI["Error"]
BLOCK = 4096
IO = b"dd: /dev/rdisk9: Input/output error\n"


class Sink(io.BytesIO):
    def close(self):
        pass


class FakeProc:
    def __init__(self, stdout=b"", stderr=b"", status=0):
        self.stdout = io.BufferedReader(io.BytesIO(stdout))
        self.stdin = Sink()
        self.stderr = io.BytesIO(stderr)
        self.status = status
        self.pid = 4242

    def wait(self):
        return self.status

    def communicate(self, timeout=None):
        return None, self.stderr.read()


def fake_device(data, bad=(), sector_errors=3):
    calls = []

    def dd(*operands, **kwargs):
        ops = dict(operand.split("=", 1) for operand in operands)
        calls.append(ops)
        if ops.get("conv") == "noerror,sync":
            return FakeProc(stderr=IO * sector_errors)
        size, skip, count = int(ops["bs"]), int(ops["skip"]), int(ops["count"])
        out = b""
        for index in range(skip, skip + count):
            if index in bad:
                return FakeProc(out, IO, 1)
            out += data[index * size:(index + 1) * size]
        return FakeProc(out)

    return dd, calls


def disk(identifier="disk9", **changes):
    result = {
        "DeviceIdentifier": identifier,
        "DeviceNode": "/dev/" + identifier,
        "WholeDisk": True,
        "VirtualOrPhysical": "Physical",
        "Internal": False,
        "OSInternalMedia": False,
        "RemovableMediaOrExternalDevice": True,
        "WritableMedia": True,
        "TotalSize": 4 * BLOCK,
        "DeviceBlockSize": 512,
        "MediaName": "Test USB",
        "BusProtocol": "USB",
        "SMARTStatus": "Not Supported",
    }
    result.update(changes)
    return result


class DiskIntegrityTests(unittest.TestCase):
    def setUp(self):
        for name in ("run", "Popen"):
            guard = mock.patch.object(
                subprocess, name, side_effect=AssertionError("external process execution is forbidden"))
            guard.start()
            self.addCleanup(guard.stop)
        patch = mock.patch.dict(DI, {"BLOCK": BLOCK})
        patch.start()
        self.addCleanup(patch.stop)
        quiet = contextlib.redirect_stderr(io.StringIO())
        quiet.__enter__()
        self.addCleanup(quiet.__exit__, None, None, None)

    def report(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            verdict = DI["report"](*args)
        return verdict, out.getvalue()

    def test_pattern_is_deterministic_and_position_dependent(self):
        pattern = DI["pattern"]
        self.assertEqual(pattern(b"s", 3, BLOCK), pattern(b"s", 3, BLOCK))
        self.assertNotEqual(pattern(b"s", 3, BLOCK), pattern(b"s", 4, BLOCK))
        self.assertNotEqual(pattern(b"s", 3, BLOCK), pattern(b"t", 3, BLOCK))
        self.assertEqual(len(pattern(b"s", 0, 100)), 100)

    def test_sample_spans_cover_start_and_partial_end(self):
        size = 100 * BLOCK + 512
        spans = DI["sample_spans"](size, 8)
        self.assertEqual(len(spans), 8)
        self.assertEqual(spans[0], (0, BLOCK))
        self.assertEqual(spans[-1], (100 * BLOCK, size))
        self.assertEqual(DI["sample_spans"](BLOCK, 64), [(0, BLOCK)])

    def test_full_read_resumes_after_bad_block_and_counts_sectors(self):
        data = bytes(4 * BLOCK)
        dd, calls = fake_device(data, bad={1})
        with mock.patch.dict(DI, {"dd": dd}):
            result = DI["read_pass"]("/dev/rdisk9", len(data), 512)
        self.assertEqual(result["bad"], [(BLOCK, 3, True)])
        self.assertEqual(result["bytes"], len(data))
        self.assertIsNone(result["stopped"])
        self.assertEqual([(c["bs"], c["skip"], c["count"]) for c in calls],
                         [(str(BLOCK), "0", "4"), ("512", "8", "8"), (str(BLOCK), "2", "2")])
        verdict, text = self.report(disk(), "full", 1, None, result, {}, None)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("3 in 1 region(s)", text)

    def test_clean_full_read_passes_with_scope_notes(self):
        data = bytes(4 * BLOCK)
        dd, _ = fake_device(data)
        with mock.patch.dict(DI, {"dd": dd}):
            result = DI["read_pass"]("/dev/rdisk9", len(data), 512)
        verdict, text = self.report(disk(), "full", 1, None, result, {}, "smartctl not installed")
        self.assertEqual(verdict, "PASS")
        self.assertIn("Bad sectors   0", text)
        self.assertIn("cannot detect fake capacity", text)

    def test_fast_mode_reads_only_samples(self):
        data = bytes(100 * BLOCK)
        dd, calls = fake_device(data)
        spans = DI["sample_spans"](len(data), 4)
        with mock.patch.dict(DI, {"dd": dd}):
            result = DI["read_pass"]("/dev/rdisk9", len(data), 512, None, spans)
        self.assertEqual(result["bytes"], 4 * BLOCK)
        self.assertEqual(len(calls), 4)
        verdict, text = self.report(disk(TotalSize=len(data)), "fast", 1, None, result, {}, None)
        self.assertEqual(verdict, "PASS")
        self.assertIn("Fast mode read only", text)

    def test_verify_flags_fake_capacity(self):
        seed = b"seed"
        pattern = DI["pattern"]
        data = pattern(seed, 0, BLOCK) + pattern(seed, 1, BLOCK) + bytes(2 * BLOCK)
        dd, _ = fake_device(data)
        with mock.patch.dict(DI, {"dd": dd}):
            result = DI["read_pass"]("/dev/rdisk9", len(data), 512, seed)
        self.assertEqual((result["first_mismatch"], result["mismatch"]), (2 * BLOCK, 2 * BLOCK))
        write = {"bytes": len(data), "seconds": 1, "error_at": None}
        verdict, text = self.report(disk(), "write", 2, write, result, {}, None)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("likely fake capacity", text)

    def test_read_failure_without_io_error_is_not_a_bad_sector(self):
        def dd(*operands, **kwargs):
            return FakeProc(b"", b"sudo: a password is required\n", 1)
        with mock.patch.dict(DI, {"dd": dd}), self.assertRaisesRegex(Error, "password is required"):
            DI["read_pass"]("/dev/rdisk9", 4 * BLOCK, 512)

    def test_read_stops_after_too_many_bad_regions(self):
        data = bytes(10 * BLOCK)
        dd, _ = fake_device(data, bad=set(range(10)))
        with mock.patch.dict(DI, {"dd": dd, "MAX_BAD_REGIONS": 3}):
            result = DI["read_pass"]("/dev/rdisk9", len(data), 512)
        self.assertEqual(len(result["bad"]), 3)
        self.assertIn("3 unreadable regions", result["stopped"])

    def test_write_pass_writes_pattern_and_reports_error_offset(self):
        procs = []

        def dd(*operands, **kwargs):
            procs.append(FakeProc())
            return procs[-1]
        with mock.patch.dict(DI, {"dd": dd}):
            result = DI["write_pass"]("/dev/rdisk9", 2 * BLOCK + 512, b"seed")
        self.assertEqual(result["error_at"], None)
        expected = b"".join(DI["pattern"](b"seed", i, n) for i, n in ((0, BLOCK), (1, BLOCK), (2, 512)))
        self.assertEqual(procs[0].stdin.getvalue(), expected)

        def failing(*operands, **kwargs):
            return FakeProc(stderr=IO + b"2+0 records out\n8192 bytes transferred in 1 secs\n", status=1)
        with mock.patch.dict(DI, {"dd": failing}):
            result = DI["write_pass"]("/dev/rdisk9", 4 * BLOCK, b"seed")
        self.assertEqual(result["error_at"], 8192)

    def test_smart_findings_nvme_and_ata(self):
        nvme = {"smart_status": {"passed": True}, "power_on_time": {"hours": 1200},
                "nvme_smart_health_information_log": {"percentage_used": 3, "media_errors": 2,
                                                      "critical_warning": 0, "data_units_written": 2}}
        facts, failures, warnings = DI["smart_findings"](nvme, "Verified")
        self.assertIn("1200 power-on hours", facts)
        self.assertIn("3% endurance used", facts)
        self.assertEqual(failures, ["2 NVMe media/data-integrity errors"])
        ata = {"smart_status": {"passed": True}, "ata_smart_attributes": {"table": [
            {"id": 5, "raw": {"value": 8}}, {"id": 197, "raw": {"value": 1}}, {"id": 198, "raw": {"value": 0}}]}}
        facts, failures, warnings = DI["smart_findings"](ata, "Verified")
        self.assertEqual(failures, ["SMART reports 1 pending sectors"])
        self.assertEqual(warnings, ["SMART reports 8 reallocated sectors"])
        self.assertEqual(DI["smart_findings"]({}, "Failing")[1], ["macOS reports SMART status Failing"])

    def test_write_candidates_exclude_internal_and_startup_disks(self):
        disks = {"disk0": disk("disk0", Internal=True, RemovableMediaOrExternalDevice=False),
                 "disk4": disk("disk4"), "disk5": disk("disk5"),
                 "disk6": disk("disk6", VirtualOrPhysical="Virtual")}
        listing = mock.Mock(return_value=list(disks))
        details = mock.Mock(side_effect=lambda device: disks.get(device[5:], {}))
        with mock.patch.dict(DI, {"listed_disks": listing, "info": details,
                                  "backing_disks": mock.Mock(return_value={"disk5"})}):
            self.assertEqual([d["DeviceIdentifier"] for d in DI["candidate_disks"](True)], ["disk4"])
            self.assertEqual([d["DeviceIdentifier"] for d in DI["candidate_disks"](False)],
                             ["disk0", "disk4", "disk5"])

    def test_choose_accepts_raw_and_dev_paths_and_rejects_others(self):
        disks = [disk("disk4")]
        for wanted in ("disk4", "/dev/disk4", "/dev/rdisk4", "rdisk4"):
            self.assertIs(DI["choose"](disks, wanted, False), disks[0])
        with self.assertRaisesRegex(Error, "not an eligible"):
            DI["choose"](disks, "disk0", True)

    def test_write_cancellation_never_runs_privileged_commands(self):
        command = mock.Mock()
        with mock.patch.dict(DI, {"candidate_disks": mock.Mock(return_value=[disk("disk4")]),
                                  "command": command}), \
                mock.patch.object(sys, "argv", ["diskintegrity", "--write", "disk4"]), \
                mock.patch.object(sys, "platform", "darwin"), \
                mock.patch("os.geteuid", return_value=501), \
                mock.patch.object(sys.stdin, "isatty", return_value=True), \
                mock.patch("builtins.input", return_value="/dev/disk5"), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(DI["main"](), 0)
        command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
