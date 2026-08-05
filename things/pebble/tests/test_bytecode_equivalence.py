"""The core correctness claim for the VM: it must produce *identical*
output to the tree-walking interpreter on every program, since it's meant
to be a drop-in alternative execution strategy, not a different language.
Reuses the same source snippets test_interpreter.py already exercises,
run through both engines and diffed.
"""
import pytest

from pebble.compiler import compile_program
from pebble.errors import RuntimeErrorPebble
from pebble.interpreter import Interpreter
from pebble.lexer import Lexer
from pebble.parser import parse
from pebble.vm import VM


def run_tree_walker(source):
    output = []
    tokens = Lexer(source).scan_tokens()
    stmts = parse(tokens)
    Interpreter(output=output.append).interpret(stmts)
    return output


def run_vm(source):
    output = []
    tokens = Lexer(source).scan_tokens()
    stmts = parse(tokens)
    chunk = compile_program(stmts)
    VM(output=output.append).run(chunk)
    return output


def assert_same_output(source):
    tree_output = run_tree_walker(source)
    vm_output = run_vm(source)
    assert vm_output == tree_output, f"VM: {vm_output}\ntree-walker: {tree_output}"
    return vm_output


PROGRAMS = [
    "print(1 + 2 * 3 - 4 / 2);",
    "print(7 % 3);",
    'print("foo" + "bar");',
    "print(1 < 2); print(2 <= 2); print(3 > 5);",
    'print(1 == "1"); print(nil == false); print(1 == 1.0);',
    'if (0) { print("zero truthy"); } else { print("zero falsy"); }',
    "print(false and (1 == 1)); print(true or (1 == 2));",
    "print(-5); print(!true); print(!nil);",
    "let x = 10; print(x); x = 20; print(x);",
    'let x = "outer"; { let x = "inner"; print(x); } print(x);',
    'let x = 1; { x = 2; } print(x);',
    'if (1 < 2) { print("yes"); } else { print("no"); }',
    "let i = 0; while (i < 5) { print(i); i = i + 1; }",
    'for (let i = 0; i < 4; i = i + 1) { print("i", i); }',
    "let i = 0; while (true) { if (i == 3) { break; } print(i); i = i + 1; }",
    "for (let i = 0; i < 6; i = i + 1) { if (i % 2 == 0) { continue; } print(i); }",
    "fn add(a, b) { return a + b; } print(add(2, 3));",
    "fn f() { let x = 1; } print(f());",
    "fn fact(n) { if (n <= 1) { return 1; } return n * fact(n - 1); } print(fact(8));",
    """
    fn make_counter() {
        let count = 0;
        fn inc() { count = count + 1; return count; }
        return inc;
    }
    let c1 = make_counter();
    let c2 = make_counter();
    print(c1()); print(c1()); print(c2());
    """,
    "let square = fn(x) { return x * x; }; print(square(5));",
    "let l = [10, 20, 30]; print(l[1]); print(l[-1]);",
    "let l = [1, 2, 3]; l[1] = 99; print(l);",
    "print([1, 2] + [3, 4]);",
    'print(["a", "b"]);',
    'print(len("hello")); print(len([1, 2, 3]));',
    'print(str(42)); print(num("3.5") + 1);',
    'print(type(1)); print(type("s")); print(type(true)); print(type(nil)); print(type([1]));',
    "print(range(3)); print(range(2, 5));",
    "let l = [1, 2]; push(l, 3); print(l); print(pop(l)); print(l);",
    'print(1, "two", 3.0);',
    """
    fn map(list, f) {
        let result = [];
        for (let i = 0; i < len(list); i = i + 1) {
            push(result, f(list[i]));
        }
        return result;
    }
    print(map([1, 2, 3], fn(x) { return x * x; }));
    """,
    """
    fn fib(n) {
        if (n < 2) { return n; }
        return fib(n - 1) + fib(n - 2);
    }
    print(fib(15));
    """,
]


@pytest.mark.parametrize("source", PROGRAMS)
def test_vm_matches_tree_walker_output(source):
    assert_same_output(source)


def test_vm_matches_tree_walker_on_runtime_error_type():
    source = 'print(1 + "a");'
    with pytest.raises(RuntimeErrorPebble):
        run_tree_walker(source)
    with pytest.raises(RuntimeErrorPebble):
        run_vm(source)


def test_vm_matches_tree_walker_on_undefined_variable():
    source = "print(nope);"
    with pytest.raises(RuntimeErrorPebble):
        run_tree_walker(source)
    with pytest.raises(RuntimeErrorPebble):
        run_vm(source)


def test_vm_matches_tree_walker_on_division_by_zero():
    source = "print(1 / 0);"
    with pytest.raises(RuntimeErrorPebble):
        run_tree_walker(source)
    with pytest.raises(RuntimeErrorPebble):
        run_vm(source)


def test_vm_matches_tree_walker_on_wrong_argument_count():
    source = "fn f(a, b) { return a + b; } f(1);"
    with pytest.raises(RuntimeErrorPebble):
        run_tree_walker(source)
    with pytest.raises(RuntimeErrorPebble):
        run_vm(source)


def test_vm_handles_deeper_recursion_than_the_tree_walking_interpreter():
    """The headline real advantage the VM turned out to have: Pebble-level
    function calls push an explicit frame onto a plain list instead of
    recursing through Python's own call stack, so Pebble recursion depth
    isn't tied to Python's ~1000-frame default recursion limit. The
    tree-walking interpreter reliably fails around a few hundred frames
    deep (each Pebble call costs several nested Python calls: _evaluate,
    _eval_Call, execute_block, ...); the VM handles orders of magnitude
    deeper recursion with no special configuration.
    """
    source = """
    fn count_down(n) {
        if (n <= 0) { return 0; }
        return count_down(n - 1);
    }
    print(count_down(5000));
    """
    with pytest.raises(RecursionError):
        run_tree_walker(source)

    vm_output = run_vm(source)
    assert vm_output == ["0"]
