"""Recursive-descent parser with precedence climbing for expressions.

Precedence, low to high: OR, AND, NOT, comparison (= != <> < <= > >= LIKE
IN IS NULL), additive (+ -), multiplicative (* / %), unary minus, primary.
"""
from __future__ import annotations

from typing import Optional

from .ast_nodes import (
    BinaryOp, ColumnDef, ColumnRef, CreateTable, Delete, FunctionCall,
    InExpr, Insert, IsNull, JoinClause, Literal, OrderItem, Select,
    SelectItem, Star, UnaryOp, Update,
)
from .errors import ParseError
from .lexer import Token, TokType, tokenize

_COLUMN_TYPES = {"INTEGER", "REAL", "TEXT"}
_COMPARISON_OPS = {"=", "!=", "<>", "<", "<=", ">", ">="}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _peek_ahead(self, n: int) -> Optional[Token]:
        idx = self.pos + n
        return self.tokens[idx] if idx < len(self.tokens) else None

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokType.EOF:
            self.pos += 1
        return tok

    def _check_keyword(self, *keywords: str) -> bool:
        tok = self._peek()
        return tok.type == TokType.KEYWORD and tok.value in keywords

    def _check_op(self, *ops: str) -> bool:
        tok = self._peek()
        return tok.type == TokType.OP and tok.value in ops

    def _match_keyword(self, *keywords: str) -> bool:
        if self._check_keyword(*keywords):
            self._advance()
            return True
        return False

    def _match_op(self, *ops: str) -> bool:
        if self._check_op(*ops):
            self._advance()
            return True
        return False

    def _expect_keyword(self, keyword: str) -> Token:
        if not self._check_keyword(keyword):
            tok = self._peek()
            raise ParseError(f"expected {keyword!r}, got {tok.value!r} at position {tok.pos}")
        return self._advance()

    def _expect_op(self, op: str) -> Token:
        if not self._check_op(op):
            tok = self._peek()
            raise ParseError(f"expected {op!r}, got {tok.value!r} at position {tok.pos}")
        return self._advance()

    def _expect_ident(self) -> str:
        tok = self._peek()
        if tok.type != TokType.IDENT:
            raise ParseError(f"expected identifier, got {tok.value!r} at position {tok.pos}")
        self._advance()
        return tok.value

    # ---- entry points ----

    def parse_statement(self):
        stmt = self._parse_one()
        self._match_op(";")
        if self._peek().type != TokType.EOF:
            tok = self._peek()
            raise ParseError(f"unexpected trailing token {tok.value!r} at position {tok.pos}")
        return stmt

    def _parse_one(self):
        if self._check_keyword("SELECT"):
            return self._parse_select()
        if self._check_keyword("CREATE"):
            return self._parse_create_table()
        if self._check_keyword("INSERT"):
            return self._parse_insert()
        if self._check_keyword("UPDATE"):
            return self._parse_update()
        if self._check_keyword("DELETE"):
            return self._parse_delete()
        tok = self._peek()
        raise ParseError(f"unexpected token {tok.value!r} at position {tok.pos}")

    # ---- CREATE TABLE ----

    def _parse_create_table(self) -> CreateTable:
        self._expect_keyword("CREATE")
        self._expect_keyword("TABLE")
        name = self._expect_ident()
        self._expect_op("(")
        columns = []
        while True:
            col_name = self._expect_ident()
            type_tok = self._advance()
            if type_tok.type != TokType.KEYWORD or type_tok.value not in _COLUMN_TYPES:
                raise ParseError(f"expected column type at position {type_tok.pos}")
            primary_key = False
            if self._match_keyword("PRIMARY"):
                self._expect_keyword("KEY")
                primary_key = True
            columns.append(ColumnDef(col_name, type_tok.value, primary_key))
            if self._match_op(","):
                continue
            break
        self._expect_op(")")
        return CreateTable(name, columns)

    # ---- INSERT ----

    def _parse_insert(self) -> Insert:
        self._expect_keyword("INSERT")
        self._expect_keyword("INTO")
        table = self._expect_ident()
        columns = None
        if self._check_op("("):
            self._advance()
            columns = [self._expect_ident()]
            while self._match_op(","):
                columns.append(self._expect_ident())
            self._expect_op(")")
        self._expect_keyword("VALUES")
        rows = [self._parse_value_tuple()]
        while self._match_op(","):
            rows.append(self._parse_value_tuple())
        return Insert(table, columns, rows)

    def _parse_value_tuple(self) -> list:
        self._expect_op("(")
        values = [self._parse_expr()]
        while self._match_op(","):
            values.append(self._parse_expr())
        self._expect_op(")")
        return values

    # ---- SELECT ----

    def _parse_select(self) -> Select:
        self._expect_keyword("SELECT")
        distinct = self._match_keyword("DISTINCT")
        columns = [self._parse_select_item()]
        while self._match_op(","):
            columns.append(self._parse_select_item())
        from_table = None
        from_alias = None
        joins = []
        if self._match_keyword("FROM"):
            from_table = self._expect_ident()
            from_alias = self._parse_optional_alias()
            while self._check_keyword("JOIN", "INNER", "LEFT"):
                joins.append(self._parse_join())
        where = self._parse_expr() if self._match_keyword("WHERE") else None
        group_by = []
        if self._match_keyword("GROUP"):
            self._expect_keyword("BY")
            group_by = [self._parse_expr()]
            while self._match_op(","):
                group_by.append(self._parse_expr())
        having = self._parse_expr() if self._match_keyword("HAVING") else None
        order_by = []
        if self._match_keyword("ORDER"):
            self._expect_keyword("BY")
            order_by = [self._parse_order_item()]
            while self._match_op(","):
                order_by.append(self._parse_order_item())
        limit = None
        if self._match_keyword("LIMIT"):
            tok = self._peek()
            if tok.type != TokType.NUMBER:
                raise ParseError(f"expected number after LIMIT at position {tok.pos}")
            self._advance()
            limit = int(tok.value)
        return Select(
            columns, from_table, from_alias, joins, where, group_by, having,
            order_by, limit, distinct,
        )

    def _parse_join(self) -> JoinClause:
        self._match_keyword("INNER")
        if self._match_keyword("LEFT"):
            raise ParseError("LEFT JOIN is not supported (INNER JOIN / JOIN only)")
        self._expect_keyword("JOIN")
        table = self._expect_ident()
        alias = self._parse_optional_alias()
        self._expect_keyword("ON")
        on = self._parse_expr()
        return JoinClause(table, alias, on)

    def _parse_optional_alias(self) -> Optional[str]:
        if self._match_keyword("AS"):
            return self._expect_ident()
        if self._peek().type == TokType.IDENT:
            return self._advance().value
        return None

    def _parse_select_item(self) -> SelectItem:
        if self._check_op("*"):
            self._advance()
            return SelectItem(Star())
        expr = self._parse_expr()
        alias = None
        if self._match_keyword("AS"):
            alias = self._expect_ident()
        elif self._peek().type == TokType.IDENT:
            alias = self._advance().value
        return SelectItem(expr, alias)

    def _parse_order_item(self) -> OrderItem:
        expr = self._parse_expr()
        descending = False
        if self._match_keyword("DESC"):
            descending = True
        elif self._match_keyword("ASC"):
            descending = False
        return OrderItem(expr, descending)

    # ---- UPDATE ----

    def _parse_update(self) -> Update:
        self._expect_keyword("UPDATE")
        table = self._expect_ident()
        self._expect_keyword("SET")
        assignments = [self._parse_assignment()]
        while self._match_op(","):
            assignments.append(self._parse_assignment())
        where = self._parse_expr() if self._match_keyword("WHERE") else None
        return Update(table, assignments, where)

    def _parse_assignment(self):
        name = self._expect_ident()
        self._expect_op("=")
        expr = self._parse_expr()
        return (name, expr)

    # ---- DELETE ----

    def _parse_delete(self) -> Delete:
        self._expect_keyword("DELETE")
        self._expect_keyword("FROM")
        table = self._expect_ident()
        where = self._parse_expr() if self._match_keyword("WHERE") else None
        return Delete(table, where)

    # ---- expressions ----

    def _parse_expr(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self._match_keyword("OR"):
            left = BinaryOp("OR", left, self._parse_and())
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self._match_keyword("AND"):
            left = BinaryOp("AND", left, self._parse_not())
        return left

    def _parse_not(self):
        if self._match_keyword("NOT"):
            return UnaryOp("NOT", self._parse_not())
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_additive()
        tok = self._peek()
        if tok.type == TokType.OP and tok.value in _COMPARISON_OPS:
            op = self._advance().value
            return BinaryOp(op, left, self._parse_additive())
        if self._check_keyword("IS"):
            self._advance()
            negated = self._match_keyword("NOT")
            self._expect_keyword("NULL")
            return IsNull(left, negated)
        if self._check_keyword("LIKE"):
            self._advance()
            return BinaryOp("LIKE", left, self._parse_additive())
        if self._check_keyword("NOT") and self._peek_ahead(1) is not None and \
                self._peek_ahead(1).type == TokType.KEYWORD and self._peek_ahead(1).value == "LIKE":
            self._advance()
            self._expect_keyword("LIKE")
            return UnaryOp("NOT", BinaryOp("LIKE", left, self._parse_additive()))
        if self._check_keyword("IN"):
            self._advance()
            self._expect_op("(")
            values = [self._parse_expr()]
            while self._match_op(","):
                values.append(self._parse_expr())
            self._expect_op(")")
            return InExpr(left, values)
        return left

    def _parse_additive(self):
        left = self._parse_term()
        while self._check_op("+", "-"):
            op = self._advance().value
            left = BinaryOp(op, left, self._parse_term())
        return left

    def _parse_term(self):
        left = self._parse_unary()
        while self._check_op("*", "/", "%"):
            op = self._advance().value
            left = BinaryOp(op, left, self._parse_unary())
        return left

    def _parse_unary(self):
        if self._match_op("-"):
            return UnaryOp("-", self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self):
        tok = self._peek()
        if tok.type == TokType.NUMBER:
            self._advance()
            return Literal(float(tok.value) if "." in tok.value else int(tok.value))
        if tok.type == TokType.STRING:
            self._advance()
            return Literal(tok.value)
        if tok.type == TokType.KEYWORD and tok.value == "NULL":
            self._advance()
            return Literal(None)
        if tok.type == TokType.OP and tok.value == "(":
            self._advance()
            expr = self._parse_expr()
            self._expect_op(")")
            return expr
        if tok.type == TokType.IDENT:
            name = self._advance().value
            if self._check_op("("):
                self._advance()
                distinct = self._match_keyword("DISTINCT")
                if self._check_op("*"):
                    self._advance()
                    args = ["*"]
                elif self._check_op(")"):
                    args = []
                else:
                    args = [self._parse_expr()]
                    while self._match_op(","):
                        args.append(self._parse_expr())
                self._expect_op(")")
                return FunctionCall(name.upper(), args, distinct)
            if self._match_op("."):
                if self._check_op("*"):
                    self._advance()
                    return Star(name)
                return ColumnRef(name, self._expect_ident())
            return ColumnRef(None, name)
        raise ParseError(f"unexpected token {tok.value!r} at position {tok.pos}")


def parse(sql: str):
    """Parse a single SQL statement (optionally ;-terminated)."""
    return Parser(tokenize(sql)).parse_statement()


def parse_many(sql: str) -> list:
    """Parse a script containing zero or more ;-separated statements."""
    parser = Parser(tokenize(sql))
    statements = []
    while parser._peek().type != TokType.EOF:
        if parser._match_op(";"):
            continue
        statements.append(parser._parse_one())
        parser._match_op(";")
    return statements
