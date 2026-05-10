import sqlite3
import wave
from pathlib import Path

TEST_FILES = Path("test-files")
GOOD_SQLITE = TEST_FILES / "sqlite" / "good.sqlite"
GOOD_WAVE = TEST_FILES / "wave" / "good.wav"
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


def main() -> None:
    create_sqlite(GOOD_SQLITE)
    create_wave(GOOD_WAVE)
    write_bytes(BAD_INVALID_UTF8_M3U8, bytes([0xFF, 0xFE, 0xFA]))
    write_bytes(
        BAD_CONTROL_CHARS_NFO,
        bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 65, 66, 67]),
    )


if __name__ == "__main__":
    main()
