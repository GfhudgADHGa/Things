# minidb

A small SQL engine from scratch: a hand-written tokenizer, a
recursive-descent parser, an in-memory table store, and a query executor
supporting `CREATE TABLE`, `INSERT`, `SELECT` (with `WHERE`, `JOIN`,
`GROUP BY`/`HAVING`/aggregates, `ORDER BY`, `LIMIT`, `DISTINCT`), `UPDATE`,
and `DELETE`. No dependencies.

The correctness proof here is the same idea as `regex` (checked against
Python's `re`) and `difftool` (checked against `difflib`): run the same
schema, data, and query through **Python's own built-in `sqlite3` module**
and require the two engines agree, row for row. SQL has a lot of
easy-to-get-subtly-wrong semantics — three-valued `NULL` logic, what `/`
does to two integers, whether `LIKE` is case-sensitive — and a real,
independently-implemented engine catches exactly the mistakes that
hand-picking your own "expected" values would not.

```bash
python3 main.py examples/demo.sql
```

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
INSERT INTO users VALUES (1, 'Alice', 30), (2, 'Bob', 25), (3, 'Carol', NULL);

SELECT name FROM users WHERE age IS NOT NULL ORDER BY age DESC;
--  name
-- -----
-- Alice
-- Bob

SELECT u.name, SUM(o.amount) AS total
FROM users u JOIN orders o ON u.id = o.user_id
GROUP BY u.name
HAVING SUM(o.amount) > 40
ORDER BY total DESC;
```

## Two real bugs the oracle caught

Both of these were found by `tests/test_oracle.py` disagreeing with
`sqlite3`, not by reasoning about the SQL spec up front — exactly the
point of testing against a real oracle instead of hand-written expected
values.

**`LIKE` case-sensitivity.** The first implementation matched `LIKE`
case-sensitively (the naive reading of "pattern matching"). The very
first oracle test — `'Foo' LIKE 'f%'` — disagreed: SQLite's `LIKE` is
case-insensitive for ASCII by default. Fixed by matching with
`re.IGNORECASE`.

**Integer division truncation.** `-7 / 2` here (and in SQLite) is `-3`.
Python's `-7 // 2` is `-4` — floor division, not truncation toward zero.
SQLite's rule: if *both* operands of `/` or `%` are `INTEGER`, the result
is computed with C-style truncating division; if either operand is
`REAL`, it's ordinary floating-point division. Division or modulo by zero
yields `NULL` (not an error) in both cases. `executor.py`'s `_c_divmod`
implements the truncating version explicitly rather than reaching for
Python's `//`/`%`, which would have quietly given wrong answers for every
query mixing negative integers with division — a case none of the
hand-written executor tests happened to include until the oracle forced
the question.

## Architecture

```
minidb/
  lexer.py       hand-written tokenizer (keywords, numbers, strings with
                   '' escaping, operators, -- comments)
  ast_nodes.py     dataclasses for every expression and statement shape
  parser.py         recursive-descent parser; expressions use precedence
                      climbing (OR < AND < NOT < comparison < + - < * / %)
  storage.py         Database/Table: typed columns, INTEGER/REAL/TEXT
                       coercion on insert and update
  executor.py         WHERE/JOIN/GROUP BY/HAVING/ORDER BY/LIMIT/DISTINCT,
                        NULL-aware three-valued AND/OR/NOT, SQLite-matching
                        division/modulo and LIKE semantics
```

`RowContext` and `GroupContext` (in `executor.py`) are the two "shapes" an
expression can be evaluated against: a `RowContext` resolves a bare
`SELECT SUM(x) ...` as an error (no group to aggregate over yet), while a
`GroupContext` wraps a list of rows and resolves column references against
an arbitrary representative row (matching SQLite's own lenient behavior
for non-aggregated columns in a `GROUP BY` query) and function calls as
real aggregates over the whole group. The rest of the executor — `WHERE`
filtering, `JOIN`, `ORDER BY` — doesn't need to know which kind of context
it's looking at; `eval_expr` dispatches through `.get_column()` /
`.get_aggregate()` either way.

## What's supported

- `CREATE TABLE t (col TYPE [PRIMARY KEY], ...)` — `INTEGER`/`REAL`/`TEXT`
- `INSERT INTO t [(cols...)] VALUES (...), (...)`
- `SELECT [DISTINCT] items FROM t [alias] [JOIN t2 [alias] ON cond]...
  [WHERE cond] [GROUP BY cols] [HAVING cond] [ORDER BY cols [ASC|DESC]]
  [LIMIT n]` — including a `FROM`-less `SELECT 1 + 1` for scalar
  expressions, `t.*`/`*` expansion, and `ORDER BY` referencing a
  `SELECT`-list alias
- `UPDATE t SET col = expr, ... [WHERE cond]` (all assignments read the
  pre-update row, so `SET a = b, b = a` is a real swap)
- `DELETE FROM t [WHERE cond]`
- Expressions: arithmetic, comparisons, `AND`/`OR`/`NOT` with proper
  three-valued `NULL` logic, `LIKE` (with `%`/`_`, case-insensitive),
  `IN (literal, ...)`, `IS [NOT] NULL`
- Aggregates: `COUNT(*)`, `COUNT([DISTINCT] x)`, `SUM`, `AVG`, `MIN`, `MAX`

**Not supported** (out of scope for a small oracle-testable engine, not
bugs): subqueries, `LEFT`/`OUTER`/`CROSS JOIN` (`INNER JOIN`/`JOIN` only),
indexes, transactions, persistence to disk (everything lives in memory
for the lifetime of the `Database` object), `ALTER TABLE`.

## Usage

```bash
python3 main.py script.sql     # run a script non-interactively
python3 main.py                # interactive REPL, statements end in ';'
```

Or as a library:

```python
from minidb import Database, execute, parse_many

db = Database()
for stmt in parse_many("CREATE TABLE t (a INTEGER); INSERT INTO t VALUES (1), (2);"):
    execute(db, stmt)

result = execute(db, next(iter(parse_many("SELECT SUM(a) FROM t"))))
result.headers  # ['SUM(a)']
result.rows     # [[3]]
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

318 tests: the lexer and parser (tokenization edge cases, operator
precedence, every statement shape), the executor against hand-computed
expected values (three-valued `NULL` logic, `JOIN`, `GROUP BY`/`HAVING`,
`UPDATE` swap semantics, integer truncating division), and
`test_oracle.py` — real cross-checks against `sqlite3` across `WHERE`,
`ORDER BY`/`LIMIT`, `JOIN`, `GROUP BY`/aggregates, and division/modulo,
plus 200 randomized-fuzz trials (random small integer tables, random
`WHERE` clauses) compared row-for-row against `sqlite3`, the same
"don't just hand-pick cases you already know work" idea as `difftool`'s
fuzz test against `difflib`.

## Possible expansions

- Subquery support (`WHERE id IN (SELECT ...)`, correlated subqueries)
- `LEFT JOIN` (parser already rejects it explicitly rather than silently
  mis-executing it as an `INNER JOIN`)
- An actual index (the executor does a full table scan for every query;
  there's no B-tree here the way there is in `kvstore`)
- Disk persistence — `Database` is pure in-memory today
