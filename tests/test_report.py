import os
import tempfile
import unittest
from pathlib import Path

from filevalidator.report import (
    MAX_XML_MESSAGE_BYTES,
    TRUNCATION_MARKER,
    JsonReport,
    ReportEntry,
    XmlReport,
    _decode_xml10_text,
    _encode_xml10_text,
    _truncate_xml_message,
)


class XmlReportTest(unittest.TestCase):
    def test_base_round_trip(self):
        base = os.path.abspath("test-files")

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.xml"
            with XmlReport(report_path, "report.xsl", base=base):
                pass

            loaded = XmlReport.load_report(report_path)

        self.assertEqual(base, loaded.base)

    def test_invalid_xml_characters_round_trip(self):
        path = "bad\x01name.pdf"
        message = "PDF starts with '\u069e*\x01H', but literal \\x01 remains unambiguous"

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.xml"
            with XmlReport(report_path, "report.xsl") as report:
                report.write(path, ReportEntry(code=1, message=message, size=123))

            raw = report_path.read_bytes()
            loaded = XmlReport.load_report(report_path)

        self.assertNotIn(b"\x01", raw)
        self.assertIn(b'path-encoding="backslash-xml10"', raw)
        self.assertIn(b'message-encoding="backslash-xml10"', raw)
        self.assertIn("\u069e".encode(), raw)
        self.assertIn(b"PDF starts with", raw)
        self.assertEqual({path: ReportEntry(1, message, 123)}, loaded)

    def test_file_metadata_round_trip(self):
        expected = ReportEntry(1, "broken", 123, 456)
        expected_without_mtime = ReportEntry(1, "broken", 123)

        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "report.xml"
            with XmlReport(xml_path, "report.xsl") as report:
                report.write("sample.bin", expected)
                report.write("sample-no-mtime.bin", expected_without_mtime)

            json_path = Path(tmpdir) / "report.json"
            with JsonReport(json_path) as report:
                report.write("sample.bin", expected)
                report.write("sample-no-mtime.bin", expected_without_mtime)

            xml_loaded = XmlReport.load_report(xml_path)
            json_loaded = JsonReport.load_report(json_path)

        expected_report = {"sample.bin": expected, "sample-no-mtime.bin": expected_without_mtime}
        self.assertEqual(expected_report, xml_loaded)
        self.assertEqual(expected_report, json_loaded)

    def test_missing_size_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "report.xml"
            xml_path.write_text(
                '<?xml version="1.0" encoding="utf-8"?><report><file code="1" path="sample.bin">broken</file></report>',
                encoding="utf-8",
            )
            json_path = Path(tmpdir) / "report.json"
            json_path.write_text('{"path":"sample.bin","code":1,"message":"broken"}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "does not contain the file size"):
                XmlReport.load_report(xml_path)
            with self.assertRaisesRegex(ValueError, "does not contain the file size"):
                JsonReport.load_report(json_path)

    def test_large_message_is_truncated_below_parser_limit(self):
        message = "a" * (MAX_XML_MESSAGE_BYTES + 100)

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.xml"
            with XmlReport(report_path, "report.xsl") as report:
                report.write("sample.bin", ReportEntry(code=1, message=message, size=123))

            loaded_message = XmlReport.load_report(report_path)["sample.bin"].message

        self.assertEqual(MAX_XML_MESSAGE_BYTES, len(loaded_message.encode("utf-8")))
        self.assertIn(TRUNCATION_MARKER, loaded_message)
        beginning, end = loaded_message.split(TRUNCATION_MARKER)
        self.assertTrue(message.startswith(beginning))
        self.assertTrue(message.endswith(end))

    def test_escaped_message_truncation_respects_encoded_limit(self):
        message = "\x01" * 100
        truncated = _truncate_xml_message(message, max_bytes=101)
        encoded, encoding = _encode_xml10_text(truncated)

        self.assertLessEqual(len(encoded.encode("utf-8")), 101)
        self.assertEqual(truncated, _decode_xml10_text(encoded, encoding))
        beginning, end = truncated.split(TRUNCATION_MARKER)
        self.assertTrue(message.startswith(beginning))
        self.assertTrue(message.endswith(end))

    def test_duplicate_encoded_paths_are_rejected_after_decoding(self):
        path = "bad\x01name.pdf"

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.xml"
            with XmlReport(report_path, "report.xsl") as report:
                report.write(path, ReportEntry(code=1, message="first", size=123))
                report.write(path, ReportEntry(code=1, message="second", size=123))

            with self.assertRaises(ValueError):
                XmlReport.load_report(report_path)


if __name__ == "__main__":
    unittest.main()
