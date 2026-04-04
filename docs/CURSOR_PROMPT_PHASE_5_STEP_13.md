Перед кодом (кратко)
Фаза: Phase 5 / Step 13 — support / handoff entry hardening

Почему идём сюда
- private chat + Mini App booking/payment flow уже работает
- success path, expiry path и chat cleanup уже усилены
- следующий важный MVP gap: пользователь должен иметь понятный и безопасный путь к помощи / человеку в сложных случаях
- по продуктовым требованиям handoff обязателен для сложных кейсов, а private chat и Mini App должны уметь вести пользователя к помощи без ложных обещаний

Что уже есть
- /help и /contact в private chat существуют
- Mini App имеет help/support entry points на UX-уровне
- сложные кейсы по проектным правилам уже определены (payment issue, discount, custom pickup, complaint, explicit request_human и т.д.)
- но нужно укрепить именно entry / presentation / initial handoff path, не переписывая весь operator workflow

Цель этого среза
Сделать понятный, безопасный и MVP-реалистичный support path:
1. private chat ясно предлагает помощь и человеческую эскалацию
2. Mini App на high-friction экранах даёт понятный support path
3. если реальный handoff creation path уже есть, использовать его
4. если full operator lifecycle ещё не готов, не обещать то, чего система пока не делает

Жёсткие границы scope
Не менять:
- payment core logic
- booking core logic
- schema / migrations, если можно избежать
- admin/operator full workflow
- waitlist
- Railway/webhook split
- group assistant broad logic
- real PSP integration

Разрешённый scope
- private bot help/contact/handoff entry behavior
- Mini App help/support presentation and CTA
- thin service-level handoff entry if a minimal real path already exists
- user-facing copy and classification for “needs human”
- docs
- узкие tests

Нужно сделать
1. Проанализировать, что уже есть в коде для handoff:
   - модели / сервисы / причины / приоритет
   - существует ли минимальный create_handoff path
2. Если минимальный реальный handoff path уже существует безопасно:
   - подключить его в узком MVP-срезе для private chat /contact or explicit “need human”
   - сохранять reason/category/context минимально и безопасно
3. Если full real handoff path ещё не готов:
   - не симулировать ложный handoff
   - дать честный user-facing support path:
     - contact guidance
     - clear next step
     - сохранение UX-consistency без ложного обещания “operator already assigned”
4. Усилить private chat:
   - /help
   - /contact
   - явный request human / support CTA where appropriate
5. Усилить Mini App:
   - support/help CTA на high-friction screens:
     - Payment
     - Booking Detail
     - History / expired released booking
   - тексты должны различать:
     - scripted help available now
     - human/operator path if applicable
6. Обновить локализацию en + ro
7. Обновить docs:
   - docs/PHASE_5_STEP_13_NOTES.md
   - docs/CHAT_HANDOFF.md
   - docs/PHASE_5_STEP_8_SMOKE_CHECK.md (короткий блок Step 13)

Ожидаемый результат
После реализации:
- пользователь в private chat и Mini App понимает, куда идти за помощью
- explicit “I need a human” / contact path не теряется
- система не обещает handoff, если полного handoff lifecycle ещё нет
- если реальный minimal handoff path уже существует, он используется честно и ограниченно

Предпочтительный подход
- сначала thin entry path, не full operator system
- не выдумывать новые доменные статусы
- reuse existing handoff reasons/categories if they already exist
- UX copy должен быть честным и коротким

Проверки
- py_compile изменённых файлов
- узкие unit tests на help/contact/handoff entry behavior
- ручной smoke:
  1. /help
  2. /contact
  3. явный request human in private chat
  4. support CTA from booking detail
  5. support CTA from payment / expired booking
- полный suite не запускать

Перед кодом сообщи кратко:
1. есть ли уже реальный minimal handoff create path
2. что будет сделано кодом, а что останется только честным UX/presentation
3. какой safe slice выбран

После кодирования отчитайся строго:
1. изменённые файлы
2. что изменено в private chat help/contact/handoff entry
3. что изменено в Mini App support path
4. используется ли реальный handoff create path или только UX guidance
5. как проверить Step 13 вручную
6. что осталось вне scope