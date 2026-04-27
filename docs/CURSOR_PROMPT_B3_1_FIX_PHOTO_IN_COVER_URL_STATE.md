Fix B3.1 supplier offer cover photo intake.

Problem:
When supplier clicks “Trimite URL imagine”, FSM moves to entering_cover_url.
If supplier then sends a Telegram photo, bot still expects HTTPS URL and rejects/ignores it.

Expected:
Telegram photo must be accepted in both:
- choosing_cover_media
- entering_cover_url

Scope:
- small bugfix only
- update photo handler/state filters
- reuse existing photo validation and storage logic
- update/add tests

Must NOT:
- add gallery
- download files
- change publish behavior
- create Tour
- touch Mini App
- touch booking/payment
- add AI

Tests:
- photo accepted from choosing_cover_media
- photo accepted from entering_cover_url
- invalid document still rejected
- URL path still works
- no photo path still works

After coding:
- files changed
- tests run
- confirm bug fixed