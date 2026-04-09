from __future__ import annotations
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional

_MAX_BUFFER = 10_000


class RunnerError(Exception):
    pass


@dataclass
class RunState:
    run_id: str
    run_type: str = "unknown"
    buffer: list[str] = field(default_factory=list)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    done: bool = False
    exit_code: Optional[int] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None


OnComplete = Callable[[str, RunState], Coroutine[Any, Any, None]]


class RunnerService:
    def __init__(self) -> None:
        self._runs: dict[str, RunState] = {}
        self._active_run_id: Optional[str] = None

    def get_state(self, run_id: str) -> Optional[RunState]:
        return self._runs.get(run_id)

    @property
    def is_busy(self) -> bool:
        return self._active_run_id is not None

    async def start(
        self,
        cmd: list[str],
        cwd: Optional[str] = None,
        run_type: str = "unknown",
        on_complete: Optional[OnComplete] = None,
    ) -> str:
        if self.is_busy:
            raise RunnerError("A run is already in progress")
        run_id = str(uuid.uuid4())
        state = RunState(run_id=run_id, run_type=run_type)
        self._runs[run_id] = state
        self._active_run_id = run_id
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        asyncio.create_task(self._read(run_id, process, on_complete))
        return run_id

    async def _read(
        self,
        run_id: str,
        process: asyncio.subprocess.Process,
        on_complete: Optional[OnComplete],
    ) -> None:
        state = self._runs[run_id]
        assert process.stdout is not None
        async for raw in process.stdout:
            line = raw.decode()
            if len(state.buffer) < _MAX_BUFFER:
                state.buffer.append(line)
            await state.queue.put({"type": "log", "line": line})
        await process.wait()
        state.exit_code = process.returncode
        state.done = True
        state.ended_at = datetime.now(timezone.utc)
        sentinel = (
            {"type": "done"}
            if process.returncode == 0
            else {"type": "error", "message": f"Process exited with code {process.returncode}"}
        )
        await state.queue.put(sentinel)
        self._active_run_id = None
        if on_complete is not None:
            await on_complete(run_id, state)


# Singleton used across routers
runner = RunnerService()
