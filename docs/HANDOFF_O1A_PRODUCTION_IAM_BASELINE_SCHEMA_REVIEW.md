# HANDOFF_O1A_PRODUCTION_IAM_BASELINE_SCHEMA_REVIEW

## Project

Tours_BOT

## Block

O1A — Production IAM Baseline Design / Schema Review

## Purpose

Inspect current identity/auth schema and document how production IAM should reuse existing User/Supplier/admin/supplier-auth foundations without creating duplicate identity systems.

## Mode

Docs-only schema review / design review.

## Included

- User / Telegram identity inventory;
- Mini App identity review;
- Supplier identity review;
- Supplier admin auth review;
- Admin auth review;
- order ownership review;
- reuse vs add vs avoid-duplication rules;
- target production IAM model;
- access policy matrix;
- recommended implementation sequence;
- open decisions.

## Excluded

- no app code;
- no tests;
- no migrations;
- no endpoints;
- no auth implementation;
- no permission implementation;
- no invite flow;
- no QR;
- no manifest;
- no driver UI;
- no Layer A mutation.

## Expected files

- `docs/O1A_PRODUCTION_IAM_BASELINE_SCHEMA_REVIEW.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

## Verification expected

```bash
git diff -- docs/O1A_PRODUCTION_IAM_BASELINE_SCHEMA_REVIEW.md
git diff -- docs/CHAT_HANDOFF.md
git diff -- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
git status --short