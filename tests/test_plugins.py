import os
import unittest
from pathlib import Path

from filevalidator.plug import PluginError
from filevalidator.plugins.archives import Archives
from filevalidator.plugins.cue import CUE
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
            code, message = instance.validate(os.fspath(path), path.suffix[1:], strict=True)
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
    def test_pdf(self):
        plugin_test(self, PDF(), "pdf")

    def test_cue(self):
        plugin_test(self, CUE(), "cue")

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
