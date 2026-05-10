# CURSOR_PROMPT_B13D_AUDIT_RETENTION_AND_DOCS_FINALIZE

Review and finalize B13D before commit.

B13D implementation exists but is not committed.

## Current B13D implementation

- Table: `supplier_offer_showcase_publish_attempts`
- Migration: `alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py`
- Model: `app/models/supplier_offer_showcase_publish_attempt.py`
- Enums:
  - `SupplierOfferShowcasePublishAttemptStatus`
  - `SupplierOfferShowcasePublishActorSurface`
- Repository:
  - `app/repositories/supplier_offer_showcase_publish_attempt.py`
- Service:
  - `app/services/supplier_offer_showcase_publish_attempt_service.py`
- Tests:
  - `tests/unit/test_supplier_offer_showcase_publish_attempt.py`
- Live publish path is not wired.

## Critical review item: audit retention vs cascade delete

The current report says:

- FK to `supplier_offers.id ON DELETE CASCADE`
- `SupplierOffer.showcase_publish_attempts` relationship uses cascade delete-orphan

This may be wrong for an audit table.

Please inspect project conventions and decide.

### Required analysis

Check existing related/audit tables and relationships:

- supplier offer bridge/link/audit tables;
- execution attempts;
- telegram idempotency tables;
- payment/order audit style if relevant.

Then decide whether `supplier_offer_showcase_publish_attempts` should use:

1. `ON DELETE CASCADE` + delete-orphan;
2. `ON DELETE RESTRICT` / no cascade;
3. nullable FK + `ON DELETE SET NULL`;
4. existing project convention if clearly established.

### Preferred audit principle

For public publish audit, do not silently delete audit history unless the project convention clearly requires it.

If no strong convention exists, prefer:

- no ORM delete-orphan cascade;
- DB FK `RESTRICT` or `SET NULL`;
- document the choice.

If changing the migration/model is necessary, change it now before commit.

## Docs finalize

Update:

`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`

Add B13D implementation note:
- table/model/repository/service skeleton implemented;
- statuses actually used;
- actor surfaces actually used;
- live publish not wired;
- retention/delete policy decision.

Update:

`docs/B13_CHANNEL_ADAPTER_DESIGN.md`

Add short B13D pointer:
- publish attempt table skeleton exists;
- adapter publish still behavior-preserving;
- no retry/idempotency enforcement yet.

Update:

`docs/CHAT_HANDOFF.md`

Add B13D completed entry:
- migration/table/model/repository/service skeleton;
- no live publish integration;
- no retry behavior;
- no publish readiness changes;
- no Mini App / booking/payment/orders;
- tests run;
- next B13E can wire audit into publish path if approved.

Create/update:

`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`

Include:
- checkpoint;
- migration name;
- model/table fields;
- statuses/actor surfaces;
- retention/delete policy;
- repo/service methods;
- tests run;
- non-goals preserved;
- next likely step:
  - B13E wire attempts into publish path while preserving behavior.

Update:

`docs/CURSOR_PROMPT_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON.md`

Add completion note:
- implemented;
- migration name;
- tests;
- safety confirmations.

Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` only if a real unresolved decision remains.

## Forbidden

Do not wire attempts into live publish.
Do not call Telegram.
Do not change publish behavior.
Do not change publish readiness.
Do not add retries.
Do not add new channels.
Do not touch Mini App.
Do not touch booking/payment/orders.

## Required tests after any migration/model adjustment

Run:

```powershell
python -m alembic upgrade head
python -m compileall app tests
python -m unittest tests/unit/test_supplier_offer_showcase_publish_attempt.py -v
python -m unittest tests/unit/test_supplier_offer_track3_moderation.py -v