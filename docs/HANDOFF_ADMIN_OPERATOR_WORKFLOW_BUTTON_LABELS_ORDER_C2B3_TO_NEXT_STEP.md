# HANDOFF_ADMIN_OPERATOR_WORKFLOW_BUTTON_LABELS_ORDER_C2B3_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — C2B3

## Goal

Rename/reorder current Telegram admin buttons according to accepted UX policy.

## Allowed

- Rename labels
- Reorder rows
- Update tests
- Update docs

## Not allowed

- New actions
- New callbacks
- Publish button
- Bridge button
- Activate catalog button
- Execution link button
- Booking/payment changes
- Mini App changes

## Desired button order

1. Actualizează / Preview
2. Pregătește / Aprobă text
3. Aprobă oferta / Respinge oferta
4. Orders / Requests
5. Previous / Next
6. Back / Home

## Next possible slice after C2B3

Manual Telegram UX check, then decide:
- legacy moderation confirmation,
- or pause admin workflow and return to business-plan open items.