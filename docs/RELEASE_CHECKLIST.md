# Release Checklist

## Purpose
Track the minimum release checks required before production deployment of Tours_BOT.

## Environment
- [ ] local validated
- [ ] staging validated
- [ ] production env vars prepared

## Database
- [ ] migrations tested locally
- [ ] migrations tested on staging
- [ ] PostgreSQL connectivity verified
- [ ] rollback approach understood

## Backend
- [ ] app starts successfully
- [ ] `/health` works
- [ ] `/healthz` works
- [ ] logging works

## Telegram
- [ ] bot token configured correctly
- [ ] webhook configured correctly
- [ ] private chat works
- [ ] group behavior checked
- [ ] Mini App launch works
- [ ] deep links checked

## Payments
- [ ] payment sandbox verified
- [ ] payment status updates verified
- [ ] failed payment path checked

## Booking
- [ ] reservation flow works
- [ ] reservation expiry works
- [ ] waitlist flow checked
- [ ] status transitions checked

## Admin
- [ ] admin access checked
- [ ] critical actions logged
- [ ] content approval flow checked

## Multilingual
- [ ] default language works
- [ ] fallback works
- [ ] no broken mixed-language states

## Final
- [ ] smoke test completed
- [ ] rollback plan reviewed
- [ ] known limitations documented
