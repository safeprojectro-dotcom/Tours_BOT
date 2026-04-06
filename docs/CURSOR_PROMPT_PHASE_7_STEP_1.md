Продолжаем Tours_BOT от последнего approved checkpoint.

Используй как source of truth:
1. docs/IMPLEMENTATION_PLAN.md
2. docs/CHAT_HANDOFF.md
3. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
4. docs/PHASE_6_REVIEW.md
5. docs/TESTING_STRATEGY.md
6. docs/AI_ASSISTANT_SPEC.md
7. docs/AI_DIALOG_FLOWS.md
8. docs/TECH_SPEC_TOURS_BOT.md
9. docs/TELEGRAM_SETUP.md

Контекст:
- Phase 6 review accepted
- current checkpoint is after Phase 6 stabilization
- admin/handoff/order surfaces already exist
- public booking/payment flows must remain untouched
- next phase is Phase 7: Group Assistant And Operator Handoff

Текущая задача:
Phase 7 / Step 1

Нужен только один узкий safe slice:
GROUP BEHAVIOR + HANDOFF RULES FOUNDATION (documentation-first)

Важно:
это НЕ full Telegram group implementation yet.
Это first safe slice to define the operational rules before coding group bot behavior.

Что именно сделать:
1. Create one dedicated document:
   - `docs/GROUP_ASSISTANT_RULES.md`

2. In that document, define the narrow operational foundation for Phase 7:
   - allowed group triggers:
     - mentions
     - approved commands
     - approved trigger phrases
   - forbidden behavior:
     - no private data collection in group
     - no long personal negotiation in group
     - no payment-sensitive discussion in group
     - no answering every message
   - CTA strategy:
     - route to private chat
     - route to Mini App when appropriate
   - anti-spam principles
   - handoff trigger categories for group/private:
     - discount request
     - group booking
     - custom pickup
     - complaint
     - unclear payment issue
     - explicit human request
     - low-confidence answer
   - minimal operator continuity requirements:
     - preserve context
     - preserve language
     - preserve reason/category

3. Align this document explicitly with:
   - docs/AI_ASSISTANT_SPEC.md
   - docs/AI_DIALOG_FLOWS.md
   - docs/TELEGRAM_SETUP.md
   - Phase 7 in docs/IMPLEMENTATION_PLAN.md

4. Update `docs/CHAT_HANDOFF.md`
Reflect that:
- Phase 7 / Step 1 completed
- current phase is now Phase 7
- next safe step should be a first narrow implementation slice for actual group trigger evaluation / handoff trigger helper logic

5. Optional tiny doc cleanup only if needed:
- if docs/TELEGRAM_SETUP.md needs a very small alignment note for group assumptions, add only a minimal documentation update
- do not widen this into real Telegram setup or webhook implementation

Жёсткие правила:
- no production code changes unless absolutely tiny and documentation-related
- no bot runtime behavior changes yet
- no new API endpoints
- no admin/payment/public flow changes
- do not start real operator workflow engine here
- this step is primarily documentation-first foundation

Перед началом кратко зафиксируй:
1. текущее состояние проекта
2. почему Phase 7 starts with documentation-first foundation
3. что сейчас нельзя трогать

После выполнения дай отчёт:
1. какие документы созданы/изменены
2. что зафиксировано в GROUP_ASSISTANT_RULES.md
3. как обновлён CHAT_HANDOFF.md
4. какой Next Safe Step теперь указан
5. подтверждение, что production code and public flows were not changed