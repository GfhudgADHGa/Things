from pebble.bytecode import Op
from pebble.compiler import compile_program
from pebble.errors import ParseError
from pebble.lexer import Lexer
from pebble.parser import parse


def compile_source(source):
    tokens = Lexer(source).scan_tokens()
    stmts = parse(tokens)
    return compile_program(stmts)


def ops_only(chunk):
    return [op for op, _ in chunk.code]


def test_literal_compiles_to_const_pop():
    chunk = compile_source("5;")
    assert ops_only(chunk) == [Op.CONST, Op.POP]
    assert chunk.code[0][1] == 5.0


def test_let_without_initializer_defaults_to_nil_const():
    chunk = compile_source("let x;")
    assert chunk.code[0] == (Op.CONST, None)
    assert chunk.code[1][0] == Op.DEFINE_VAR


def test_binary_expression_compiles_operands_then_operator():
    chunk = compile_source("1 + 2;")
    ops = ops_only(chunk)
    assert ops == [Op.CONST, Op.CONST, Op.ADD, Op.POP]


def test_if_without_else_has_single_patched_jump():
    chunk = compile_source("if (true) { 1; }")
    jumps = [i for i, (op, _) in enumerate(chunk.code) if op == Op.JUMP_IF_FALSE]
    assert len(jumps) == 1
    target = chunk.code[jumps[0]][1]
    assert target == len(chunk.code)  # jumps to the very end


def test_if_with_else_has_two_jumps():
    chunk = compile_source("if (true) { 1; } else { 2; }")
    ops = ops_only(chunk)
    assert Op.JUMP_IF_FALSE in ops
    assert Op.JUMP in ops


def test_while_loop_jumps_back_to_condition():
    chunk = compile_source("while (true) { 1; }")
    jump_indices = [i for i, (op, _) in enumerate(chunk.code) if op == Op.JUMP]
    assert len(jump_indices) == 1
    # the backward jump should target index 0, where the condition check begins
    assert chunk.code[jump_indices[0]][1] == 0


def test_break_outside_loop_raises_at_compile_time():
    import pytest

    with pytest.raises(ParseError):
        compile_source("break;")


def test_continue_outside_loop_raises_at_compile_time():
    import pytest

    with pytest.raises(ParseError):
        compile_source("continue;")


def test_function_expr_compiles_to_separate_chunk():
    chunk = compile_source("fn f(a, b) { return a + b; }")
    make_fn_ops = [op for op, operand in chunk.code if op == Op.MAKE_FUNCTION]
    assert len(make_fn_ops) == 1
    function_chunk = next(operand for op, operand in chunk.code if op == Op.MAKE_FUNCTION)
    assert function_chunk.param_names == ["a", "b"]
    assert function_chunk.name == "f"


def test_function_without_explicit_return_gets_implicit_nil_return():
    chunk = compile_source("fn f() { let x = 1; }")
    function_chunk = next(operand for op, operand in chunk.code if op == Op.MAKE_FUNCTION)
    assert function_chunk.code[-2] == (Op.CONST, None)
    assert function_chunk.code[-1][0] == Op.RETURN


def test_block_emits_scope_enter_and_exit():
    chunk = compile_source("{ let x = 1; }")
    ops = ops_only(chunk)
    assert ops[0] == Op.ENTER_SCOPE
    assert ops[-1] == Op.EXIT_SCOPE


def test_list_literal_compiles_elements_then_build_list():
    chunk = compile_source("[1, 2, 3];")
    ops = ops_only(chunk)
    assert ops == [Op.CONST, Op.CONST, Op.CONST, Op.BUILD_LIST, Op.POP]
    build_list_operand = chunk.code[3][1]
    assert build_list_operand == 3


def test_call_expression_includes_arg_count_and_line():
    chunk = compile_source("foo(1, 2, 3);")
    call_operand = next(operand for op, operand in chunk.code if op == Op.CALL)
    argc, line = call_operand
    assert argc == 3
