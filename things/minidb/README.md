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

## `CREATE INDEX`: a real B-tree, and a measured 130x speedup

`CREATE INDEX idx ON t(col)` builds a textbook CLRS-style B-tree
(`btree.py`) over that column. When a query's `WHERE` clause is exactly
a single comparison (`=`, `<`, `<=`, `>`, `>=`) between an indexed column
and a literal — and there's no `JOIN` — the executor looks candidate rows
up in the B-tree instead of scanning the whole table. On a 20,000-row
table, `SELECT id FROM t WHERE amount = 42` measured **~130x faster**
with the index than without (`test_index_gives_a_measured_speedup_on_a_large_table`,
which prints the actual numbers on each run rather than asserting a
specific ratio, since exact timings vary by machine — the assertion is
just "index beats scan," which it does comfortably).

Correctness is enforced structurally, not just tested for: the index
path is only ever a *candidate generator* — `execute_select` always
re-evaluates the complete original `WHERE` expression against every
row the index (or the scan) produces before including it, unconditionally.
That means an index bug could at worst make a query slower (by
returning a candidate set that's too large, immediately filtered back
down to correct), never wrong — and `test_indexed_executor.py` checks
the actual claim that matters anyway: the exact same query against the
exact same data returns identical results with and without an index,
across 20 randomized tables and 8 query shapes, plus after `INSERT`,
`UPDATE`, and `DELETE` on an indexed table.

`UPDATE`/`DELETE` don't maintain the B-tree incrementally — they rebuild
every index on the affected table from scratch afterward. `INSERT` (pure
append) does update indexes incrementally, since appending never
invalidates another row's stored position the way deleting does.
Rebuilding is O(n) instead of O(log n), a deliberate simplicity-over-
performance tradeoff (the same kind `kvstore`'s own `range_query` README
section is upfront about) — it means the B-tree only ever needs
`insert()`, never deletion, which is by far the fussier half of a real
B-tree implementation to get right.

## Architecture

```
minidb/
  lexer.py       hand-written tokenizer (keywords, numbers, strings with
                   '' escaping, operators, -- comments)
  ast_nodes.py     dataclasses for every expression and statement shape
  parser.py         recursive-descent parser; expressions use precedence
                      climbing (OR < AND < NOT < comparison < + - < * / %)
  storage.py         Database/Table: typed columns, INTEGER/REAL/TEXT
                       coercion on insert and update; per-column B-tree
                       indexes
  btree.py            BTree: a CLRS-style B-tree (insert + range search
                        only -- see below for why no deletion is needed)
  executor.py         WHERE/JOIN/GROUP BY/HAVING/ORDER BY/LIMIT/DISTINCT,
                        NULL-aware three-valued AND/OR/NOT, SQLite-matching
                        division/modulo and LIKE semantics, and the
                        index-assisted WHERE evaluation described above
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
- `CREATE INDEX idx ON t(col)` — see above; speeds up simple equality/range
  `WHERE` predicates on that column
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
index use across a `JOIN` or for compound `WHERE` conditions (only a
single simple comparison on an indexed column, see above), transactions,
persistence to disk (everything lives in memory for the lifetime of the
`Database` object), `ALTER TABLE`/`DROP INDEX`.

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

558 tests: the lexer and parser (tokenization edge cases, operator
precedence, every statement shape including `CREATE INDEX`), the
executor against hand-computed expected values (three-valued `NULL`
logic, `JOIN`, `GROUP BY`/`HAVING`, `UPDATE` swap semantics, integer
truncating division), `test_oracle.py` — real cross-checks against
`sqlite3` across `WHERE`, `ORDER BY`/`LIMIT`, `JOIN`, `GROUP BY`/
aggregates, and division/modulo, plus 200 randomized-fuzz trials (random
small integer tables, random `WHERE` clauses) compared row-for-row
against `sqlite3` — `test_btree.py` (the B-tree itself against a
brute-force baseline: equality search, range search, and internal
sortedness, across randomized trees), and `test_indexed_executor.py`
(indexed vs. unindexed results compared across 20 randomized tables and
8 query shapes, including after `INSERT`/`UPDATE`/`DELETE`, plus the
measured-speedup benchmark).

## Possible expansions

- Subquery support (`WHERE id IN (SELECT ...)`, correlated subqueries)
- `LEFT JOIN` (parser already rejects it explicitly rather than silently
  mis-executing it as an `INNER JOIN`)
- Index use across compound `WHERE` conditions (`WHERE a = 1 AND b = 2`
  currently falls back to a full scan even if `a` is indexed) and across
  `JOIN`s
- Disk persistence — `Database` is pure in-memory today
