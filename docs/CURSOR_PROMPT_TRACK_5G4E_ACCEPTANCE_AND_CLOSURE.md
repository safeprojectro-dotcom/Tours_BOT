Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после уже реализованных и проверенных Track 5g.4a–5g.4d.

Не начинай заново.
Не открывай новую архитектуру.
Не добавляй новую функциональность без необходимости.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не лезь в RFQ/bridge execution logic.
Не меняй payment-entry / reconciliation semantics.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- payment/reconciliation authority не меняется
- Mini App остаётся thin delivery layer
- service layer владеет policy/business rules
- UI не дублирует backend rules

Это соответствует текущему handoff и implementation plan: Mini App должен использовать существующие сервисы для reserve → payment → booking visibility, без нового payment/booking architecture.  
`MINI_APP_UX.md` также требует human-readable booking/payment states и ясный reserve/payment flow, а не raw backend statuses. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}

## Что уже считается завершённым

Считать уже закрытым и не переоткрывать:
- Track 5a–5f v1
- Track 5g, 5g.1, 5g.2, 5g.3
- Track 5g.4a — strict virgin-capacity hold semantics
- Track 5g.4b — payment continuation validation
- Track 5g.4c — Mode 2 UX/copy polish
- Track 5g.4d — booking visibility / human-readable state mapping

Фактически уже подтверждено:
1. Mode 2 self-serve whole-bus разрешён только при:
   - `seats_available == seats_total`
   - `seats_count = seats_total`
2. Partial full-bus inventory блокирует self-serve и оставляет assisted/manual catalog path
3. После valid Mode 2 virgin hold тот же Order идёт в тот же existing payment-entry path
4. Repeated payment-entry reuse работает по existing Layer A semantics
5. Mini App user-facing copy и booking visibility уже доведены до human-readable состояния
6. RFQ leakage в Mode 2 copy/booking visibility не должен появляться

## Exact next safe step

Implement only the closing acceptance/documentation slice:

# Track 5g.4e / Acceptance and closure

### Goal
Formally verify and record that the standalone catalog Mode 2 Mini App flow is now assembled end-to-end on top of Layer A, without reopening design or adding new product scope.

This is an acceptance / closure step.
Not a new feature step.
Not a design rewrite.
Not a marketplace step.

## What must be done

### 1. Acceptance summary for the completed Mode 2 slice
Create a short project-facing acceptance summary for Track 5g.4a–5g.4d, covering:
- what was implemented
- what user behavior is now supported
- what remains explicitly postponed
- compatibility / must-not-break notes

Keep it narrow and factual.

### 2. Verify end-to-end closure of the current Mode 2 path
Summarize and validate that the current standalone catalog Mode 2 path now covers:
- catalog/detail/preparation
- self-serve whole-bus hold only under virgin capacity
- payment continuation through existing payment-entry
- user-facing payment CTA/copy
- booking visibility / human-readable states

### 3. Confirm non-regression boundaries
Document that the slice did NOT change:
- Mode 1 semantics
- RFQ/bridge execution behavior
- payment reconciliation semantics
- supplier marketplace behavior
- charter pricing model
- admin flows

### 4. Update continuity docs only if needed
Only if the current docs materially need it, make narrow updates to:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- maybe a dedicated acceptance note doc if that is the cleanest path

Do not rewrite large sections.
Do not broaden scope.
Do not re-open already closed tracks.

### 5. Keep postponed items explicit
The closure step must clearly keep postponed:
- separate charter pricing model
- supplier-defined catalog Mode 2 policy path
- broader localization completion beyond current touched strings
- E2E/UI-runner coverage if not already present
- private bot charter UX expansion
- any RFQ/bridge CTA polish unless explicitly scheduled later

## Likely files/modules to touch

Prefer documentation only unless a tiny corrective test/doc adjustment is truly needed.

Expected likely files:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- optional new small doc such as:
  - `docs/TRACK_5G4_MODE2_ACCEPTANCE_SUMMARY.md`
  or similar

Optional tests only if a final focused regression/acceptance slice is truly useful.
Prefer not to touch production code unless an actual gap is found.

## What must NOT change

Do not change:
- production booking/payment logic
- service-layer policy
- API behavior unless a genuine acceptance blocker is found
- RFQ / bridge services
- my requests / 5f v1
- admin behavior
- waitlist
- handoff workflow
- Mini App auth/init
- charter pricing model
- supplier-defined Mode 2 execution policy
- private bot flows

## Before coding
Output briefly:
1. current state
2. what is already completed
3. exact next safe step
4. files likely to change
5. risks
6. what remains postponed

## Implementation constraints
- closure/doc step only
- prefer no production code changes
- prefer no migrations
- keep it short, factual, and compatible with current continuity
- do not turn this into a broad documentation rewrite
- do not reopen design discussions already settled in 5g.4a–5g.4d

## Tests required
Only if useful and very focused:
- one small acceptance/regression slice confirming no Mode 1 regression and no RFQ leakage, if not already sufficiently covered

If existing recent tests are already enough, say so and do not add pointless new ones.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run or not run
4. results
5. what is now formally accepted/closed
6. compatibility notes
7. postponed items

## Extra continuity note
This step is the closure of the current Mode 2 Mini App executable/catalog branch.
It is not permission to start a new design track.
Once complete, this branch should be considered closed unless a bug/regression is found.