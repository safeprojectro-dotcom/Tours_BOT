# HANDOFF_B15A_ADMIN_PUBLISHING_CONSOLE_DESIGN_TO_NEXT_STEP

## Checkpoint

B13/B14 conversion and booking smoke work is closed:

- Supplier Offer #12 full conversion path verified.
- Tour #6 booking preparation fixed.
- Temporary hold expiry persistence fixed and production-verified.

## B15A purpose

Design the Admin Publishing Console / Channel Publication model.

The Telegram channel will support multiple post types:

- new supplier tours;
- existing tour promotions;
- last seats;
- reminders;
- private transport ads;
- info posts;
- future marketing formats.

The system must prevent admin overload and avoid hardcoding a new feature for every ad type.

## Core principle

Channel Publication = Template + Conversion Target + Safety Policy + Publication Mode.

Supplier Offer Admin prepares products.

Publishing Console manages channel communication.

## Safety

B15A is docs-only.

No code.
No tests.
No migrations.
No production calls.
No publish.
No execution-link mutation.
No booking/payment/order changes.

## Expected next step

Recommended next prompt:

`CURSOR_PROMPT_B15B_READ_ONLY_PUBLISHING_CONSOLE.md`

Goal:

Create read-only admin view/API/Telegram card showing today’s publication candidates, readiness, target, next action, and blockers — no publish or mutation.