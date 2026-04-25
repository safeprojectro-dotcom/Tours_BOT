You are continuing Tours_BOT project.

Previous step added heavy debug instrumentation for Mini App identity tracing.

Task:
Clean up debug noise and keep only safe, controlled logging.

==================================================
GOAL
==================================================

Remove all temporary debug instrumentation that was added for:

- tg_bridge_probe_* parameters
- excessive print/log statements
- noisy runtime tracing

But KEEP minimal safe logging that can be enabled via flag.

==================================================
RULES
==================================================

DO NOT:
- change identity logic
- change booking/payment logic
- change API contracts
- remove fail-closed behavior

==================================================
CLEANUP REQUIRED
==================================================

1. Remove:
- tg_bridge_probe_* injection in assets/index.html
- any debug-only URL params
- excessive print() or log lines without guard
- temporary diagnostic code blocks

2. Keep ONLY:

Add controlled logging like:

if settings.MINI_APP_DEBUG_TRACE:
    log.info(
        "mini_app_identity",
        extra={
            "route": route,
            "has_identity": bool(user_id),
            "source": source_label
        }
    )

3. Add flag in config:

MINI_APP_DEBUG_TRACE = False

==================================================
FILES TO CLEAN
==================================================

- assets/index.html
- mini_app/app.py
- mini_app/api_client.py
- app/api/routes/mini_app.py

==================================================
OUTPUT
==================================================

Before coding:
- what debug code exists
- what will be removed
- what will be kept

After coding:
- files changed
- logs removed vs kept
- confirmation that no debug noise remains
- confirmation that safe trace is behind flag

==================================================
IMPORTANT
==================================================

The system must behave exactly the same.

Only logging changes.