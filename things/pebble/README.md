# pebble

A small dynamically-typed scripting language, implemented from scratch: a
hand-written lexer, a recursive-descent parser, and a tree-walking
interpreter. No external dependencies.

```
let greeting = "hello";
print(greeting + ", world");

fn fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}
print(fib(10));  // 55
```

## Language

- **Types**: numbers (floats), strings, booleans, `nil`, lists, functions.
  No classes/objects.
- **Variables**: `let x = 5;` — block-scoped, shadowing allowed.
- **Operators**: `+ - * / %`, comparisons (`< <= > >= == !=`), logic
  (`and or !`) with short-circuiting. `+` also concatenates strings and
  lists.
- **Truthiness**: only `nil` and `false` are falsy — `0` and `""` are
  truthy (unlike some scripting languages, on purpose, to avoid surprises
  in loop counters).
- **Control flow**: `if`/`else`, `while`, C-style `for (init; cond; incr)`,
  `break`, `continue`.
- **Functions**: `fn name(params) { ... }` or anonymous `fn(params) { ... }`
  expressions. Real closures — a nested function captures its enclosing
  scope by reference, not by value (see `examples/closures.pebble`).
- **Lists**: `[1, 2, 3]`, indexed with `list[i]` (negative indices work),
  assignable with `list[i] = v`, concatenated with `+`.
- **Comments**: `// line comment`.

### Built-in functions

| Function | Does |
|---|---|
| `print(...)` | prints space-separated values |
| `len(x)` | length of a list or string |
| `str(x)` / `num(x)` | convert to string / number |
| `type(x)` | `"number"`, `"string"`, `"bool"`, `"nil"`, `"list"`, or `"function"` |
| `range(n)` / `range(a, b)` / `range(a, b, step)` | build a list of numbers |
| `push(list, v)` / `pop(list)` | mutate a list in place |
| `clock()` | seconds since epoch, for timing |

## Usage

```bash
python3 main.py                    # start the REPL
python3 main.py examples/fibonacci.pebble  # run a script (tree-walking interpreter)
python3 main.py examples/fibonacci.pebble --vm  # run it via the bytecode VM instead
```

The REPL buffers input until parens/braces balance, so you can paste a
multi-line function definition and it runs as soon as it's complete.

## Architecture

```
pebble/
  lexer.py         source text -> tokens
  ast_nodes.py     AST node dataclasses (Expr / Stmt subclasses)
  parser.py         recursive-descent parser, standard precedence climbing
  environment.py    scope chain (dict + parent pointer) for variables
  interpreter.py    tree-walking evaluator + Callable/PebbleFunction/closures
  compiler.py         AST -> bytecode compiler (see "Two execution
                       strategies" below)
  bytecode.py           Op enum + Chunk: a flat instruction list + constant
                          pool
  vm.py                   executes a Chunk directly instead of re-walking
                            the AST
  builtins.py        native functions installed into the global scope
  errors.py           LexError / ParseError / RuntimeErrorPebble
  cli.py               run_file(), repl()
```

Notably, `for` is **not** desugared into a `while` loop internally (a
common shortcut). Early on it was, and that broke `continue`: desugaring
`for (init; cond; incr) body` into `while (cond) { body; incr; }` means a
`continue` inside `body` raises past the increment statement entirely,
looping forever without `i` ever changing. `for` gets its own AST node and
interpreter case instead, so `continue` correctly falls through to the
increment before re-checking the condition. (This was caught by an
infinite-loop test hang during development, not by inspection — a good
reminder that "obviously correct" desugarings deserve a test with a
`continue` in a `for` loop specifically.)

## Two execution strategies, and an honest result

`compiler.py` compiles the same AST the tree-walker evaluates into a flat
bytecode `Chunk` (a list of `(Op, operand)` instructions plus a constant
pool), and `vm.py` executes that directly: a `while` loop stepping an
instruction pointer, instead of `interpreter.py`'s recursive
`_evaluate`/`_execute` re-dispatching on AST node type at every single
node, every time. Variable scoping still goes through the *exact same*
`Environment` chain the tree-walker uses — `GET_VAR`/`SET_VAR`/
`DEFINE_VAR` instructions just call `env.get()`/`.assign()`/`.define()`
directly — so closures and scoping semantics are identical by
construction, not by re-deriving them for a second time. `--vm` runs a
script through this path instead; `tests/test_bytecode_equivalence.py`
runs three dozen programs through both engines and requires byte-for-byte
identical output.

The natural assumption going in was "compile once, then run a flat
instruction loop" would be faster than re-walking a tree with reflection-
based dispatch (`getattr(self, f"_eval_{type(node).__name__}")`) on every
node, every time. Measured on `fib(27)`:

| engine | time |
|---|---|
| tree-walking interpreter | 5.0s |
| bytecode VM (initial version) | 12.1s — **2.4x slower** |
| bytecode VM (after reordering dispatch) | 8.3s — still **1.6x slower** |

Profiling the first version showed the bulk of execution time wasn't in
any individual opcode's handler — it was the dispatch `elif` chain itself,
because Python's `if/elif` is a linear scan and the chain listed opcodes
in a fairly arbitrary (roughly categorical) order, so hot opcodes like
`CALL` and `RETURN` sat near the bottom, checked-and-rejected against a
dozen `==` comparisons on every single instruction. Reordering the chain
by measured hit frequency (`GET_VAR`, `CONST`, arithmetic, `CALL`,
`RETURN` first) cut the gap from 2.4x to 1.6x — a real improvement, but
not enough to close it. This tracks with a fairly well-known result in
language-implementation circles: a hand-rolled dispatch loop in pure
Python is competing against CPython's *own* already-optimized function-
call and attribute-lookup machinery, which is what the tree-walker's
`getattr`-based dispatch rides on for free. Beating it usually needs a
host language with real computed-goto/switch dispatch (C, or a Python
extension), not more elif-chain tuning.

What the VM *does* have, and honestly earned rather than assumed going
in: Pebble-level function calls no longer recurse through Python's own
call stack (they push an explicit frame onto a plain list inside one
`while` loop), so Pebble recursion depth isn't tied to Python's default
1000-frame recursion limit. The tree-walking interpreter reliably raises
`RecursionError` on Pebble recursion a few hundred frames deep (each
Pebble call costs several nested Python calls). The VM handled a Pebble
call recursing 100,000 deep with no special configuration at all in
testing. See `test_vm_handles_deeper_recursion_than_the_tree_walking_interpreter`.

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

131 tests across the lexer, parser, interpreter, compiler, and VM: token
scanning (including string escapes and error cases), AST shape for every
grammar construct, operator semantics and type errors, scoping/shadowing,
closures capturing by reference, recursion, all control flow including
`break` and `continue` inside both `while` and `for`, list operations,
every built-in function, bytecode compilation (jump targets patched
correctly for `if`/`while`/`break`/`continue`, functions compiled to
their own chunk with an implicit nil return appended), and the VM/
tree-walker equivalence and deep-recursion tests described above.

## Possible expansions

- Static-ish arity/type checking as an optional pre-pass
- String methods, dictionaries/maps as a builtin type
- A real performance win for the VM would likely need stack-slot-indexed
  locals (resolved at compile time) instead of name-keyed `Environment`
  dict lookups shared with the tree-walker — the current VM optimizes for
  reusing proven-correct scoping code, not for raw speed
- Modules / multi-file programs
