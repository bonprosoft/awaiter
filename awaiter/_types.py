import ast
from typing import Any, Callable, Coroutine, TypeVar

TASTNode = TypeVar("TASTNode", bound=ast.AST)
TAsyncFunction = TypeVar(
    "TAsyncFunction", bound=Callable[..., Coroutine[Any, Any, Any]]
)
