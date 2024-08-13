import os
import unittest
from pathlib import Path

from filevalidator.plugins.archives import Archives
from filevalidator.plugins.images import Images
from filevalidator.plugins.orc import ORC
from filevalidator.plugins.parquet import Parquet
from filevalidator.plugins.pdf import PDF
from filevalidator.plugins.srt import SRT
from filevalidator.plugins.zip import Zip


def plugin_test(self, instance, name: str) -> None:
    for path in (Path("test-files") / name).glob("*"):
        with self.subTest(path=path):
            code, message = instance.validate(os.fspath(path), path.suffix[1:], strict=True)
            if path.name.startswith("good"):
                truth = 0
            elif path.name.startswith("bad"):
                truth = 1
            else:
                self.fail("test file didn't start with good or bad")

            self.assertEqual(truth, code, message)


class PluginsTest(unittest.TestCase):
    def test_pdf(self):
        plugin_test(self, PDF(), "pdf")

    def test_srt(self):
        plugin_test(self, SRT(), "srt")

    def test_images(self):
        plugin_test(self, Images(), "images")

    def test_parquet(self):
        plugin_test(self, Parquet(), "parquet")

    def test_orc(self):
        plugin_test(self, ORC(), "orc")

    def test_zip(self):
        plugin_test(self, Zip(), "zip")

    def test_archives(self):
        # plugin_test(self, Archives("UnRAR.exe", "7z.exe"), "archives")
        plugin_test(self, Archives("Rar.exe", "7z.exe"), "archives")
