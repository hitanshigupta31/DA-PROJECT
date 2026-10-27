# FairShare update

## Added in this version
- Search and filters for expense description, category, payer/group, and date range.
- Expense editing and deletion with server-side validation and replacement of related split records.
- Monthly group budgets and current-month spend progress.
- Group activity history for key group and expense actions.
- Category breakdown visualization and a refreshed responsive interface.

## Database compatibility
The app uses `db.create_all()` to create missing tables, including `group_budgets` and `activity_logs`. Existing expense/user/group data is not dropped. Stop the old server and restart with the updated `backend/app.py`.


## Database proof and landing-page refinement
- Replaced the database placeholder script with explicit MySQL `CREATE TABLE IF NOT EXISTS` statements for all eight tables, including primary keys, foreign keys, indexes, and unique constraints.
- Added `database/teacher_demo.sql` with schema inspection, row counts, JOINs, GROUP BY/SUM reports, expense splits, budgets, and activity-history queries.
- Added `DATABASE_PROOF.md` with a practical teacher-demo walkthrough.
- Expanded the landing page with budget, search, and activity feature cards plus a three-step workflow section.
- Kept the existing Flask/SQLAlchemy application and existing database records; no database reset is required.

## Dashboard refinement
- Rebuilt the authenticated overview as a more information-dense workspace dashboard.
- Added a six-month spending trend calculated from saved expenses, without chart APIs or external libraries.
- Added a net-position summary aggregated from each group's balance endpoint.
- Added current-month spend, budget progress per group, group-at-a-glance rows, and a cross-group activity timeline.
- Added direct group-opening actions from dashboard cards and budget cards.
- Kept the existing database schema, authentication, expense workflows, settlement logic, and API provider-free.
- Packaged source files only; local `.env` credentials and the `.venv` environment are intentionally excluded.

## UI refresh
- Refined the visual system with richer sage/ivory surfaces, warmer panel tints, more dimensional cards, improved focus states, and clearer dashboard chart contrast.
- Presentation-only change: no application features, routes, calculations, or database schema changed.


## Editorial UI redesign (visual-only)
- Replaced the pale green/white look with deep indigo, lavender, warm ivory, and coral accents.
- Simplified Overview to three summary metrics, one spending trend, and recent expenses.
- Moved visual emphasis away from repeated dashboard panels; detailed categories remain in Reports and budgets remain available within group workflows.
- Added a separate `frontend/css/ui-redesign.css` stylesheet and cache-busted stylesheet references.
- No database schema, backend routes, calculations, or feature behavior changed.

## Semantic finance UI pass
- Applied the deep-teal palette (#0F766E) with amber highlights and explicit owed/owing/settled semantic colors.
- Reworked the dashboard hero into a compact financial summary with a prominent, data-driven net position.
- Added a live "Who owes whom" preview from the existing settlement suggestions.
- Gave summary cards distinct restrained icon tints, improved contrast, and standardised cards around 16px radii and soft shadows.
- Reduced overview clutter by prioritising balances, six-month spending, and recent expenses; detailed budgets and activity remain in their dedicated workflows.
- No backend routes, database schema, or settlement calculations were changed.

## Mocha & Black UI refinement
- Replaced the dashboard's people illustration with a restrained CSS-only decorative panel to keep the Overview mature and lightweight.
- Applied the Mocha & Black palette: warm ivory, mocha brown, espresso text, and subtle taupe surfaces.
- Preserved the existing Overview structure, Flask routes, database access, expense logic, and settlement navigation.
- Kept settlement details on the Settlements page rather than adding a separate Overview snapshot.

## Coffee Noir dashboard refinement
- Made Total Spending the dominant espresso-filled summary card with white typography.
- Replaced the abstract welcome-side decoration with live “You are owed” and “You owe” figures and a settlement progress indicator.
- Increased monetary figure sizing and enabled tabular numerals for clearer financial scanning.
- Added deterministic initials avatars for recent expense payers and category chips for transaction categories.
- Added a compact monthly spending sparkline, layered shadows, and subtle hover lift.
- Kept existing Flask routes, MySQL schema, and expense/settlement calculations intact.

## UI refresh — Mocha & Burgundy
- Replaced the cream shell with a dark chocolate and burgundy theme.
- Removed the redundant Overview Quick Actions panel.
- Retained the live balance summary, dominant spending card, recent expenses, and monthly trend.
- Updated frontend cache-busting versions to `mocha-burgundy-1`.
