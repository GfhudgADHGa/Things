"""Recursive-descent parser: tokens -> AST."""
from __future__ import annotations

from typing import List, Optional

from . import ast_nodes as ast
from .errors import ParseError
from .lexer import Token, TokenType as T


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    # ---- token stream helpers ----

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _at_end(self) -> bool:
        return self._peek().type == T.EOF

    def _advance(self) -> Token:
        if not self._at_end():
            self.current += 1
        return self._previous()

    def _check(self, type_: T) -> bool:
        return not self._at_end() and self._peek().type == type_

    def _match(self, *types: T) -> bool:
        if self._peek().type in types:
            self._advance()
            return True
        return False

    def _consume(self, type_: T, message: str) -> Token:
        if self._check(type_):
            return self._advance()
        raise ParseError(message, self._peek().line)

    # ---- entry point ----

    def parse(self) -> List[ast.Stmt]:
        statements = []
        while not self._at_end():
            statements.append(self._declaration())
        return statements

    # ---- declarations & statements ----

    def _declaration(self) -> ast.Stmt:
        if self._match(T.LET):
            return self._let_declaration()
        if self._match(T.FN):
            return self._function_declaration()
        return self._statement()

    def _let_declaration(self) -> ast.Stmt:
        name = self._consume(T.IDENTIFIER, "Expected variable name.")
        initializer = None
        if self._match(T.EQUAL):
            initializer = self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after variable declaration.")
        return ast.LetStmt(name, initializer)

    def _function_declaration(self) -> ast.Stmt:
        name = self._consume(T.IDENTIFIER, "Expected function name.")
        func_expr = self._function_body(name.lexeme)
        return ast.LetStmt(name, func_expr)

    def _function_body(self, name: str) -> ast.FunctionExpr:
        self._consume(T.LPAREN, f"Expected '(' after function name.")
        params = []
        if not self._check(T.RPAREN):
            while True:
                params.append(self._consume(T.IDENTIFIER, "Expected parameter name."))
                if not self._match(T.COMMA):
                    break
        self._consume(T.RPAREN, "Expected ')' after parameters.")
        self._consume(T.LBRACE, "Expected '{' before function body.")
        body = ast.Block(self._block())
        return ast.FunctionExpr(params, body, name)

    def _statement(self) -> ast.Stmt:
        if self._match(T.IF):
            return self._if_statement()
        if self._match(T.WHILE):
            return self._while_statement()
        if self._match(T.FOR):
            return self._for_statement()
        if self._match(T.RETURN):
            return self._return_statement()
        if self._match(T.BREAK):
            line = self._previous().line
            self._consume(T.SEMICOLON, "Expected ';' after 'break'.")
            return ast.Break(line)
        if self._match(T.CONTINUE):
            line = self._previous().line
            self._consume(T.SEMICOLON, "Expected ';' after 'continue'.")
            return ast.Continue(line)
        if self._match(T.LBRACE):
            return ast.Block(self._block())
        return self._expression_statement()

    def _if_statement(self) -> ast.Stmt:
        self._consume(T.LPAREN, "Expected '(' after 'if'.")
        condition = self._expression()
        self._consume(T.RPAREN, "Expected ')' after if condition.")
        then_branch = self._statement()
        else_branch = self._statement() if self._match(T.ELSE) else None
        return ast.If(condition, then_branch, else_branch)

    def _while_statement(self) -> ast.Stmt:
        self._consume(T.LPAREN, "Expected '(' after 'while'.")
        condition = self._expression()
        self._consume(T.RPAREN, "Expected ')' after while condition.")
        body = self._statement()
        return ast.While(condition, body)

    def _for_statement(self) -> ast.Stmt:
        """C-style for(init; cond; increment) body.

        Kept as its own AST node (rather than desugared into a while loop)
        so that 'continue' can correctly run the increment before looping,
        instead of skipping straight back to the condition.
        """
        self._consume(T.LPAREN, "Expected '(' after 'for'.")

        initializer: Optional[ast.Stmt]
        if self._match(T.SEMICOLON):
            initializer = None
        elif self._match(T.LET):
            initializer = self._let_declaration()
        else:
            initializer = self._expression_statement()

        condition = None if self._check(T.SEMICOLON) else self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after loop condition.")

        increment = None if self._check(T.RPAREN) else self._expression()
        self._consume(T.RPAREN, "Expected ')' after for clauses.")

        body = self._statement()
        return ast.For(initializer, condition, increment, body)

    def _return_statement(self) -> ast.Stmt:
        line = self._previous().line
        value = None if self._check(T.SEMICOLON) else self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after return value.")
        return ast.Return(value, line)

    def _block(self) -> List[ast.Stmt]:
        statements = []
        while not self._check(T.RBRACE) and not self._at_end():
            statements.append(self._declaration())
        self._consume(T.RBRACE, "Expected '}' after block.")
        return statements

    def _expression_statement(self) -> ast.Stmt:
        expr = self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after expression.")
        return ast.ExpressionStmt(expr)

    # ---- expressions, lowest to highest precedence ----

    def _expression(self) -> ast.Expr:
        return self._assignment()

    def _assignment(self) -> ast.Expr:
        expr = self._or()

        if self._match(T.EQUAL):
            equals_line = self._previous().line
            value = self._assignment()
            if isinstance(expr, ast.Variable):
                return ast.Assign(expr.name, value)
            if isinstance(expr, ast.IndexGet):
                return ast.IndexSet(expr.collection, expr.index, value, equals_line)
            raise ParseError("Invalid assignment target.", equals_line)

        return expr

    def _or(self) -> ast.Expr:
        expr = self._and()
        while self._match(T.OR):
            operator = self._previous()
            right = self._and()
            expr = ast.Logical(expr, operator, right)
        return expr

    def _and(self) -> ast.Expr:
        expr = self._equality()
        while self._match(T.AND):
            operator = self._previous()
            right = self._equality()
            expr = ast.Logical(expr, operator, right)
        return expr

    def _equality(self) -> ast.Expr:
        expr = self._comparison()
        while self._match(T.BANG_EQUAL, T.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _comparison(self) -> ast.Expr:
        expr = self._term()
        while self._match(T.GREATER, T.GREATER_EQUAL, T.LESS, T.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _term(self) -> ast.Expr:
        expr = self._factor()
        while self._match(T.PLUS, T.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _factor(self) -> ast.Expr:
        expr = self._unary()
        while self._match(T.STAR, T.SLASH, T.PERCENT):
            operator = self._previous()
            right = self._unary()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _unary(self) -> ast.Expr:
        if self._match(T.BANG, T.MINUS):
            operator = self._previous()
            right = self._unary()
            return ast.Unary(operator, right)
        return self._call()

    def _call(self) -> ast.Expr:
        expr = self._primary()
        while True:
            if self._match(T.LPAREN):
                expr = self._finish_call(expr)
            elif self._match(T.LBRACKET):
                line = self._previous().line
                index = self._expression()
                self._consume(T.RBRACKET, "Expected ']' after index.")
                expr = ast.IndexGet(expr, index, line)
            else:
                break
        return expr

    def _finish_call(self, callee: ast.Expr) -> ast.Expr:
        line = self._previous().line
        arguments = []
        if not self._check(T.RPAREN):
            while True:
                arguments.append(self._expression())
                if not self._match(T.COMMA):
                    break
        self._consume(T.RPAREN, "Expected ')' after arguments.")
        return ast.Call(callee, arguments, line)

    def _primary(self) -> ast.Expr:
        if self._match(T.FALSE):
            return ast.Literal(False)
        if self._match(T.TRUE):
            return ast.Literal(True)
        if self._match(T.NIL):
            return ast.Literal(None)
        if self._match(T.NUMBER, T.STRING):
            return ast.Literal(self._previous().literal)
        if self._match(T.IDENTIFIER):
            return ast.Variable(self._previous())
        if self._match(T.LPAREN):
            expr = self._expression()
            self._consume(T.RPAREN, "Expected ')' after expression.")
            return expr
        if self._match(T.LBRACKET):
            elements = []
            if not self._check(T.RBRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(T.COMMA):
                        break
            self._consume(T.RBRACKET, "Expected ']' after list elements.")
            return ast.ListLiteral(elements)
        if self._match(T.FN):
            return self._function_body("<anonymous>")

        raise ParseError(f"Unexpected token '{self._peek().lexeme}'.", self._peek().line)


def parse(tokens: List[Token]) -> List[ast.Stmt]:
    return Parser(tokens).parse()
