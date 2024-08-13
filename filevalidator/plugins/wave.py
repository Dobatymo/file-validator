import wave
from typing import Iterator, Tuple

from genutility.iter import consume

from ..plug import Filetypes


def iter_wave(wr: wave.Wave_read, chunksize: int = 10000) -> Iterator[bytes]:
    frames = wr.getnframes()
    while frames > 0:
        n = min(frames, chunksize)
        yield wr.readframes(n)
        frames -= chunksize


@Filetypes.plugin(["wav"])
class WAVE:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with wave.open(path, "rb") as wr:
                consume(iter_wave(wr))

            return (0, "")
        except wave.Error as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
