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
BAD_INVALID_UTF8_M3U8 = TEST_FILES / "m3u8" / "bad.invalid-utf8.m3u8"
BAD_CONTROL_CHARS_NFO = TEST_FILES / "nfo" / "bad.control-chars.nfo"


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


def main() -> None:
    create_sqlite(GOOD_SQLITE)
    create_wave(GOOD_WAVE)
    create_truncated_wave(GOOD_WAVE, BAD_TRUNCATED_WAVE)
    create_animated_gifs(GOOD_ANIMATED_GIF, BAD_TRUNCATED_ANIMATED_GIF)
    create_pdf_with_corrupt_stream(BAD_PDF_STREAM)
    write_bytes(BAD_INVALID_UTF8_M3U8, bytes([0xFF, 0xFE, 0xFA]))
    write_bytes(
        BAD_CONTROL_CHARS_NFO,
        bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 65, 66, 67]),
    )


if __name__ == "__main__":
    main()
