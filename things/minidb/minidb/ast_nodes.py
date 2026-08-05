"""AST node definitions for expressions and statements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


# ---- Expressions ----

@dataclass
class Literal:
    value: object  # int, float, str, or None


@dataclass
class ColumnRef:
    table: Optional[str]
    name: str


@dataclass
class Star:
    table: Optional[str] = None


@dataclass
class BinaryOp:
    op: str
    left: "Expr"
    right: "Expr"


@dataclass
class UnaryOp:
    op: str
    operand: "Expr"


@dataclass
class InExpr:
    expr: "Expr"
    values: list


@dataclass
class IsNull:
    expr: "Expr"
    negated: bool = False


@dataclass
class FunctionCall:
    name: str
    args: list
    distinct: bool = False


Expr = Union[Literal, ColumnRef, Star, BinaryOp, UnaryOp, InExpr, IsNull, FunctionCall]


# ---- Statements ----

@dataclass
class ColumnDef:
    name: str
    type: str
    primary_key: bool = False


@dataclass
class CreateTable:
    name: str
    columns: list


@dataclass
class CreateIndex:
    name: str
    table: str
    column: str


@dataclass
class Insert:
    table: str
    columns: Optional[list]
    rows: list


@dataclass
class JoinClause:
    table: str
    alias: Optional[str]
    on: "Expr"


@dataclass
class SelectItem:
    expr: "Expr"
    alias: Optional[str] = None


@dataclass
class OrderItem:
    expr: "Expr"
    descending: bool = False


@dataclass
class Select:
    columns: list
    from_table: Optional[str] = None
    from_alias: Optional[str] = None
    joins: list = field(default_factory=list)
    where: Optional["Expr"] = None
    group_by: list = field(default_factory=list)
    having: Optional["Expr"] = None
    order_by: list = field(default_factory=list)
    limit: Optional[int] = None
    distinct: bool = False


@dataclass
class Update:
    table: str
    assignments: list
    where: Optional["Expr"]


@dataclass
class Delete:
    table: str
    where: Optional["Expr"]


Statement = Union[CreateTable, CreateIndex, Insert, Select, Update, Delete]
