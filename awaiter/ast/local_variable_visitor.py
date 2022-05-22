import ast
from typing import Dict, Optional

VariableDeclarations = Dict[str, ast.AnnAssign]


class LocalVariableVisitor(ast.NodeTransformer):
    """Get a list of local variables by traversing assign statements.

    In order to use `nonlocal` in each continuations, this class also replaces
    assignments with type annotations with simple assignments.
    Note that this class won't traverse nested functions, recursively.
    """

    def __init__(self, root_stmt: ast.stmt) -> None:
        self._root_stmt = root_stmt
        self._declarations: VariableDeclarations = {}

    def _register_variable(
        self, variable: ast.Name, annotation: Optional[ast.expr] = None
    ) -> None:
        if variable.id in self._declarations:
            return

        end_lineno = getattr(variable, "end_lineno", None)
        end_col_offset = getattr(variable, "end_col_offset", None)

        if annotation is None:
            # Use None as the annotation
            annotation = ast.Constant(
                value=None,
                kind=None,
                lineno=variable.lineno,
                col_offset=variable.col_offset,
                end_lineno=end_lineno,
                end_col_offset=end_col_offset,
            )

        # Declare the variable in a simple assignment `<variable>: <annotation>`
        self._declarations[variable.id] = ast.AnnAssign(
            target=variable,
            annotation=annotation,
            value=None,
            simple=1,
            lineno=variable.lineno,
            col_offset=variable.col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        # Assign statement (e.g. `foo = bar`)
        targets = node.targets
        for t in targets:
            if not isinstance(t, ast.Name):
                continue
            self._register_variable(t)

        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Optional[ast.stmt]:
        # Assign statement with type annotation (e.g. `foo: int = bar`)
        # The statement could be one of the following:
        # A) a: int  # simple
        # A2) a: int = 10  # with initializer
        # B) a.b: int  # attribute assign
        # C) a[1]: int  # subscript assign
        #
        # This class only targets A and A2 since only they are required to bind variables
        # in `nonlocal` statement.

        if isinstance(node.target, ast.Name):
            # NOTE:
            self._register_variable(node.target, node.annotation)
            if node.value is None:
                return None

            return ast.Assign(
                targets=[node.target],
                value=node.value,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        return node

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AugAssign:
        # AugAssign statement (e.g. `foo += bar`)
        if isinstance(node.target, ast.Name):
            self._register_variable(node.target)

        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        # Start traversal only if the root node is given
        if node is self._root_stmt:
            return super().generic_visit(node)
        else:
            return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        # Start traversal only if the root node is given
        if node is self._root_stmt:
            return super().generic_visit(node)
        else:
            return node

    def get_variable_declarations(self) -> VariableDeclarations:
        return self._declarations
