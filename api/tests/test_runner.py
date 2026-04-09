import asyncio
import pytest
from pathlib import Path
from services.runner import RunnerService, RunnerError

FIXTURE_SCRIPT = str(Path(__file__).parent / "fixtures" / "echo_script.py")


@pytest.fixture
def runner():
    svc = RunnerService()
    yield svc
    svc._runs.clear()
    svc._active_run_id = None


async def test_start_run_returns_run_id(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    assert run_id is not None
    await asyncio.sleep(0.5)


async def test_buffer_contains_output(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)
    state = runner.get_state(run_id)
    assert any("line one" in line for line in state.buffer)


async def test_done_flag_set_after_exit(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)
    assert runner.get_state(run_id).done is True


async def test_exit_code_zero_on_success(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)
    assert runner.get_state(run_id).exit_code == 0


async def test_exit_code_nonzero_on_failure(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT, "1"])
    await asyncio.sleep(0.5)
    assert runner.get_state(run_id).exit_code == 1


async def test_concurrency_rejected_when_busy(runner):
    await runner.start(["python", FIXTURE_SCRIPT])
    with pytest.raises(RunnerError, match="already in progress"):
        await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)


async def test_on_complete_callback_called(runner):
    called_with = []

    async def cb(run_id, state):
        called_with.append((run_id, state.exit_code))

    run_id = await runner.start(["python", FIXTURE_SCRIPT], on_complete=cb)
    await asyncio.sleep(0.5)
    assert len(called_with) == 1
    assert called_with[0] == (run_id, 0)
