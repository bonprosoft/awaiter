import sys
from typing import Any, Awaitable, Callable, Coroutine, TypeVar

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable


T = TypeVar("T")


@runtime_checkable
class Awaiter(Protocol):
    def __awaiter__(
        self, continuation: Callable[[], Coroutine[Any, Any, T]]
    ) -> Awaitable[Any]:
        pass
