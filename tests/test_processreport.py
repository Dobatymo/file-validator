import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from filevalidator.processreport import (
    FileMetadataMismatch,
    resolve_report_path,
    trash_invalid,
    validate_file_metadata,
)
from filevalidator.report import ReportEntry, XmlReport


class ProcessReportTest(unittest.TestCase):
    def test_report_base_selects_scanned_file_instead_of_current_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scanned = root / "scanned"
            current = root / "current"
            scanned.mkdir()
            current.mkdir()
            scanned_path = scanned / "same.bin"
            current_path = current / "same.bin"
            scanned_path.write_bytes(b"scan")
            current_path.write_bytes(b"fake")
            stat = scanned_path.stat()
            os.utime(current_path, ns=(stat.st_atime_ns, stat.st_mtime_ns))

            report_path = root / "report.xml"
            with XmlReport(report_path, "report.xsl", base=os.fspath(scanned)) as report:
                report.write("same.bin", ReportEntry(1, "broken", stat.st_size, stat.st_mtime_ns))

            loaded = XmlReport.load_report(report_path)
            previous_cwd = Path.cwd()
            try:
                os.chdir(current)
                resolved = resolve_report_path("same.bin", report_base=loaded.base)
                with patch("filevalidator.processreport.send2trash") as send2trash:
                    trash_invalid(resolved, loaded["same.bin"])
            finally:
                os.chdir(previous_cwd)

        send2trash.assert_called_once_with(os.path.abspath(scanned_path))

    def test_override_base_replaces_report_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stored = root / "stored"
            override = root / "override"
            stored.mkdir()
            override.mkdir()

            resolved = resolve_report_path("sample.bin", report_base=os.fspath(stored), override_base=override)

        self.assertEqual(os.path.abspath(override / "sample.bin"), resolved)

    def test_relative_path_without_base_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not specify a base directory"):
            resolve_report_path("sample.bin")

    def test_size_change_prevents_action(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.bin"
            path.write_bytes(b"changed")
            entry = ReportEntry(1, "broken", 1, path.stat().st_mtime_ns)

            with patch("filevalidator.processreport.send2trash") as send2trash:
                with self.assertRaisesRegex(FileMetadataMismatch, "File size changed"):
                    trash_invalid(os.fspath(path), entry)

        send2trash.assert_not_called()

    def test_mtime_change_prevents_action_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.bin"
            path.write_bytes(b"same size")
            stat = path.stat()
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
            entry = ReportEntry(1, "broken", stat.st_size, stat.st_mtime_ns)

            with self.assertRaisesRegex(FileMetadataMismatch, "modification time changed"):
                validate_file_metadata(os.fspath(path), entry)

    def test_ignore_mtime_still_validates_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.bin"
            path.write_bytes(b"same size")
            stat = path.stat()
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
            entry = ReportEntry(1, "broken", stat.st_size, stat.st_mtime_ns)

            with patch("filevalidator.processreport.send2trash") as send2trash:
                acted = trash_invalid(os.fspath(path), entry, ignore_mtime=True)

        self.assertTrue(acted)
        send2trash.assert_called_once_with(os.fspath(path))

    def test_missing_mtime_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.bin"
            path.write_bytes(b"data")

            validate_file_metadata(os.fspath(path), ReportEntry(1, "broken", 4))


if __name__ == "__main__":
    unittest.main()
