"""Shared I/O utilities for the anonymization pipeline."""

import contextlib
import os
import tempfile
from pathlib import Path


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically via write-to-tmp + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        Path(tmp_path).replace(path)
    except BaseException:
        with contextlib.suppress(OSError):
            Path(tmp_path).unlink()
        raise
