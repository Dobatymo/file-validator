import sqlite3
from typing import Tuple

from genutility.sqlite import to_uri

from ..plug import Filetypes


@Filetypes.plugin(["sqlite", "sqlite3"])
class Sqlite:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            uri = to_uri(path, mode="ro")
            con = sqlite3.connect(uri, uri=True)
            res = con.execute("PRAGMA quick_check;")
            # res = con.execute("PRAGMA integrity_check;")
            message = "\n".join(row[0] for row in res.fetchall())
            if message == "ok":
                return (0, "")
            else:
                return (1, message)
        except sqlite3.DatabaseError as e:
            return (1, str(e))
        except sqlite3.OperationalError as e:
            return (1, str(e))
