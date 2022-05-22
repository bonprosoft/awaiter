import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from awaiter import dispatch_to_executor, use_awaiter


@use_awaiter(debug=True)
async def method(executor: ThreadPoolExecutor) -> int:
    value: int = 10
    original_ident: int = threading.get_ident()
    await asyncio.sleep(0.1)

    # Change current thread to executor
    await dispatch_to_executor(executor)
    assert original_ident != threading.get_ident()

    value += 5
    await asyncio.sleep(0.1)

    return value


with ThreadPoolExecutor() as executor:
    print(asyncio.run(method(executor)))  # 15
