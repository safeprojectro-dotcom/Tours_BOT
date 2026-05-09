# Руководство оператора: supplier offer → каталог / showcase / конверсия

Краткий канонический порядок действий в центральном **Admin API**. Документ только справочный — изменений коду не задаёт.

---

## 1. Назначение

Это **единая рекомендуемая последовательность** для оператора: разбор оффера → при необходимости канал (showcase) → **`Tour`** в центральном каталоге Mini App → явная конверсия (**execution link**, лендинг, маршрут бота).

Серверные шлюзы уже безопасны и разделены (**упаковка**, **модерация**, **мост**, **`open_for_sale`**, **publish**, **ссылка исполнения** — разные сущности). Но **конечные точки фрагментированы**: порядок по памяти ошибочен.

Руководство нужно, чтобы **не опираться на память** и каждый раз явно сверяться с одним «окном наблюдения» перед мутациями.

**Цепочка конверсии (как в коде и смоках, C2B9B):** оффер **→** AI/admin packaging (`generate`, `approve` packaging) **→** модерация + готовность к publish (`review-package`, `conversion_closure`) **→** публикация showcase (**`POST …/publish`** **или** Telegram **Publică / Publish** при **`publish_showcase_channel.enabled`** — **C2B8B**, с двойным перечитыванием **`review-package`**) **→** явный мост **`Tour`** (**`POST …/tour-bridge`**, **`create_tour_bridge`**) **→** активация каталога при допустимости (**`POST …/tours/{id}/activate-for-catalog`**, **`activate_tour_for_catalog`**, guard **B8.3**) **→** создание/активация **execution link** (**`POST …/execution-link`**; в Telegram — мастер ссылок для **`published`**) **→** **B11** `/start supoffer_<id>` ведёт в **точный** тур Mini App **только** при активной ссылке **`+`** **`OPEN_FOR_SALE`** **`+`** видимости в каталоге **→** бронирование/оплата остаются **Layer A**. **Примечание:** в таблице §3 шаги **5–7** часто делают **до** канального **publish** (каталог может быть зелёным раньше ссылки); **execution link** после **`published`** (см. шаг **10**).

---

## 2. Золотое правило

**Всегда начинать с одного и того же чтения:**

```http
GET /admin/supplier-offers/{offer_id}/review-package
```

**`review-package`** — единая **сводка только для чтения**: оффер, **`conversion_closure`**, **`recommended_next_actions`**, **`warnings`**, **`bridge_readiness`**, **`linked_tour_catalog`**, **`showcase_preview`**, **`execution_links_review`**, **`mini_app_conversion_preview`**, **`content_quality_review`**, **`cover_media_quality_review`**, **`ai_public_copy_review`**.  

Ничего не меняет в базе и не шлёт Telegram — только наблюдение. Любой следующий **POST** — осознанное действие после проверки этой сводки.

Авторизация: **`Authorization: Bearer …`** или **`X-Admin-Token`** (как у остальных **`/admin/*`**).

---

## 3. Каноническая последовательность

Порядок столбцов: **Шаг → Что проверить (поля review-package и оффера) → Действие (endpoint) → Как проверить после → Замечание по безопасности**

| Шаг | Что проверить | Действие (endpoint) | Проверка после | Безопасность |
|-----|----------------|---------------------|----------------|--------------|
| 1 | **`conversion_closure.next_missing_step`**, **`warnings`**, **`content_quality_review`**, **`ai_public_copy_review`**, **`bridge_readiness`**, **`recommended_next_actions`** | Нет — только **`GET …/review-package`** | Ответ **200**, ясный следующий «пробел» по цепочке | Только чтение |
| 2 | При необходимости черновик упаковки (**packaging** не сгенерирован / устарел по процессу) | **`POST /admin/supplier-offers/{id}/packaging/generate`** | **`GET …/review-package`** или **`GET /admin/supplier-offers/{id}`** — статус упаковки | Не публикует в Telegram и не создаёт **`Tour`** |
| 3 | **`offer.packaging_status`**, блокеры **`bridge_readiness`** при отклонённой упаковке | **`POST …/packaging/approve`** (тело по контракту, при необходимости **`accept_warnings`**) | **`review-package`**: упаковка одобрена для материализации моста | Не lifecycle и не канал |
| 4 | **`lifecycle_status`**, готовность к модерации | **`POST …/moderation/approve`** (или **reject** по политике) | **`offer.lifecycle_status`**, **`review-package`** | Одобрение модерации ≠ публикация в канал |
| 5 | **`bridge_readiness.can_attempt_bridge`**, **`missing_fields`** | **`POST …/supplier-offers/{id}/tour-bridge`** | **`active_tour_bridge`**, **`tour_id`** в ответе | Повтор **POST** идемпотентен при том же мосте |
| 6 | **`linked_tour_catalog.can_activate_for_catalog`**, конфликт **B8.3** если есть | **`POST /admin/tours/{tour_id}/activate-for-catalog`** | **`status: open_for_sale`**, код тура | Каталог Mini App ≙ **`OPEN_FOR_SALE`**, не автомат из модерации |
| 7 | Центральный каталог видит тур (**опционально для смока**) | Нет POST — **`GET /mini-app/catalog`** (фильтры по необходимости) | В списке есть **`tour_code`** из шага 6 | Каталог может быть доступен **до** execution link |
| 8 | **`showcase_preview`**, **`can_publish_now`** если будете выводить в канал | **`GET …/showcase-preview`** | **`caption_html`**, предупреждения превью | Превью не отправляет в Telegram |
| 9 | Только если нужна публикация в канал и допускает копия/конфиг; **`operator_workflow.publish_showcase_channel`** | **`POST …/publish`** **или** Telegram **Publică / Publish** (**C2B8B**: подтверждение **`+`** дважды **`GET …/review-package`**) | **`lifecycle_status: published`**, при необходимости **`telegram_message_id`** | Реальный пост в канал; без конфига возможна **503** |
| 10 | **`execution_links_review.can_create_execution_link`**, причина предпроверки | **`POST …/execution-link`** с **`{ "tour_id": … }`** | **`GET …/execution-links`**, **`conversion_closure`** | Только при **`published`**; не подменяет Layer A |
| 11 | Полная конверсия (**landing**, бот **`supoffer_<id>`** → точный тур) | Нет нового POST — снова **`GET …/review-package`** и при необходимости **`GET /mini-app/supplier-offers/{id}`** | **`conversion_closure`**: флаги и **`next_missing_step: null`** | Landing и точный роут бота требуют активную ссылку исполнения + видимость каталога |

**Жёсткое правило порядка:** **`publish`** (если используете) → затем **`execution-link`** — иначе ссылка исполнения не создастся (**lifecycle** не **`published`**).

**Частый смок без канала:** шаги **9–10** можно помечать как «не выполнялись», если публикация в реальный канал по тексту/политике небезопасна — каталог при этом уже может быть «зелёным» по шагам **5–7**.

**Slice B (API):** ответ **`GET …/review-package`** содержит read-only **`operator_workflow`**: текущее **`state`**, **`primary_next_action`**, список **`actions`** с **`danger_level`** (**`safe_read`** / **`safe_mutation`** / **`conversion_enabling`** / **`public_dangerous`** — публикация showcase всегда **`public_dangerous`** при выключенном действии тоже), **`requires_confirmation`**, подсказки **`endpoint`**. Ничего не выполняется этим **GET**; кнопки Telegram / веб-админки / batch не добавляются.

**Slice C1 (Telegram admin-карточка):** текст карточки оффера в приватном admin-потоке (**`/admin_ops`** и др.) дополняется **только отображением** того же **`operator_workflow`**, собранного через **`SupplierOfferReviewPackageService.review_package()`**. Полная сводка по-прежнему только в **`GET …/review-package`**.

**Slice C1.1:** в Telegram блок **компактный** (без длинных **`endpoint`** и сырых **`danger_level`** в тексте): **`state`**, код следующего шага, короткие подписи риска/подтверждения, до трёх блокеров и трёх предупреждений (предпочтительно коды), короткий footer read-only.

**Slice C2A (Telegram — только безопасные кнопки):** inline-кнопки могут появиться только для кодов **`review_package_refresh`** и **`get_showcase_preview`** (из **`operator_workflow.actions`**, если **`enabled`**). Колбэки **не выполняют POST**: карточка перезагружается свежим **`review-package`**; превью showcase через **`SupplierOfferModerationService.showcase_preview`** (**ничего не отправляет в канал**). **C2A не включает** мутации packaging/модерации/showcase — они в **C2B1+**; **C2B8B** (**publish showcase**) — отдельное **публично-опасное** действие с подтверждением и двойным **`review-package`**.

**Политика UX кнопок Telegram (принята, docs-only):** карточка админа **не** консоль разработчика; подписи **1–2 слова**, по действию/результату; **не** snake_case, endpoints, enum, HTTP в тексте кнопок. Отключённые действия **`operator_workflow`** — **скрывать**, не показывать как disabled. Безопасное чтение — без подтверждения; безопасная мутация — подтверждение и повторное **`GET …/review-package`** перед выполнением; **публикация showcase** (**`publish_showcase_channel`**) — **два** перечитывания **`review-package`** (**C2B8B**). Ориентир подписей RO/EN: **`review_package_refresh`** → **Actualizează / Refresh**; **`get_showcase_preview`** → **Preview**; **`generate_packaging_draft`** → **Generează text** или **Pregătește**; **`approve_packaging_for_publish`** → **Aprobă text / Aprobă pachet** (не голое «Aprobă»); legacy модерация → **Aprobă oferta**, **Respinge oferta**; showcase publish → **Publică / Publish**. Порядок кнопок: наблюдение/чтение → packaging → legacy модерация → ops/publish → навигация. **На Telegram-карточке нет** кнопок **`create_tour_bridge`**, **`activate_tour_for_catalog`** (материализация/каталог — **Admin API**); **`create_execution_link`** — HTTP **или** мастер в Telegram при **`published`**; **publish showcase** — **есть** (**C2B8B**).

**Slice C2B3 (Telegram):** реализованы только короткие подписи RO/EN и логический порядок кнопок в карточке оффера (**observe/read → packaging → legacy модерация → showcase publish (если действие включено) → Orders/Requests → навигация**); дальнейшие мутационные колбэки добавлены отдельными слайсами (**C2B1–C2B8B**, **C2B6** — см. ниже). **`create_tour_bridge`** **/** **`activate_tour_for_catalog`** на карточке **нет** (**Admin API**).

**Slice C2B4:** Telegram **Preview**: при используемом **`cover_media_reference`** (**`telegram_photo:{file_id}`** или **HTTPS**) админ получает **`sendPhoto`** с тем же **`caption_html`**, что выдаёт **`build_showcase_publication`** (**GET …/showcase-preview** / будущий канал); только приватный чат админа; явное уведомление «локальная превью — не в канал»; без **`publish`**, без записи **`showcase_message_id`**. Нет фото / ошибка отправки — текстовый превью как раньше.

**Slice C2B5 / C2B8A:** В **`GET …/review-package`** добавлен read-only **`cover_media_quality_review`** и строки в **`warnings`** **`/`** **`operator_workflow.warnings`** (детерминированные сигналы по обложке и B7.1 **`media_review`**). **C2B8A:** **`publish_showcase_channel`** в **`operator_workflow`** выключено, пока упаковка не **`approved_for_publish`**, или пока активны «жёсткие» коды **`cover_media_quality_review`** (подмножество генератора **`evaluate_*`** **`;`** для режима **`photo_with_caption`** действуют дополнительные коды **`/`** для **`text_only`** они игнорируются **`;`** **`cover_media_missing_showcase_photo`** сам по себе не блокирует). **`POST …/publish`** не менялся.
**Slice C2B6:** В Telegram-карточке оффера — кнопка **«Cere poză» / Request photo** (если заполнен **`cover_media_reference`**): подтверждение в два шага **`+`** повторное чтение **`review-package`** перед выполнением **`;`** вызывает **`SupplierOfferMediaReviewService.request_replacement`** (фиксированная причина в аудите, **`reviewed_by = telegram:{admin_id}`**) **`;`** **не** меняет **`cover_media_reference`**, **не** трогает **`publish`**, **не** шлёт в канал **.**

**Slice C2B7.1:** Центральный **Admin API** — **`PUT /admin/supplier-offers/{offer_id}/cover`** **`(`** JSON **`cover_media_reference`** **`)`** задаёт только колонку **`SupplierOffer.cover_media_reference`** (или **`null`** для сброса)**;** без загрузки файлов**,** без **`publish`**, без изменения **`packaging_draft_json.media_review`** — после замены обложки при необходимости отдельно **`POST …/media/approve-for-card`**.

---

## Связанные документы

| Документ | Зачем |
|----------|--------|
| [`PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md) | Смок staging/prod, переменные окружения |
| [`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) | Превью и публикация showcase |
| [`ADMIN_CONTENT_QUALITY_GATE.md`](ADMIN_CONTENT_QUALITY_GATE.md) | Советы по качеству текста (**не блокирует API**) |
| [`AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md`](AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md) | Fact-lock для **`ai_public_copy_v1`** |
| *(UX)* | Политика подписей/порядка Telegram — см. абзац **«Политика UX кнопок Telegram»** выше |

---

## Контроль документа

| Поле | Значение |
|------|----------|
| **Тип** | Playbook Slice A + Slice B (**`operator_workflow`**) + Slice C1 / C1.1 / **C2A** / **C2B1** / **C2B2** / **C2B3** / **C2B4** / **C2B5** / **C2B6** (Telegram) + **C2B7.1** (**HTTP** **`PUT …/cover`**) + UX policy (подписи/порядок — см. §3) |
| **Язык** | Русский |
