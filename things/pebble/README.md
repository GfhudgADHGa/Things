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
python3 main.py examples/fibonacci.pebble  # run a script
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

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

71 tests across the lexer, parser, and interpreter: token scanning
(including string escapes and error cases), AST shape for every grammar
construct, operator semantics and type errors, scoping/shadowing, closures
capturing by reference, recursion, all control flow including `break` and
`continue` inside both `while` and `for`, list operations, and every
built-in function.

## Possible expansions

- Static-ish arity/type checking as an optional pre-pass
- String methods, dictionaries/maps as a builtin type
- A bytecode compiler + VM instead of tree-walking, for speed
- Modules / multi-file programs
