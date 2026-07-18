from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class TrackingStateStore:
    """
    Файл для связи UI-процесса и background service.

    Оба процесса читают один tracking_state.json.
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> dict[str, Any] | None:
        if not self._path.exists():
            return None

        try:
            return json.loads(
                self._path.read_text(encoding="utf-8")
            )
        except (
            OSError,
            TypeError,
            json.JSONDecodeError,
        ):
            return None

    def begin(
        self,
        *,
        run_id: int,
        database_path: Path | str,
        min_time: int,
        min_distance: float,
    ) -> None:
        self.write(
            {
                "active": True,
                "run_id": int(run_id),
                "database_path": str(database_path),
                "state_path": str(self._path),
                "min_time": int(min_time),
                "min_distance": float(min_distance),
            }
        )

    def request_stop(self, run_id: int) -> None:
        state = self.read()

        if state is None:
            return

        if int(state.get("run_id", -1)) != run_id:
            return

        state["active"] = False
        self.write(state)

    def write(self, state: dict[str, Any]) -> None:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self._path.with_name(
            f"{self._path.name}.{os.getpid()}.tmp"
        )

        temporary_path.write_text(
            json.dumps(
                state,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary_path,
            self._path,
        )

    def clear(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass