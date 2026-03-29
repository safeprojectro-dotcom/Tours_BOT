# Post-Step Checklist

Run after each meaningful Cursor implementation step.

## Environment
- [ ] `.venv` is active
- [ ] correct Python version is used

## Code sanity
- [ ] `python -m compileall app alembic` passed

## Database changes
If schema/models changed:
- [ ] `python -m alembic current`
- [ ] `python -m alembic heads`
- [ ] `python -m alembic downgrade -1`
- [ ] `python -m alembic upgrade head`

## App startup
- [ ] `uvicorn app.main:app --reload` starts
- [ ] `/health` returns OK
- [ ] `/healthz` returns OK

## Tests
If tests exist:
- [ ] `pytest` passed

## Logs
- [ ] no traceback
- [ ] no config/import/ORM errors

## Commit readiness
- [ ] only intended files changed
- [ ] no `.venv`, `__pycache__`, `.egg-info`, or secrets are staged