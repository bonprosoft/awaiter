import ast

import astor

from .._types import TASTNode


def _remove_decorator(node: ast.AsyncFunctionDef, deco_name: str) -> None:
    for idx, deco in enumerate(node.decorator_list):
        assert isinstance(deco, ast.expr)
        if isinstance(deco, ast.Call):
            expr_str = astor.to_source(deco.func).strip()
        else:
            expr_str = astor.to_source(deco).strip()

        if expr_str == deco_name:
            node.decorator_list.pop(idx)
            break
    else:
        raise RuntimeError(f"Failed to find decorator: '{deco_name}'")


class DecoratorRemover(ast.NodeTransformer):
    def __init__(self, deco_name: str) -> None:
        self._deco_name = deco_name

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        _remove_decorator(node, self._deco_name)
        return node


def remove_decorator(node: TASTNode, deco_name: str) -> TASTNode:
    new_node: TASTNode = DecoratorRemover(deco_name).visit(node)
    return new_node
