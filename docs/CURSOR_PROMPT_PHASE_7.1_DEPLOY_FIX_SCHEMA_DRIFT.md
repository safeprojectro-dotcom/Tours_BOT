Do not implement new features.

Current production/staging failure root cause is confirmed:
- deployed code reads `tours.sales_mode`
- Railway database schema does not yet contain `tours.sales_mode`
- traceback confirms: `psycopg.errors.UndefinedColumn: column tours.sales_mode does not exist`

Task:
1. update deployment/handoff documentation only
2. clearly record that the failure was caused by missing migration application
3. emphasize that Phase 7.1 requires:
   - `python -m alembic upgrade head`
   before or during deploy
4. do not change business logic
5. do not change Mini App/bot logic
6. do not continue to next feature step until schema is in sync

Update:
- `COMMIT_PUSH_DEPLOY.md`
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if schema drift risk should be called out operationally

After updating docs, report:
1. exact wording added for the deploy-critical warning
2. exact wording added in handoff
3. confirmation that no code paths were changed