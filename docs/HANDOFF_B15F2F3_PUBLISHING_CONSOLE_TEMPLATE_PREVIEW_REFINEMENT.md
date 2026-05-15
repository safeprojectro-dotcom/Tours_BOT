
---

## 4. HANDOFF content

**HANDOFF file name:**

`HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md`

```md
# HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT

## Project
Tours_BOT

## Block
B15F2/B15F3 — Publishing Console Template / Preview Refinement

## Prerequisites

Closed checkpoints:
- f63244 docs: record publish readiness suggest-only smoke
- 06cc17 feat: add publish readiness suggest-only display metadata
- 48c65cf docs: record publish readiness read-only smoke
- 30321e9 feat: add read-only publish readiness metadata
- d3db31 docs: design guarded auto publish gates

## Goal

Improve publishing console read models with clearer template/preview display metadata.

## Scope

Read-only only:
- preview status
- template family
- template/display summary
- safety note
- next action label/code
- placeholder metadata for tour promotion rows

## Must not happen

- Telegram publish/send/retry
- showcase channel post
- scheduler
- auto-publish
- publish attempt creation
- prepare_conversion_chain execution
- bridge/tour/execution-link mutation
- order/payment/reservation/seat mutation
- migration
- Mini App/B11 routing changes

## Expected result

Publishing console consumers can show clearer read-only states:

- supplier offer showcase candidate
- already published supplier offer
- blocked supplier offer
- tour promotion placeholder
- no public action executed

## Next after B15F2/B15F3

If passed:
- read-only Railway smoke for publishing console preview fields
- then decide between:
  - deeper template library design/read-only rows
  - UI/admin copy polish
  - separate go/no-go before any public publish automation

Do not jump to auto-publish.