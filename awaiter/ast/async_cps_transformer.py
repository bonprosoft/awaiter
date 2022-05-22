import ast
from itertools import count
from typing import List, Sequence

from .._types import TASTNode
from .local_variable_visitor import LocalVariableVisitor


def _create_async_function(name: str, body: Sequence[ast.stmt]) -> ast.AsyncFunctionDef:
    assert len(body) > 0
    return ast.AsyncFunctionDef(
        name=name,
        args=ast.arguments(
            posonlyargs=[],
            args=[],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
            vararg=None,
            kwarg=None,
        ),
        body=body,
        decorator_list=[],
        lineno=body[0].lineno,
        col_offset=body[0].col_offset,
    )


def _is_await_expr_statement(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Await)


def _check_and_call_awaiter_statement(
    name: str, expr: ast.Await, continuation_id: str
) -> List[ast.stmt]:
    awaitable_id = f"{name}_awaitable"
    awaiter_id = f"{name}_awaiter"

    awaitable_obj = ast.Name(
        id=awaitable_id,
        lineno=expr.lineno,
        col_offset=expr.col_offset,
        ctx=ast.Store(),
    )
    ret: List[ast.stmt] = []
    ret.append(
        ast.Assign(
            targets=[awaitable_obj],
            value=expr.value,
            lineno=expr.lineno,
            col_offset=expr.col_offset,
        )
    )
    code = f"""{awaiter_id} = getattr({awaitable_id}, '__awaiter__', None)
if {awaiter_id} is None:
    await {awaitable_id}
    return await {continuation_id}()
else:
    return await {awaiter_id}({continuation_id})"""
    node: ast.Module = ast.parse(code)
    ret.extend(node.body)

    return ret


def _split_function_into_continuations(
    function_name_base: str,
    statements: Sequence[ast.stmt],
    local_vars: Sequence[str],
) -> List[ast.AsyncFunctionDef]:
    continuations: List[ast.AsyncFunctionDef] = []
    i = 0
    counter = count()
    n_statements = len(statements)

    while i < n_statements:
        j = 0
        while i + j < n_statements:
            statement = statements[i + j]
            j += 1
            if _is_await_expr_statement(statement):
                break

        # should -1 at the end
        fragment = list(statements[i : i + j])
        i += j
        assert len(fragment) > 0
        if len(local_vars) > 0:
            non_local = ast.Nonlocal(
                names=list(local_vars),
                lineno=fragment[0].lineno,
                col_offset=fragment[0].col_offset,
            )
            fragment.insert(0, non_local)
        continuations.append(
            _create_async_function(
                f"_{function_name_base}_continuation_{next(counter)}",
                fragment,
            )
        )
    return continuations


def _chain_continuations(
    src: ast.AsyncFunctionDef,
    to: ast.AsyncFunctionDef,
) -> None:
    last_statement = src.body[-1]
    if _is_await_expr_statement(last_statement):
        assert isinstance(last_statement, ast.Expr)
        assert isinstance(last_statement.value, ast.Await)
        src.body.pop(-1)
        src.body.extend(
            _check_and_call_awaiter_statement(src.name, last_statement.value, to.name),
        )
    else:
        expr = _await_call_function_expr(to.name, src.lineno, src.col_offset)
        src.body.append(
            _return_statement(
                expr,
                last_statement.lineno,
                last_statement.col_offset,
            )
        )


def _await_call_function_expr(
    name: str,
    lineno: int,
    col_offset: int,
) -> ast.Await:
    return ast.Await(
        value=ast.Call(
            func=ast.Name(
                id=name,
                lineno=lineno,
                col_offset=col_offset,
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[],
            lineno=lineno,
            col_offset=col_offset,
        ),
        lineno=lineno,
        col_offset=col_offset,
    )


def _return_statement(value: ast.expr, lineno: int, col_offset: int) -> ast.Return:
    return ast.Return(
        value=value,
        lineno=lineno,
        col_offset=col_offset,
    )


class AsyncCPSTransformer(ast.NodeTransformer):
    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        children: List[ast.stmt] = node.body
        local_var_visitor = LocalVariableVisitor(node)
        node = local_var_visitor.visit(node)
        local_vars = local_var_visitor.get_variable_declarations()

        continuations: List[ast.AsyncFunctionDef] = _split_function_into_continuations(
            node.name,
            children,
            list(local_vars.keys()),
        )
        n_continuations = len(continuations)
        for idx in range(n_continuations - 1):
            _chain_continuations(continuations[idx], continuations[idx + 1])

        node.body = []
        node.body.extend(local_vars.values())
        node.body.extend(continuations)
        _chain_continuations(node, continuations[0])

        return node


def transform_async_to_cps(node: TASTNode) -> TASTNode:
    new_node: TASTNode = AsyncCPSTransformer().visit(node)
    return new_node
