import sqlite3
import wave
import zlib
from pathlib import Path

TEST_FILES = Path("test-files")
GOOD_SQLITE = TEST_FILES / "sqlite" / "good.sqlite"
GOOD_WAVE = TEST_FILES / "wave" / "good.wav"
BAD_TRUNCATED_WAVE = TEST_FILES / "wave" / "bad.truncated-data.wav"
GOOD_ANIMATED_GIF = TEST_FILES / "images" / "good.animated.gif"
BAD_TRUNCATED_ANIMATED_GIF = TEST_FILES / "images" / "bad.truncated-later-frame.gif"
BAD_PDF_STREAM = TEST_FILES / "pdf" / "bad.stream.badtest.pdf"
GOOD_JSONLZ4 = TEST_FILES / "jsonlz4" / "good.jsonlz4"
BAD_JSONLZ4_MAGIC = TEST_FILES / "jsonlz4" / "bad.magic.jsonlz4"
BAD_JSONLZ4_JSON = TEST_FILES / "jsonlz4" / "bad.json.jsonlz4"
BAD_JSONLZ4_TRUNCATED = TEST_FILES / "jsonlz4" / "bad.truncated.jsonlz4"
BAD_INVALID_UTF8_M3U8 = TEST_FILES / "m3u8" / "bad.invalid-utf8.m3u8"
BAD_CONTROL_CHARS_NFO = TEST_FILES / "nfo" / "bad.control-chars.nfo"
GOOD_VOBSUB_IDX = TEST_FILES / "vobsub" / "good.idx"
BAD_VOBSUB_IDX = TEST_FILES / "vobsub" / "bad.timestamp.idx"
GOOD_VOBSUB_SUB = TEST_FILES / "vobsub" / "good.sub"
BAD_VOBSUB_SUB = TEST_FILES / "vobsub" / "bad.not-vobsub.sub"
BAD_TRUNCATED_VOBSUB_SUB = TEST_FILES / "vobsub" / "bad.truncated.sub"


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def create_sqlite(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    con = sqlite3.connect(path)
    try:
        con.execute("create table example(id integer primary key, name text)")
        con.execute("insert into example(name) values (?)", ("ok",))
        con.commit()
    finally:
        con.close()


def create_wave(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as fw:
        fw.setnchannels(1)
        fw.setsampwidth(1)
        fw.setframerate(8000)
        fw.writeframes(bytes([128] * 16))


def create_truncated_wave(good_path: Path, bad_path: Path) -> None:
    data = good_path.read_bytes()
    write_bytes(bad_path, data[:-8])


def create_animated_gifs(good_path: Path, bad_path: Path) -> None:
    from PIL import Image

    good_path.parent.mkdir(parents=True, exist_ok=True)
    frames = [Image.new("RGB", (16, 16), color) for color in ("red", "green", "blue")]
    frames[0].save(good_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    write_bytes(bad_path, good_path.read_bytes()[:-30])


def create_pdf_with_corrupt_stream(path: Path) -> None:
    stream = bytearray(zlib.compress(b"BT 72 720 Td (Hello) Tj ET"))
    stream[0] ^= 0xFF
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> /Contents 4 0 R >>",
        b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream) + bytes(stream) + b"\nendstream",
    ]

    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode("ascii"))
        data.extend(obj)
        data.extend(b"\nendobj\n")

    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    write_bytes(path, bytes(data))


def create_jsonlz4_files() -> None:
    import lz4.block

    magic = b"mozLz40\0"
    good = magic + lz4.block.compress(b'{"ok": true}')
    write_bytes(GOOD_JSONLZ4, good)
    write_bytes(BAD_JSONLZ4_MAGIC, b"badmagic" + good[len(magic) :])
    write_bytes(BAD_JSONLZ4_JSON, magic + lz4.block.compress(b"not json"))
    write_bytes(BAD_JSONLZ4_TRUNCATED, good[:-3])


def create_vobsub_files() -> None:
    write_bytes(
        GOOD_VOBSUB_IDX,
        b"""# VobSub index file, v7 (do not modify this line!)
size: 720x480
palette: 000000, ffffff, 808080, c0c0c0, ff0000, 00ff00, 0000ff, ffff00, 00ffff, ff00ff, 800000, 008000, 000080, 808000, 008080, 800080
langidx: 0
id: en, index: 0
delay: +00:00:00:000
timestamp: -00:00:00:080, filepos: 000000000
timestamp: 00:00:01:000, filepos: 000001000
\0""",
    )
    write_bytes(
        BAD_VOBSUB_IDX,
        b"""# VobSub index file, v7 (do not modify this line!)
size: 720x480
timestamp: broken, filepos: 000000000
""",
    )
    pack = b"\x00\x00\x01\xba\x44\x00\x04\x00\x04\x01\x01\x89\xc3\xf8"
    write_bytes(GOOD_VOBSUB_SUB, pack + b"\x00\x00\x01\xbd\x00\x04\x20\x00\x00\x00")
    write_bytes(BAD_VOBSUB_SUB, b"not a vobsub sub file")
    write_bytes(BAD_TRUNCATED_VOBSUB_SUB, pack + b"\x00\x00\x01\xbd\x00\x04\x20")


def main() -> None:
    create_sqlite(GOOD_SQLITE)
    create_wave(GOOD_WAVE)
    create_truncated_wave(GOOD_WAVE, BAD_TRUNCATED_WAVE)
    create_animated_gifs(GOOD_ANIMATED_GIF, BAD_TRUNCATED_ANIMATED_GIF)
    create_pdf_with_corrupt_stream(BAD_PDF_STREAM)
    create_jsonlz4_files()
    create_vobsub_files()
    write_bytes(BAD_INVALID_UTF8_M3U8, bytes([0xFF, 0xFE, 0xFA]))
    write_bytes(
        BAD_CONTROL_CHARS_NFO,
        bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 65, 66, 67]),
    )


if __name__ == "__main__":
    main()
