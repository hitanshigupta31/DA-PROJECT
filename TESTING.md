# FairShare test checklist

## Account and groups
- Register two accounts using different email addresses.
- Create a group with account A and copy the invitation code.
- Log in as account B, open Groups → Join a group, and enter the code.
- Confirm both members are listed in the group and the invitation code is not enough to expose group data to non-members.
- Try joining the same group twice; the application should reject the duplicate membership.

## Expenses and balances
- Add an equal-split expense with both group members selected.
- Add a custom-split expense whose shares add up exactly to the total.
- Try a custom split that does not add up; it should be rejected.
- Edit an expense description, amount, payer, category, date, and split; confirm the balance changes.
- Delete an expense; confirm it disappears and balances are recalculated.
- Search by description and filter by category, payer, and date range.

## Budget and activity
- Set a monthly group budget.
- Add an expense dated in the current month and confirm the budget progress changes.
- Check an expense dated in a different month; it should not count toward current-month spending.
- Confirm group activity shows expense creation, edits/deletions, membership, budget updates, and settlements.

## Settlements and reports
- Verify suggested payments match the net balances.
- Record a payment that does not exceed the current debt; balances should update.
- Attempt to record a payment above the current debt; the application should reject it.
- Compare the category report in FairShare with `SELECT category, SUM(amount) FROM expenses GROUP BY category;` in MySQL Workbench.

## Database
- Confirm `users`, `groups`, `group_members`, `expenses`, `expense_splits`, `settlements`, `group_budgets`, and `activity_logs` exist in `fairshare_db`.
- Restart Flask and verify records remain in MySQL.
