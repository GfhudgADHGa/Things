"""AST -> bytecode compiler. Variable scoping is compiled down to
ENTER_SCOPE/EXIT_SCOPE plus named GET_VAR/SET_VAR/DEFINE_VAR instructions
that operate on the exact same Environment chain the tree-walking
interpreter uses (see environment.py) -- so closures and scoping rules
stay identical between the two by construction, not by re-deriving them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from . import ast_nodes as ast
from .bytecode import Chunk, Op
from .errors import ParseError

_BINARY_OPS = {
    "+": Op.ADD, "-": Op.SUB, "*": Op.MUL, "/": Op.DIV, "%": Op.MOD,
    "==": Op.EQ, "!=": Op.NEQ, "<": Op.LT, "<=": Op.LE, ">": Op.GT, ">=": Op.GE,
}


@dataclass
class _LoopContext:
    continue_target: Optional[int] = None
    break_jumps: List[int] = field(default_factory=list)
    continue_jumps: List[int] = field(default_factory=list)


class Compiler:
    def __init__(self):
        self._loop_stack: List[_LoopContext] = []

    def compile_program(self, statements: List[ast.Stmt]) -> Chunk:
        chunk = Chunk(name="<script>")
        for stmt in statements:
            self._compile_stmt(chunk, stmt)
        return chunk

    def _compile_function(self, expr: ast.FunctionExpr) -> Chunk:
        chunk = Chunk(param_names=[p.lexeme for p in expr.params], name=expr.name)
        self._compile_stmt(chunk, expr.body)
        # a function that "falls off the end" without an explicit return yields nil
        chunk.emit(Op.CONST, None)
        chunk.emit(Op.RETURN)
        return chunk

    # ---- statements ----

    def _compile_stmt(self, chunk: Chunk, stmt: ast.Stmt) -> None:
        method = getattr(self, f"_stmt_{type(stmt).__name__}")
        method(chunk, stmt)

    def _stmt_ExpressionStmt(self, chunk: Chunk, stmt: ast.ExpressionStmt) -> None:
        self._compile_expr(chunk, stmt.expression)
        chunk.emit(Op.POP)

    def _stmt_LetStmt(self, chunk: Chunk, stmt: ast.LetStmt) -> None:
        if stmt.initializer is not None:
            self._compile_expr(chunk, stmt.initializer)
        else:
            chunk.emit(Op.CONST, None)
        chunk.emit(Op.DEFINE_VAR, stmt.name.lexeme)

    def _stmt_Block(self, chunk: Chunk, stmt: ast.Block) -> None:
        chunk.emit(Op.ENTER_SCOPE)
        for s in stmt.statements:
            self._compile_stmt(chunk, s)
        chunk.emit(Op.EXIT_SCOPE)

    def _stmt_If(self, chunk: Chunk, stmt: ast.If) -> None:
        self._compile_expr(chunk, stmt.condition)
        else_jump = chunk.emit(Op.JUMP_IF_FALSE)
        self._compile_stmt(chunk, stmt.then_branch)

        if stmt.else_branch is not None:
            end_jump = chunk.emit(Op.JUMP)
            chunk.patch_jump(else_jump, len(chunk.code))
            self._compile_stmt(chunk, stmt.else_branch)
            chunk.patch_jump(end_jump, len(chunk.code))
        else:
            chunk.patch_jump(else_jump, len(chunk.code))

    def _stmt_While(self, chunk: Chunk, stmt: ast.While) -> None:
        loop_start = len(chunk.code)
        self._compile_expr(chunk, stmt.condition)
        exit_jump = chunk.emit(Op.JUMP_IF_FALSE)

        ctx = _LoopContext(continue_target=loop_start)
        self._loop_stack.append(ctx)
        self._compile_stmt(chunk, stmt.body)
        self._loop_stack.pop()

        chunk.emit(Op.JUMP, loop_start)
        loop_end = len(chunk.code)
        chunk.patch_jump(exit_jump, loop_end)
        for idx in ctx.break_jumps:
            chunk.patch_jump(idx, loop_end)
        for idx in ctx.continue_jumps:
            chunk.patch_jump(idx, loop_start)

    def _stmt_For(self, chunk: Chunk, stmt: ast.For) -> None:
        chunk.emit(Op.ENTER_SCOPE)
        if stmt.initializer is not None:
            self._compile_stmt(chunk, stmt.initializer)

        loop_start = len(chunk.code)
        if stmt.condition is not None:
            self._compile_expr(chunk, stmt.condition)
        else:
            chunk.emit(Op.CONST, True)
        exit_jump = chunk.emit(Op.JUMP_IF_FALSE)

        ctx = _LoopContext()
        self._loop_stack.append(ctx)
        self._compile_stmt(chunk, stmt.body)
        self._loop_stack.pop()

        increment_start = len(chunk.code)
        if stmt.increment is not None:
            self._compile_expr(chunk, stmt.increment)
            chunk.emit(Op.POP)
        chunk.emit(Op.JUMP, loop_start)

        loop_end = len(chunk.code)
        chunk.patch_jump(exit_jump, loop_end)
        for idx in ctx.break_jumps:
            chunk.patch_jump(idx, loop_end)
        for idx in ctx.continue_jumps:
            chunk.patch_jump(idx, increment_start)

        chunk.emit(Op.EXIT_SCOPE)

    def _stmt_Return(self, chunk: Chunk, stmt: ast.Return) -> None:
        if stmt.value is not None:
            self._compile_expr(chunk, stmt.value)
        else:
            chunk.emit(Op.CONST, None)
        chunk.emit(Op.RETURN)

    def _stmt_Break(self, chunk: Chunk, stmt: ast.Break) -> None:
        if not self._loop_stack:
            raise ParseError("'break' outside of a loop.", stmt.line)
        idx = chunk.emit(Op.BREAK)
        self._loop_stack[-1].break_jumps.append(idx)

    def _stmt_Continue(self, chunk: Chunk, stmt: ast.Continue) -> None:
        if not self._loop_stack:
            raise ParseError("'continue' outside of a loop.", stmt.line)
        ctx = self._loop_stack[-1]
        idx = chunk.emit(Op.CONTINUE)
        if ctx.continue_target is not None:
            chunk.patch_jump(idx, ctx.continue_target)
        else:
            ctx.continue_jumps.append(idx)

    # ---- expressions ----

    def _compile_expr(self, chunk: Chunk, expr: ast.Expr) -> None:
        method = getattr(self, f"_expr_{type(expr).__name__}")
        method(chunk, expr)

    def _expr_Literal(self, chunk: Chunk, expr: ast.Literal) -> None:
        chunk.emit(Op.CONST, expr.value)

    def _expr_ListLiteral(self, chunk: Chunk, expr: ast.ListLiteral) -> None:
        for element in expr.elements:
            self._compile_expr(chunk, element)
        chunk.emit(Op.BUILD_LIST, len(expr.elements))

    def _expr_Variable(self, chunk: Chunk, expr: ast.Variable) -> None:
        chunk.emit(Op.GET_VAR, (expr.name.lexeme, expr.name.line))

    def _expr_Assign(self, chunk: Chunk, expr: ast.Assign) -> None:
        self._compile_expr(chunk, expr.value)
        chunk.emit(Op.SET_VAR, (expr.name.lexeme, expr.name.line))

    def _expr_IndexGet(self, chunk: Chunk, expr: ast.IndexGet) -> None:
        self._compile_expr(chunk, expr.collection)
        self._compile_expr(chunk, expr.index)
        chunk.emit(Op.GET_INDEX, expr.line)

    def _expr_IndexSet(self, chunk: Chunk, expr: ast.IndexSet) -> None:
        self._compile_expr(chunk, expr.collection)
        self._compile_expr(chunk, expr.index)
        self._compile_expr(chunk, expr.value)
        chunk.emit(Op.SET_INDEX, expr.line)

    def _expr_Unary(self, chunk: Chunk, expr: ast.Unary) -> None:
        self._compile_expr(chunk, expr.right)
        if expr.operator.lexeme == "-":
            chunk.emit(Op.NEG, expr.operator.line)
        else:
            chunk.emit(Op.NOT)

    def _expr_Logical(self, chunk: Chunk, expr: ast.Logical) -> None:
        self._compile_expr(chunk, expr.left)
        if expr.operator.lexeme == "or":
            short_circuit = chunk.emit(Op.JUMP_IF_TRUE_NO_POP)
        else:
            short_circuit = chunk.emit(Op.JUMP_IF_FALSE_NO_POP)
        chunk.emit(Op.POP)
        self._compile_expr(chunk, expr.right)
        chunk.patch_jump(short_circuit, len(chunk.code))

    def _expr_Binary(self, chunk: Chunk, expr: ast.Binary) -> None:
        self._compile_expr(chunk, expr.left)
        self._compile_expr(chunk, expr.right)
        chunk.emit(_BINARY_OPS[expr.operator.lexeme], expr.operator.line)

    def _expr_Call(self, chunk: Chunk, expr: ast.Call) -> None:
        self._compile_expr(chunk, expr.callee)
        for arg in expr.arguments:
            self._compile_expr(chunk, arg)
        chunk.emit(Op.CALL, (len(expr.arguments), expr.line))

    def _expr_FunctionExpr(self, chunk: Chunk, expr: ast.FunctionExpr) -> None:
        function_chunk = self._compile_function(expr)
        chunk.emit(Op.MAKE_FUNCTION, function_chunk)


def compile_program(statements: List[ast.Stmt]) -> Chunk:
    return Compiler().compile_program(statements)
