-- A small tour of what minidb supports. Run with:
--   python3 main.py examples/demo.sql

CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
INSERT INTO users (id, name, age) VALUES
    (1, 'Alice', 30), (2, 'Bob', 25), (3, 'Carol', NULL), (4, 'Dave', 25);

CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER);
INSERT INTO orders (id, user_id, amount) VALUES
    (1, 1, 100), (2, 1, 50), (3, 2, 30), (4, 4, 70);

-- WHERE, IS NULL, LIKE (case-insensitive, like SQLite), ORDER BY with NULLs
SELECT name, age FROM users WHERE age IS NOT NULL ORDER BY age DESC;
SELECT name FROM users WHERE name LIKE 'a%';

-- INNER JOIN
SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id
ORDER BY u.name, o.amount;

-- GROUP BY / HAVING / aggregates, ordering by a select-list alias
SELECT u.name, SUM(o.amount) AS total
FROM users u JOIN orders o ON u.id = o.user_id
GROUP BY u.name
HAVING SUM(o.amount) > 40
ORDER BY total DESC;

-- UPDATE and DELETE
UPDATE users SET age = age + 1 WHERE age IS NOT NULL;
DELETE FROM users WHERE age IS NULL;
SELECT * FROM users ORDER BY id;
