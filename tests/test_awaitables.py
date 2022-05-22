import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

import asyncx
import pytest

from awaiter import detach, dispatch_to_executor, dispatch_to_loop, use_awaiter


@pytest.fixture
def executor() -> Iterator[ThreadPoolExecutor]:
    with ThreadPoolExecutor() as executor:
        yield executor


@pytest.fixture
def loop() -> Iterator[asyncx.EventLoopThread]:
    with asyncx.EventLoopThread() as thread:
        yield thread


@pytest.mark.asyncio
async def test_dispatch_to_executor(executor: ThreadPoolExecutor) -> None:
    @use_awaiter
    async def method(arg: int) -> int:
        value = 10
        loop_ident = threading.get_ident()
        await asyncio.sleep(0.1)
        assert loop_ident == threading.get_ident()

        await dispatch_to_executor(executor)
        executor_ident = threading.get_ident()
        assert executor_ident != loop_ident

        value += 1
        value += arg
        await asyncio.sleep(0.1)
        assert executor_ident == threading.get_ident()

        return value

    assert await method(5) == 16


@pytest.mark.asyncio
async def test_dispatch_to_loop(loop: asyncx.EventLoopThread) -> None:
    @use_awaiter
    async def method(arg: int) -> int:
        value = 10
        original_ident = threading.get_ident()
        await asyncio.sleep(0.1)
        assert original_ident == threading.get_ident()

        await dispatch_to_loop(loop.loop)
        dispatched_ident = threading.get_ident()
        assert dispatched_ident != original_ident

        value += 1
        value += arg
        await asyncio.sleep(0.1)
        assert dispatched_ident == threading.get_ident()

        return value

    assert await method(5) == 16


@pytest.mark.asyncio
async def test_detach(loop: asyncx.EventLoopThread) -> None:
    detach_obj = detach()
    caller_awaited = asyncio.Event()
    callee_completed = asyncio.Event()

    @use_awaiter
    async def method() -> None:
        original_ident = threading.get_ident()
        await asyncio.sleep(0.1)

        assert original_ident == threading.get_ident()
        await detach_obj
        assert original_ident == threading.get_ident()

        await asyncio.sleep(0.1)
        assert caller_awaited.is_set()

        await asyncio.sleep(0.1)
        assert original_ident == threading.get_ident()
        callee_completed.set()

    assert await method() is None
    caller_awaited.set()

    assert detach_obj.task is not None
    await detach_obj.task
    assert callee_completed.is_set()
