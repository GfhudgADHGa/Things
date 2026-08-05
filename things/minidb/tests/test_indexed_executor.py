"""The correctness proof for CREATE INDEX: an index must never change a
query's result, only how fast it's found. Every test here runs the same
query twice against the same data -- once with an index on the relevant
column, once without -- and requires identical results. Then a separate
benchmark demonstrates the actual point of building this: a real,
measured wall-clock speedup on a large table.
"""
import random
import time

import pytest

from minidb import Database, execute, parse_many


def run(db, sql):
    result = None
    for stmt in parse_many(sql):
        result = execute(db, stmt)
    return result


def _build_db(with_index: bool, rows: list) -> Database:
    db = Database()
    run(db, "CREATE TABLE t (id INTEGER PRIMARY KEY, category TEXT, amount INTEGER)")
    for row_id, category, amount in rows:
        run(db, f"INSERT INTO t VALUES ({row_id}, '{category}', {amount})")
    if with_index:
        run(db, "CREATE INDEX idx_amount ON t(amount)")
    return db


def _random_rows(rng: random.Random, n: int) -> list:
    categories = ["a", "b", "c", "d"]
    return [(i, rng.choice(categories), rng.randint(0, 100)) for i in range(n)]


@pytest.mark.parametrize("query", [
    "SELECT id FROM t WHERE amount = 50",
    "SELECT id FROM t WHERE amount > 80",
    "SELECT id FROM t WHERE amount >= 80",
    "SELECT id FROM t WHERE amount < 10",
    "SELECT id FROM t WHERE amount <= 10",
    "SELECT id FROM t WHERE amount = 999",  # matches nothing
    "SELECT id, category FROM t WHERE amount = 50 AND category = 'a'",
    "SELECT COUNT(*) FROM t WHERE amount > 50",
])
@pytest.mark.parametrize("seed", range(20))
def test_indexed_and_unindexed_results_match(query, seed):
    rng = random.Random(seed)
    rows = _random_rows(rng, 200)
    db_plain = _build_db(with_index=False, rows=rows)
    db_indexed = _build_db(with_index=True, rows=rows)

    result_plain = run(db_plain, query)
    result_indexed = run(db_indexed, query)

    assert result_plain.headers == result_indexed.headers
    assert sorted(map(tuple, result_plain.rows)) == sorted(map(tuple, result_indexed.rows))


def test_index_used_after_insert_matches_unindexed(tmp_path=None):
    rng = random.Random(0)
    rows = _random_rows(rng, 50)
    db = _build_db(with_index=True, rows=rows)
    run(db, "INSERT INTO t VALUES (999, 'z', 50)")

    db_plain = _build_db(with_index=False, rows=rows)
    run(db_plain, "INSERT INTO t VALUES (999, 'z', 50)")

    q = "SELECT id FROM t WHERE amount = 50"
    assert sorted(r[0] for r in run(db, q).rows) == sorted(r[0] for r in run(db_plain, q).rows)


def test_index_rebuilt_after_delete_stays_correct():
    rng = random.Random(1)
    rows = _random_rows(rng, 80)
    db = _build_db(with_index=True, rows=rows)
    run(db, "DELETE FROM t WHERE category = 'a'")

    db_plain = _build_db(with_index=False, rows=rows)
    run(db_plain, "DELETE FROM t WHERE category = 'a'")

    for amount in [10, 50, 90]:
        q = f"SELECT id FROM t WHERE amount = {amount}"
        assert sorted(r[0] for r in run(db, q).rows) == sorted(r[0] for r in run(db_plain, q).rows)


def test_index_rebuilt_after_update_stays_correct():
    rng = random.Random(2)
    rows = _random_rows(rng, 80)
    db = _build_db(with_index=True, rows=rows)
    run(db, "UPDATE t SET amount = amount + 1000 WHERE category = 'b'")

    db_plain = _build_db(with_index=False, rows=rows)
    run(db_plain, "UPDATE t SET amount = amount + 1000 WHERE category = 'b'")

    for amount in [1000, 1050, 1100, 50]:
        q = f"SELECT id FROM t WHERE amount >= {amount}"
        expected = sorted(r[0] for r in run(db_plain, q).rows)
        actual = sorted(r[0] for r in run(db, q).rows)
        assert actual == expected


def test_create_index_on_missing_column_raises():
    from minidb import ExecutionError, SchemaError
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER)")
    with pytest.raises((ExecutionError, SchemaError)):
        run(db, "CREATE INDEX idx ON t(nonexistent)")


def test_create_duplicate_index_raises():
    from minidb import SchemaError
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER)")
    run(db, "CREATE INDEX idx1 ON t(a)")
    with pytest.raises(SchemaError):
        run(db, "CREATE INDEX idx2 ON t(a)")


def test_null_values_are_not_indexed_but_still_excluded_correctly():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER, b INTEGER)")
    run(db, "INSERT INTO t VALUES (1, NULL), (2, 5), (NULL, 5)")
    run(db, "CREATE INDEX idx_b ON t(b)")
    result = run(db, "SELECT a FROM t WHERE b = 5")
    assert sorted((r[0] for r in result.rows), key=lambda v: (v is None, v)) == [2, None]


def test_query_plan_falls_back_to_scan_for_non_indexed_column():
    db = Database()
    run(db, "CREATE TABLE t (a INTEGER, b INTEGER)")
    run(db, "INSERT INTO t VALUES (1, 10), (2, 20)")
    run(db, "CREATE INDEX idx_a ON t(a)")
    # WHERE is on b, which has no index -- must still work correctly
    result = run(db, "SELECT a FROM t WHERE b = 20")
    assert [r[0] for r in result.rows] == [2]


# ---- the actual point: a measured speedup ----

def test_index_gives_a_measured_speedup_on_a_large_table():
    rng = random.Random(7)
    rows = _random_rows(rng, 20000)
    db_indexed = _build_db(with_index=True, rows=rows)
    db_plain = _build_db(with_index=False, rows=rows)

    query = "SELECT id FROM t WHERE amount = 42"
    # sanity: same answer either way
    assert sorted(r[0] for r in run(db_plain, query).rows) == sorted(r[0] for r in run(db_indexed, query).rows)

    trials = 5
    start = time.perf_counter()
    for _ in range(trials):
        run(db_plain, query)
    scan_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(trials):
        run(db_indexed, query)
    index_time = time.perf_counter() - start

    print(f"\nfull scan: {scan_time:.4f}s, indexed: {index_time:.4f}s, "
          f"speedup: {scan_time / index_time:.1f}x")
    assert index_time < scan_time
