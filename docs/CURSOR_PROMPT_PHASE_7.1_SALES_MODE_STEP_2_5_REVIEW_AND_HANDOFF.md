Finalize and document **Phase 7.1 / Sales Mode / Step 2** after implementation.

Goal:
- review the completed backend/service-layer policy slice
- ensure no customer-facing behavior changed accidentally
- update handoff/docs
- keep scope narrow

Tasks:
1. review all Step 2 changed files for scope creep
2. confirm no Mini App/private bot behavior changed
3. update `docs/CHAT_HANDOFF.md`
4. update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if new temporary decisions were introduced
5. add/update `COMMIT_PUSH_DEPLOY.md` for Step 2
6. run focused tests and smoke checks

Must explicitly confirm:
- `tour.sales_mode` remains source of truth
- backend policy is centralized
- no direct whole-bus booking exists yet
- no operator-assisted whole-bus path exists yet
- no customer surface has been changed

After completion, report:
1. sections changed in docs
2. tests/checks run
3. final next safe step