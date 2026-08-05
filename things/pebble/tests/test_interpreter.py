import pytest

from pebble.cli import run_source
from pebble.errors import RuntimeErrorPebble
from pebble.interpreter import Interpreter


def run(source):
    output = []
    interpreter = Interpreter(output=output.append)
    run_source(source, interpreter)
    return output


# ---- arithmetic & literals ----

def test_arithmetic():
    assert run("print(1 + 2 * 3 - 4 / 2);") == ["5"]


def test_modulo():
    assert run("print(7 % 3);") == ["1"]


def test_integers_print_without_decimal():
    assert run("print(4 / 2);") == ["2"]


def test_float_prints_with_decimal():
    assert run("print(5 / 2);") == ["2.5"]


def test_string_concat():
    assert run('print("foo" + "bar");') == ["foobar"]


def test_comparisons():
    assert run("print(1 < 2); print(2 <= 2); print(3 > 5);") == ["true", "true", "false"]


def test_equality_across_types():
    assert run('print(1 == "1"); print(nil == false); print(1 == 1.0);') == [
        "false",
        "false",
        "true",
    ]


def test_truthiness_only_nil_and_false_are_falsy():
    assert run('if (0) { print("zero truthy"); } else { print("zero falsy"); }') == [
        "zero truthy"
    ]
    assert run('if ("") { print("empty truthy"); } else { print("empty falsy"); }') == [
        "empty truthy"
    ]
    assert run('if (nil) { print("nil truthy"); } else { print("nil falsy"); }') == [
        "nil falsy"
    ]


def test_logical_and_or_short_circuit_and_return_operand():
    assert run("print(false and (1 / 0));") == ["false"]
    assert run("print(true or (1 / 0));") == ["true"]
    assert run("print(1 and 2);") == ["2"]


def test_unary_negate_and_not():
    assert run("print(-5); print(!true); print(!nil);") == ["-5", "false", "true"]


def test_mismatched_addition_raises():
    with pytest.raises(RuntimeErrorPebble):
        run('print(1 + "a");')


def test_division_by_zero_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("print(1 / 0);")


# ---- variables & scoping ----

def test_variable_declaration_and_use():
    assert run("let x = 10; print(x);") == ["10"]


def test_reassignment():
    assert run("let x = 1; x = 2; print(x);") == ["2"]


def test_undefined_variable_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("print(nope);")


def test_block_scoping_shadows_outer():
    out = run(
        """
        let x = "outer";
        {
            let x = "inner";
            print(x);
        }
        print(x);
        """
    )
    assert out == ["inner", "outer"]


def test_assignment_targets_enclosing_scope_not_shadow():
    out = run(
        """
        let x = 1;
        {
            x = 2;
        }
        print(x);
        """
    )
    assert out == ["2"]


# ---- control flow ----

def test_if_else():
    assert run('if (1 < 2) { print("yes"); } else { print("no"); }') == ["yes"]


def test_while_loop():
    out = run("let i = 0; while (i < 3) { print(i); i = i + 1; }")
    assert out == ["0", "1", "2"]


def test_for_loop():
    out = run('for (let i = 0; i < 3; i = i + 1) { print("i", i); }')
    assert out == ["i 0", "i 1", "i 2"]


def test_break_exits_loop():
    out = run("let i = 0; while (true) { if (i == 3) { break; } print(i); i = i + 1; }")
    assert out == ["0", "1", "2"]


def test_continue_skips_rest_of_body():
    out = run(
        """
        for (let i = 0; i < 5; i = i + 1) {
            if (i % 2 == 0) { continue; }
            print(i);
        }
        """
    )
    assert out == ["1", "3"]


# ---- functions & closures ----

def test_function_call_and_return():
    assert run("fn add(a, b) { return a + b; } print(add(2, 3));") == ["5"]


def test_function_without_return_yields_nil():
    assert run("fn f() { let x = 1; } print(f());") == ["nil"]


def test_recursion():
    out = run(
        """
        fn fact(n) {
            if (n <= 1) { return 1; }
            return n * fact(n - 1);
        }
        print(fact(6));
        """
    )
    assert out == ["720"]


def test_closures_capture_by_reference():
    out = run(
        """
        fn make_counter() {
            let count = 0;
            fn inc() { count = count + 1; return count; }
            return inc;
        }
        let c1 = make_counter();
        let c2 = make_counter();
        print(c1()); print(c1()); print(c2());
        """
    )
    assert out == ["1", "2", "1"]


def test_anonymous_function_expression():
    assert run("let square = fn(x) { return x * x; }; print(square(5));") == ["25"]


def test_wrong_argument_count_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("fn f(a, b) { return a + b; } f(1);")


def test_calling_non_function_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("let x = 5; x();")


# ---- lists ----

def test_list_literal_and_index():
    assert run("let l = [10, 20, 30]; print(l[1]);") == ["20"]


def test_negative_index():
    assert run("let l = [10, 20, 30]; print(l[-1]);") == ["30"]


def test_index_assignment():
    assert run("let l = [1, 2, 3]; l[1] = 99; print(l);") == ["[1, 99, 3]"]


def test_list_out_of_range_raises():
    with pytest.raises(RuntimeErrorPebble):
        run("let l = [1]; print(l[5]);")


def test_list_concatenation():
    assert run("print([1, 2] + [3, 4]);") == ["[1, 2, 3, 4]"]


def test_nested_list_printing_quotes_strings():
    assert run('print(["a", "b"]);') == ['["a", "b"]']


# ---- builtins ----

def test_builtin_len():
    assert run('print(len("hello")); print(len([1, 2, 3]));') == ["5", "3"]


def test_builtin_str_and_num():
    assert run('print(str(42)); print(num("3.5") + 1);') == ["42", "4.5"]


def test_builtin_type():
    out = run(
        'print(type(1)); print(type("s")); print(type(true)); '
        'print(type(nil)); print(type([1])); print(type(fn() {}));'
    )
    assert out == ["number", "string", "bool", "nil", "list", "function"]


def test_builtin_range():
    assert run("print(range(3));") == ["[0, 1, 2]"]
    assert run("print(range(2, 5));") == ["[2, 3, 4]"]


def test_builtin_push_and_pop():
    out = run(
        """
        let l = [1, 2];
        push(l, 3);
        print(l);
        print(pop(l));
        print(l);
        """
    )
    assert out == ["[1, 2, 3]", "3", "[1, 2]"]


def test_print_multiple_arguments_space_separated():
    assert run('print(1, "two", 3.0);') == ["1 two 3"]
