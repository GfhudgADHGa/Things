"""AST node definitions. Plain dataclasses; the interpreter dispatches on type."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from .lexer import Token

# ---- Expressions -----------------------------------------------------------


class Expr:
    pass


@dataclass
class Literal(Expr):
    value: Any


@dataclass
class ListLiteral(Expr):
    elements: List[Expr]


@dataclass
class Variable(Expr):
    name: Token


@dataclass
class Assign(Expr):
    name: Token
    value: Expr


@dataclass
class IndexGet(Expr):
    collection: Expr
    index: Expr
    line: int


@dataclass
class IndexSet(Expr):
    collection: Expr
    index: Expr
    value: Expr
    line: int


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Call(Expr):
    callee: Expr
    arguments: List[Expr]
    line: int


@dataclass
class FunctionExpr(Expr):
    params: List[Token]
    body: "Block"
    name: str = "<anonymous>"


# ---- Statements --------------------------------------------------------


class Stmt:
    pass


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr


@dataclass
class LetStmt(Stmt):
    name: Token
    initializer: Optional[Expr]


@dataclass
class Block(Stmt):
    statements: List[Stmt]


@dataclass
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]


@dataclass
class While(Stmt):
    condition: Expr
    body: Stmt


@dataclass
class For(Stmt):
    initializer: Optional[Stmt]
    condition: Optional[Expr]
    increment: Optional[Expr]
    body: Stmt


@dataclass
class Return(Stmt):
    value: Optional[Expr]
    line: int


@dataclass
class Break(Stmt):
    line: int


@dataclass
class Continue(Stmt):
    line: int
