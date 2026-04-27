You are continuing Tours_BOT after B4.2.

Goal:
B4.2.1 — Marketing Template Polish.

Problem:
B4.2 works, but the Telegram draft still has polish issues:
- discount code is shown even when there is no actual discount percent/amount
- technical line “Vanzare / Plata” appears in public post
- program text can contain embedded “Program:” and “Inclus:” lines, causing duplicate included info
- included/excluded can be duplicated between program block and separate include block
- extra spacing before disclaimer
- mixed language is acceptable for supplier-provided text, but system labels should stay clean Romanian

Scope:
Small formatting polish only.

Implement rules:
1. Discount block:
- Show discount code only if there is an actual discount:
  - discount_percent > 0 OR discount_amount > 0
- If only discount_code exists with no percent/amount, do not show it in public Telegram post.
- Keep raw values in grounding/debug if needed.

2. Remove technical sales/payment line from telegram_post_draft:
- Do not show:
  “Vanzare: ... · Plata: ...”
- Sales/payment data may stay in layout_hint.grounding_debug.

3. Program cleanup:
- Strip leading “Program:” label from program block.
- Remove embedded lines that start with:
  - “Inclus:”
  - “Include:”
  - “Included:”
  - “• Inclus:”
  - “✅ Include:”
- Do not remove supplier-provided normal program text.
- Included info should appear only in ✅ Include block.

4. Spacing:
- No leading spaces before “🔒”.
- Avoid double blank lines beyond intended section breaks.

5. Keep safe boundaries:
- no AI call
- no publish
- no Tour creation
- no Mini App catalog
- no booking/payment
- no lifecycle changes

Tests:
- discount code alone is not shown
- discount code + percent is shown
- discount code + amount is shown
- technical sales/payment line absent from Telegram draft
- program cleanup removes embedded Inclus lines
- no leading space before full_bus disclaimer
- existing B4/B4.1/B4.2 tests pass

Before coding:
1. summarize observed issues from offer #8 output
2. list files expected to change
3. explain why this is formatting-only and safe

After coding:
1. files changed
2. polish rules implemented
3. tests run
4. confirm no AI/publish/Tour/Mini App/booking/payment changes
5. next safe step: B4.3 or B5