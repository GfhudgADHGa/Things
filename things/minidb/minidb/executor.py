"""Executes parsed statements against a Database.

Two SQL behaviors worth calling out because they were only discovered by
cross-checking against sqlite3 as an oracle (see tests/test_oracle.py and
the README):

  * ``LIKE`` is case-insensitive for ASCII by default in SQLite. An
    earlier version of this executor did a case-sensitive regex match,
    which the oracle tests caught immediately (`'Foo' LIKE 'f%'` disagreed
    between the two engines).
  * ``/`` and ``%`` between two INTEGER operands use C-style truncating
    division (toward zero), not Python's floor division/modulo. `-7 / 2`
    is `-3` in SQLite (and here) but `-4` with Python's `//`. Division or
    modulo by zero yields NULL rather than raising.
"""
from __future__ import annotations

import re as _re
from dataclasses import dataclass
from typing import Optional

from .ast_nodes import (
    BinaryOp, ColumnRef, CreateTable, Delete, FunctionCall, InExpr, Insert,
    IsNull, Literal, OrderItem, Select, Star, Update, UnaryOp,
)
from .errors import ExecutionError
from .storage import Database, Table


@dataclass
class QueryResult:
    headers: list
    rows: list


# ---- row / group contexts ----

class RowContext:
    """A single (possibly joined) row: values keyed by qualified (table, col)
    and by bare column name (when unambiguous)."""

    __slots__ = ("by_qualified", "by_unqualified")

    def __init__(self):
        self.by_qualified: dict = {}
        self.by_unqualified: dict = {}

    def add(self, table_name: str, col: str, value) -> None:
        self.by_qualified[(table_name, col)] = value
        self.by_unqualified.setdefault(col, []).append(value)

    def get_column(self, table: Optional[str], col: str):
        if table is not None:
            key = (table, col)
            if key not in self.by_qualified:
                raise ExecutionError(f"no such column: {table}.{col}")
            return self.by_qualified[key]
        candidates = self.by_unqualified.get(col)
        if not candidates:
            raise ExecutionError(f"no such column: {col}")
        if len(candidates) > 1:
            raise ExecutionError(f"ambiguous column reference: {col}")
        return candidates[0]

    def get_aggregate(self, func: FunctionCall):
        raise ExecutionError(f"aggregate function {func.name}() used outside of GROUP BY/aggregate context")


def _merge_contexts(a: RowContext, b: RowContext) -> RowContext:
    merged = RowContext()
    merged.by_qualified.update(a.by_qualified)
    merged.by_qualified.update(b.by_qualified)
    for col, vals in a.by_unqualified.items():
        merged.by_unqualified.setdefault(col, []).extend(vals)
    for col, vals in b.by_unqualified.items():
        merged.by_unqualified.setdefault(col, []).extend(vals)
    return merged


class GroupContext:
    """A group of rows for GROUP BY / whole-table aggregation. Column
    references resolve against an arbitrary representative row (SQLite's
    own lenient behavior for non-aggregated, non-grouped columns); function
    calls are evaluated as aggregates over the whole group."""

    __slots__ = ("rows", "_rep")

    def __init__(self, rows: list):
        self.rows = rows
        self._rep = rows[0] if rows else RowContext()

    def get_column(self, table: Optional[str], col: str):
        return self._rep.get_column(table, col)

    def get_aggregate(self, func: FunctionCall):
        return _eval_aggregate(func, self.rows)


def _scan_table(table: Table, alias: Optional[str]) -> list:
    name = alias or table.name
    contexts = []
    for row in table.rows:
        ctx = RowContext()
        for col, value in zip(table.columns, row):
            ctx.add(name, col.name, value)
        contexts.append(ctx)
    return contexts


def _join(left_rows: list, table: Table, alias: Optional[str], on_expr) -> list:
    right_rows = _scan_table(table, alias)
    result = []
    for lctx in left_rows:
        for rctx in right_rows:
            merged = _merge_contexts(lctx, rctx)
            if eval_expr(on_expr, merged) is True:
                result.append(merged)
    return result


# ---- expression evaluation ----

def _c_divmod(a: int, b: int) -> tuple:
    """Truncating (toward zero) integer division, matching SQLite/C, not
    Python's floor-based `//`."""
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q, a - b * q


def _like_to_regex(pattern: str) -> str:
    parts = []
    for ch in pattern:
        if ch == "%":
            parts.append(".*")
        elif ch == "_":
            parts.append(".")
        else:
            parts.append(_re.escape(ch))
    return "^" + "".join(parts) + "$"


def _and(a, b):
    if a is False or b is False:
        return False
    if a is None or b is None:
        return None
    return True


def _or(a, b):
    if a is True or b is True:
        return True
    if a is None or b is None:
        return None
    return False


def _eval_binary(expr: BinaryOp, ctx):
    op = expr.op
    if op == "AND":
        return _and(eval_expr(expr.left, ctx), eval_expr(expr.right, ctx))
    if op == "OR":
        return _or(eval_expr(expr.left, ctx), eval_expr(expr.right, ctx))
    left = eval_expr(expr.left, ctx)
    right = eval_expr(expr.right, ctx)
    if op == "LIKE":
        if left is None or right is None:
            return None
        return _re.match(_like_to_regex(str(right)), str(left), _re.IGNORECASE | _re.DOTALL) is not None
    if left is None or right is None:
        return None
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if right == 0:
            return None
        if isinstance(left, int) and isinstance(right, int):
            return _c_divmod(left, right)[0]
        return left / right
    if op == "%":
        if right == 0:
            return None
        return _c_divmod(int(left), int(right))[1]
    if op == "=":
        return left == right
    if op in ("!=", "<>"):
        return left != right
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    raise ExecutionError(f"unknown operator {op!r}")


def _eval_aggregate(func: FunctionCall, rows: list):
    name = func.name
    if name == "COUNT":
        if func.args == ["*"]:
            return len(rows)
        values = [eval_expr(func.args[0], r) for r in rows]
        values = [v for v in values if v is not None]
        if func.distinct:
            values = list(set(values))
        return len(values)
    if not func.args or func.args == ["*"]:
        raise ExecutionError(f"{name}() requires a single argument")
    values = [eval_expr(func.args[0], r) for r in rows]
    values = [v for v in values if v is not None]
    if func.distinct:
        values = list(set(values))
    if name == "SUM":
        return sum(values) if values else None
    if name == "AVG":
        return (sum(values) / len(values)) if values else None
    if name == "MIN":
        return min(values) if values else None
    if name == "MAX":
        return max(values) if values else None
    raise ExecutionError(f"unknown function: {name}")


def eval_expr(expr, ctx):
    if isinstance(expr, Literal):
        return expr.value
    if isinstance(expr, ColumnRef):
        return ctx.get_column(expr.table, expr.name)
    if isinstance(expr, FunctionCall):
        return ctx.get_aggregate(expr)
    if isinstance(expr, UnaryOp):
        val = eval_expr(expr.operand, ctx)
        if expr.op == "-":
            return None if val is None else -val
        if expr.op == "NOT":
            if val is None:
                return None
            return not val
        raise ExecutionError(f"unknown unary operator {expr.op!r}")
    if isinstance(expr, BinaryOp):
        return _eval_binary(expr, ctx)
    if isinstance(expr, InExpr):
        val = eval_expr(expr.expr, ctx)
        if val is None:
            return None
        values = [eval_expr(v, ctx) for v in expr.values]
        return val in values
    if isinstance(expr, IsNull):
        val = eval_expr(expr.expr, ctx)
        result = val is None
        return (not result) if expr.negated else result
    if isinstance(expr, Star):
        raise ExecutionError("'*' is only valid in the top-level SELECT list")
    raise ExecutionError(f"cannot evaluate expression: {expr!r}")


def _contains_aggregate(expr) -> bool:
    if isinstance(expr, FunctionCall):
        return True
    if isinstance(expr, BinaryOp):
        return _contains_aggregate(expr.left) or _contains_aggregate(expr.right)
    if isinstance(expr, UnaryOp):
        return _contains_aggregate(expr.operand)
    if isinstance(expr, InExpr):
        return _contains_aggregate(expr.expr) or any(_contains_aggregate(v) for v in expr.values)
    if isinstance(expr, IsNull):
        return _contains_aggregate(expr.expr)
    return False


def _sort_key(value):
    # NULLs sort first (SQLite default); reverse=True for DESC naturally
    # flips this to NULLs-last, matching SQLite's DESC behavior too.
    return (0, 0) if value is None else (1, value)


def _apply_order_by(contexts: list, order_by: list) -> list:
    for item in reversed(order_by):
        contexts.sort(key=lambda ctx: _sort_key(eval_expr(item.expr, ctx)), reverse=item.descending)
    return contexts


def _table_has_column(tables_info: list, name: str) -> bool:
    return any(any(c.name == name for c in t.columns) for t, _ in tables_info)


def _resolve_order_by_aliases(order_by: list, stmt: Select, tables_info: list) -> list:
    """ORDER BY may reference a SELECT-list alias (`SELECT SUM(x) AS total
    ... ORDER BY total`), which isn't a real column on any table. A real
    column of the same name always takes precedence, matching typical SQL
    resolution order."""
    alias_map = {item.alias: item.expr for item in stmt.columns if item.alias}
    resolved = []
    for item in order_by:
        expr = item.expr
        if (isinstance(expr, ColumnRef) and expr.table is None and expr.name in alias_map
                and not _table_has_column(tables_info, expr.name)):
            expr = alias_map[expr.name]
        resolved.append(OrderItem(expr, item.descending))
    return resolved


def _group_rows(rows: list, group_by: list) -> list:
    if not group_by:
        return [rows]
    groups: dict = {}
    order = []
    for ctx in rows:
        key = tuple(eval_expr(g, ctx) for g in group_by)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(ctx)
    return [groups[k] for k in order]


def _expr_header(expr) -> str:
    if isinstance(expr, ColumnRef):
        return expr.name
    if isinstance(expr, Literal):
        return str(expr.value)
    if isinstance(expr, FunctionCall):
        args = "*" if expr.args == ["*"] else ", ".join(_expr_header(a) for a in expr.args)
        return f"{expr.name}({args})"
    if isinstance(expr, BinaryOp):
        return f"{_expr_header(expr.left)} {expr.op} {_expr_header(expr.right)}"
    if isinstance(expr, UnaryOp):
        return f"{expr.op} {_expr_header(expr.operand)}"
    return "expr"


def _expand_select_items(stmt: Select, tables_info: list) -> list:
    expanded = []
    for item in stmt.columns:
        if isinstance(item.expr, Star):
            if item.expr.table is not None:
                matches = [t for t in tables_info if t[1] == item.expr.table]
                if not matches:
                    raise ExecutionError(f"no such table: {item.expr.table}")
                table_obj, alias = matches[0]
                for col in table_obj.columns:
                    expanded.append((col.name, ColumnRef(alias, col.name)))
            else:
                for table_obj, alias in tables_info:
                    for col in table_obj.columns:
                        expanded.append((col.name, ColumnRef(alias, col.name)))
        else:
            header = item.alias or _expr_header(item.expr)
            expanded.append((header, item.expr))
    return expanded


# ---- statement execution ----

def execute_create_table(db: Database, stmt: CreateTable) -> None:
    db.create_table(stmt.name, stmt.columns)


def execute_insert(db: Database, stmt: Insert) -> int:
    table = db.get_table(stmt.table)
    col_names = stmt.columns if stmt.columns is not None else table.column_names()
    empty_ctx = RowContext()
    count = 0
    for value_exprs in stmt.rows:
        if len(value_exprs) != len(col_names):
            raise ExecutionError("number of values does not match number of columns")
        values_by_name = {name: eval_expr(expr, empty_ctx) for name, expr in zip(col_names, value_exprs)}
        row = []
        for i, col in enumerate(table.columns):
            row.append(table.coerce(i, values_by_name[col.name]) if col.name in values_by_name else None)
        table.rows.append(row)
        count += 1
    return count


def execute_select(db: Database, stmt: Select) -> QueryResult:
    if stmt.from_table is None:
        # FROM-less SELECT (e.g. `SELECT 1 + 1`): a single row of no columns.
        tables_info: list = []
        rows = [RowContext()]
    else:
        table = db.get_table(stmt.from_table)
        tables_info = [(table, stmt.from_alias or stmt.from_table)]
        rows = _scan_table(table, stmt.from_alias)
        for join in stmt.joins:
            jt = db.get_table(join.table)
            tables_info.append((jt, join.alias or join.table))
            rows = _join(rows, jt, join.alias, join.on)

    if stmt.where is not None:
        rows = [r for r in rows if eval_expr(stmt.where, r) is True]

    has_aggregate = any(_contains_aggregate(item.expr) for item in stmt.columns) or (
        stmt.having is not None and _contains_aggregate(stmt.having)
    )
    use_grouping = bool(stmt.group_by) or has_aggregate

    if use_grouping:
        contexts = [GroupContext(g) for g in _group_rows(rows, stmt.group_by)]
        if stmt.having is not None:
            contexts = [g for g in contexts if eval_expr(stmt.having, g) is True]
    else:
        contexts = rows

    if stmt.order_by:
        order_by = _resolve_order_by_aliases(stmt.order_by, stmt, tables_info)
        contexts = _apply_order_by(list(contexts), order_by)

    if stmt.limit is not None:
        contexts = contexts[: stmt.limit]

    expanded = _expand_select_items(stmt, tables_info)
    headers = [h for h, _ in expanded]
    out_rows = []
    seen = set()
    for ctx in contexts:
        values = [eval_expr(expr, ctx) for _, expr in expanded]
        if stmt.distinct:
            key = tuple(values)
            if key in seen:
                continue
            seen.add(key)
        out_rows.append(values)
    return QueryResult(headers, out_rows)


def execute_update(db: Database, stmt: Update) -> int:
    table = db.get_table(stmt.table)
    for name, _ in stmt.assignments:
        table.column_index(name)  # validates the column exists
    count = 0
    for row in table.rows:
        ctx = RowContext()
        for col, value in zip(table.columns, row):
            ctx.add(table.name, col.name, value)
        if stmt.where is not None and eval_expr(stmt.where, ctx) is not True:
            continue
        for name, expr in stmt.assignments:
            idx = table.column_index(name)
            row[idx] = table.coerce(idx, eval_expr(expr, ctx))
        count += 1
    return count


def execute_delete(db: Database, stmt: Delete) -> int:
    table = db.get_table(stmt.table)
    keep = []
    deleted = 0
    for row in table.rows:
        ctx = RowContext()
        for col, value in zip(table.columns, row):
            ctx.add(table.name, col.name, value)
        if stmt.where is not None and eval_expr(stmt.where, ctx) is not True:
            keep.append(row)
        else:
            deleted += 1
    table.rows = keep
    return deleted


def execute(db: Database, stmt):
    if isinstance(stmt, CreateTable):
        return execute_create_table(db, stmt)
    if isinstance(stmt, Insert):
        return execute_insert(db, stmt)
    if isinstance(stmt, Select):
        return execute_select(db, stmt)
    if isinstance(stmt, Update):
        return execute_update(db, stmt)
    if isinstance(stmt, Delete):
        return execute_delete(db, stmt)
    raise ExecutionError(f"cannot execute statement: {stmt!r}")
