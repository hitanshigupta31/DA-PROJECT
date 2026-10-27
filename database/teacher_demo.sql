-- FairShare: demonstration queries for MySQL Workbench
-- Run each query separately after importing schema.sql and using fairshare_db.
USE fairshare_db;

-- 1. Prove the database contains all eight application tables.
SHOW TABLES;

-- 2. Show the schema/columns of key tables.
DESCRIBE users;
DESCRIBE `groups`;
DESCRIBE group_members;
DESCRIBE expenses;
DESCRIBE expense_splits;
DESCRIBE settlements;
DESCRIBE group_budgets;
DESCRIBE activity_logs;

-- 3. Count stored records in every table (run after adding demo data through the app).
SELECT 'users' AS table_name, COUNT(*) AS records FROM users
UNION ALL SELECT 'groups', COUNT(*) FROM `groups`
UNION ALL SELECT 'group_members', COUNT(*) FROM group_members
UNION ALL SELECT 'expenses', COUNT(*) FROM expenses
UNION ALL SELECT 'expense_splits', COUNT(*) FROM expense_splits
UNION ALL SELECT 'settlements', COUNT(*) FROM settlements
UNION ALL SELECT 'group_budgets', COUNT(*) FROM group_budgets
UNION ALL SELECT 'activity_logs', COUNT(*) FROM activity_logs;

-- 4. JOIN: show each group's members and roles.
SELECT g.name AS group_name, u.name AS member_name, u.email, gm.role, gm.joined_at
FROM group_members gm
JOIN `groups` g ON g.id = gm.group_id
JOIN users u ON u.id = gm.user_id
ORDER BY g.name, u.name;

-- 5. JOIN + GROUP BY: total expense spending by category and group.
SELECT g.name AS group_name, e.category, SUM(e.amount) AS total_spent
FROM expenses e
JOIN `groups` g ON g.id = e.group_id
GROUP BY g.id, g.name, e.category
ORDER BY g.name, total_spent DESC;

-- 6. JOIN: expense ledger showing description, payer, category and amount.
SELECT g.name AS group_name, e.title, e.category, e.amount,
       u.name AS paid_by, e.expense_date
FROM expenses e
JOIN `groups` g ON g.id = e.group_id
JOIN users u ON u.id = e.paid_by
ORDER BY e.expense_date DESC, e.id DESC;

-- 7. Show each expense split (who owes what share for each expense).
SELECT e.title AS expense, g.name AS group_name, u.name AS participant,
       es.share_amount
FROM expense_splits es
JOIN expenses e ON e.id = es.expense_id
JOIN `groups` g ON g.id = e.group_id
JOIN users u ON u.id = es.user_id
ORDER BY e.id, u.name;

-- 8. Show budget versus current-month spending.
SELECT g.name AS group_name, b.monthly_limit,
       COALESCE(SUM(CASE
         WHEN YEAR(e.expense_date) = YEAR(CURDATE())
          AND MONTH(e.expense_date) = MONTH(CURDATE())
         THEN e.amount ELSE 0 END), 0) AS spent_this_month,
       b.monthly_limit - COALESCE(SUM(CASE
         WHEN YEAR(e.expense_date) = YEAR(CURDATE())
          AND MONTH(e.expense_date) = MONTH(CURDATE())
         THEN e.amount ELSE 0 END), 0) AS remaining
FROM group_budgets b
JOIN `groups` g ON g.id = b.group_id
LEFT JOIN expenses e ON e.group_id = g.id
GROUP BY g.id, g.name, b.monthly_limit;

-- 9. Activity history: show recent logged events with the user's name.
SELECT g.name AS group_name, u.name AS performed_by,
       a.action, a.details, a.created_at
FROM activity_logs a
JOIN `groups` g ON g.id = a.group_id
LEFT JOIN users u ON u.id = a.user_id
ORDER BY a.created_at DESC
LIMIT 25;
