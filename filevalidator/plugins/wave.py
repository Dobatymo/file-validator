import wave
from typing import Iterator

from genutility.iter import consume

from ..plug import Filetypes, ValidationResult


def iter_wave(wr: wave.Wave_read, chunksize: int = 10000) -> Iterator[bytes]:
    frames = wr.getnframes()
    frame_size = wr.getnchannels() * wr.getsampwidth()
    while frames > 0:
        n = min(frames, chunksize)
        data = wr.readframes(n)
        expected_size = n * frame_size
        if len(data) != expected_size:
            raise wave.Error(f"Truncated WAVE data: expected {expected_size} bytes, got {len(data)}")
        yield data
        frames -= n


@Filetypes.plugin(["wav"])
class WAVE:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            with wave.open(path, "rb") as wr:
                consume(iter_wave(wr))

            return (0, "")
        except wave.Error as e:
            return (1, str(e))
        except OSError:
            raise
        except Exception as e:
            return (1, str(e))
