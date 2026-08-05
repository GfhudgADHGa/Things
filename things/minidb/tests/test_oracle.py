"""Cross-checks minidb's query results against Python's built-in `sqlite3`
module, used purely as an independent oracle: run the same schema, data,
and query through both engines and require identical result sets.

This is the same testing philosophy used elsewhere in this repo (Python's
`re`/`difflib` as oracles, Pillow as a GIF-decode oracle, published perft
values for chess) -- comparing against a real, independently-implemented
engine catches bugs that hand-written expected-value tests would miss
because the same misunderstanding that produced the bug would also have
produced the wrong "expected" value.

Two real, interesting SQL semantics were only found this way (see the
module docstring in executor.py for the fixes):
  - LIKE is case-insensitive by default in SQLite.
  - Integer `/` and `%` truncate toward zero (C-style), not Python's
    floor-based `//`/`%`.
"""
import random
import sqlite3

import pytest

from minidb import Database, execute, parse_many


def _run_minidb(schema_sql: str, query_sql: str):
    db = Database()
    for stmt in parse_many(schema_sql):
        execute(db, stmt)
    result = execute(db, next(iter(parse_many(query_sql))))
    return result.headers, result.rows


def _run_sqlite(schema_sql: str, query_sql: str):
    con = sqlite3.connect(":memory:")
    try:
        cur = con.cursor()
        cur.executescript(schema_sql)
        cur.execute(query_sql)
        rows = [list(r) for r in cur.fetchall()]
        headers = [d[0] for d in cur.description]
        return headers, rows
    finally:
        con.close()


def _normalize(rows):
    # SQLite's Python driver returns 0/1 ints for boolean results; minidb
    # returns Python bools. Normalize so the comparison isn't sensitive to
    # that (deliberate, documented) representational difference.
    def norm(v):
        return int(v) if isinstance(v, bool) else v
    return [[norm(v) for v in row] for row in rows]


def _sort_key(row):
    return [(0,) if v is None else (1, v) for v in row]


def assert_same_results(schema_sql: str, query_sql: str, order_sensitive: bool = False):
    mini_headers, mini_rows = _run_minidb(schema_sql, query_sql)
    sqlite_headers, sqlite_rows = _run_sqlite(schema_sql, query_sql)
    mini_rows = _normalize(mini_rows)
    sqlite_rows = _normalize(sqlite_rows)
    if order_sensitive:
        assert mini_rows == sqlite_rows, (
            f"\nquery: {query_sql}\nminidb:  {mini_rows}\nsqlite3: {sqlite_rows}"
        )
    else:
        assert sorted(mini_rows, key=_sort_key) == sorted(sqlite_rows, key=_sort_key), (
            f"\nquery: {query_sql}\nminidb:  {mini_rows}\nsqlite3: {sqlite_rows}"
        )


USERS_SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
INSERT INTO users (id, name, age) VALUES
    (1, 'Alice', 30), (2, 'Bob', 25), (3, 'Carol', NULL), (4, 'Dave', 25), (5, 'eve', 41);
"""

ORDERS_SCHEMA = USERS_SCHEMA + """
CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER);
INSERT INTO orders (id, user_id, amount) VALUES
    (1, 1, 100), (2, 1, 50), (3, 2, 30), (4, 4, 70), (5, 99, 10);
"""


@pytest.mark.parametrize("query", [
    "SELECT * FROM users",
    "SELECT name, age FROM users",
    "SELECT id FROM users WHERE age > 25",
    "SELECT id FROM users WHERE age >= 25 AND age <= 30",
    "SELECT id FROM users WHERE age = 25 OR age = 30",
    "SELECT id FROM users WHERE NOT age = 25",
    "SELECT id FROM users WHERE age != 25",
    "SELECT id FROM users WHERE age IS NULL",
    "SELECT id FROM users WHERE age IS NOT NULL",
    "SELECT id FROM users WHERE age = NULL",  # always empty: NULL comparisons are unknown
    "SELECT id FROM users WHERE age IN (25, 30)",
    "SELECT id FROM users WHERE name LIKE 'a%'",
    "SELECT id FROM users WHERE name LIKE 'A%'",  # case-insensitive LIKE
    "SELECT id FROM users WHERE name LIKE '_ob'",
    "SELECT id FROM users WHERE name LIKE '%o%'",
    "SELECT DISTINCT age FROM users",
    "SELECT name, age + 1 FROM users",
    "SELECT name FROM users WHERE age * 2 > 50",
])
def test_where_and_projection_matches_sqlite(query):
    assert_same_results(USERS_SCHEMA, query)


@pytest.mark.parametrize("query", [
    "SELECT id FROM users ORDER BY age",
    "SELECT id FROM users ORDER BY age DESC",
    "SELECT id FROM users ORDER BY age ASC, name DESC",
    "SELECT id FROM users ORDER BY name LIMIT 2",
    "SELECT id FROM users ORDER BY id DESC LIMIT 0",
    "SELECT id FROM users ORDER BY id LIMIT 100",
])
def test_order_by_and_limit_matches_sqlite(query):
    assert_same_results(USERS_SCHEMA, query, order_sensitive=True)


@pytest.mark.parametrize("query", [
    "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id",
    "SELECT u.name, o.amount FROM users u INNER JOIN orders o ON u.id = o.user_id "
    "WHERE o.amount > 40",
    "SELECT COUNT(*) FROM users u JOIN orders o ON u.id = o.user_id",
])
def test_join_matches_sqlite(query):
    assert_same_results(ORDERS_SCHEMA, query)


@pytest.mark.parametrize("query", [
    "SELECT age, COUNT(*) FROM users GROUP BY age",
    "SELECT age, COUNT(*) FROM users GROUP BY age HAVING COUNT(*) > 1",
    "SELECT COUNT(*), SUM(age), AVG(age), MIN(age), MAX(age) FROM users",
    "SELECT COUNT(*), SUM(age), AVG(age), MIN(age), MAX(age) FROM users WHERE age IS NULL",
    "SELECT COUNT(DISTINCT age) FROM users",
    "SELECT u.id, SUM(o.amount) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id",
])
def test_group_by_and_aggregates_match_sqlite(query):
    assert_same_results(ORDERS_SCHEMA, query)


@pytest.mark.parametrize("query", [
    "SELECT -7 / 2",
    "SELECT 7 / -2",
    "SELECT -7 / -2",
    "SELECT 7 / 2",
    "SELECT -7 % 2",
    "SELECT 7 % -2",
    "SELECT -7 % -2",
    "SELECT 1 / 0",
    "SELECT 1 % 0",
    "SELECT 7 / 2.0",
    "SELECT 7.0 / 2",
])
def test_integer_division_and_modulo_match_sqlite(query):
    assert_same_results(USERS_SCHEMA, query)


def test_update_and_select_afterward_match_sqlite():
    schema = USERS_SCHEMA + "UPDATE users SET age = age + 1 WHERE age IS NOT NULL;"
    assert_same_results(schema, "SELECT id, age FROM users ORDER BY id", order_sensitive=True)


def test_delete_and_select_afterward_match_sqlite():
    schema = USERS_SCHEMA + "DELETE FROM users WHERE age < 30;"
    assert_same_results(schema, "SELECT id FROM users ORDER BY id", order_sensitive=True)


# ---- randomized fuzz comparison ----
#
# Small random integer tables plus randomly-generated WHERE clauses,
# compared against sqlite3 across many trials -- the same "don't just
# hand-pick cases you already know work" idea as difftool's fuzz test
# against difflib.

_COMPARISONS = ["=", "!=", "<", "<=", ">", ">="]


def _random_schema_and_data(rng: random.Random) -> str:
    n = rng.randint(0, 8)
    values = []
    for i in range(n):
        a = rng.choice([str(rng.randint(-10, 10)), "NULL"])
        b = rng.choice([str(rng.randint(-10, 10)), "NULL"])
        values.append(f"({i}, {a}, {b})")
    stmt = "CREATE TABLE t (id INTEGER, a INTEGER, b INTEGER);"
    if values:
        stmt += f"INSERT INTO t VALUES {', '.join(values)};"
    return stmt


def _random_where(rng: random.Random) -> str:
    op = rng.choice(_COMPARISONS)
    left = rng.choice(["a", "b"])
    right = rng.choice(["a", "b", str(rng.randint(-10, 10))])
    clause = f"{left} {op} {right}"
    if rng.random() < 0.5:
        joiner = rng.choice(["AND", "OR"])
        op2 = rng.choice(_COMPARISONS)
        left2 = rng.choice(["a", "b"])
        right2 = rng.choice(["a", "b", str(rng.randint(-10, 10))])
        clause = f"({clause}) {joiner} ({left2} {op2} {right2})"
    return clause


@pytest.mark.parametrize("seed", range(200))
def test_fuzz_where_clauses_match_sqlite(seed):
    rng = random.Random(seed)
    schema = _random_schema_and_data(rng)
    where = _random_where(rng)
    query = f"SELECT id FROM t WHERE {where}"
    assert_same_results(schema, query)
