# FairShare — Group Expense & Settlement Management

A database-driven group expense application built with **HTML, CSS, vanilla JavaScript, Python Flask, SQLAlchemy and MySQL**. No AI/ML or third-party APIs are required.

## Features
- Account registration and login with hashed passwords and server-side sessions.
- Create groups and join existing groups using invitation codes.
- Record expenses with a description, category, payer, date, notes, and equal/custom participant splits.
- Edit or delete expenses; the app replaces associated split records transactionally and recalculates balances from the database.
- Group balances, optimized settlement suggestions, and recorded settlement history.
- Search and filter expenses by description, category, payer/group, and date range.
- Category spending visualizations and overview dashboard.
- Monthly group budget with current-month spend, progress percentage, and remaining/over-budget indicator.
- Group activity history for group creation/joining, expense changes, budget changes, and recorded settlements.
- MySQL relational tables, primary/foreign keys, unique constraints, SQL aggregation and joins.
- Responsive UI with a richer green, ivory and lime visual theme.

## Project structure

```text
FairShare/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # create locally; do not commit/share
├── database/
│   ├── schema.sql             # Full CREATE TABLE statements and relationships
│   └── teacher_demo.sql       # Queries for demonstrating MySQL to your teacher
├── DATABASE_PROOF.md          # Step-by-step database demonstration guide
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── README.md
└── TESTING.md
```

## Setup on Windows / VS Code

1. Start the MySQL server.
2. Open `database/schema.sql` in MySQL Workbench and execute the whole script. It creates `fairshare_db` and explicitly defines all eight tables, their columns, primary keys, foreign keys, unique constraints, and indexes. The Flask app also creates any missing tables at startup.
3. Copy `backend/.env.example` to `backend/.env` and enter your own MySQL credentials. If the password contains URL-reserved characters, URL-encode them in `DATABASE_URL` (for example, `!` becomes `%21`). Keep `.env` private.
4. From the project root, activate your virtual environment and install dependencies:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```

5. Start the server:

   ```powershell
   python backend/app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

If your existing environment is already activated and dependencies are installed, you only need step 5.

## Important database update note

The new features add two tables: `group_budgets` and `activity_logs`. SQLAlchemy's `db.create_all()` creates missing tables automatically when the app starts. It does not delete or recreate your existing data. No database reset is required. If you already have a running app, stop it with `Ctrl+C` and restart it after replacing the files.

## Suggested MySQL demonstration

For a full guided demonstration, follow `DATABASE_PROOF.md`. It explains how to show the schema, create sample records through the app, and prove that those records persist in MySQL. The complete set of presentation queries is in `database/teacher_demo.sql`.

Run these queries in MySQL Workbench after using the app:

```sql
USE fairshare_db;
SHOW TABLES;
SELECT * FROM group_members;
SELECT * FROM expenses ORDER BY id DESC;
SELECT * FROM expense_splits ORDER BY expense_id DESC;
SELECT * FROM group_budgets;
SELECT * FROM activity_logs ORDER BY created_at DESC;
```

Example category aggregation:

```sql
SELECT category, SUM(amount) AS total_spent
FROM expenses
GROUP BY category
ORDER BY total_spent DESC;
```

Example join showing group membership:

```sql
SELECT g.name AS group_name, u.name AS member_name, gm.role
FROM group_members gm
JOIN `groups` g ON g.id = gm.group_id
JOIN users u ON u.id = gm.user_id
ORDER BY g.name, u.name;
```

## Security notes

Use a unique random `SECRET_KEY`, keep `backend/.env` out of source control, and never share your database password in screenshots. This is a local academic project; production deployment would additionally require CSRF protection, rate limiting, database migrations, password reset/email verification, and deployment-specific security configuration.

## Dashboard refinement in this ZIP

The logged-in Overview page now includes a six-month spending trend, total and current-month spending, your net position across groups, per-group budget progress, recent transactions, group summaries, and a cross-group activity timeline. These are calculated from the app's existing Flask/MySQL endpoints; no external charting service or API is used.

For safety, this ZIP does not contain your local `backend/.env` file or Python virtual environment. Keep your existing `.env` file in your working copy, or create it from `.env.example` with your own credentials.


## UI refresh
This version includes a warm ivory, espresso, and terracotta visual refresh. The application functionality and MySQL schema are unchanged. For security, local `.env` credentials and the Python `.venv` directory are not included; create `backend/.env` from `backend/.env.example` on your machine.
