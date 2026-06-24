from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from typing import Any


class JsonMemory:
    """Memoria key-value persistente con scrittura atomica, adatta a demo e piccoli agenti."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            raise RuntimeError(f"Memoria non leggibile: {self.path}") from exc

    def _write(self, data: dict[str, Any]) -> None:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
            prefix=f".{self.path.name}.",
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2, sort_keys=True)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = Path(tmp.name)
        temp_path.replace(self.path)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._read().get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def append(self, key: str, value: Any) -> None:
        with self._lock:
            data = self._read()
            items = data.setdefault(key, [])
            if not isinstance(items, list):
                raise TypeError(f"La chiave {key!r} non contiene una lista")
            items.append(value)
            self._write(data)
