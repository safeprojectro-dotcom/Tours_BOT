Перед кодом (кратко)
Фаза: Phase 5 / Step 12B — reusable/editable Telegram home & catalog messages

Почему идём сюда
- Step 12A уже ввёл cleanup для transient service messages
- но в private chat всё ещё накапливаются старые ответы на команды /start и /tours
- пользователю по-прежнему кажется, что бот “засоряет” ленту
- нужен следующий safe шаг: не только чистить prompts, но и переиспользовать/обновлять основные service messages

Проблема
Сейчас home/catalog entry messages часто отправляются как новые сообщения.
Из-за этого в ленте остаются:
- старые /start ответы
- старые browse/catalog ответы
- старые CTA-карточки
даже если пользователь уже перешёл дальше.

Цель этого среза
Сделать Telegram private chat чище за счёт:
1. одного reusable home message
2. одного reusable catalog message
3. best-effort edit existing message instead of sending new
4. fallback delete+send only when edit is impossible

Жёсткие границы scope
Не менять:
- booking logic
- payment logic
- Mini App flow
- schema / migrations
- webhook
- admin/operator/waitlist
- business semantics of commands

Разрешённый scope
- app/bot/transient_messages.py
- app/bot/handlers/private_entry.py
- app/bot/messages.py
- app/bot/keyboards.py
- при необходимости небольшой helper для edit-or-replace logic
- docs
- узкие unit tests

Минимальный safe slice
1. Выделить 2 главные message-категории:
   - HOME_MESSAGE
   - CATALOG_MESSAGE
2. Для /start и /tours:
   - если есть ранее зарегистрированное service message этого типа в текущем chat/user flow, сначала попытаться edit_message_text / edit_message_reply_markup
   - если edit невозможен (message deleted, too old, wrong content type, Telegram error) — fallback:
     a) попытаться удалить старое
     b) отправить новое
     c) зарегистрировать новый id
3. Сохранить текущий cleanup transient prompts из Step 12A
4. Не редактировать и не удалять:
   - user messages
   - payment success
   - booking confirmations
   - help/contact meaningful replies
   - booking detail style informational anchors
5. Не пытаться охватить вообще все команды — только /start и /tours как самые шумные

Ожидаемый результат
- повторный /start не плодит длинную ленту одинаковых home messages
- повторный /tours не плодит длинную ленту одинаковых catalog responses
- private chat становится ближе к “одному живому экрану” внутри Telegram
- важные итоговые сообщения не исчезают

Предпочтительный подход
- использовать best-effort edit, не ломая flow
- если нельзя edit — fallback на delete+send
- не делать сложную persistent storage, достаточно текущего in-memory transient registry
- логика должна быть безопасной и молча деградировать, а не ломать UX

Проверки
- py_compile изменённых файлов
- узкие unit tests для:
  - store/register of home/catalog message ids
  - edit-or-replace helper behavior where practical
- ручной smoke:
  1. /start несколько раз -> в чате не копится много стартовых блоков
  2. /tours несколько раз -> старый каталог не остаётся пачкой
  3. важные итоговые сообщения по-прежнему остаются
  4. /language и filter cleanup из Step 12A не ломаются
- полный suite не запускать

Перед кодом сообщи кратко:
1. как будут храниться reusable home/catalog message ids
2. какой fallback при неудачном edit

После кодирования отчитайся строго:
1. изменённые файлы
2. какие сообщения теперь edit/reuse вместо нового send
3. как работает fallback logic
4. что специально не трогается
5. как проверить Step 12B вручную
6. что осталось вне scope