"""Tree-walking interpreter: evaluates the AST directly, no bytecode."""
from __future__ import annotations

from typing import Any, List, Optional

from . import ast_nodes as ast
from .environment import Environment
from .errors import RuntimeErrorPebble
from .lexer import TokenType as T


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class Callable:
    def call(self, interpreter: "Interpreter", arguments: List[Any], line: int) -> Any:
        raise NotImplementedError

    def arity(self) -> Optional[int]:
        """Returns expected argument count, or None if variadic."""
        raise NotImplementedError


class PebbleFunction(Callable):
    def __init__(self, declaration: ast.FunctionExpr, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: "Interpreter", arguments: List[Any], line: int) -> Any:
        env = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            env.define(param.lexeme, arg)
        try:
            interpreter.execute_block(self.declaration.body.statements, env)
        except ReturnSignal as r:
            return r.value
        return None

    def __repr__(self) -> str:
        return f"<fn {self.declaration.name}>"


class NativeFunction(Callable):
    def __init__(self, name: str, arity: Optional[int], fn):
        self.name = name
        self._arity = arity
        self.fn = fn

    def arity(self) -> Optional[int]:
        return self._arity

    def call(self, interpreter: "Interpreter", arguments: List[Any], line: int) -> Any:
        return self.fn(interpreter, arguments, line)

    def __repr__(self) -> str:
        return f"<native fn {self.name}>"


def is_truthy(value: Any) -> bool:
    return value is not None and value is not False


def stringify(value: Any) -> str:
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(repr_of(v) for v in value) + "]"
    return repr(value)


def repr_of(value: Any) -> str:
    """Like stringify, but strings are quoted -- used inside list printing."""
    if isinstance(value, str):
        return '"' + value + '"'
    return stringify(value)


class Interpreter:
    def __init__(self, output=print):
        self.globals = Environment()
        self.environment = self.globals
        self.output = output
        from . import builtins as pebble_builtins

        pebble_builtins.install(self.globals)

    def interpret(self, statements: List[ast.Stmt]) -> None:
        for statement in statements:
            self._execute(statement)

    # ---- statement execution ----

    def _execute(self, stmt: ast.Stmt) -> None:
        method = getattr(self, f"_exec_{type(stmt).__name__}")
        method(stmt)

    def execute_block(self, statements: List[ast.Stmt], env: Environment) -> None:
        previous = self.environment
        try:
            self.environment = env
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    def _exec_ExpressionStmt(self, stmt: ast.ExpressionStmt) -> None:
        self._evaluate(stmt.expression)

    def _exec_LetStmt(self, stmt: ast.LetStmt) -> None:
        value = self._evaluate(stmt.initializer) if stmt.initializer is not None else None
        self.environment.define(stmt.name.lexeme, value)

    def _exec_Block(self, stmt: ast.Block) -> None:
        self.execute_block(stmt.statements, Environment(self.environment))

    def _exec_If(self, stmt: ast.If) -> None:
        if is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)

    def _exec_While(self, stmt: ast.While) -> None:
        while is_truthy(self._evaluate(stmt.condition)):
            try:
                self._execute(stmt.body)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _exec_For(self, stmt: ast.For) -> None:
        previous = self.environment
        try:
            self.environment = Environment(previous)
            if stmt.initializer is not None:
                self._execute(stmt.initializer)
            while stmt.condition is None or is_truthy(self._evaluate(stmt.condition)):
                try:
                    self._execute(stmt.body)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                if stmt.increment is not None:
                    self._evaluate(stmt.increment)
        finally:
            self.environment = previous

    def _exec_Return(self, stmt: ast.Return) -> None:
        value = self._evaluate(stmt.value) if stmt.value is not None else None
        raise ReturnSignal(value)

    def _exec_Break(self, stmt: ast.Break) -> None:
        raise BreakSignal()

    def _exec_Continue(self, stmt: ast.Continue) -> None:
        raise ContinueSignal()

    # ---- expression evaluation ----

    def _evaluate(self, expr: ast.Expr) -> Any:
        method = getattr(self, f"_eval_{type(expr).__name__}")
        return method(expr)

    def _eval_Literal(self, expr: ast.Literal) -> Any:
        return expr.value

    def _eval_ListLiteral(self, expr: ast.ListLiteral) -> Any:
        return [self._evaluate(e) for e in expr.elements]

    def _eval_Variable(self, expr: ast.Variable) -> Any:
        return self.environment.get(expr.name.lexeme, expr.name.line)

    def _eval_Assign(self, expr: ast.Assign) -> Any:
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name.lexeme, value, expr.name.line)
        return value

    def _eval_IndexGet(self, expr: ast.IndexGet) -> Any:
        collection = self._evaluate(expr.collection)
        index = self._evaluate(expr.index)
        return self._do_index_get(collection, index, expr.line)

    def _do_index_get(self, collection: Any, index: Any, line: int) -> Any:
        if isinstance(collection, list):
            if not isinstance(index, float) or not index.is_integer():
                raise RuntimeErrorPebble("List index must be an integer.", line)
            i = int(index)
            if not (-len(collection) <= i < len(collection)):
                raise RuntimeErrorPebble("List index out of range.", line)
            return collection[i]
        if isinstance(collection, str):
            if not isinstance(index, float) or not index.is_integer():
                raise RuntimeErrorPebble("String index must be an integer.", line)
            i = int(index)
            if not (-len(collection) <= i < len(collection)):
                raise RuntimeErrorPebble("String index out of range.", line)
            return collection[i]
        raise RuntimeErrorPebble("Only lists and strings can be indexed.", line)

    def _eval_IndexSet(self, expr: ast.IndexSet) -> Any:
        collection = self._evaluate(expr.collection)
        index = self._evaluate(expr.index)
        value = self._evaluate(expr.value)
        if not isinstance(collection, list):
            raise RuntimeErrorPebble("Only lists support index assignment.", expr.line)
        if not isinstance(index, float) or not index.is_integer():
            raise RuntimeErrorPebble("List index must be an integer.", expr.line)
        i = int(index)
        if not (-len(collection) <= i < len(collection)):
            raise RuntimeErrorPebble("List index out of range.", expr.line)
        collection[i] = value
        return value

    def _eval_Unary(self, expr: ast.Unary) -> Any:
        right = self._evaluate(expr.right)
        if expr.operator.type == T.MINUS:
            if not isinstance(right, float):
                raise RuntimeErrorPebble("Operand of '-' must be a number.", expr.operator.line)
            return -right
        if expr.operator.type == T.BANG:
            return not is_truthy(right)
        raise RuntimeErrorPebble("Unknown unary operator.", expr.operator.line)

    def _eval_Logical(self, expr: ast.Logical) -> Any:
        left = self._evaluate(expr.left)
        if expr.operator.type == T.OR:
            if is_truthy(left):
                return left
        else:  # AND
            if not is_truthy(left):
                return left
        return self._evaluate(expr.right)

    def _eval_Binary(self, expr: ast.Binary) -> Any:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op = expr.operator.type
        line = expr.operator.line

        if op == T.PLUS:
            if isinstance(left, float) and isinstance(right, float):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise RuntimeErrorPebble(
                "Operands of '+' must both be numbers, both strings, or both lists.", line
            )

        if op in (T.MINUS, T.STAR, T.SLASH, T.PERCENT):
            self._check_numbers(left, right, line)
            if op == T.MINUS:
                return left - right
            if op == T.STAR:
                return left * right
            if op == T.SLASH:
                if right == 0:
                    raise RuntimeErrorPebble("Division by zero.", line)
                return left / right
            if right == 0:
                raise RuntimeErrorPebble("Division by zero.", line)
            return left % right

        if op in (T.GREATER, T.GREATER_EQUAL, T.LESS, T.LESS_EQUAL):
            if isinstance(left, float) and isinstance(right, float):
                pass
            elif isinstance(left, str) and isinstance(right, str):
                pass
            else:
                raise RuntimeErrorPebble(
                    "Operands for comparison must both be numbers or both strings.", line
                )
            if op == T.GREATER:
                return left > right
            if op == T.GREATER_EQUAL:
                return left >= right
            if op == T.LESS:
                return left < right
            return left <= right

        if op == T.EQUAL_EQUAL:
            return left == right
        if op == T.BANG_EQUAL:
            return left != right

        raise RuntimeErrorPebble("Unknown binary operator.", line)

    def _check_numbers(self, left: Any, right: Any, line: int) -> None:
        if not isinstance(left, float) or not isinstance(right, float):
            raise RuntimeErrorPebble("Operands must be numbers.", line)

    def _eval_Call(self, expr: ast.Call) -> Any:
        callee = self._evaluate(expr.callee)
        arguments = [self._evaluate(a) for a in expr.arguments]

        if not isinstance(callee, Callable):
            raise RuntimeErrorPebble("Can only call functions.", expr.line)

        arity = callee.arity()
        if arity is not None and len(arguments) != arity:
            raise RuntimeErrorPebble(
                f"Expected {arity} argument(s) but got {len(arguments)}.", expr.line
            )
        return callee.call(self, arguments, expr.line)

    def _eval_FunctionExpr(self, expr: ast.FunctionExpr) -> Any:
        return PebbleFunction(expr, self.environment)
