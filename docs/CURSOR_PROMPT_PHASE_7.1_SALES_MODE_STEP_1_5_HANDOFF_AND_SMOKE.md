Finalize and freeze the already completed **Phase 7.1 / Sales Mode / Step 1** without broadening scope.

Goal:
- document the completed Step 1 clearly
- update handoff continuity
- add or refine commit/deploy notes
- run narrow smoke/verification only
- do not introduce any new product behavior

Current completed scope of Step 1:
- `TourSalesMode` enum added
- `Tour.sales_mode` added
- safe default for existing tours: `per_seat`
- admin read/write surfaces expose `sales_mode`
- migration added for `tour_sales_mode` + `tours.sales_mode`

Do not implement anything new in this step.

Tasks:
1. update `docs/CHAT_HANDOFF.md` to reflect:
   - old Phase 7 remains closed enough for staging/MVP
   - active track is Phase 7.1 — tour sales mode
   - Step 1 is completed
   - next safe step is backend/service-layer policy only
2. create or refine `COMMIT_PUSH_DEPLOY.md` for this step
3. run narrow verification:
   - `python -m compileall app alembic tests`
   - `python -m alembic current`
   - `python -m alembic heads`
   - `python -m pytest tests/unit/test_api_admin.py -v`
   - recommended: downgrade -1 / upgrade head
4. verify startup assumptions if local environment allows:
   - app starts
   - `/health`
   - `/healthz`

Must not change:
- booking logic
- payment logic
- Mini App behavior
- private bot behavior
- operator/full-bus flow
- direct whole-bus booking

After completion, report:
1. files changed
2. checks run
3. results
4. final next safe step wording