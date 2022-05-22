from __future__ import annotations

import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor
from typing import Any, Callable, Coroutine, Generator, Generic, Optional, TypeVar

T = TypeVar("T")
TResult = TypeVar("TResult")


class _ExecutorAwaitable:
    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    def __await__(self) -> Generator[None, None, Any]:
        raise RuntimeError(
            "Do not call __await__ of this object. "
            "Make sure that your function has a @use_awaiter decorator"
        )

    async def __awaiter__(
        self, continuation: Callable[[], Coroutine[Any, Any, TResult]]
    ) -> TResult:
        future = self._executor.submit(lambda: asyncio.run(continuation()))
        return await asyncio.wrap_future(future)


def dispatch_to_executor(executor: ThreadPoolExecutor) -> _ExecutorAwaitable:
    return _ExecutorAwaitable(executor)


class _EventLoopAwaitable:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def __await__(self) -> Generator[None, None, Any]:
        raise RuntimeError(
            "Do not call __await__ of this object. "
            "Make sure that your function has a @use_awaiter decorator"
        )

    async def __awaiter__(
        self, continuation: Callable[[], Coroutine[Any, Any, TResult]]
    ) -> TResult:
        running_loop = asyncio.get_running_loop()
        if running_loop is self._loop:
            return await continuation()
        else:
            future = asyncio.run_coroutine_threadsafe(continuation(), self._loop)
            return await asyncio.wrap_future(future)


def dispatch_to_loop(loop: asyncio.AbstractEventLoop) -> _EventLoopAwaitable:
    return _EventLoopAwaitable(loop)


class _DetachAwaitable(Generic[T]):
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task[T]] = None

    def __await__(self) -> Generator[None, None, Any]:
        raise RuntimeError(
            "Do not call __await__ of this object. "
            "Make sure that your function has a @use_awaiter decorator"
        )

    @property
    def task(self) -> Optional[asyncio.Task[T]]:
        return self._task

    async def __awaiter__(
        self, continuation: Callable[[], Coroutine[Any, Any, T]]
    ) -> None:
        assert self._task is None
        running_loop = asyncio.get_running_loop()
        self._task = running_loop.create_task(continuation())


def detach() -> _DetachAwaitable[Any]:
    return _DetachAwaitable()
