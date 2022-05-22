import asyncio
from typing import Any, Awaitable, Callable, Generator, Optional

import pytest

from awaiter import use_awaiter


class _TestAwaitable:
    def __init__(self) -> None:
        self.called = False
        self.continuation: Optional[Callable[[], Awaitable[Any]]] = None

    def __await__(self) -> Generator[None, None, Any]:
        raise AssertionError()

    async def __awaiter__(self, continuation: Callable[[], Awaitable[Any]]) -> Any:
        self.called = True
        self.continuation = continuation
        return await continuation()


@use_awaiter(debug=True)
async def _global_func(awaitable: _TestAwaitable, value: int) -> int:
    await asyncio.sleep(0.1)
    await awaitable
    value += 1
    return value


async def _global_func2(awaitable: _TestAwaitable) -> None:
    await awaitable


@pytest.mark.asyncio
async def test_global_function() -> None:
    awaitable = _TestAwaitable()
    assert await _global_func(awaitable, 10) == 11
    assert awaitable.called
    assert awaitable.continuation is not None
    assert await awaitable.continuation() == 12

    with pytest.raises(AssertionError):
        await _global_func2(awaitable)


@pytest.mark.asyncio
async def test_local_function() -> None:
    @use_awaiter(debug=True)
    async def _local_func(awaitable: _TestAwaitable, value: int) -> int:
        await asyncio.sleep(0.1)
        await awaitable
        value += 1
        return value

    awaitable = _TestAwaitable()
    assert await _local_func(awaitable, 10) == 11
    assert awaitable.called
    assert awaitable.continuation is not None
    assert await awaitable.continuation() == 12


@pytest.mark.asyncio
async def test_method() -> None:
    class Foo:
        def __init__(self) -> None:
            self.value = 10

        @use_awaiter(debug=True)
        async def method(self, awaitable: _TestAwaitable, value: int) -> int:
            await asyncio.sleep(0.1)
            await awaitable
            self.value += value + 1
            return self.value

    awaitable = _TestAwaitable()
    instance = Foo()
    assert await instance.method(awaitable, 10) == 21
    assert awaitable.called
    assert awaitable.continuation is not None
    assert await awaitable.continuation() == 32
