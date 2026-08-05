import pytest

from pebble.compiler import compile_program
from pebble.errors import RuntimeErrorPebble
from pebble.lexer import Lexer
from pebble.parser import parse
from pebble.vm import VM, BytecodeFunction


def run(source):
    output = []
    tokens = Lexer(source).scan_tokens()
    stmts = parse(tokens)
    chunk = compile_program(stmts)
    VM(output=output.append).run(chunk)
    return output


def test_calling_non_function_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("let x = 5; x();")


def test_list_index_out_of_range_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("let l = [1]; print(l[5]);")


def test_negating_non_number_raises():
    with pytest.raises(RuntimeErrorPebble):
        run('-"hello";')


def test_bytecode_function_repr_includes_name():
    tokens = Lexer("fn greet() { return nil; }").scan_tokens()
    stmts = parse(tokens)
    chunk = compile_program(stmts)
    vm = VM()
    vm.run(chunk)
    fn = vm.globals.get("greet", 1)
    assert isinstance(fn, BytecodeFunction)
    assert "greet" in repr(fn)


def test_top_level_script_can_fall_off_the_end_without_return():
    # a plain script chunk has no explicit RETURN appended (unlike function
    # chunks) -- running off the end of it must not crash
    assert run("let x = 1; print(x);") == ["1"]


def test_global_functions_are_visible_to_each_other():
    output = run(
        """
        fn is_even(n) {
            if (n == 0) { return true; }
            return is_odd(n - 1);
        }
        fn is_odd(n) {
            if (n == 0) { return false; }
            return is_even(n - 1);
        }
        print(is_even(10));
        print(is_odd(10));
        """
    )
    assert output == ["true", "false"]


def test_nested_closures_capture_independently():
    output = run(
        """
        fn make_adder(n) {
            return fn(x) { return x + n; };
        }
        let add5 = make_adder(5);
        let add10 = make_adder(10);
        print(add5(1));
        print(add10(1));
        """
    )
    assert output == ["6", "11"]


def test_short_circuit_and_does_not_evaluate_right_side():
    # dividing by zero on the right side would raise if it were evaluated
    output = run('print(false and (1 / 0 == 1));')
    assert output == ["false"]


def test_short_circuit_or_does_not_evaluate_right_side():
    output = run('print(true or (1 / 0 == 1));')
    assert output == ["true"]
