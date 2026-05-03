"""
RemotePath — a POSIX path descriptor for remote filesystem operations.

Mimics the parts of pathlib.Path used by ConfigManager and project_scanner
(/ operator, .name, .stem, .suffix, .parent) but does NOT perform any I/O.
All I/O goes through LocalFileSystem or RemoteFileSystem.
"""


class RemotePath:
    """Immutable POSIX path descriptor.  Supports the / operator and common
    path properties.  Does not perform any filesystem operations itself."""

    __slots__ = ("_path",)

    def __init__(self, path: str):
        p = str(path).replace("\\", "/")
        while "//" in p:
            p = p.replace("//", "/")
        if len(p) > 1:
            p = p.rstrip("/")
        self._path = p

    # ── Path arithmetic ───────────────────────────────────────────────────────

    def __truediv__(self, other) -> "RemotePath":
        return RemotePath(self._path + "/" + str(other).lstrip("/"))

    # ── Representation ────────────────────────────────────────────────────────

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"RemotePath({self._path!r})"

    def __fspath__(self) -> str:
        return self._path

    # ── Comparison / hashing (needed for sorted(), set(), dict keys) ──────────

    def __eq__(self, other) -> bool:
        return self._path == str(other)

    def __hash__(self) -> int:
        return hash(self._path)

    def __lt__(self, other) -> bool:
        return self._path < str(other)

    def __le__(self, other) -> bool:
        return self._path <= str(other)

    # ── Path properties ───────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self._path.rsplit("/", 1)[-1]

    @property
    def stem(self) -> str:
        n = self.name
        dot = n.rfind(".")
        return n[:dot] if dot > 0 else n

    @property
    def suffix(self) -> str:
        n = self.name
        dot = n.rfind(".")
        return n[dot:] if dot > 0 else ""

    @property
    def parent(self) -> "RemotePath":
        idx = self._path.rfind("/")
        if idx <= 0:
            return RemotePath("/")
        return RemotePath(self._path[:idx])

    @property
    def parts(self) -> tuple:
        return tuple(p for p in self._path.split("/") if p)

    def is_absolute(self) -> bool:
        return self._path.startswith("/")

    def endswith(self, suffix: str) -> bool:
        return self._path.endswith(suffix)

    def resolve(self) -> "RemotePath":
        return self

    def relative_to(self, other) -> "RemotePath":
        base = str(other).rstrip("/")
        if self._path.startswith(base + "/"):
            return RemotePath(self._path[len(base) + 1:])
        if self._path == base:
            return RemotePath(".")
        raise ValueError(f"{self!r} is not relative to {other!r}")
