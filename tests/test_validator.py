import os
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from filevalidator.plug import Filetypes
from filevalidator.report import ReportEntry, XmlReport
from filevalidator.validator import get_relative_report_base, load_resume_info, validate_paths


class CapturingReport:
    def __init__(self) -> None:
        self.rows: List[Tuple[str, ReportEntry]] = []

    def write(self, path: str, entry: ReportEntry) -> None:
        self.rows.append((path, entry))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class ValidatorTest(unittest.TestCase):
    def test_relative_reports_reject_multiple_input_directories(self):
        with self.assertRaisesRegex(ValueError, "exactly one input directory"):
            get_relative_report_base([Path("first"), Path("second")], relative=True)

    def test_global_os_error_returns_unable_to_validate(self):
        class MissingFilePlugin:
            def validate(self, path: str, ext: str, file_size: int, strict: bool = True):
                raise FileNotFoundError(2, "No such file or directory", path)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.boom"
            path.write_text("exists for scan", encoding="utf-8")
            report = CapturingReport()

            plugins = Filetypes.PLUGINS.copy()
            try:
                Filetypes.PLUGINS[MissingFilePlugin] = {"boom"}
                validate_paths([Path(tmpdir)], report, only={"boom"})
            finally:
                Filetypes.PLUGINS.clear()
                Filetypes.PLUGINS.update(plugins)

        self.assertEqual(1, len(report.rows))
        reported_path, entry = report.rows[0]
        normalized_reported_path = reported_path[4:] if reported_path.startswith("\\\\?\\") else reported_path
        self.assertEqual(os.fspath(path), normalized_reported_path)
        self.assertEqual(-1, entry.code)
        self.assertIn("No such file or directory", entry.message)
        self.assertEqual(len("exists for scan"), entry.size)
        self.assertIsInstance(entry.mtime_ns, int)

    def test_scan_records_metadata_from_before_validation(self):
        received_sizes = []

        class MutatingPlugin:
            def validate(self, path: str, ext: str, file_size: int, strict: bool = True):
                received_sizes.append(file_size)
                with open(path, "a", encoding="utf-8") as fw:
                    fw.write("changed")
                return (0, "")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.mutate"
            path.write_text("original", encoding="utf-8")
            original_stat = path.stat()
            report = CapturingReport()

            plugins = Filetypes.PLUGINS.copy()
            try:
                Filetypes.PLUGINS[MutatingPlugin] = {"mutate"}
                validate_paths([Path(tmpdir)], report, only={"mutate"})
            finally:
                Filetypes.PLUGINS.clear()
                Filetypes.PLUGINS.update(plugins)

        self.assertEqual(1, len(report.rows))
        _reported_path, entry = report.rows[0]
        self.assertEqual(0, entry.code)
        self.assertEqual("", entry.message)
        self.assertEqual(original_stat.st_size, entry.size)
        self.assertEqual(original_stat.st_mtime_ns, entry.mtime_ns)
        self.assertEqual([original_stat.st_size], received_sizes)

    def test_stale_resume_entry_is_revalidated(self):
        class InvalidPlugin:
            def validate(self, path: str, ext: str, file_size: int, strict: bool = True):
                return (1, "new validation result")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.resume"
            path.write_text("current", encoding="utf-8")
            report_path = Path(tmpdir) / "resume.xml"
            with XmlReport(report_path, "report.xsl") as report:
                report.write(path.name, ReportEntry(code=0, message="stale result", size=1, mtime_ns=1))

            output = CapturingReport()
            plugins = Filetypes.PLUGINS.copy()
            try:
                Filetypes.PLUGINS[InvalidPlugin] = {"resume"}
                validate_paths(
                    [Path(tmpdir)],
                    output,
                    relative=True,
                    only={"resume"},
                    resume_info=load_resume_info(report_path, [Path(tmpdir)], True),
                )
            finally:
                Filetypes.PLUGINS.clear()
                Filetypes.PLUGINS.update(plugins)

        self.assertEqual(1, len(output.rows))
        _reported_path, entry = output.rows[0]
        self.assertEqual(1, entry.code)
        self.assertEqual("new validation result", entry.message)

    def test_relative_resume_rejects_different_report_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            old_base = root / "old"
            new_base = root / "new"
            old_base.mkdir()
            new_base.mkdir()
            report_path = root / "resume.xml"
            with XmlReport(report_path, "report.xsl", base=os.fspath(old_base)) as report:
                report.write("sample.resume", ReportEntry(code=0, message="old result", size=4, mtime_ns=1))

            with self.assertRaisesRegex(ValueError, "--allow-resume-base-change"):
                load_resume_info(report_path, [new_base], True)

    def test_relative_resume_can_allow_different_report_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            old_base = root / "old"
            new_base = root / "new"
            old_base.mkdir()
            new_base.mkdir()
            path = new_base / "sample.resume"
            path.write_text("same", encoding="utf-8")
            stat = path.stat()
            report_path = root / "resume.xml"
            with XmlReport(report_path, "report.xsl", base=os.fspath(old_base)) as report:
                report.write(
                    "sample.resume",
                    ReportEntry(code=0, message="old result", size=stat.st_size, mtime_ns=stat.st_mtime_ns),
                )

            output = CapturingReport()
            validate_paths(
                [new_base],
                output,
                relative=True,
                only={"resume"},
                resume_info=load_resume_info(report_path, [new_base], True, allow_resume_base_change=True),
            )

        self.assertEqual([("sample.resume", ReportEntry(0, "old result", stat.st_size, stat.st_mtime_ns))], output.rows)


if __name__ == "__main__":
    unittest.main()
