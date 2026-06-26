import os
import sys
import tempfile
import unittest
from pathlib import Path

from filevalidator.limits import CommandError, CommandTimeout, check_file_size, run_command, timeout_result
from filevalidator.plug import PluginError
from filevalidator.plugins.archives import Archives
from filevalidator.plugins.cue import CUE
from filevalidator.plugins.executable import Executable
from filevalidator.plugins.images import Images
from filevalidator.plugins.ini import INI
from filevalidator.plugins.iso import Iso
from filevalidator.plugins.json import JSON
from filevalidator.plugins.m3u import M3U8
from filevalidator.plugins.nfo import NFO
from filevalidator.plugins.orc import ORC
from filevalidator.plugins.parquet import Parquet
from filevalidator.plugins.pdf import PDF
from filevalidator.plugins.python import Python
from filevalidator.plugins.raw_images import RawImages
from filevalidator.plugins.sfv import SFV
from filevalidator.plugins.sqlite import Sqlite
from filevalidator.plugins.srt import SRT
from filevalidator.plugins.toml import TOML
from filevalidator.plugins.videos import Videos
from filevalidator.plugins.wave import WAVE
from filevalidator.plugins.xml import XML
from filevalidator.plugins.yaml import YAML
from filevalidator.plugins.zip import Zip


def plugin_test(self, instance, name: str) -> None:
    for path in (Path("test-files") / name).glob("*"):
        with self.subTest(path=path):
            code, message = instance.validate(os.fspath(path), path.suffix[1:], path.stat().st_size, strict=True)
            if path.name.startswith("good"):
                truth = 0
            elif path.name.startswith("bad"):
                truth = 1
            else:
                self.fail("test file didn't start with good or bad")

            if path.stem.endswith("badtest"):
                # self.skipTest("The validator doesn't work correctly for this test") # this should only skip the subtest, but doesn't
                print(f"Skipping {path.name}")
                continue

            self.assertEqual(truth, code, message)


class PluginsTest(unittest.TestCase):
    def test_cue(self):
        plugin_test(self, CUE(), "cue")

    def test_executable(self):
        plugin_test(self, Executable(), "executable")

    def test_pdf(self):
        plugin_test(self, PDF(), "pdf")

    def test_pdf_qpdf_detects_corrupt_stream(self):
        instance = PDF(qpdf_binary=os.environ.get("QPDF_BINARY"))
        if instance.qpdf_binary is None:
            self.skipTest("qpdf is not available")

        path = Path("test-files/pdf/bad.stream.badtest.pdf")
        code, message = instance.validate(os.fspath(path), "pdf", path.stat().st_size)

        self.assertEqual(1, code, message)

    def test_pdf_falls_back_to_pypdf(self):
        instance = PDF(qpdf_binary="file-validator-definitely-missing-qpdf")
        path = Path("test-files/pdf/good.pdf")

        code, message = instance.validate(os.fspath(path), "pdf", path.stat().st_size)

        self.assertEqual(0, code, message)

    def test_srt(self):
        plugin_test(self, SRT(), "srt")

    def test_images(self):
        plugin_test(self, Images(), "images")

    def test_ini(self):
        plugin_test(self, INI(), "ini")

    def test_json(self):
        plugin_test(self, JSON(), "json")

    def test_m3u8(self):
        plugin_test(self, M3U8(), "m3u8")

    def test_nfo(self):
        plugin_test(self, NFO(), "nfo")

    def test_parquet(self):
        plugin_test(self, Parquet(), "parquet")

    def test_orc(self):
        plugin_test(self, ORC(), "orc")

    def test_toml(self):
        plugin_test(self, TOML(), "toml")

    def test_yaml(self):
        plugin_test(self, YAML(), "yaml")

    def test_iso(self):
        plugin_test(self, Iso(), "iso")

    def test_zip(self):
        plugin_test(self, Zip(), "zip")

    def test_raw_images(self):
        plugin_test(self, RawImages(), "raw_images")

    def test_python(self):
        plugin_test(self, Python(), "python")

    def test_sfv(self):
        plugin_test(self, SFV(), "sfv")

    def test_sqlite(self):
        plugin_test(self, Sqlite(), "sqlite")

    def test_wave(self):
        plugin_test(self, WAVE(), "wave")

    def test_xml(self):
        plugin_test(self, XML(), "xml")

    def test_videos(self):
        try:
            plugin_test(self, Videos(), "videos")
        except PluginError as e:
            self.skipTest(f"Skipping due to: {e}")

    def test_archives(self):
        try:
            # plugin_test(self, Archives("UnRAR.exe", "7z.exe"), "archives")
            plugin_test(self, Archives("Rar.exe", "7z.exe"), "archives")
        except PluginError as e:
            self.skipTest(f"Skipping due to: {e}")

    def test_archive_error_identifies_missing_executable(self):
        instance = object.__new__(Archives)
        instance.timeout = 1
        instance.unrar_binary = Path("rar")
        instance.sevenzip_binary = None
        instance.unrar_binary_config = "rar"
        instance.sevenzip_binary_config = "missing-7z"

        with self.assertRaisesRegex(PluginError, "extension '7z'.*missing-7z"):
            instance.validate("sample.7z", "7z", 0)

    def test_archive_error_identifies_unimplemented_format(self):
        instance = object.__new__(Archives)
        instance.timeout = 1
        instance.unrar_binary = Path("rar")
        instance.sevenzip_binary = Path("7z")
        instance.unrar_binary_config = "rar"
        instance.sevenzip_binary_config = "7z"

        with self.assertRaisesRegex(PluginError, "extension 'wim'.*not implemented"):
            instance.validate("sample.wim", "wim", 0)


class ResourceLimitsTest(unittest.TestCase):
    def test_oversize_returns_unable_to_validate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.json"
            path.write_text("{}", encoding="utf-8")

            code, message = JSON(max_file_size=1).validate(os.fspath(path), "json", path.stat().st_size)

        self.assertEqual(-1, code)
        self.assertIn("File too large", message)

    def test_extension_size_override_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.json"
            path.write_text("{}", encoding="utf-8")

            result = check_file_size(path.stat().st_size, "json", 1, {"json": 10})

        self.assertIsNone(result)

    def test_none_size_limit_disables_size_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.json"
            path.write_text("{}", encoding="utf-8")

            result = check_file_size(path.stat().st_size, "json", None)

        self.assertIsNone(result)

    def test_subprocess_timeout_maps_to_unable_to_validate(self):
        cmd = [sys.executable, "-c", "import time; time.sleep(1)"]

        with self.assertRaises(CommandTimeout) as cm:
            run_command(cmd, 0.01)

        code, message = timeout_result(cmd, 0.01, cm.exception.output)
        self.assertEqual(-1, code)
        self.assertIn("Timed out", message)

    def test_subprocess_failure_output_is_decoded_text(self):
        cmd = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([0xff])); raise SystemExit(1)"]

        with self.assertRaises(CommandError) as cm:
            run_command(cmd, 1)

        self.assertIsInstance(cm.exception.output, str)
        self.assertEqual("\xff", cm.exception.output)
