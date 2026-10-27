# Demonstrating MySQL in FairShare

FairShare uses **MySQL as its persistent relational database**, Flask for server-side request handling, SQLAlchemy to map Python models to database tables, and HTML/CSS/JavaScript for the user interface.

## What to show your teacher

### 1. Show the actual schema
1. Open `database/schema.sql` in MySQL Workbench.
2. Execute the entire script (lightning-bolt button).
3. In the SCHEMAS panel, refresh `fairshare_db` and expand **Tables**.
4. You should see these eight tables: `users`, `groups`, `group_members`, `expenses`, `expense_splits`, `settlements`, `group_budgets`, and `activity_logs`.
5. Expand any table to show its columns, indexes, and foreign keys. You can also run `SHOW TABLES;` and `DESCRIBE expenses;`.

### 2. Create real data through the application
1. Start the Flask application and open `http://127.0.0.1:5000`.
2. Register two accounts.
3. From the first account, create a group.
4. From the second account, join using the invitation code.
5. Add an expense, set a budget, and record a settlement if appropriate.

### 3. Prove the app writes to MySQL
Open `database/teacher_demo.sql` and run its queries. In particular:
- The table-count query shows stored records.
- The member query demonstrates `JOIN` across users, groups, and group_members.
- The category query demonstrates `SUM`, `GROUP BY`, and sorting.
- The expense-split query shows each member's recorded share.
- The budget and activity queries demonstrate the two added feature tables.

### 4. Show persistence
Create a record in the web app, refresh the page or restart Flask, then query the relevant table again in Workbench. The record should still exist because it is stored in MySQL rather than only in browser memory.

## Important distinction

The SQL script explicitly creates the tables. The Flask application also calls SQLAlchemy `db.create_all()` on startup. This is safe for existing tables: it creates missing tables and does not drop existing tables or records. The SQL file is the visible, reviewable schema; SQLAlchemy is the application's database access layer.

## If Workbench shows no rows

That does not mean the database is not working. It may simply be an empty database. Add test records through FairShare first, then rerun the demonstration queries. Do not run `DROP DATABASE` or delete tables to refresh the project.
