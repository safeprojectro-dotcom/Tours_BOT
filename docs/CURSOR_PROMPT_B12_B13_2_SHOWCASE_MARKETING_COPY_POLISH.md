# CURSOR_PROMPT_B12_B13_2_SHOWCASE_MARKETING_COPY_POLISH

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a focused B12/B13.2 marketing copy polish step.

Do not change booking/payment/order/reservation logic.
Do not change Mini App UI.
Do not change Telegram publishing lifecycle.
Do not add media/photo publishing.
Do not add sendPhoto/sendMediaGroup.
Do not add object storage or Telegram download.
Do not change B11 routing.
Do not change B10.6 bot behavior.

---

## Current checkpoint

B12/B13.1 branded Romanian Telegram showcase text template was implemented.

Current template improved the post with:

- emoji sections
- title
- route/destination
- period/date
- price
- transport/capacity
- include/exclude
- disclaimer
- CTA lines

Manual review showed the structure is better, but marketing copy still needs polish.

Issues identified:

1. Price for fixed FULL_BUS offer must be clear and firm:
   - not “orientativ de la” when base_price/currency are known and offer is fixed full_bus.
   - should say: `Preț: 500 RON / grup`.

2. FULL_BUS must clearly mean whole bus / group package:
   - customer buys the whole bus/package.
   - individual seats are not sold separately.

3. Program section should appear when program/itinerary fields exist.
   - A tour post without program feels like transport-only.
   - But do not invent program items.

4. CTA should be short and strong:
   - one line:
     `ℹ️ Detalii | ✅ Rezervă`

5. Replace generic availability disclaimer with custom-request upsell:
   - `🧭 Ai nevoie de alt traseu sau alt număr de locuri? Cere o ofertă personalizată.`

6. Replace:
   - `ℹ️ Nu include:`
   with:
   - `❌ Nu include:`

---

## Target output style

For FULL_BUS fixed package, the Telegram post should look close to this:

```text
🚌 Tur privat: Timișoara → Cluj

📍 Ruta: Timișoara → Cluj
📅 28–29 aprilie 2026
🕘 Plecare: 21:00 · Întoarcere: 11:00

🗺️ Program:
• Plecare din Timișoara
• Deplasare spre Cluj
• Întoarcere spre Timișoara

💰 Preț: 500 RON / grup
🚌 Format: autocar întreg
👥 Capacitate: până la 80 persoane

ℹ️ Locurile individuale nu se vând separat.

✅ Include: transport
❌ Nu include: cheltuieli personale

🧭 Ai nevoie de alt traseu sau alt număr de locuri? Cere o ofertă personalizată.

ℹ️ Detalii | ✅ Rezervă