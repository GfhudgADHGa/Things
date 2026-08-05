import pytest

from pebble import ast_nodes as ast
from pebble.errors import ParseError
from pebble.lexer import Lexer
from pebble.parser import parse


def parse_source(source):
    return parse(Lexer(source).scan_tokens())


def test_parse_let_declaration():
    stmts = parse_source("let x = 5;")
    assert len(stmts) == 1
    assert isinstance(stmts[0], ast.LetStmt)
    assert stmts[0].name.lexeme == "x"
    assert isinstance(stmts[0].initializer, ast.Literal)
    assert stmts[0].initializer.value == 5.0


def test_parse_let_without_initializer():
    stmts = parse_source("let x;")
    assert stmts[0].initializer is None


def test_parse_binary_precedence():
    stmts = parse_source("1 + 2 * 3;")
    expr = stmts[0].expression
    assert isinstance(expr, ast.Binary)
    assert expr.operator.lexeme == "+"
    assert isinstance(expr.right, ast.Binary)
    assert expr.right.operator.lexeme == "*"


def test_parse_function_declaration_desugars_to_let():
    stmts = parse_source("fn add(a, b) { return a + b; }")
    assert isinstance(stmts[0], ast.LetStmt)
    assert stmts[0].name.lexeme == "add"
    fn = stmts[0].initializer
    assert isinstance(fn, ast.FunctionExpr)
    assert [p.lexeme for p in fn.params] == ["a", "b"]


def test_parse_if_else():
    stmts = parse_source("if (true) { 1; } else { 2; }")
    assert isinstance(stmts[0], ast.If)
    assert stmts[0].else_branch is not None


def test_parse_if_without_else():
    stmts = parse_source("if (true) { 1; }")
    assert stmts[0].else_branch is None


def test_parse_while():
    stmts = parse_source("while (true) { break; }")
    assert isinstance(stmts[0], ast.While)
    assert isinstance(stmts[0].body.statements[0], ast.Break)


def test_parse_for_produces_for_node():
    stmts = parse_source("for (let i = 0; i < 3; i = i + 1) { print(i); }")
    for_stmt = stmts[0]
    assert isinstance(for_stmt, ast.For)
    assert isinstance(for_stmt.initializer, ast.LetStmt)
    assert isinstance(for_stmt.condition, ast.Binary)
    assert isinstance(for_stmt.increment, ast.Assign)


def test_parse_for_with_omitted_clauses():
    stmts = parse_source("for (;;) { break; }")
    for_stmt = stmts[0]
    assert for_stmt.initializer is None
    assert for_stmt.condition is None
    assert for_stmt.increment is None


def test_parse_list_literal():
    stmts = parse_source("[1, 2, 3];")
    expr = stmts[0].expression
    assert isinstance(expr, ast.ListLiteral)
    assert len(expr.elements) == 3


def test_parse_index_get():
    stmts = parse_source("x[0];")
    expr = stmts[0].expression
    assert isinstance(expr, ast.IndexGet)


def test_parse_index_assignment():
    stmts = parse_source("x[0] = 5;")
    expr = stmts[0].expression
    assert isinstance(expr, ast.IndexSet)


def test_parse_assignment_to_non_target_raises():
    with pytest.raises(ParseError):
        parse_source("1 = 2;")


def test_parse_call_expression():
    stmts = parse_source("foo(1, 2, 3);")
    expr = stmts[0].expression
    assert isinstance(expr, ast.Call)
    assert len(expr.arguments) == 3


def test_parse_anonymous_function():
    stmts = parse_source("let f = fn(x) { return x; };")
    assert isinstance(stmts[0].initializer, ast.FunctionExpr)
    assert stmts[0].initializer.name == "<anonymous>"


def test_parse_missing_semicolon_raises():
    with pytest.raises(ParseError):
        parse_source("let x = 5")


def test_parse_unclosed_paren_raises():
    with pytest.raises(ParseError):
        parse_source("(1 + 2;")


def test_parse_logical_and_or():
    stmts = parse_source("true and false or true;")
    expr = stmts[0].expression
    assert isinstance(expr, ast.Logical)
    assert expr.operator.lexeme == "or"
