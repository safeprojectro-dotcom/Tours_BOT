# HANDOFF_B7_3A_MEDIA_POLICY_ACCEPTANCE_TO_NEXT_STEP

Project: Tours_BOT

## Current checkpoint

B7.3 media pipeline policy has been accepted and documented.

B7 status:
- B7.1 media review metadata completed.
- B7.2 card render preview plan completed.
- B7.3A media policy acceptance completed.
- B7.3 implementation pipeline is still not implemented.

## Accepted B7.3 policy

- Raw supplier media is not publish-safe.
- Telegram file_id / telegram_photo:{file_id} is not a stable public URL.
- approved_for_card is not the same as publish_safe.
- publish_safe is not the same as published.
- Publication remains a separate explicit admin action.
- Railway local filesystem must not be used as canonical durable storage.
- Durable publish-safe media should use future object storage/S3-compatible storage if/when download/storage is explicitly scoped.
- AI/card prompt/render preview JSON is metadata, not binary media.
- Fallback branded card may remain a placeholder/planned derived asset until renderer/storage exists.
- Mini App execution truth must remain independent of marketing media.

## Not implemented

- Telegram getFile/download.
- durable object storage.
- real public URL lifecycle.
- real card rendering.
- Telegram sendPhoto/sendMediaGroup.
- automatic publish.
- Mini App media UI redesign.
- B10.6 bot router/consultant redesign.
- B11 deep-link routing.
- B12/B13 template/channel adapter layer.

## Next safe options

Choose explicitly:

1. B7.3B — metadata-only publish_safe stub in packaging_draft_json; no download/storage.
2. B7.4 — storage abstraction design/implementation, only if object storage policy is selected.
3. B11 — Telegram deep-link routing.
4. B10.6 — Telegram bot router/consultant redesign.
5. B12/B13 — marketing template library / channel adapters.

Do not start any next step automatically.