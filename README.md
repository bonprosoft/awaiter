# awaiter

Bring C# Awaitable/Awaiter concept to Python asyncio

:warning: This library is not ready for use.

## Example

We provide some utility methods to demonstrate some motivating examples of this library:
- `awaiter.dispatch_to_executor`
- `awaiter.dispatch_to_loop`
- `awaiter.detach`

```py
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from awaiter import dispatch_to_executor, use_awaiter

executor = ThreadPoolExecutor()

@use_awaiter
async def method() -> int:
    value: int = 10
    original_ident: int = threading.get_ident()
    await asyncio.sleep(0.1)

    # Change current thread to executor!!!
    await dispatch_to_executor(executor)
    assert original_ident != threading.get_ident()

    value += 5
    await asyncio.sleep(0.1)

    return value

print(asyncio.run(method()))  # 15
```

You can customize the `await` behavior by defining a custom awaitable object with `__awaiter__` method like the following:
```py
class ExecutorAwaitable:
    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    def __await__(self) -> Generator[None, None, Any]:
        # Required to pass the static-type checking
        raise RuntimeError()

    async def __awaiter__(
        self, continuation: Callable[[], Coroutine[Any, Any, TResult]]
    ) -> TResult:
        future = self._executor.submit(lambda: asyncio.run(continuation()))
        return await asyncio.wrap_future(future)
```


## How it works

Python uses the generator mechanism to realize a coroutine object,
which means the only caller (`asyncio.EventLoop`) of coroutines can configure the execution.
At the moment, there is no way for a coroutine to tell event loop to schedule it on a different loop.

This library manipulates the abstract syntax tree (AST) of a given function
to transform code into a sort of the Continuation-passing style.
Such conversions allows us to introduce `awaitable / awaiter` pattern like the one in C#:
- https://devblogs.microsoft.com/premier-developer/dissecting-the-async-methods-in-c/

The above example is converted into the following code at runtime:
```py
async def method() ->int:
    value: int
    original_ident: int

    async def _method_continuation_0():
        nonlocal value, original_ident
        value = 10
        original_ident = threading.get_ident()
        _method_continuation_0_awaitable = asyncio.sleep(0.1)
        _method_continuation_0_awaiter = getattr(
            _method_continuation_0_awaitable, '__awaiter__', None)
        if _method_continuation_0_awaiter is None:
            await _method_continuation_0_awaitable
            return await _method_continuation_1()
        else:
            return await _method_continuation_0_awaiter(_method_continuation_1)

    async def _method_continuation_1():
        nonlocal value, original_ident
        _method_continuation_1_awaitable = dispatch_to_executor(executor)
        _method_continuation_1_awaiter = getattr(
            _method_continuation_1_awaitable, '__awaiter__', None)
        if _method_continuation_1_awaiter is None:
            await _method_continuation_1_awaitable
            return await _method_continuation_2()
        else:
            return await _method_continuation_1_awaiter(_method_continuation_2)

    async def _method_continuation_2():
        nonlocal value, original_ident
        assert original_ident != threading.get_ident()
        value += 5
        _method_continuation_2_awaitable = asyncio.sleep(0.1)
        _method_continuation_2_awaiter = getattr(
            _method_continuation_2_awaitable, '__awaiter__', None)
        if _method_continuation_2_awaiter is None:
            await _method_continuation_2_awaitable
            return await _method_continuation_3()
        else:
            return await _method_continuation_2_awaiter(_method_continuation_3)

    async def _method_continuation_3():
        nonlocal value, original_ident
        return value
    return await _method_continuation_0()
```

You can check the conversion result by setting `debug=True` option in the `use_awaiter` decorator.
