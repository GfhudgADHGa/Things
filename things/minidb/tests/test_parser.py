import pytest

from minidb.ast_nodes import (
    BinaryOp, ColumnRef, CreateIndex, CreateTable, Delete, FunctionCall,
    InExpr, Insert, IsNull, Literal, Select, Star, UnaryOp, Update,
)
from minidb.errors import ParseError
from minidb.parser import parse, parse_many


def test_parse_create_table():
    stmt = parse("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    assert isinstance(stmt, CreateTable)
    assert stmt.name == "t"
    assert [c.name for c in stmt.columns] == ["id", "name"]
    assert stmt.columns[0].primary_key is True
    assert stmt.columns[1].primary_key is False


def test_parse_create_index():
    stmt = parse("CREATE INDEX idx_age ON users(age)")
    assert isinstance(stmt, CreateIndex)
    assert stmt.name == "idx_age"
    assert stmt.table == "users"
    assert stmt.column == "age"


def test_parse_insert_with_explicit_columns():
    stmt = parse("INSERT INTO t (id, name) VALUES (1, 'a'), (2, 'b')")
    assert isinstance(stmt, Insert)
    assert stmt.columns == ["id", "name"]
    assert len(stmt.rows) == 2
    assert stmt.rows[0] == [Literal(1), Literal("a")]


def test_parse_insert_without_columns():
    stmt = parse("INSERT INTO t VALUES (1, 'a')")
    assert stmt.columns is None


def test_parse_simple_select():
    stmt = parse("SELECT a, b FROM t")
    assert isinstance(stmt, Select)
    assert [c.expr for c in stmt.columns] == [ColumnRef(None, "a"), ColumnRef(None, "b")]
    assert stmt.from_table == "t"


def test_parse_select_star():
    stmt = parse("SELECT * FROM t")
    assert isinstance(stmt.columns[0].expr, Star)


def test_parse_select_without_from():
    stmt = parse("SELECT 1 + 1")
    assert stmt.from_table is None


def test_parse_where_operator_precedence():
    # AND binds tighter than OR
    stmt = parse("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3")
    where = stmt.where
    assert isinstance(where, BinaryOp) and where.op == "OR"
    assert isinstance(where.right, BinaryOp) and where.right.op == "AND"


def test_parse_arithmetic_precedence():
    stmt = parse("SELECT a FROM t WHERE a = 1 + 2 * 3")
    right = stmt.where.right
    assert isinstance(right, BinaryOp) and right.op == "+"
    assert isinstance(right.right, BinaryOp) and right.right.op == "*"


def test_parse_parenthesized_expr_overrides_precedence():
    stmt = parse("SELECT a FROM t WHERE a = (1 + 2) * 3")
    right = stmt.where.right
    assert right.op == "*"
    assert right.left.op == "+"


def test_parse_unary_minus_and_not():
    stmt = parse("SELECT -a FROM t WHERE NOT b = 1")
    assert isinstance(stmt.columns[0].expr, UnaryOp) and stmt.columns[0].expr.op == "-"
    assert isinstance(stmt.where, UnaryOp) and stmt.where.op == "NOT"


def test_parse_like_and_not_like():
    stmt = parse("SELECT a FROM t WHERE a LIKE 'x%' AND NOT a LIKE 'y%'")
    assert stmt.where.left.op == "LIKE"
    assert stmt.where.right.op == "NOT"


def test_parse_in_expr():
    stmt = parse("SELECT a FROM t WHERE a IN (1, 2, 3)")
    assert isinstance(stmt.where, InExpr)
    assert stmt.where.values == [Literal(1), Literal(2), Literal(3)]


def test_parse_is_null_and_is_not_null():
    stmt = parse("SELECT a FROM t WHERE a IS NULL")
    assert isinstance(stmt.where, IsNull) and stmt.where.negated is False
    stmt2 = parse("SELECT a FROM t WHERE a IS NOT NULL")
    assert stmt2.where.negated is True


def test_parse_join_with_alias_and_on():
    stmt = parse("SELECT a FROM t1 x JOIN t2 y ON x.id = y.t1_id")
    assert stmt.from_alias == "x"
    assert len(stmt.joins) == 1
    assert stmt.joins[0].table == "t2"
    assert stmt.joins[0].alias == "y"


def test_left_join_rejected():
    with pytest.raises(ParseError):
        parse("SELECT a FROM t1 LEFT JOIN t2 ON t1.id = t2.id")


def test_parse_group_by_having_order_by_limit():
    stmt = parse(
        "SELECT a, COUNT(*) FROM t GROUP BY a HAVING COUNT(*) > 1 "
        "ORDER BY a DESC LIMIT 5"
    )
    assert stmt.group_by == [ColumnRef(None, "a")]
    assert isinstance(stmt.having, BinaryOp)
    assert stmt.order_by[0].descending is True
    assert stmt.limit == 5


def test_parse_function_call_star_and_distinct():
    stmt = parse("SELECT COUNT(*), COUNT(DISTINCT a) FROM t")
    first = stmt.columns[0].expr
    second = stmt.columns[1].expr
    assert isinstance(first, FunctionCall) and first.args == ["*"]
    assert isinstance(second, FunctionCall) and second.distinct is True


def test_parse_select_item_alias():
    stmt = parse("SELECT a AS x, b y FROM t")
    assert stmt.columns[0].alias == "x"
    assert stmt.columns[1].alias == "y"


def test_parse_update():
    stmt = parse("UPDATE t SET a = 1, b = a + 1 WHERE id = 5")
    assert isinstance(stmt, Update)
    assert stmt.assignments[0][0] == "a"
    assert stmt.where is not None


def test_parse_delete():
    stmt = parse("DELETE FROM t WHERE id = 5")
    assert isinstance(stmt, Delete)


def test_parse_qualified_and_star_column():
    stmt = parse("SELECT t.a, u.* FROM t JOIN u ON t.id = u.t_id")
    assert stmt.columns[0].expr == ColumnRef("t", "a")
    assert isinstance(stmt.columns[1].expr, Star)
    assert stmt.columns[1].expr.table == "u"


def test_trailing_garbage_raises():
    with pytest.raises(ParseError):
        parse("SELECT a FROM t; SELECT b FROM t")  # two statements via parse()


def test_parse_many_splits_on_semicolons():
    stmts = parse_many("CREATE TABLE t (a INTEGER); INSERT INTO t VALUES (1); SELECT * FROM t;")
    assert len(stmts) == 3


def test_parse_many_ignores_trailing_whitespace_and_empty_statements():
    stmts = parse_many("SELECT 1;;  ;\n")
    assert len(stmts) == 1


def test_unexpected_token_raises_parse_error():
    with pytest.raises(ParseError):
        parse("FROB a b c")
