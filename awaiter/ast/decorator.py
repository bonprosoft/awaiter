from __future__ import annotations

import ast
import inspect
import re
import types
from functools import partial, wraps
from typing import Callable, List, Optional, Union, overload

import astor

from .._types import TAsyncFunction
from .async_cps_transformer import transform_async_to_cps
from .decorator_remover import remove_decorator

LEADING_WS_PATTERN = re.compile(r"\s*")


def _remove_leading_whitespaces(source: str) -> str:
    # NOTE: Removing leading whitespace is required to parse code by `ast.parse` method
    n_whitespaces = 0
    whitespaces = LEADING_WS_PATTERN.search(source)
    if whitespaces is not None:
        n_whitespaces = whitespaces.end()

    ret: List[str] = []
    for line in source.splitlines(keepends=True):
        if len(line) > n_whitespaces:
            ret.append(line[n_whitespaces:])
        else:
            ret.append(line)

    return "".join(ret)


def _decorator_impl(
    func: TAsyncFunction,
    deco_name: str,
    frame: types.FrameType,
    debug: bool,
) -> TAsyncFunction:
    source = inspect.getsource(func)
    source = _remove_leading_whitespaces(source)

    module_ast = ast.parse(source)
    func_ast = transform_async_to_cps(module_ast)
    remove_decorator(func_ast, deco_name)

    if debug:
        print(astor.to_source(func_ast))

    globals = frame.f_globals.copy()
    globals.update(frame.f_locals)
    recompiled_source = compile(func_ast, "<awaiter>", "exec")
    exec(recompiled_source, globals)

    new_function: TAsyncFunction = globals[func.__name__]
    return new_function


@overload
def use_awaiter(
    func: TAsyncFunction,
) -> TAsyncFunction:
    ...


@overload
def use_awaiter(
    func: None = None,
    *,
    deco_name: str = ...,
    debug: bool = ...,
) -> Callable[[TAsyncFunction], TAsyncFunction]:
    ...


def use_awaiter(
    func: Optional[TAsyncFunction] = None,
    *,
    deco_name: str = "use_awaiter",
    debug: bool = False,
) -> Union[TAsyncFunction, partial[TAsyncFunction]]:
    if func is None:
        return partial(use_awaiter, deco_name=deco_name, debug=debug)

    frame = inspect.currentframe()
    assert frame is not None
    frame = frame.f_back
    assert frame is not None
    return wraps(func)(_decorator_impl(func, deco_name, frame, debug))
