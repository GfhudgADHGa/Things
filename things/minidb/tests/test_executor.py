import pytest

from minidb import Database, ExecutionError, SchemaError, execute, parse_many


def run(db, sql):
    """Execute a (possibly multi-statement) script, returning the result of
    the last statement."""
    result = None
    for stmt in parse_many(sql):
        result = execute(db, stmt)
    return result


def make_users_db():
    db = Database()
    run(db, """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
        INSERT INTO users (id, name, age) VALUES
            (1, 'Alice', 30), (2, 'Bob', 25), (3, 'Carol', NULL), (4, 'Dave', 25);
    """)
    return db


# ---- CREATE TABLE / schema ----

def test_create_table_then_select_empty():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER)")
    result = run(db, "SELECT * FROM t")
    assert result.headers == ["a"]
    assert result.rows == []


def test_duplicate_table_name_raises():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER)")
    with pytest.raises(SchemaError):
        run(db, "CREATE TABLE t (a INTEGER)")


def test_select_from_missing_table_raises():
    db = Database()
    with pytest.raises(SchemaError):
        run(db, "SELECT * FROM nope")


# ---- INSERT ----

def test_insert_coerces_types():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER, b REAL, c TEXT)")
    run(db, "INSERT INTO t VALUES (1, 2, 3)")
    result = run(db, "SELECT * FROM t")
    assert result.rows == [[1, 2.0, "3"]]


def test_insert_missing_columns_default_to_null():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER, b INTEGER)")
    run(db, "INSERT INTO t (a) VALUES (1)")
    result = run(db, "SELECT * FROM t")
    assert result.rows == [[1, None]]


def test_insert_wrong_value_count_raises():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER, b INTEGER)")
    with pytest.raises(ExecutionError):
        run(db, "INSERT INTO t VALUES (1)")


def test_insert_returns_row_count():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER)")
    count = run(db, "INSERT INTO t VALUES (1), (2), (3)")
    assert count == 3


# ---- SELECT: WHERE / ORDER BY / LIMIT / DISTINCT ----

def test_select_where_filters_rows():
    db = make_users_db()
    result = run(db, "SELECT name FROM users WHERE age >= 30")
    assert result.rows == [["Alice"]]


def test_select_where_null_comparison_is_never_true():
    db = make_users_db()
    # Carol's age is NULL; `age = NULL` is never true (three-valued logic)
    result = run(db, "SELECT name FROM users WHERE age = NULL")
    assert result.rows == []


def test_select_is_null_and_is_not_null():
    db = make_users_db()
    result = run(db, "SELECT name FROM users WHERE age IS NULL")
    assert result.rows == [["Carol"]]
    result2 = run(db, "SELECT name FROM users WHERE age IS NOT NULL ORDER BY name")
    assert result2.rows == [["Alice"], ["Bob"], ["Dave"]]


def test_select_order_by_desc_puts_nulls_last():
    db = make_users_db()
    result = run(db, "SELECT name FROM users ORDER BY age DESC")
    assert [r[0] for r in result.rows] == ["Alice", "Bob", "Dave", "Carol"]


def test_select_order_by_asc_puts_nulls_first():
    db = make_users_db()
    result = run(db, "SELECT name FROM users ORDER BY age ASC")
    assert [r[0] for r in result.rows] == ["Carol", "Bob", "Dave", "Alice"]


def test_select_order_by_multiple_columns():
    db = make_users_db()
    result = run(db, "SELECT name, age FROM users WHERE age IS NOT NULL ORDER BY age ASC, name DESC")
    assert result.rows == [["Dave", 25], ["Bob", 25], ["Alice", 30]]


def test_select_limit():
    db = make_users_db()
    result = run(db, "SELECT name FROM users ORDER BY id LIMIT 2")
    assert [r[0] for r in result.rows] == ["Alice", "Bob"]


def test_select_distinct():
    db = make_users_db()
    result = run(db, "SELECT DISTINCT age FROM users WHERE age IS NOT NULL ORDER BY age")
    assert result.rows == [[25], [30]]


def test_select_and_or_not_three_valued_logic():
    db = make_users_db()
    # age IS NULL for Carol, so `age > 20 AND age < 40` is NULL (not True) for her -> excluded
    result = run(db, "SELECT name FROM users WHERE age > 20 AND age < 40 ORDER BY name")
    assert [r[0] for r in result.rows] == ["Alice", "Bob", "Dave"]


def test_select_like_is_case_insensitive():
    db = make_users_db()
    result = run(db, "SELECT name FROM users WHERE name LIKE 'a%'")
    assert result.rows == [["Alice"]]


def test_select_like_underscore_wildcard():
    db = make_users_db()
    result = run(db, "SELECT name FROM users WHERE name LIKE 'B_b'")
    assert result.rows == [["Bob"]]


def test_select_in_expr():
    db = make_users_db()
    result = run(db, "SELECT name FROM users WHERE age IN (25, 30) ORDER BY name")
    assert [r[0] for r in result.rows] == ["Alice", "Bob", "Dave"]


def test_select_arithmetic_and_alias():
    db = make_users_db()
    result = run(db, "SELECT name, age + 1 AS next_age FROM users WHERE name = 'Alice'")
    assert result.headers == ["name", "next_age"]
    assert result.rows == [["Alice", 31]]


def test_select_no_from_clause():
    db = Database()
    result = run(db, "SELECT 1 + 1, 'x'")
    assert result.rows == [[2, "x"]]


def test_select_star_expands_all_columns():
    db = make_users_db()
    result = run(db, "SELECT * FROM users WHERE id = 1")
    assert result.headers == ["id", "name", "age"]
    assert result.rows == [[1, "Alice", 30]]


# ---- integer division / modulo (C-style truncation, matching SQLite) ----

def test_integer_division_truncates_toward_zero():
    db = Database()
    result = run(db, "SELECT -7 / 2, 7 / -2, -7 / -2, 7 / 2")
    assert result.rows == [[-3, -3, 3, 3]]


def test_modulo_matches_c_style_truncation():
    db = Database()
    result = run(db, "SELECT -7 % 2, 7 % -2")
    assert result.rows == [[-1, 1]]


def test_division_by_zero_is_null():
    db = Database()
    result = run(db, "SELECT 1 / 0, 1 % 0, 1.0 / 0")
    assert result.rows == [[None, None, None]]


def test_division_with_a_real_operand_uses_float_division():
    db = Database()
    result = run(db, "SELECT 7 / 2.0")
    assert result.rows == [[3.5]]


# ---- JOIN ----

def test_inner_join():
    db = Database()
    run(db, """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER);
        INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');
        INSERT INTO orders VALUES (1, 1, 100), (2, 1, 50), (3, 2, 30);
    """)
    result = run(db, """
        SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id
        ORDER BY u.name, o.amount
    """)
    assert result.rows == [["Alice", 50], ["Alice", 100], ["Bob", 30]]


def test_join_excludes_unmatched_rows():
    db = Database()
    run(db, """
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER);
        INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');
        INSERT INTO orders VALUES (1, 1);
    """)
    result = run(db, "SELECT u.name FROM users u JOIN orders o ON u.id = o.user_id")
    assert result.rows == [["Alice"]]  # Bob has no matching order, INNER JOIN drops him


def test_ambiguous_unqualified_column_after_join_raises():
    db = Database()
    run(db, """
        CREATE TABLE a (id INTEGER);
        CREATE TABLE b (id INTEGER);
        INSERT INTO a VALUES (1);
        INSERT INTO b VALUES (1);
    """)
    with pytest.raises(ExecutionError):
        run(db, "SELECT id FROM a JOIN b ON a.id = b.id")


# ---- GROUP BY / aggregates / HAVING ----

def test_group_by_with_aggregates():
    db = make_users_db()
    result = run(db, "SELECT age, COUNT(*) FROM users GROUP BY age ORDER BY age")
    # Carol's NULL age forms its own group
    assert result.rows == [[None, 1], [25, 2], [30, 1]]


def test_having_filters_groups():
    db = make_users_db()
    result = run(db, "SELECT age, COUNT(*) AS n FROM users GROUP BY age HAVING COUNT(*) > 1")
    assert result.rows == [[25, 2]]


def test_order_by_select_alias_referencing_aggregate():
    db = make_users_db()
    result = run(db, "SELECT age, COUNT(*) AS n FROM users GROUP BY age ORDER BY n DESC, age")
    assert result.rows[0] == [25, 2]


def test_whole_table_aggregate_without_group_by():
    db = make_users_db()
    result = run(db, "SELECT COUNT(*), SUM(age), AVG(age), MIN(age), MAX(age) FROM users")
    assert result.rows == [[4, 80, 80 / 3, 25, 30]]


def test_aggregate_over_empty_result_set():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER)")
    result = run(db, "SELECT COUNT(*), SUM(a), AVG(a), MIN(a), MAX(a) FROM t")
    assert result.rows == [[0, None, None, None, None]]


def test_count_distinct():
    db = make_users_db()
    result = run(db, "SELECT COUNT(DISTINCT age) FROM users")
    assert result.rows == [[2]]  # 25 and 30 (NULL excluded)


def test_aggregate_used_outside_group_context_raises():
    # Referring to an aggregate column result directly per-row without GROUP BY
    # is fine (whole-table group); but calling get_aggregate on a bare
    # RowContext (e.g. inside a WHERE clause) should raise clearly.
    db = make_users_db()
    with pytest.raises(ExecutionError):
        run(db, "SELECT name FROM users WHERE COUNT(*) > 0")


# ---- UPDATE / DELETE ----

def test_update_sets_matching_rows():
    db = make_users_db()
    count = run(db, "UPDATE users SET age = 99 WHERE name = 'Bob'")
    assert count == 1
    result = run(db, "SELECT age FROM users WHERE name = 'Bob'")
    assert result.rows == [[99]]


def test_update_assignments_see_pre_update_values():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER, b INTEGER); INSERT INTO t VALUES (1, 1)")
    run(db, "UPDATE t SET a = b, b = a")  # classic swap; must not use the just-written `a`
    result = run(db, "SELECT a, b FROM t")
    assert result.rows == [[1, 1]]  # started equal, so this doesn't prove much numerically...
    run(db, "UPDATE t SET a = 5")
    run(db, "UPDATE t SET a = b, b = a")
    result2 = run(db, "SELECT a, b FROM t")
    assert result2.rows == [[1, 5]]  # a becomes old b (1), b becomes old a (5)


def test_delete_with_where():
    db = make_users_db()
    count = run(db, "DELETE FROM users WHERE age IS NULL")
    assert count == 1
    result = run(db, "SELECT COUNT(*) FROM users")
    assert result.rows == [[3]]


def test_delete_without_where_clears_table():
    db = make_users_db()
    run(db, "DELETE FROM users")
    result = run(db, "SELECT COUNT(*) FROM users")
    assert result.rows == [[0]]
